# inference/services/ml_infer.py
from pathlib import Path
import pickle
import numpy as np
import tensorflow as tf
import ffmpeg, librosa, soundfile as sf
from django.conf import settings

# Pipeline helpers
from inference.pipeline.Trimming_Video_Audio_Extraction import trim_video_to_speech
from inference.pipeline.Audio_Feature_Extraction import extract_features as extract_audio_features
from inference.pipeline.Video_Feature_Extraction import process_video

# =========================
# Keras 3 shims for legacy H5 configs
# (drop unsupported kwargs like batch_input_shape/time_major)
# We also REGISTER these classes so Keras can locate them by name.
# =========================
@tf.keras.utils.register_keras_serializable(package="Legacy")
class LegacyGRU(tf.keras.layers.GRU):
    @classmethod
    def from_config(cls, config):
        config.pop("batch_input_shape", None)
        config.pop("time_major", None)
        return super().from_config(config)

@tf.keras.utils.register_keras_serializable(package="Legacy")
class LegacyLSTM(tf.keras.layers.LSTM):
    @classmethod
    def from_config(cls, config):
        config.pop("batch_input_shape", None)
        config.pop("time_major", None)
        return super().from_config(config)

# =========================
# Cached globals
# =========================
_LOADED = False
_FUSION = None
_CLASS_NAMES = None
_LANDMARK_SCALER = None
_LANDMARK_PCA = None
_VISUAL_SCALER = None
_VISUAL_PCA = None

# =========================
# Constants (must match training)
# =========================
MAX_T = 422                 # audio temporal length fed to fusion model
NUM_FRAMES = 30             # number of frames per clip after interpolation
EXPECTED_VIDEO_FEATURE_DIM = 54  # (landmark_pca + visual_pca) per-frame dim
EXPECTED_AUDIO_FEATURES = 1080   # audio feature count (F dimension)

# =========================
# Helpers
# =========================
def _pkl(p: Path):
    with open(p, "rb") as f:
        return pickle.load(f)

def _ensure_wav(video_path: Path, wav_path: Path):
    """
    Extract mono 16k WAV from video if missing, then trim/pad to ~0.42s (training window).
    """
    if not wav_path.exists():
        stream = ffmpeg.input(str(video_path))
        stream = ffmpeg.output(
            stream, str(wav_path),
            format="wav", ar=16000, ac=1, vn=None, loglevel="error"
        )
        ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)

    y, sr = librosa.load(wav_path, sr=16000, mono=True)
    tgt = int(0.42 * sr)
    if len(y) > tgt:
        y = y[:tgt]
    elif len(y) < tgt:
        y = np.pad(y, (0, tgt - len(y)))
    sf.write(wav_path, y, sr)

# =========================
# Loader (runs once per process)
# =========================
def load_once():
    """
    Load models/scalers once per process (Keras 3/TF 2.16 compatible).
    """
    global _LOADED, _FUSION, _CLASS_NAMES, _LANDMARK_SCALER, _LANDMARK_PCA, _VISUAL_SCALER, _VISUAL_PCA
    if _LOADED:
        return

    art = Path(settings.INFER_ARTIFACTS_DIR)

    # Keras 3 compatibility: map legacy names to shim classes
    custom = {
        # provide both legacy and original names
        "GRU": LegacyGRU,
        "LegacyGRU": LegacyGRU,
        "LSTM": LegacyLSTM,
        "LegacyLSTM": LegacyLSTM,
        # wrappers
        "Bidirectional": tf.keras.layers.Bidirectional,
        "TimeDistributed": tf.keras.layers.TimeDistributed,
        # regularizers sometimes serialized as 'L2'/'l2'
        "L2": tf.keras.regularizers.L2,
        "l2": tf.keras.regularizers.l2,
    }

    # Models
    _FUSION = tf.keras.models.load_model(art / "final_model.h5", custom_objects=custom, compile=False)

    # Artifacts
    _CLASS_NAMES     = np.load(art / "label_encoder_classes.npy", allow_pickle=True)
    _LANDMARK_SCALER = _pkl(art / "landmark_scaler.pkl")
    _LANDMARK_PCA    = _pkl(art / "landmark_pca.pkl")
    _VISUAL_SCALER   = _pkl(art / "visual_scaler.pkl")
    _VISUAL_PCA      = _pkl(art / "visual_pca.pkl")

    _LOADED = True

# =========================
# Public API
# =========================
def predict_from_video(video_file: str | Path) -> dict:
    """
    Returns:
      {
        'top_class': str,
        'probs': [{'label': str, 'p': float}, ...]
      }
    """
    load_once()

    video_path = Path(video_file)
    out_dir = Path(settings.INFER_RUNTIME_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Trim to speech (produces <stem>_speech.mp4)
    trimmed = trim_video_to_speech(str(video_path), str(out_dir))
    if not trimmed:
        cand = out_dir / f"{video_path.stem}_speech.mp4"
        if not cand.exists():
            raise RuntimeError("Trimming failed; no output produced")
        trimmed = str(cand)
    trimmed_path = Path(trimmed)

    # 2) Audio features
    wav_path = out_dir / f"{video_path.stem}_audio.wav"
    _ensure_wav(video_path, wav_path)

    a_feat = extract_audio_features(str(wav_path))  # (F, T)
    if a_feat.shape[0] != EXPECTED_AUDIO_FEATURES:
        raise RuntimeError(f"Audio features first dim must be {EXPECTED_AUDIO_FEATURES}, got {a_feat.shape}")
    T = a_feat.shape[1]
    if T < MAX_T:
        a_feat = np.pad(a_feat, ((0, 0), (0, MAX_T - T)))
    elif T > MAX_T:
        a_feat = a_feat[:, :MAX_T]
    a_in = a_feat[None, ...].transpose(0, 2, 1)  # (1, MAX_T, F)

    # 3) Visual/landmark features via process_video -> saves npy files
    process_video(
        str(trimmed_path),
        str(out_dir / video_path.stem),  # frames/debug folder
        str(out_dir),                    # landmark features here
        str(out_dir),                    # visual features here
        is_first_video=True,
        plot=False
    )

    vid_feat_path = out_dir / f"{trimmed_path.stem}_features.npy"
    vis_feat_path = out_dir / f"{trimmed_path.stem}_visual_features.npy"
    if not vid_feat_path.exists():
        raise FileNotFoundError(f"Missing landmark features: {vid_feat_path}")
    if not vis_feat_path.exists():
        raise FileNotFoundError(f"Missing visual features: {vis_feat_path}")

    video_features  = np.load(vid_feat_path)   # (30, 276) -> transformed by PCA below
    visual_features = np.load(vis_feat_path)   # (30, 512) (zeros if visual backbone missing)

    # 4) scale + pca + concat
    video_features  = _LANDMARK_SCALER.transform(video_features)
    video_features  = _LANDMARK_PCA.transform(video_features)
    visual_features = _VISUAL_SCALER.transform(visual_features)
    visual_features = _VISUAL_PCA.transform(visual_features)

    combined = np.concatenate([video_features, visual_features], axis=-1)  # (30, 54)
    if combined.shape != (NUM_FRAMES, EXPECTED_VIDEO_FEATURE_DIM):
        raise RuntimeError(f"Expected {(NUM_FRAMES, EXPECTED_VIDEO_FEATURE_DIM)}, got {combined.shape}")

    v_in = combined[None, ...]  # (1, 30, 54)

    # 5) Predict
    probs = _FUSION.predict([a_in, v_in], verbose=0)[0]
    top = int(np.argmax(probs))
    return {
        "top_class": str(_CLASS_NAMES[top]),
        "probs": [{"label": str(_CLASS_NAMES[i]), "p": float(p)} for i, p in enumerate(probs)]
    }

import os
from pathlib import Path

import cv2
import dlib
import numpy as np
from scipy.spatial import procrustes
from scipy.spatial.distance import euclidean
from numpy.polynomial.polynomial import Polynomial
from itertools import combinations

import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import torch.nn as nn

# =========================
# Settings & artifact paths
# =========================
try:
    from django.conf import settings
    ART = Path(getattr(settings, "INFER_ARTIFACTS_DIR", Path(__file__).resolve().parents[1] / "ml_artifacts"))
    RUNTIME = Path(getattr(settings, "INFER_RUNTIME_DIR", Path(__file__).resolve().parents[1] / "_runtime"))
    DLIB_PATH = Path(getattr(settings, "DLIB_SHAPE_PREDICTOR_PATH", ART / "shape_predictor_68_face_landmarks.dat"))
    REF_LANDMARKS_PATH = Path(getattr(settings, "REFERENCE_LANDMARKS_PATH", ART / "reference_landmarks.npy"))
    REF_EYE_DIST_PATH  = Path(getattr(settings, "REFERENCE_EYE_DIST_PATH", ART / "reference_inter_eye_distance.npy"))
except Exception:
    ART = Path(__file__).resolve().parents[1] / "ml_artifacts"
    RUNTIME = Path(__file__).resolve().parents[1] / "_runtime"
    DLIB_PATH = ART / "shape_predictor_68_face_landmarks.dat"
    REF_LANDMARKS_PATH = ART / "reference_landmarks.npy"
    REF_EYE_DIST_PATH  = ART / "reference_inter_eye_distance.npy"

RUNTIME.mkdir(parents=True, exist_ok=True)
PLOTS_DIR = RUNTIME / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
plot_output_dir = str(PLOTS_DIR)  # used only if plot=True

# =========================
# Headless plotting (optional)
# =========================
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None

# =========================
# Dlib detector / predictor
# =========================
if not DLIB_PATH.exists():
    raise FileNotFoundError(f"dlib shape predictor not found at: {DLIB_PATH}")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(str(DLIB_PATH))

# =========================
# Optional reference helpers (if you pre-created them)
# These are *not* required; process_video can set reference on first frame.
# =========================
REFERENCE_LANDMARKS = np.load(REF_LANDMARKS_PATH) if REF_LANDMARKS_PATH.exists() else None
REFERENCE_INTER_EYE_DISTANCE = float(np.load(REF_EYE_DIST_PATH)[0]) if REF_EYE_DIST_PATH.exists() else None
REFERENCE_SET = (REFERENCE_LANDMARKS is not None) and (REFERENCE_INTER_EYE_DISTANCE is not None)

# =========================
# Constants
# =========================
BASE_OUTPUT_SIZE = (128, 128)
NUM_FRAMES = 30
NORM_BOX_WIDTH = 1.2
NORM_BOX_HEIGHT = 0.8
DISPARITY_THRESHOLD = 0.02
VISUAL_FEATURE_DIM = 512  # resnet18 penultimate feature size

# =========================
# Visual backbone (optional, safe fallback to zeros)
# =========================
PRETRAINED_PATH = ART / "lrw_resnet18_dctcn_video.pth"
pretrained_model_path = str(PRETRAINED_PATH)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

feature_extractor = None
try:
    if Path(pretrained_model_path).exists() and Path(pretrained_model_path).stat().st_size > 1024:
        model = models.resnet18(weights=None)  # no internet fetch
        model.fc = nn.Linear(model.fc.in_features, 500)

        # Safe checkpoint loading (works across torch versions)
        try:
            checkpoint = torch.load(pretrained_model_path, map_location=device, weights_only=True)  # torch>=2.2
        except TypeError:
            checkpoint = torch.load(pretrained_model_path, map_location=device)

        state_dict = checkpoint.get('model_state_dict', checkpoint)
        model_dict = model.state_dict()
        state_dict = {k: v for k, v in state_dict.items() if k in model_dict and model_dict[k].shape == v.shape}
        model_dict.update(state_dict)
        model.load_state_dict(model_dict, strict=False)
        model = model.to(device).eval()

        class ResNetFeatureExtractor(nn.Module):
            def __init__(self, m):
                super().__init__()
                self.features = nn.Sequential(*list(m.children())[:-1])  # remove final fc
            def forward(self, x):
                x = self.features(x)
                return x.view(x.size(0), -1)  # (B, 512)

        feature_extractor = ResNetFeatureExtractor(model).to(device).eval()
        print(f"[INFO] Visual backbone loaded from {pretrained_model_path}")
    else:
        print(f"[WARN] Visual weights missing or too small at {pretrained_model_path}. Using zero visual features.")
except Exception as e:
    print(f"[WARN] Failed to load visual backbone: {e}. Using zero visual features.")
    feature_extractor = None

# image transform used for visual backbone (defined regardless)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# =========================
# Helpers
# =========================
def preprocess_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)
    equalized = cv2.equalizeHist(filtered)
    return equalized

def landmarks_to_array(landmarks):
    return np.array([[landmarks.part(i).x, landmarks.part(i).y] for i in range(68)])

def array_to_landmarks(array, rect):
    array = np.clip(array, 0, max(rect.width(), rect.height()))
    array = np.where(np.isfinite(array), array, 0)
    points = [dlib.point(int(x), int(y)) for x, y in array]
    return dlib.full_object_detection(rect, dlib.points(points))

def get_inter_eye_distance(landmarks):
    left_eye = (landmarks.part(36).x, landmarks.part(36).y)
    right_eye = (landmarks.part(45).x, landmarks.part(45).y)
    return euclidean(left_eye, right_eye)

def normalize_landmarks(landmarks_array, inter_eye_distance):
    norm_landmarks = landmarks_array / inter_eye_distance
    centroid = np.mean(norm_landmarks, axis=0)
    return norm_landmarks - centroid, centroid

def plot_landmarks_before_after(frame, original_landmarks, aligned_landmarks, video_name, frame_idx):
    if plt is None:
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    ax1.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    for i in range(68):
        x, y = original_landmarks.part(i).x, original_landmarks.part(i).y
        ax1.plot(x, y, 'ro', markersize=2)
    ax1.set_title(f"Before Alignment (Frame {frame_idx})"); ax1.axis('off')

    ax2.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    for i in range(68):
        x, y = aligned_landmarks.part(i).x, aligned_landmarks.part(i).y
        ax2.plot(x, y, 'bo', markersize=2)
    ax2.set_title(f"After Alignment (Frame {frame_idx})"); ax2.axis('off')

    plt.suptitle(f"Video: {video_name}")
    plt.tight_layout()
    os.makedirs(plot_output_dir, exist_ok=True)
    plot_path = os.path.join(plot_output_dir, f"{video_name}_frame_{frame_idx:04d}.png")
    try:
        plt.savefig(plot_path)
        print(f"Saved alignment plot: {plot_path}")
    except Exception as e:
        print(f"Failed to save plot {plot_path}: {e}")
    finally:
        plt.close()

def compute_curvature(points):
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    poly = Polynomial.fit(x, y, 2)
    deriv1 = poly.deriv(1)
    deriv2 = poly.deriv(2)
    curvature = np.mean([abs(deriv2(x[i])) / (1 + deriv1(x[i])**2)**1.5 for i in range(len(x))])
    return curvature

def compute_lip_distances(norm_landmarks):
    lip_points = norm_landmarks[48:68]
    distances = [euclidean(p1, p2) for (p1, p2) in combinations(lip_points, 2)]
    return np.array(distances)

def extract_features(curr_frame, prev_frame, curr_norm_landmarks, prev_norm_landmarks):
    curr_norm_pts = curr_norm_landmarks
    curr_width = euclidean(curr_norm_pts[48], curr_norm_pts[54])
    curr_height = euclidean(curr_norm_pts[51], curr_norm_pts[57])
    geometric = [0, 0]
    if prev_norm_landmarks is not None:
        prev_norm_pts = prev_norm_landmarks
        prev_width = euclidean(prev_norm_pts[48], prev_norm_pts[54])
        prev_height = euclidean(prev_norm_pts[51], prev_norm_pts[57])
        geometric = [curr_width - prev_width, curr_height - prev_height]
    else:
        prev_norm_pts = None

    curr_upper = [curr_norm_pts[i] for i in range(48, 55)]
    curr_lower = [curr_norm_pts[i] for i in range(54, 60)] + [curr_norm_pts[48]]
    curr_inner = [curr_norm_pts[i] for i in range(60, 68)]
    curr_outer = [curr_norm_pts[i] for i in range(48, 60)]
    curr_curvatures = [
        compute_curvature(curr_upper),
        compute_curvature(curr_lower),
        compute_curvature(curr_inner),
        compute_curvature(curr_outer),
    ]
    curvature_features = [0, 0, 0, 0]
    if prev_norm_pts is not None:
        prev_upper = [prev_norm_pts[i] for i in range(48, 55)]
        prev_lower = [prev_norm_pts[i] for i in range(54, 60)] + [prev_norm_pts[48]]
        prev_inner = [prev_norm_pts[i] for i in range(60, 68)]
        prev_outer = [prev_norm_pts[i] for i in range(48, 60)]
        prev_curvatures = [
            compute_curvature(prev_upper),
            compute_curvature(prev_lower),
            compute_curvature(prev_inner),
            compute_curvature(prev_outer),
        ]
        curvature_features = [c - p for c, p in zip(curr_curvatures, prev_curvatures)]

    flow_features = np.zeros(40)
    if prev_norm_pts is not None:
        curr_pts = np.array([curr_norm_pts[i] for i in range(48, 68)], dtype=np.float32)
        prev_pts = np.array([prev_norm_pts[i] for i in range(48, 68)], dtype=np.float32)
        flow_features = (curr_pts - prev_pts).flatten()

    landmark_features = np.zeros(40)
    if prev_norm_pts is not None:
        landmark_diff = [(c[0] - p[0], c[1] - p[1]) for c, p in zip(curr_norm_pts[48:68], prev_norm_pts[48:68])]
        landmark_features = np.array(landmark_diff).flatten()

    curr_lip_distances = compute_lip_distances(curr_norm_pts)
    if prev_norm_pts is not None:
        prev_lip_distances = compute_lip_distances(prev_norm_pts)
        lip_distance_features = curr_lip_distances - prev_lip_distances
    else:
        lip_distance_features = curr_lip_distances

    combined = np.concatenate([geometric, curvature_features, flow_features, landmark_features, lip_distance_features])
    return combined

def extract_visual_features(frames):
    """Return (N, 512) features; zeros if visual backbone unavailable."""
    if feature_extractor is None:
        return np.zeros((len(frames), VISUAL_FEATURE_DIM), dtype=np.float32)
    visual_features = []
    for frame in frames:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        input_tensor = transform(pil_image).unsqueeze(0).to(device)
        with torch.no_grad():
            features = feature_extractor(input_tensor)
        visual_features.append(features.cpu().numpy().flatten())
    return np.array(visual_features)

def interpolate_frames(frames, landmarks_list, norm_landmarks_list, total_frames, target_frames=NUM_FRAMES):
    if total_frames == 0:
        return [], [], []
    if total_frames >= target_frames:
        idx = np.linspace(0, total_frames - 1, target_frames, dtype=int)
        return [frames[i] for i in idx], [landmarks_list[i] for i in idx], [norm_landmarks_list[i] for i in idx]

    x_new = np.linspace(0, total_frames - 1, target_frames)
    out_frames, out_landmarks, out_norm = [], [], []
    for t in x_new:
        i = int(t); frac = t - i
        if i + 1 < len(frames):
            frame = cv2.addWeighted(frames[i], 1 - frac, frames[i + 1], frac, 0)
            interp_points = []
            for j in range(68):
                x = int((1 - frac) * landmarks_list[i].part(j).x + frac * landmarks_list[i + 1].part(j).x)
                y = int((1 - frac) * landmarks_list[i].part(j).y + frac * landmarks_list[i + 1].part(j).y)
                interp_points.append(dlib.point(x, y))
            rect = dlib.rectangle(0, 0, frame.shape[1], frame.shape[0])
            landmarks = dlib.full_object_detection(rect, dlib.points(interp_points))
            norm_lm = (1 - frac) * norm_landmarks_list[i] + frac * norm_landmarks_list[i + 1]
        else:
            frame = frames[-1]
            landmarks = landmarks_list[-1]
            norm_lm = norm_landmarks_list[-1]
        out_frames.append(frame); out_landmarks.append(landmarks); out_norm.append(norm_lm)
    return out_frames, out_landmarks, out_norm

def crop_mouth_region(frame, landmarks=None, video_name=None, frame_idx=None, plot=False, is_reference_frame=False):
    """Return (crop, aligned_landmarks, aligned_norm_landmarks) or (None, None, None)."""
    global REFERENCE_LANDMARKS, REFERENCE_INTER_EYE_DISTANCE, REFERENCE_SET
    preprocessed = preprocess_frame(frame)

    if landmarks is None:
        rects = detector(preprocessed, 1)
        if len(rects) == 0:
            return None, None, None
        rect = rects[0]
        landmarks = predictor(preprocessed, rect)
    else:
        rect = dlib.rectangle(0, 0, frame.shape[1], frame.shape[0])

    original_landmarks = landmarks
    current_landmarks = landmarks_to_array(landmarks)
    curr_inter_eye_distance = get_inter_eye_distance(original_landmarks)
    norm_current_landmarks, norm_centroid = normalize_landmarks(current_landmarks, curr_inter_eye_distance)

    if is_reference_frame and not REFERENCE_SET:
        REFERENCE_LANDMARKS = norm_current_landmarks
        REFERENCE_INTER_EYE_DISTANCE = 1.0
        REFERENCE_SET = True
        aligned_norm_landmarks = norm_current_landmarks
        aligned_landmarks_array = current_landmarks
    else:
        if REFERENCE_LANDMARKS is None:
            return None, None, None
        _, mtx2, disparity = procrustes(REFERENCE_LANDMARKS, norm_current_landmarks)
        if disparity > DISPARITY_THRESHOLD:
            return None, None, None
        aligned_norm_landmarks = mtx2
        aligned_landmarks_array = aligned_norm_landmarks * curr_inter_eye_distance
        curr_centroid = np.mean(current_landmarks, axis=0)
        aligned_centroid = np.mean(aligned_landmarks_array, axis=0)
        shift = curr_centroid - aligned_centroid
        aligned_landmarks_array += shift
        if not np.all(np.isfinite(aligned_landmarks_array)):
            return None, None, None

    # compute crop box in original pixel space using normalized lips region
    norm_lip_points = aligned_norm_landmarks[48:68]
    norm_mid_x = np.mean(norm_lip_points[:, 0])
    norm_mid_y = np.mean(norm_lip_points[:, 1])
    norm_half_w = NORM_BOX_WIDTH / 2
    norm_half_h = NORM_BOX_HEIGHT / 2

    x1 = int((norm_mid_x - norm_half_w) * curr_inter_eye_distance + norm_centroid[0])
    y1 = int((norm_mid_y - norm_half_h) * curr_inter_eye_distance + norm_centroid[1])
    x2 = int((norm_mid_x + norm_half_w) * curr_inter_eye_distance + norm_centroid[0])
    y2 = int((norm_mid_y + norm_half_h) * curr_inter_eye_distance + norm_centroid[1])

    # tweak margins
    x1 = max(0, x1 + 10); y1 = max(0, y1 + 60)
    x2 = min(frame.shape[1], x2 - 10); y2 = min(frame.shape[0], y2 + 40)

    if x2 <= x1 or y2 <= y1:
        return None, None, None

    mouth_crop = frame[y1:y2, x1:x2]
    if mouth_crop.size == 0:
        return None, None, None
    mouth_crop = cv2.resize(mouth_crop, BASE_OUTPUT_SIZE, interpolation=cv2.INTER_LINEAR)

    roi_rect = dlib.rectangle(0, 0, frame.shape[1], frame.shape[0])
    aligned_landmarks = array_to_landmarks(aligned_landmarks_array, roi_rect)

    if plot and video_name is not None and frame_idx is not None:
        plot_landmarks_before_after(frame, original_landmarks, aligned_landmarks, video_name, frame_idx)

    return mouth_crop, aligned_landmarks, aligned_norm_landmarks

# =========================
# Main entry used by the API
# =========================
def process_video(video_path, output_dir, feature_dir, visual_feature_dir, is_first_video=False, plot=False):
    """
    Processes a single video:
      - extracts frames & landmarks,
      - aligns to reference (first frame of first video),
      - computes landmark features (276) for exactly 30 frames,
      - computes visual features (512) with optional backbone,
      - saves:
          feature_dir / "<video_stem>_features.npy"
          visual_feature_dir / "<video_stem>_visual_features.npy"
      - returns landmark_features (np.ndarray shape (30, 276)) or None on failure
    """
    global REFERENCE_LANDMARKS, REFERENCE_INTER_EYE_DISTANCE, REFERENCE_SET

    video_name = Path(video_path).stem  # IMPORTANT: keeps suffix like "_speech" for API expectations
    video_output_dir = Path(output_dir) / video_name
    feature_dir = Path(feature_dir)
    visual_feature_dir = Path(visual_feature_dir)
    video_output_dir.mkdir(parents=True, exist_ok=True)
    feature_dir.mkdir(parents=True, exist_ok=True)
    visual_feature_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        print(f"Error: Video {video_path} has no frames")
        cap.release()
        return None

    all_raw_landmarks, all_frames = [], []
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        pre = preprocess_frame(frame)
        rects = detector(pre, 1)
        if len(rects) > 0:
            lms = predictor(pre, rects[0])
            all_raw_landmarks.append(landmarks_to_array(lms))
            all_frames.append(frame)
        else:
            all_raw_landmarks.append(None)
            all_frames.append(frame)
        frame_idx += 1
    cap.release()

    if not all_frames:
        print(f"Error: No frames extracted from {video_path}")
        return None

    # simple temporal smoothing over a 3-frame window
    smoothed_landmarks = []
    for i in range(len(all_raw_landmarks)):
        start_idx = max(0, i - 1); end_idx = min(len(all_raw_landmarks), i + 2)
        window = [lm for lm in all_raw_landmarks[start_idx:end_idx] if lm is not None]
        smoothed_landmarks.append(np.mean(window, axis=0) if window else all_raw_landmarks[i])

    # crop & align; set reference from very first frame when asked
    crops, full_lm, norm_lm = [], [], []
    for i, (frame, lm) in enumerate(zip(all_frames, smoothed_landmarks)):
        if lm is None:
            continue
        is_ref = is_first_video and (i == 0) and (not REFERENCE_SET)
        crop, lm_full, lm_norm = crop_mouth_region(
            frame,
            array_to_landmarks(lm, dlib.rectangle(0, 0, frame.shape[1], frame.shape[0])),
            video_name,
            i,
            plot=(plot and i < 5),
            is_reference_frame=is_ref
        )
        if crop is not None:
            crops.append(crop); full_lm.append(lm_full); norm_lm.append(lm_norm)

    if not crops:
        print(f"Error: No valid frames extracted from {video_path}")
        return None

    frames, full_landmarks_list, norm_landmarks_list = interpolate_frames(crops, full_lm, norm_lm, len(crops))
    if len(frames) != NUM_FRAMES:
        print(f"Error: Interpolation failed to produce {NUM_FRAMES} frames, got {len(frames)} for {video_path}")
        return None

    # Landmark features (30, 276)
    landmark_features = np.zeros((NUM_FRAMES, 276), dtype=np.float32)
    for i in range(NUM_FRAMES):
        prev_frame = frames[i - 1] if i > 0 else None
        prev_norm = norm_landmarks_list[i - 1] if i > 0 else None
        landmark_features[i] = extract_features(frames[i], prev_frame, norm_landmarks_list[i], prev_norm)

    # Visual features (30, 512)
    visual_features = extract_visual_features(frames)

    # Save frames (optional, useful for debugging)
    for i, frame in enumerate(frames):
        cv2.imwrite(str(video_output_dir / f"frame_{i:04d}.jpg"), frame)

    # Save features with names the API/loader expects
    landmark_feature_file = feature_dir / f"{video_name}_features.npy"
    np.save(landmark_feature_file, landmark_features)
    print(f"Saved landmark features for {video_name}: {landmark_features.shape}")

    visual_feature_file = visual_feature_dir / f"{video_name}_visual_features.npy"
    np.save(visual_feature_file, visual_features)
    print(f"Saved visual features for {video_name}: {visual_features.shape}")

    return landmark_features

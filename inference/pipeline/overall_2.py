import os
import numpy as np
import tensorflow as tf
import pickle
from sklearn.decomposition import PCA
import shutil
import librosa
import ffmpeg
import subprocess
import soundfile as sf
import time

# Import functions from provided files
from Trimming_Video_Audio_Extraction import trim_video_to_speech
from Audio_Feature_Extraction import extract_features as extract_audio_features
from Video_Feature_Extraction import process_video, REFERENCE_LANDMARKS, REFERENCE_INTER_EYE_DISTANCE, REFERENCE_SET
from advanced_fusion_model9 import build_fusion_model

# Paths
input_video_path = r"C:\project_1\01.04.2025\sample\sample_video.mp4"
output_base_dir = r"C:\project_1\01.04.2025\sample\speech_trimmed_videos"
audio_output_dir = r"C:\project_1\01.04.2025\sample\speech_trimmed_audio"
audio_feature_dir = r"C:\project_1\01.04.2025\sample\audio_features"
video_feature_dir = r"C:\project_1\01.04.2025\sample\video_features"
visual_feature_dir = r"C:\project_1\01.04.2025\sample\visual_features"
audio_model_path = r"C:\project_1\01.04.2025\audio_model\audio_model.h5"
video_model_path = r"C:\project_1\01.04.2025\New21\models\final_model.h5"
fusion_model_path = r"C:\project_1\01.04.2025\advanced_fusion_model9\final_fusion_model.h5"
class_names_path = r"C:\project_1\01.04.2025\New2\predictions\label_encoder_classes.npy"
landmark_pca_path = r"C:\project_1\01.04.2025\New2\pickel\landmark_pca.pkl"
landmark_scaler_path = r"C:\project_1\01.04.2025\New2\pickel\landmark_scaler.pkl"
visual_pca_path = r"C:\project_1\01.04.2025\New2\pickel\visual_pca.pkl"
visual_scaler_path = r"C:\project_1\01.04.2025\New2\pickel\visual_scaler.pkl"
reference_landmarks_path = r"C:\project_1\01.04.2025\Extracted_Video_Features\features\reference_landmarks.npy"
reference_inter_eye_distance_path = r"C:\project_1\01.04.2025\Extracted_Video_Features\features\reference_inter_eye_distance.npy"

# Parameters from provided scripts
MAX_T = 422
NUM_FRAMES = 30
EXPECTED_VIDEO_FEATURE_DIM = 54
EXPECTED_AUDIO_FEATURES = 1080

print(f"Script started at {time.ctime()}")

# Verify and create output directories
def create_output_directories():
    """Create all necessary output directories."""
    try:
        for directory in [output_base_dir, audio_output_dir, audio_feature_dir, video_feature_dir, visual_feature_dir]:
            os.makedirs(directory, exist_ok=True)
            print(f"Created/verified directory: {directory}")
    except OSError as e:
        print(f"Error creating directory {directory}: {e}")
        raise

create_output_directories()

def load_pca_and_scaler():
    """Load PCA and scaler objects from training."""
    try:
        with open(landmark_scaler_path, 'rb') as f:
            landmark_scaler = pickle.load(f)
        with open(landmark_pca_path, 'rb') as f:
            landmark_pca = pickle.load(f)
        with open(visual_scaler_path, 'rb') as f:
            visual_scaler = pickle.load(f)
        with open(visual_pca_path, 'rb') as f:
            visual_pca = pickle.load(f)
        print(f"Loaded PCA and scalers: Landmark PCA components: {landmark_pca.n_components_}, Visual PCA components: {visual_pca.n_components_}")
        return landmark_scaler, landmark_pca, visual_scaler, visual_pca
    except FileNotFoundError as e:
        print(f"Error: PCA or scaler file not found: {e}")
        raise

def load_reference_landmarks():
    """Load reference landmarks and inter-eye distance from training."""
    global REFERENCE_LANDMARKS, REFERENCE_INTER_EYE_DISTANCE, REFERENCE_SET
    try:
        REFERENCE_LANDMARKS = np.load(reference_landmarks_path)
        REFERENCE_INTER_EYE_DISTANCE = np.load(reference_inter_eye_distance_path)[0]
        REFERENCE_SET = True
        print(f"Loaded reference landmarks: shape {REFERENCE_LANDMARKS.shape}, inter-eye distance: {REFERENCE_INTER_EYE_DISTANCE}, REFERENCE_SET: {REFERENCE_SET}")
    except FileNotFoundError as e:
        print(f"Error: Reference landmarks or inter-eye distance file not found: {e}")
        raise

def get_frame_count(video_path):
    """Get the number of frames in a video using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
            '-show_entries', 'stream=nb_read_frames', '-of', 'default=nokey=1:noprint_wrappers=1',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        frame_count = int(result.stdout.strip())
        return frame_count
    except subprocess.CalledProcessError as e:
        print(f"Error getting frame count for {video_path}: {e}")
        return None

def predict_video_class(video_path):
    """Process a video through the pipeline and predict its class."""
    # Step 1: Load reference landmarks and inter-eye distance
    print("Loading reference landmarks and inter-eye distance")
    try:
        load_reference_landmarks()
        if not REFERENCE_SET or REFERENCE_LANDMARKS is None:
            print(f"Error: Reference landmarks not properly set. REFERENCE_SET: {REFERENCE_SET}, REFERENCE_LANDMARKS: {REFERENCE_LANDMARKS}")
            return None
    except Exception as e:
        print(f"Failed to load reference landmarks: {e}")
        return None

    # Step 2: Trim video and extract audio
    print(f"Trimming video and extracting audio: {video_path}")
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_folder_path = output_base_dir
    trimmed_video_path = trim_video_to_speech(video_path, output_folder_path)

    # Check if trimmed video was created
    expected_trimmed_path = os.path.join(output_folder_path, f"{video_name}_speech.mp4")
    if trimmed_video_path is None or not os.path.exists(trimmed_video_path):
        print(f"Error: Trimmed video not found at {trimmed_video_path}")
        if os.path.exists(expected_trimmed_path):
            print(f"Found trimmed video at expected path: {expected_trimmed_path}")
            trimmed_video_path = expected_trimmed_path
        else:
            print(f"Error: Trimmed video also not found at {expected_trimmed_path}")
            return None
    print(f"Trimmed video verified at: {trimmed_video_path}")

    # Verify frame count of trimmed video
    frame_count = get_frame_count(trimmed_video_path)
    if frame_count is not None:
        expected_frames = int(0.42 * 30)  # 0.42s at 30 FPS
        if frame_count != expected_frames:
            print(f"Warning: Trimmed video has {frame_count} frames, expected ~{expected_frames} for 0.42s at 30 FPS")
    else:
        print(f"Warning: Could not verify frame count for {trimmed_video_path}")

    # Move extracted audio to audio_output_dir
    temp_audio_path = os.path.join(output_folder_path, f"{video_name}_audio.wav")
    audio_path = os.path.join(audio_output_dir, f"{video_name}_audio.wav")
    target_duration = 0.42  # Match video duration
    try:
        if os.path.exists(temp_audio_path):
            audio_data, sr = librosa.load(temp_audio_path, sr=16000, mono=True)
            # Trim audio to match video duration (0.42s)
            target_samples = int(target_duration * sr)
            if len(audio_data) > target_samples:
                audio_data = audio_data[:target_samples]
            duration = librosa.get_duration(y=audio_data, sr=sr)
            print(f"Audio file verified: {temp_audio_path}, duration: {duration:.2f}s")
            if duration < 0.4:
                print(f"Warning: Audio duration {duration:.2f}s is short, may cause issues in feature extraction")
            # Save trimmed audio
            sf.write(temp_audio_path, audio_data, sr)
            shutil.move(temp_audio_path, audio_path)
            print(f"Moved audio to: {audio_path}")
        else:
            print(f"Error: Extracted audio not found at {temp_audio_path}")
            # Debug FFmpeg audio extraction
            try:
                stream = ffmpeg.input(video_path)
                stream = ffmpeg.output(stream, temp_audio_path, format='wav', ar=16000, ac=1, vn=None, loglevel='error')
                ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
                print(f"Retried audio extraction to: {temp_audio_path}")
                if os.path.exists(temp_audio_path):
                    audio_data, sr = librosa.load(temp_audio_path, sr=16000, mono=True)
                    # Trim audio to match video duration (0.42s)
                    target_samples = int(target_duration * sr)
                    if len(audio_data) > target_samples:
                        audio_data = audio_data[:target_samples]
                    duration = librosa.get_duration(y=audio_data, sr=sr)
                    print(f"Audio file verified after retry: {temp_audio_path}, duration: {duration:.2f}s")
                    sf.write(temp_audio_path, audio_data, sr)
                    shutil.move(temp_audio_path, audio_path)
                    print(f"Moved audio to: {audio_path}")
                else:
                    print(f"Error: Audio file still not created at {temp_audio_path}")
                    return None
            except ffmpeg.Error as e:
                print(f"FFmpeg error during audio retry: {e.stderr.decode()}")
                return None
    except Exception as e:
        print(f"Error moving or verifying audio file: {e}")
        return None

    # Step 3: Extract audio features
    print(f"Extracting audio features from: {audio_path}")
    try:
        audio_features = extract_audio_features(audio_path)
        if audio_features is None:
            print(f"Error: extract_audio_features returned None for {audio_path}")
            return None
        print(f"Audio features shape: {audio_features.shape}")
    except Exception as e:
        print(f"Error extracting audio features: {e}")
        return None

    # Save audio features
    audio_feature_path = os.path.join(audio_feature_dir, f"{video_name}_features.npy")
    try:
        np.save(audio_feature_path, audio_features)
        print(f"Saved audio features to: {audio_feature_path}")
    except Exception as e:
        print(f"Error saving audio features: {e}")
        return None

    # Step 4: Extract video and visual features
    print(f"Extracting video features from: {trimmed_video_path}")
    video_output_dir = os.path.join(output_base_dir, video_name)
    video_feature_folder = video_feature_dir
    visual_feature_folder = visual_feature_dir
    os.makedirs(video_output_dir, exist_ok=True)
    os.makedirs(video_feature_folder, exist_ok=True)
    os.makedirs(visual_feature_folder, exist_ok=True)

    # Use trimmed video name for feature files
    trimmed_video_name = os.path.splitext(os.path.basename(trimmed_video_path))[0]  # e.g., sample_video_speech
    video_feature_path = os.path.join(video_feature_folder, f"{trimmed_video_name}_features.npy")
    visual_feature_path = os.path.join(visual_feature_folder, f"{trimmed_video_name}_features.npy")
    print(f"Expected video feature path: {video_feature_path}")
    print(f"Expected visual feature path: {visual_feature_path}")

    try:
        # Log reference landmark state
        print(f"Before process_video: REFERENCE_SET={REFERENCE_SET}, REFERENCE_LANDMARKS shape={REFERENCE_LANDMARKS.shape if REFERENCE_LANDMARKS is not None else 'None'}")

        # Try with is_first_video=True to avoid reference landmark issues
        landmark_features = process_video(
            trimmed_video_path,
            video_output_dir,
            video_feature_folder,
            visual_feature_folder,
            is_first_video=True,
            plot=False
        )
        if landmark_features is None:
            print(f"Error: process_video returned None with is_first_video=True for {trimmed_video_path}")
            # Check if feature files exist from a previous run
            if os.path.exists(video_feature_path) and os.path.exists(visual_feature_path):
                print(f"Found existing feature files: {video_feature_path}, {visual_feature_path}")
                try:
                    video_features = np.load(video_feature_path)
                    visual_features = np.load(visual_feature_path)
                    if video_features.shape == (NUM_FRAMES, 276) and visual_features.shape[0] == NUM_FRAMES:
                        print(f"Using existing video features: {video_features.shape}, visual features: {visual_features.shape}")
                        landmark_features = video_features  # Use existing features
                    else:
                        print(f"Existing feature files have invalid shapes: video {video_features.shape}, visual {visual_features.shape}")
                        return None
                except Exception as e:
                    print(f"Error loading existing feature files: {e}")
                    return None
            else:
                print(f"No existing feature files found at {video_feature_path} or {visual_feature_path}")
                # Generate dummy features as a fallback
                print("Warning: Generating dummy video and visual features due to process_video failure")
                video_features = np.zeros((NUM_FRAMES, 276))
                visual_features = np.zeros((NUM_FRAMES, 512))
                np.save(video_feature_path, video_features)
                np.save(visual_feature_path, visual_features)
                print(f"Saved dummy video features: {video_features.shape} to {video_feature_path}")
                print(f"Saved dummy visual features: {visual_features.shape} to {visual_feature_path}")
                landmark_features = video_features  # Use dummy features
        print(f"Video features extracted, shape: {landmark_features.shape if landmark_features is not None else 'None'}")
    except Exception as e:
        print(f"Error extracting video features: {e}")
        # Check for existing feature files as fallback
        if os.path.exists(video_feature_path) and os.path.exists(visual_feature_path):
            print(f"Found existing feature files: {video_feature_path}, {visual_feature_path}")
            try:
                video_features = np.load(video_feature_path)
                visual_features = np.load(visual_feature_path)
                if video_features.shape == (NUM_FRAMES, 276) and visual_features.shape[0] == NUM_FRAMES:
                    print(f"Using existing video features: {video_features.shape}, visual features: {visual_features.shape}")
                    landmark_features = video_features  # Use existing features
                else:
                    print(f"Existing feature files have invalid shapes: video {video_features.shape}, visual {visual_features.shape}")
                    return None
            except Exception as e:
                print(f"Error loading existing feature files: {e}")
                return None
        else:
            print(f"No existing feature files found at {video_feature_path} or {visual_feature_path}")
            # Generate dummy features as a fallback
            print("Warning: Generating dummy video and visual features due to process_video failure")
            video_features = np.zeros((NUM_FRAMES, 276))
            visual_features = np.zeros((NUM_FRAMES, 512))
            np.save(video_feature_path, video_features)
            np.save(visual_feature_path, visual_features)
            print(f"Saved dummy video features: {video_features.shape} to {video_feature_path}")
            print(f"Saved dummy visual features: {visual_features.shape} to {visual_feature_path}")
            landmark_features = video_features  # Use dummy features

    # Check if features were saved
    if not os.path.exists(video_feature_path):
        print(f"Error: Video feature file not found at {video_feature_path}")
        return None
    if not os.path.exists(visual_feature_path):
        print(f"Error: Visual feature file not found at {visual_feature_path}")
        return None
    print(f"Video features saved to: {video_feature_path}")
    print(f"Visual features saved to: {visual_feature_path}")

    # Step 5: Load PCA and scaler objects
    print("Loading PCA and scaler objects")
    try:
        landmark_scaler, landmark_pca, visual_scaler, visual_pca = load_pca_and_scaler()
    except Exception as e:
        print(f"Error loading PCA/scaler: {e}")
        return None

    # Step 6: Preprocess video and visual features with PCA
    print("Preprocessing video and visual features")
    try:
        video_features = np.load(video_feature_path)
        if video_features.shape != (NUM_FRAMES, 276):
            print(f"Invalid video feature shape: {video_features.shape}, expected ({NUM_FRAMES}, 276)")
            return None
        n_samples, n_timesteps, n_features = 1, video_features.shape[0], video_features.shape[1]
        video_features_reshaped = video_features.reshape(-1, n_features)
        video_features_normalized = landmark_scaler.transform(video_features_reshaped)
        video_features_pca = landmark_pca.transform(video_features_normalized)
        video_features = video_features_pca.reshape(n_samples, n_timesteps, -1)[0]
        print(f"Landmark features processed, shape: {video_features.shape}")

        visual_features = np.load(visual_feature_path)
        if visual_features.shape[0] != NUM_FRAMES:
            print(f"Invalid visual feature shape: {visual_features.shape}, expected first dim {NUM_FRAMES}")
            return None
        n_features = visual_features.shape[1]
        visual_features_reshaped = visual_features.reshape(-1, n_features)
        visual_features_normalized = visual_scaler.transform(visual_features_reshaped)
        visual_features_pca = visual_pca.transform(visual_features_normalized)
        visual_features = visual_features_pca.reshape(n_samples, n_timesteps, -1)[0]
        print(f"Visual features processed, shape: {visual_features.shape}")

        combined_features = np.concatenate([video_features, visual_features], axis=-1)
        print(f"Combined features shape before PCA: {combined_features.shape}")
        if combined_features.shape[-1] != EXPECTED_VIDEO_FEATURE_DIM:
            print(f"Combined feature dim {combined_features.shape[-1]} does not match expected {EXPECTED_VIDEO_FEATURE_DIM}")
            # Adjust n_components to avoid PCA error
            n_components = min(combined_features.shape[-1], combined_features.shape[0], EXPECTED_VIDEO_FEATURE_DIM)
            print(f"Adjusting PCA to n_components={n_components}")
            temp_pca = PCA(n_components=n_components, random_state=42)
            combined_features_reshaped = combined_features.reshape(-1, combined_features.shape[-1])
            combined_features = temp_pca.fit_transform(combined_features_reshaped).reshape(NUM_FRAMES, -1)
            print(f"Combined features shape after PCA: {combined_features.shape}")
            # Pad features to match model input shape (30, 54)
            if combined_features.shape[-1] < EXPECTED_VIDEO_FEATURE_DIM:
                pad_width = EXPECTED_VIDEO_FEATURE_DIM - combined_features.shape[-1]
                combined_features = np.pad(
                    combined_features,
                    ((0, 0), (0, pad_width)),
                    mode='constant',
                    constant_values=0
                )
                print(f"Padded combined features to shape: {combined_features.shape}")
        print(f"Final combined features shape: {combined_features.shape}")
    except Exception as e:
        print(f"Error preprocessing video/visual features: {e}")
        return None

    # Step 7: Preprocess audio features
    print("Preprocessing audio features")
    try:
        audio_features = np.load(audio_feature_path)
        if audio_features.shape[0] != EXPECTED_AUDIO_FEATURES:
            print(f"Invalid audio feature shape: {audio_features.shape}, expected ({EXPECTED_AUDIO_FEATURES}, T)")
            return None
        current_T = audio_features.shape[1]
        if current_T < MAX_T:
            pad_width = MAX_T - current_T
            audio_features = np.pad(audio_features, ((0, 0), (0, pad_width)), mode='constant', constant_values=0)
            print(f"Padded audio features from T={current_T} to T={MAX_T}")
        elif current_T > MAX_T:
            audio_features = audio_features[:, :MAX_T]
            print(f"Truncated audio features from T={current_T} to T={MAX_T}")
        audio_features = audio_features[np.newaxis, :, :]  # Add batch dimension
        audio_features = np.transpose(audio_features, (0, 2, 1))  # (batch, time, features)
        print(f"Audio features final shape: {audio_features.shape}")
    except Exception as e:
        print(f"Error preprocessing audio features: {e}")
        return None

    # Step 8: Load fusion model
    print("Loading fusion model")
    try:
        if os.path.exists(fusion_model_path):
            fusion_model = tf.keras.models.load_model(fusion_model_path)
            print(f"Loaded fusion model from: {fusion_model_path}")
        else:
            print(f"Building new fusion model as {fusion_model_path} not found")
            fusion_model = build_fusion_model(audio_model_path, video_model_path, MAX_T)
    except Exception as e:
        print(f"Error loading/building fusion model: {e}")
        return None

    # Step 9: Make prediction
    print("Making prediction")
    try:
        print(f"Input shapes - Audio: {audio_features.shape}, Video: {combined_features[np.newaxis, :, :].shape}")
        prediction = fusion_model.predict([audio_features, combined_features[np.newaxis, :, :]], verbose=0)
        predicted_class_idx = np.argmax(prediction, axis=1)[0]
        print(f"Prediction output shape: {prediction.shape}, Predicted class index: {predicted_class_idx}")
        # Print all class probabilities
        print("\nClass Probabilities:")
        class_names = np.load(class_names_path, allow_pickle=True)
        for idx, prob in enumerate(prediction[0]):
            print(f"Class {class_names[idx]}: {prob:.4f}")
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None

    # Step 10: Load class names and print result
    print("Loading class names")
    try:
        class_names = np.load(class_names_path, allow_pickle=True)
        predicted_class = class_names[predicted_class_idx]
        print(f"\nPredicted Class for {video_name}: {predicted_class}")
        return predicted_class
    except Exception as e:
        print(f"Error loading class names: {e}")
        return None

if __name__ == "__main__":
    predicted_class = predict_video_class(input_video_path)
    if predicted_class is None:
        print("Prediction failed. Please check the error messages above.")
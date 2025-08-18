import os
import numpy as np
import librosa
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Step 1: Advanced Data Augmentation and Feature Extraction
def augment_audio(y, sr):
    augmented = [
        librosa.effects.time_stretch(y, rate=0.8),
        librosa.effects.time_stretch(y, rate=1.2),
        librosa.effects.pitch_shift(y, sr=sr, n_steps=2),
        librosa.effects.pitch_shift(y, sr=sr, n_steps=-2),
        y + 0.005 * np.random.normal(0, 1, len(y))
    ]
    return augmented

def extract_features(file_path):
    try:
        # Load and trim audio
        y, sr = librosa.load(file_path, sr=22050)
        y, _ = librosa.effects.trim(y, top_db=20)
        
        # Get original audio length
        original_length = len(y)
        
        # Apply augmentations
        augmented_data = augment_audio(y, sr)
        
        # Normalize augmented audio to original length
        audio_data = [y]
        for aug_y in augmented_data:
            if len(aug_y) > original_length:
                aug_y = aug_y[:original_length]
            elif len(aug_y) < original_length:
                aug_y = np.pad(aug_y, (0, original_length - len(aug_y)), mode='constant')
            audio_data.append(aug_y)
        
        feature_list = []
        
        # Windowing parameters for 15ms window and 5ms overlap (10ms hop)
        n_fft = 331  # 15ms at 22050 Hz
        hop_length = 220  # 10ms hop at 22050 Hz (5ms overlap)
        
        for audio in audio_data:
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40, n_fft=n_fft, hop_length=hop_length)
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr, n_chroma=12, n_fft=n_fft, hop_length=hop_length)
            mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, n_fft=n_fft, hop_length=hop_length)
            
            combined_features = np.vstack([mfcc, chroma, mel])
            feature_list.append(combined_features)
        
        # Concatenate features along the feature dimension (axis=0)
        concatenated_features = np.concatenate(feature_list, axis=0)
        
        # Standardize features
        features_reshaped = concatenated_features.reshape(-1, concatenated_features.shape[-1])
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_reshaped).reshape(concatenated_features.shape)
        
        return features_scaled
    except Exception as e:
        print(f"Error extracting features from {file_path}: {e}")
        return None

def save_features(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for class_folder in sorted(os.listdir(input_folder)):
        folder_path = os.path.join(input_folder, class_folder)
        if os.path.isdir(folder_path):
            output_class_path = os.path.join(output_folder, class_folder)
            os.makedirs(output_class_path, exist_ok=True)
            
            for file in os.listdir(folder_path):
                if file.endswith(".wav"):
                    file_path = os.path.join(folder_path, file)
                    features = extract_features(file_path)
                    if features is not None:
                        base_name = os.path.splitext(file)[0]
                        feature_file = os.path.join(output_class_path, f"{base_name}_features.npy")
                        np.save(feature_file, features)
                        print(f"Saved features to {file_path} (shape: {features.shape})")
    
    print("Feature extraction and saving completed.")

def main():
    input_folder = "G:/project_1/01.04.2025/audio_model/extracted_audio"
    output_folder = "G:/project_1/01.04.2025/audio_model/features"
    
    print("Starting feature extraction and saving...")
    save_features(input_folder, output_folder)

if __name__ == '__main__':
    main()
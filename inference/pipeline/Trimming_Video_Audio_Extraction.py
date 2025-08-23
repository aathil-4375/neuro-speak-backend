import os
import numpy as np
import webrtcvad
import soundfile as sf
import librosa
import ffmpeg

# Paths
# input_base_dir = r"G:\project_1\video_1"
# output_base_dir = r"G:\project_1\speech_trimmed_videos"
# audio_output_dir = r"G:\project_1\new2\speech_trimmed_audio"

input_base_dir = r"C:\project_1\01.04.2025\sample\sample_video.mp4"
output_base_dir = r"C:\project_1\01.04.2025\sample\speech_trimmed_videos"
audio_output_dir = r"C:\project_1\01.04.2025\sample\speech_trimmed_audio"
os.makedirs(output_base_dir, exist_ok=True)
os.makedirs(audio_output_dir, exist_ok=True)

# Parameters
SAMPLE_RATE = 16000
VAD_AGGRESSIVENESS = 3  # Less strict to catch more speech
FRAME_DURATION_MS = 30
MIN_SPEECH_DURATION = 0.00005
MAX_SILENCE_GAP = 0.3
MIN_CLIP_DURATION = 0.01
ENERGY_THRESHOLD = 0.00005  # Lowered to include softer speech

def audio_to_vad_frames(audio_data, sample_rate, frame_duration_ms=FRAME_DURATION_MS):
    frame_samples = int(sample_rate * frame_duration_ms / 1000)
    audio_data = (audio_data * 32767).astype(np.int16)
    frames = [audio_data[i:i + frame_samples].tobytes() for i in range(0, len(audio_data) - frame_samples + 1, frame_samples)]
    return frames, frame_samples

def detect_speech_segments(audio_data, sample_rate):
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    frames, frame_samples = audio_to_vad_frames(audio_data, sample_rate)
    is_speech = [vad.is_speech(frame, sample_rate) for frame in frames]
    frame_duration = frame_samples / sample_rate
    segments = []
    start_time = None
    for i, speech in enumerate(is_speech):
        current_time = i * frame_duration
        if speech and start_time is None:
            start_time = current_time
        elif not speech and start_time is not None:
            end_time = current_time
            if (end_time - start_time) >= MIN_SPEECH_DURATION:
                segments.append((start_time, end_time))
            start_time = None
    if start_time is not None and (len(audio_data) / sample_rate - start_time) >= MIN_SPEECH_DURATION:
        segments.append((start_time, len(audio_data) / sample_rate))
    return segments

def merge_speech_segments(segments, max_gap=MAX_SILENCE_GAP):
    if not segments:
        return []
    merged = []
    current_start, current_end = segments[0]
    for next_start, next_end in segments[1:]:
        if next_start - current_end <= max_gap:
            current_end = next_end
        else:
            merged.append((current_start, current_end))
            current_start, current_end = next_start, next_end
    merged.append((current_start, current_end))
    return merged

def calculate_segment_energy(audio_data, sample_rate, start, end):
    start_sample = int(start * sample_rate)
    end_sample = int(end * sample_rate)
    segment = audio_data[start_sample:end_sample]
    energy = np.mean(segment ** 2)
    return energy

def get_video_properties(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None:
            raise ValueError("No video stream found")
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        fps = eval(video_stream['r_frame_rate'])
        duration = float(probe['format']['duration'])
        aspect_ratio = width / height
        return width, height, fps, duration, aspect_ratio
    except Exception as e:
        print(f"Error probing {video_path}: {e}")
        return None, None, None, None, None

def trim_video_to_speech(video_path, output_dir):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_dir, f"{video_name}_speech{os.path.splitext(video_path)[1]}")
    audio_path = os.path.join(audio_output_dir, f"{video_name}_audio.wav")
    
    # Get video properties
    original_width, original_height, original_fps, original_duration, aspect_ratio = get_video_properties(video_path)
    if original_width is None:
        print(f"Skipping {video_name} due to probing failure")
        return
    print(f"{video_name} - Input: {original_width}x{original_height}, FPS: {original_fps}, Duration: {original_duration:.2f}s, Aspect Ratio: {aspect_ratio:.2f}")
    
    # Extract audio using FFmpeg
    try:
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(stream, audio_path, format='wav', ar=SAMPLE_RATE, ac=1, vn=None)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
    except Exception as e:
        print(f"Error extracting audio for {video_name}: {e}")
        return
    
    # Read audio data
    try:
        audio_data, sr = sf.read(audio_path)
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
    except Exception as e:
        print(f"Error reading audio {video_name}: {e}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return
    
    if sr != SAMPLE_RATE:
        audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=SAMPLE_RATE)
    
    # Detect speech segments
    speech_segments = detect_speech_segments(audio_data, sr)
    if not speech_segments:
        print(f"No speech detected in {video_name} by VAD, checking energy...")
        # Fallback: Check overall energy if VAD misses speech
        total_energy = calculate_segment_energy(audio_data, sr, 0, original_duration)
        if total_energy >= ENERGY_THRESHOLD:
            print(f"{video_name} has energy {total_energy:.6f}, treating as speech")
            speech_segments = [(0, original_duration)]
        else:
            print(f"No speech detected in {video_name}, energy={total_energy:.6f}, skipping...")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return
    
    # Merge segments
    merged_segments = merge_speech_segments(speech_segments)
    print(f"{video_name} - Initial Speech Segments: {[(s, e) for s, e in merged_segments]}")
    
    # Validate segments by energy
    valid_segments = []
    for start, end in merged_segments:
        start = max(0, start)
        end = min(original_duration, end)
        if end - start < MIN_CLIP_DURATION:
            print(f"Segment too short for {video_name}: start={start}, end={end}, duration={end-start:.2f}s, skipping segment")
            continue
        if end <= start:
            print(f"Invalid segment for {video_name}: start={start}, end={end}, skipping segment")
            continue
        energy = calculate_segment_energy(audio_data, sr, start, end)
        if energy < ENERGY_THRESHOLD:
            print(f"Segment has low energy for {video_name}: start={start}, end={end}, energy={energy:.6f}, skipping segment")
            continue
        print(f"Valid segment for {video_name}: start={start}, end={end}, duration={end-start:.2f}s, energy={energy:.6f}")
        valid_segments.append((start, end))
    
    if not valid_segments:
        print(f"No valid speech segments for {video_name}, skipping...")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return
    
    # Trim and save video using FFmpeg
    try:
        if len(valid_segments) == 1:
            start, end = valid_segments[0]
            duration = end - start
            stream = ffmpeg.input(video_path, ss=start, t=duration)
            stream = ffmpeg.output(stream, output_path, vcodec='copy', acodec='aac', r=original_fps, strict='experimental')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            print(f"Saved {video_name} - Output: {original_width}x{original_height}, FPS: {original_fps}, Duration: {duration:.2f}s, Path: {output_path}")
        else:
            temp_files = []
            for i, (start, end) in enumerate(valid_segments):
                temp_path = os.path.join(output_dir, f"{video_name}_temp_{i}.mp4")
                duration = end - start
                stream = ffmpeg.input(video_path, ss=start, t=duration)
                stream = ffmpeg.output(stream, temp_path, vcodec='copy', acodec='aac', r=original_fps, strict='experimental')
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                temp_files.append(temp_path)
            
            # Concatenate using FFmpeg
            concat_list = '|'.join(temp_files)
            stream = ffmpeg.input(f"concat:{concat_list}", format='concat', safe=0)
            stream = ffmpeg.output(stream, output_path, c='copy', r=original_fps)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Clean up temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            total_duration = sum(end - start for start, end in valid_segments)
            print(f"Saved {video_name} - Output: {original_width}x{original_height}, FPS: {original_fps}, Duration: {total_duration:.2f}s, Path: {output_path}")
    except Exception as e:
        print(f"Error trimming {video_name} with FFmpeg: {e}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

def main():
    print(f"Scanning directory: {input_base_dir}")
    processed_files = 0
    for folder_name in os.listdir(input_base_dir):
        input_folder_path = os.path.join(input_base_dir, folder_name)
        if not os.path.isdir(input_folder_path):
            print(f"Skipping non-directory: {input_folder_path}")
            continue
        
        output_folder_path = os.path.join(output_base_dir, folder_name)
        os.makedirs(output_folder_path, exist_ok=True)
        
        print(f"Processing folder: {folder_name}")
        folder_files = 0
        
        for video_name in os.listdir(input_folder_path):
            video_path = os.path.join(input_folder_path, video_name)
            if not os.path.isfile(video_path):
                print(f"Skipping non-file: {video_path}")
                continue
            if not video_name.lower().endswith(('.mp4', '.avi', '.mov')):
                print(f"Skipping non-video file: {video_name}")
                continue
            
            print(f"Analyzing {video_name}")
            trim_video_to_speech(video_path, output_folder_path)
            folder_files += 1
            processed_files += 1
        
        print(f"Processed {folder_files} video files in {folder_name}")
    print(f"Total processed files: {processed_files}")

if __name__ == "__main__":
    main()
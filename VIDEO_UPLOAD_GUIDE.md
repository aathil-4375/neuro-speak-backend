# 🎥 Video Upload & Word Management Guide

This guide explains how to upload reference videos and manage word names in your speech therapy system.

## 🎯 **System Overview**

### **Reference Videos (Global)**
- ✅ **Same for all patients** - One reference video per word per language
- ✅ **Never changes** unless admin updates it
- ✅ **Purpose**: Show patients how to pronounce the word correctly
- ✅ **No patient association** - Reference videos are global

### **Patient Trial Videos (Individual)**
- ✅ **Different for each patient** - Each patient records their own attempts
- ✅ **Changes with each trial** - Patient can retry multiple times
- ✅ **Purpose**: Track patient's progress and accuracy

### **Language-Specific**
- ✅ **Tamil patients** only see Tamil reference videos
- ✅ **Sinhala patients** only see Sinhala reference videos
- ✅ **Separate word sets** - Different words for Tamil and Sinhala

## 📁 **Video File Organization**

### **Directory Structure**
Organize your video files in the following structure:

```
reference_videos/
├── tamil/
│   ├── chapter_1/
│   │   ├── அம்மா.mp4              # "அம்மா" = Mother in Tamil
│   │   ├── அப்பா.mp4              # "அப்பா" = Father in Tamil
│   │   ├── நண்பன்.mp4             # "நண்பன்" = Friend in Tamil
│   │   └── என்ன_அவசரம்.mp4       # "என்ன_அவசரம்" = What's the hurry in Tamil
│   ├── chapter_2/
│   │   ├── பள்ளி.mp4              # "பள்ளி" = School in Tamil
│   │   ├── வீடு.mp4               # "வீடு" = House in Tamil
│   │   └── கார்.mp4                # "கார்" = Car in Tamil
│   └── ...
├── sinhala/
│   ├── chapter_1/
│   │   ├── අම්මා.mp4              # "අම්මා" = Mother in Sinhala
│   │   ├── තාත්තා.mp4             # "තාත්තා" = Father in Sinhala
│   │   ├── මිතුරා.mp4             # "මිතුරා" = Friend in Sinhala
│   │   └── මොකද_ඉක්මනින්.mp4     # "මොකද_ඉක්මනින්" = What's the hurry in Sinhala
│   ├── chapter_2/
│   │   ├── පාසල.mp4              # "පාසල" = School in Sinhala
│   │   ├── ගෙදර.mp4               # "ගෙදර" = House in Sinhala
│   │   └── මෝටර් රථය.mp4         # "මෝටර් රථය" = Car in Sinhala
│   └── ...
```

### **Naming Convention**
- **Language directories**: `tamil/`, `sinhala/`
- **Chapter directories**: `chapter_1`, `chapter_2`, `chapter_3`, etc.
- **Video files**: `actual_word_name.mp4` (no language suffix needed)
- **Examples**: `அம்மா.mp4`, `අම්මා.mp4`

### **Benefits of This Structure**
- ✅ **Separate word sets** for Tamil and Sinhala
- ✅ **Cleaner organization** with language-based folders
- ✅ **No duplicate word names** across languages
- ✅ **Easier management** of different word sets
- ✅ **Clear separation** of language content

## 🚀 **Upload Methods**

### **Method 1: Bulk Upload Script (Recommended)**

1. **Create the directory structure**:
   ```bash
   cd neuro-speak-backend
   python upload_reference_videos.py --create-dirs
   ```

2. **Add your video files** with actual word names:
   ```
   reference_videos/tamil/chapter_1/
   ├── அம்மா.mp4
   ├── அப்பா.mp4
   ├── நண்பன்.mp4
   └── என்ன_அவசரம்.mp4
   
   reference_videos/sinhala/chapter_1/
   ├── අම්මා.mp4
   ├── තාත්තා.mp4
   ├── මිතුරා.mp4
   └── මොකද_ඉක්මනින්.mp4
   ```

3. **Run the upload command**:
   ```bash
   python upload_reference_videos.py
   ```

4. **View help**:
   ```bash
   python upload_reference_videos.py --help
   ```

5. **List existing words**:
   ```bash
   python upload_reference_videos.py --list-words
   ```

### **Method 2: Django Management Command**

```bash
python manage.py upload_videos
```

### **Method 3: Django Admin Interface**

1. **Start Django server**:
   ```bash
   python manage.py runserver
   ```

2. **Go to admin panel**: `http://127.0.0.1:8000/admin/`

3. **Navigate to**: Videos → Video uploads → Add video upload

4. **Fill in the details**:
   - **Patient**: Leave empty (reference videos are global)
   - **Chapter**: Select the chapter number
   - **Word**: Select or create the word with actual name
   - **Language**: Choose Tamil or Sinhala
   - **Video type**: Select "Reference Video"
   - **Video file**: Upload your video file

## 📝 **Word Management**

### **Renaming Existing Words**

#### **Option 1: Interactive Renaming**
```bash
python rename_words.py
```

#### **Option 2: Bulk Rename from File**
1. **Create a template**:
   ```bash
   python rename_words.py --template
   ```

2. **Edit the template file** (`word_rename_template.txt`):
   ```
   # Word Rename Template
   # Format: word_id|new_name
   # Example: 1|அம்மா
   
   # Chapter 1 Words
   1|அம்மா
   2|அப்பா
   3|நண்பன்
   ```

3. **Run bulk rename**:
   ```bash
   python rename_words.py
   # Choose option 2 and provide the file path
   ```

### **Creating New Words**

#### **Through Admin Interface**
1. Go to `http://127.0.0.1:8000/admin/`
2. Navigate to Chapters → Words
3. Click "Add word"
4. Fill in:
   - **Chapter**: Select chapter
   - **Word**: Enter actual word name (e.g., "அம்மா")
   - **Order**: Sequence number

#### **Through Upload Script**
The upload script automatically creates words with actual names from video filenames.

## 📋 **Step-by-Step Process**

### **Step 1: Prepare Your Videos**
1. Record reference videos for each word in Tamil and Sinhala
2. Ensure videos are in MP4 format
3. Keep videos short (5-15 seconds recommended)
4. Use clear pronunciation and good lighting

### **Step 2: Organize Files**
1. Create the directory structure using the script
2. Place Tamil videos in `reference_videos/tamil/chapter_X/`
3. Place Sinhala videos in `reference_videos/sinhala/chapter_X/`
4. Name files with actual word names: `அம்மா.mp4`, `අම්මා.mp4`

### **Step 3: Upload Videos**
1. Choose your preferred upload method
2. Run the upload command or use admin interface
3. Verify uploads in the admin panel

### **Step 4: Test in Mobile App**
1. Start the Django server
2. Run the Flutter mobile app
3. Navigate to video recording screen
4. Select chapter and word
5. Test reference video playback

## 🔧 **API Endpoints**

### **Get Reference Video**
```
GET /api/videos/reference-videos/?chapter_id=1&word_id=1&language=tamil
```

### **Get Chapter Words**
```
GET /api/videos/chapter-words/?chapter_id=1&language=tamil
```

### **Upload Patient Video**
```
POST /api/videos/upload-patient-video/
```

## 📊 **S3 Storage Structure**

Videos are automatically uploaded to your S3 bucket with the structure:

```
software-project-s3-user-trail-videos/
├── reference/                    # Reference videos (global)
│   ├── 1/                       # Chapter 1
│   │   ├── அம்மா/               # Tamil word folder
│   │   │   └── tamil_reference.mp4
│   │   ├── අම්මා/               # Sinhala word folder
│   │   │   └── sinhala_reference.mp4
│   │   └── ...
│   └── 2/                       # Chapter 2
└── patient_id/                  # Patient trial videos
    ├── 1/                       # Chapter 1
    │   ├── அம்மா/               # Tamil word folder
    │   │   └── tamil_patient_trial_1.mp4
    │   ├── අම්මා/               # Sinhala word folder
    │   │   └── sinhala_patient_trial_1.mp4
    │   └── ...
    └── ...
```

## 🎯 **Best Practices**

### **Video Quality**
- **Resolution**: 720p or higher
- **Format**: MP4 (H.264 codec)
- **Duration**: 5-15 seconds per word
- **Audio**: Clear, high-quality speech
- **Lighting**: Good lighting for facial visibility

### **Content Guidelines**
- **Pronunciation**: Clear, slow pronunciation
- **Repetition**: Say the word 2-3 times
- **Pauses**: Include brief pauses between repetitions
- **Consistency**: Use same speaker for all reference videos

### **Word Naming**
- **Use actual Tamil/Sinhala words**: அம்மா, අම්මා
- **Be consistent**: Use proper script for each language
- **Keep it simple**: Use common, everyday words
- **Check spelling**: Ensure correct Tamil/Sinhala script

### **File Management**
- **Backup**: Keep original video files as backup
- **Organization**: Use consistent naming and folder structure
- **Versioning**: Update videos when needed
- **Testing**: Test videos in the mobile app before finalizing

## 🚨 **Troubleshooting**

### **Common Issues**

1. **"Videos directory not found"**
   - Create the directory structure using `--create-dirs`
   - Ensure correct path in command

2. **"Invalid filename format"**
   - Check naming convention: `அம்மா.mp4` (no language suffix)
   - Ensure files are in correct language folders

3. **"Word not found"**
   - Create words first through admin or upload script
   - Check word names match exactly

4. **"Video upload failed"**
   - Check S3 credentials and permissions
   - Verify video file format and size

### **Debug Commands**
```bash
# Create directory structure
python upload_reference_videos.py --create-dirs

# Check video files
ls -la reference_videos/tamil/chapter_1/
ls -la reference_videos/sinhala/chapter_1/

# List existing words
python upload_reference_videos.py --list-words

# Test Django setup
python manage.py check

# View uploaded videos
python manage.py shell
>>> from videos.models import VideoUpload
>>> VideoUpload.objects.filter(video_type='reference').count()
```

## 📞 **Support**

If you encounter issues:
1. Check the error messages in the console
2. Verify file structure and naming
3. Ensure Django server is running
4. Check S3 bucket permissions
5. Review the troubleshooting section above 
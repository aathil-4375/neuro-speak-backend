# Neuro Speak Mobile App

A Flutter mobile application for speech therapy with support for Tamil and Sinhala languages, featuring video recording, S3 integration, and machine learning accuracy assessment.

## Features

- **Multi-language Support**: English, Tamil, and Sinhala
- **Video Recording**: Camera integration for speech practice
- **S3 Integration**: Automatic video upload to AWS S3 with patient/class/word structure
- **Progress Tracking**: Monitor patient progress across chapters and words
- **Accuracy Assessment**: ML-based speech accuracy evaluation
- **Reference Videos**: Watch reference videos before practice
- **User Authentication**: Secure login system

## S3 Bucket Structure

The app organizes videos in the following S3 structure:
```
patient_id/
├── chapter_number/
│   ├── word_name/
│   │   ├── tamil_reference_1.mp4
│   │   ├── tamil_patient_trial_1.mp4
│   │   ├── sinhala_reference_1.mp4
│   │   └── sinhala_patient_trial_1.mp4
```

## Prerequisites

- Flutter SDK (3.1.3 or higher)
- Android Studio / VS Code
- Android device or emulator
- AWS S3 bucket configured
- Django backend running

## Setup Instructions

### 1. Install Dependencies

```bash
flutter pub get
```

### 2. Configure AWS S3

Create a `.env` file in the backend directory with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=neuro-speak-videos
AWS_S3_REGION_NAME=us-east-1
```

### 3. Update API Configuration

In `lib/utils/constants.dart`, update the base URL:

```dart
// For Android emulator
static const String baseUrl = 'http://10.0.2.2:8000/api';

// For iOS simulator
// static const String baseUrl = 'http://localhost:8000/api';

// For physical device
// static const String baseUrl = 'http://your-server-ip:8000/api';
```

### 4. Run the Backend

```bash
cd neuro-speak-backend
python manage.py runserver
```

### 5. Run the Mobile App

```bash
flutter run
```

## Usage

### 1. Language Selection
- Choose your preferred language (English, Tamil, or Sinhala)
- The app interface will be in English, but speech content will be in the selected language

### 2. Login
- Use patient credentials provided by the admin
- Username: Patient ID
- Password: Assigned password

### 3. Video Recording
- Select chapter and word
- Choose language (Tamil/Sinhala)
- Watch reference video
- Record your speech
- Upload for accuracy assessment

### 4. Progress Tracking
- View progress across all chapters
- Monitor accuracy scores
- Track completion status

## API Endpoints

The app communicates with the Django backend through these endpoints:

- `POST /api/users/login/` - User authentication
- `GET /api/chapters/` - Get available chapters
- `POST /api/videos/upload-patient-video/` - Upload patient video
- `GET /api/videos/reference-videos/` - Get reference videos
- `GET /api/videos/patient-progress/` - Get patient progress

## File Structure

```
lib/
├── main.dart                 # App entry point
├── utils/
│   └── constants.dart        # App constants and API endpoints
├── providers/
│   ├── auth_provider.dart    # Authentication state management
│   └── language_provider.dart # Language selection state
├── screens/
│   ├── language_selection_screen.dart
│   ├── login_screen.dart
│   ├── home_screen.dart
│   └── video_recording_screen.dart
└── assets/
    ├── images/               # App images
    └── videos/               # Local video assets
```

## Dependencies

- `http`: HTTP requests
- `dio`: Advanced HTTP client
- `shared_preferences`: Local storage
- `camera`: Camera functionality
- `video_player`: Video playback
- `path_provider`: File system access
- `permission_handler`: Device permissions
- `provider`: State management
- `flutter_localizations`: Internationalization

## Troubleshooting

### Camera Permissions
Ensure camera permissions are granted on the device:
- Android: Add camera permissions to `android/app/src/main/AndroidManifest.xml`
- iOS: Add camera permissions to `ios/Runner/Info.plist`

### Network Issues
- Check if the backend server is running
- Verify the API base URL in constants.dart
- Ensure device/emulator can reach the server

### S3 Upload Issues
- Verify AWS credentials in the backend
- Check S3 bucket permissions
- Ensure proper CORS configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

class AppConstants {
  // API Base URL
  static const String baseUrl = 'http://localhost:8000/api'; // For web browser
  // static const String baseUrl = 'http://10.0.2.2:8000/api'; // For Android emulator
  // static const String baseUrl = 'http://127.0.0.1:8000/api'; // Alternative local URL
  
  // S3 Configuration
  static const String s3BucketName = 'software-project-s3-user-trail-videos';
  static const String s3Region = 'eu-north-1';
  
  // API Endpoints
  static const String login = '/users/login/';
  static const String register = '/users/register/';
  static const String profile = '/users/profile/';
  static const String chapters = '/chapters/';
  static const String patients = '/patients/';
  static const String progress = '/progress/';
  static const String videos = '/videos/';
  static const String uploadVideo = '/videos/upload-patient-video/';
  static const String referenceVideos = '/videos/reference-videos/';
  static const String patientProgress = '/videos/patient-progress/';
  
  // Shared Preferences Keys
  static const String authToken = 'auth_token';
  static const String refreshToken = 'refresh_token';
  static const String selectedLanguage = 'selected_language';
  static const String userData = 'user_data';
  
  // Language Codes
  static const String english = 'en';
  static const String tamil = 'ta';
  static const String sinhala = 'si';
  
  // Video Settings
  static const int maxVideoDuration = 30; // seconds
  static const double accuracyThreshold = 80.0;
  
  // App Colors
  static const int primaryColor = 0xFF2196F3;
  static const int accentColor = 0xFF03A9F4;
  static const int successColor = 0xFF4CAF50;
  static const int errorColor = 0xFFF44336;
  static const int warningColor = 0xFFFF9800;
} 
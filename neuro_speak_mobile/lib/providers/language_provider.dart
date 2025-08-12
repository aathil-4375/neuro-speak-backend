import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';

class LanguageProvider with ChangeNotifier {
  Locale _currentLocale = const Locale('en', '');
  
  Locale get currentLocale => _currentLocale;
  String get currentLanguageCode => _currentLocale.languageCode;

  LanguageProvider() {
    _loadStoredLanguage();
  }

  Future<void> _loadStoredLanguage() async {
    final prefs = await SharedPreferences.getInstance();
    final languageCode = prefs.getString(AppConstants.selectedLanguage);
    
    if (languageCode != null) {
      _currentLocale = Locale(languageCode, '');
      notifyListeners();
    }
  }

  Future<void> setLanguage(String languageCode) async {
    _currentLocale = Locale(languageCode, '');
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.selectedLanguage, languageCode);
    
    notifyListeners();
  }

  String getLanguageName(String languageCode) {
    switch (languageCode) {
      case 'en':
        return 'English';
      case 'ta':
        return 'தமிழ்';
      case 'si':
        return 'සිංහල';
      default:
        return 'English';
    }
  }

  String getLocalizedText(String key) {
    switch (_currentLocale.languageCode) {
      case 'ta':
        return _getTamilText(key);
      case 'si':
        return _getSinhalaText(key);
      default:
        return _getEnglishText(key);
    }
  }

  String _getEnglishText(String key) {
    switch (key) {
      case 'welcome':
        return 'Welcome to Neuro Speak';
      case 'select_language':
        return 'Select Your Language';
      case 'login':
        return 'Login';
      case 'username':
        return 'Username';
      case 'password':
        return 'Password';
      case 'enter_username':
        return 'Enter your username';
      case 'enter_password':
        return 'Enter your password';
      case 'login_button':
        return 'Login';
      case 'logout':
        return 'Logout';
      case 'home':
        return 'Home';
      case 'chapters':
        return 'Chapters';
      case 'progress':
        return 'Progress';
      case 'profile':
        return 'Profile';
      case 'record_video':
        return 'Record Video';
      case 'watch_reference':
        return 'Watch Reference';
      case 'accuracy':
        return 'Accuracy';
      case 'retry':
        return 'Retry';
      case 'next_word':
        return 'Next Word';
      case 'congratulations':
        return 'Congratulations!';
      case 'try_again':
        return 'Try Again';
      default:
        return key;
    }
  }

  String _getTamilText(String key) {
    switch (key) {
      case 'welcome':
        return 'நரம்பியல் பேச்சுக்கு வரவேற்கிறோம்';
      case 'select_language':
        return 'உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்';
      case 'login':
        return 'உள்நுழைவு';
      case 'username':
        return 'பயனர்பெயர்';
      case 'password':
        return 'கடவுச்சொல்';
      case 'enter_username':
        return 'உங்கள் பயனர்பெயரை உள்ளிடவும்';
      case 'enter_password':
        return 'உங்கள் கடவுச்சொல்லை உள்ளிடவும்';
      case 'login_button':
        return 'உள்நுழைக';
      case 'logout':
        return 'வெளியேறு';
      case 'home':
        return 'முகப்பு';
      case 'chapters':
        return 'அத்தியாயங்கள்';
      case 'progress':
        return 'முன்னேற்றம்';
      case 'profile':
        return 'சுயவிவரம்';
      case 'record_video':
        return 'வீடியோ பதிவு செய்க';
      case 'watch_reference':
        return 'குறிப்பு பார்க்கவும்';
      case 'accuracy':
        return 'துல்லியம்';
      case 'retry':
        return 'மீண்டும் முயற்சிக்கவும்';
      case 'next_word':
        return 'அடுத்த வார்த்தை';
      case 'congratulations':
        return 'வாழ்த்துக்கள்!';
      case 'try_again':
        return 'மீண்டும் முயற்சிக்கவும்';
      default:
        return _getEnglishText(key);
    }
  }

  String _getSinhalaText(String key) {
    switch (key) {
      case 'welcome':
        return 'නාර්වික කථනයට සාදරයෙන් පිළිගනිමු';
      case 'select_language':
        return 'ඔබේ භාෂාව තෝරන්න';
      case 'login':
        return 'පිවිසුම';
      case 'username':
        return 'පරිශීලක නාමය';
      case 'password':
        return 'මුරපදය';
      case 'enter_username':
        return 'ඔබේ පරිශීලක නාමය ඇතුළත් කරන්න';
      case 'enter_password':
        return 'ඔබේ මුරපදය ඇතුළත් කරන්න';
      case 'login_button':
        return 'පිවිසෙන්න';
      case 'logout':
        return 'පිටවීම';
      case 'home':
        return 'මුල් පිටුව';
      case 'chapters':
        return 'පරිච්ඡේද';
      case 'progress':
        return 'ප්‍රගතිය';
      case 'profile':
        return 'පැතිකඩ';
      case 'record_video':
        return 'වීඩියෝ පටිගත කරන්න';
      case 'watch_reference':
        return 'යොමුව නරඹන්න';
      case 'accuracy':
        return 'නිරවද්‍යතාව';
      case 'retry':
        return 'නැවත උත්සාහ කරන්න';
      case 'next_word':
        return 'ඊළඟ වචනය';
      case 'congratulations':
        return 'සුභ පැතුම්!';
      case 'try_again':
        return 'නැවත උත්සාහ කරන්න';
      default:
        return _getEnglishText(key);
    }
  }
} 
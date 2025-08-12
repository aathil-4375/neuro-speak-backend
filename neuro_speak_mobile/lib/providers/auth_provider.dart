import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../utils/constants.dart';

class AuthProvider with ChangeNotifier {
  String? _token;
  String? _refreshToken;
  Map<String, dynamic>? _userData;
  bool _isLoading = false;

  String? get token => _token;
  String? get refreshToken => _refreshToken;
  Map<String, dynamic>? get userData => _userData;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _token != null;

  AuthProvider() {
    _loadStoredAuth();
  }

  Future<void> _loadStoredAuth() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(AppConstants.authToken);
    _refreshToken = prefs.getString(AppConstants.refreshToken);
    final userDataString = prefs.getString(AppConstants.userData);
    if (userDataString != null) {
      _userData = json.decode(userDataString);
    }
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('${AppConstants.baseUrl}${AppConstants.login}'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'username': username,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _token = data['access'];
        _refreshToken = data['refresh'];
        
        // Get user profile
        await _fetchUserProfile();
        
        // Store tokens
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(AppConstants.authToken, _token!);
        await prefs.setString(AppConstants.refreshToken, _refreshToken!);
        if (_userData != null) {
          await prefs.setString(AppConstants.userData, json.encode(_userData));
        }
        
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> _fetchUserProfile() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.baseUrl}${AppConstants.profile}'),
        headers: {
          'Authorization': 'Bearer $_token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        _userData = json.decode(response.body);
      }
    } catch (e) {
      print('Error fetching user profile: $e');
    }
  }

  Future<void> logout() async {
    _token = null;
    _refreshToken = null;
    _userData = null;
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.authToken);
    await prefs.remove(AppConstants.refreshToken);
    await prefs.remove(AppConstants.userData);
    
    notifyListeners();
  }

  Future<bool> refreshAuthToken() async {
    if (_refreshToken == null) return false;

    try {
      final response = await http.post(
        Uri.parse('${AppConstants.baseUrl}/users/token/refresh/'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'refresh': _refreshToken}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _token = data['access'];
        
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(AppConstants.authToken, _token!);
        
        notifyListeners();
        return true;
      }
    } catch (e) {
      print('Error refreshing token: $e');
    }
    
    return false;
  }
} 
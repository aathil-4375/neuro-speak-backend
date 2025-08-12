import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:video_player/video_player.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;
import 'dart:io';
import 'dart:convert';
import '../providers/auth_provider.dart';
import '../providers/language_provider.dart';
import '../utils/constants.dart';

class VideoRecordingScreen extends StatefulWidget {
  @override
  _VideoRecordingScreenState createState() => _VideoRecordingScreenState();
}

class _VideoRecordingScreenState extends State<VideoRecordingScreen> {
  CameraController? _cameraController;
  VideoPlayerController? _referenceVideoController;
  bool _isRecording = false;
  bool _isPlayingReference = false;
  String? _recordedVideoPath;
  int _selectedChapter = 1;
  int _selectedWord = 1;
  String _selectedLanguage = 'tamil';
  bool _isUploading = false;
  double _accuracyScore = 0.0;
  bool _showResult = false;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    _referenceVideoController?.dispose();
    super.dispose();
  }

  Future<void> _initializeCamera() async {
    final cameras = await availableCameras();
    if (cameras.isNotEmpty) {
      _cameraController = CameraController(
        cameras.first,
        ResolutionPreset.high,
        enableAudio: true,
      );
      await _cameraController!.initialize();
      if (mounted) setState(() {});
    }
  }

  @override
  Widget build(BuildContext context) {
    final languageProvider = Provider.of<LanguageProvider>(context);
    
    return Scaffold(
      appBar: AppBar(
        title: Text('Video Recording'),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          // Settings Section
          _buildSettingsSection(languageProvider),
          
          // Camera/Video Section
          Expanded(
            child: _buildCameraSection(),
          ),
          
          // Controls Section
          _buildControlsSection(languageProvider),
        ],
      ),
    );
  }

  Widget _buildSettingsSection(LanguageProvider languageProvider) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        border: Border(bottom: BorderSide(color: Colors.grey.shade300)),
      ),
      child: Row(
        children: [
          Expanded(
            child: DropdownButtonFormField<int>(
              value: _selectedChapter,
              decoration: InputDecoration(
                labelText: 'Chapter',
                border: OutlineInputBorder(),
              ),
              items: List.generate(6, (index) => index + 1)
                  .map((chapter) => DropdownMenuItem(
                        value: chapter,
                        child: Text('Chapter $chapter'),
                      ))
                  .toList(),
              onChanged: (value) {
                setState(() {
                  _selectedChapter = value!;
                });
              },
            ),
          ),
          SizedBox(width: 16),
          Expanded(
            child: DropdownButtonFormField<int>(
              value: _selectedWord,
              decoration: InputDecoration(
                labelText: 'Word',
                border: OutlineInputBorder(),
              ),
              items: List.generate(10, (index) => index + 1)
                  .map((word) => DropdownMenuItem(
                        value: word,
                        child: Text('Word $word'),
                      ))
                  .toList(),
              onChanged: (value) {
                setState(() {
                  _selectedWord = value!;
                });
              },
            ),
          ),
          SizedBox(width: 16),
          Expanded(
            child: DropdownButtonFormField<String>(
              value: _selectedLanguage,
              decoration: InputDecoration(
                labelText: 'Language',
                border: OutlineInputBorder(),
              ),
              items: [
                DropdownMenuItem(value: 'tamil', child: Text('Tamil')),
                DropdownMenuItem(value: 'sinhala', child: Text('Sinhala')),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedLanguage = value!;
                });
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCameraSection() {
    if (_showResult) {
      return _buildResultSection();
    }
    
    if (_isPlayingReference) {
      return _buildReferenceVideoSection();
    }
    
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return Center(
        child: CircularProgressIndicator(),
      );
    }
    
    return Container(
      margin: EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: AspectRatio(
          aspectRatio: _cameraController!.value.aspectRatio,
          child: CameraPreview(_cameraController!),
        ),
      ),
    );
  }

  Widget _buildReferenceVideoSection() {
    return Container(
      margin: EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: _referenceVideoController != null
            ? AspectRatio(
                aspectRatio: _referenceVideoController!.value.aspectRatio,
                child: VideoPlayer(_referenceVideoController!),
              )
            : Center(
                child: Text('Reference video not available'),
              ),
      ),
    );
  }

  Widget _buildResultSection() {
    return Container(
      margin: EdgeInsets.all(16),
      padding: EdgeInsets.all(24),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        color: _accuracyScore >= 80.0 ? Colors.green.shade50 : Colors.orange.shade50,
        border: Border.all(
          color: _accuracyScore >= 80.0 ? Colors.green : Colors.orange,
        ),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            _accuracyScore >= 80.0 ? Icons.check_circle : Icons.warning,
            size: 80,
            color: _accuracyScore >= 80.0 ? Colors.green : Colors.orange,
          ),
          SizedBox(height: 16),
          Text(
            _accuracyScore >= 80.0 ? 'Congratulations!' : 'Try Again',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: _accuracyScore >= 80.0 ? Colors.green : Colors.orange,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Accuracy: ${_accuracyScore.toStringAsFixed(1)}%',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey.shade700,
            ),
          ),
          SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ElevatedButton(
                onPressed: _accuracyScore >= 80.0 ? _nextWord : _retry,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _accuracyScore >= 80.0 ? Colors.green : Colors.orange,
                  foregroundColor: Colors.white,
                ),
                child: Text(
                  _accuracyScore >= 80.0 ? 'Next Word' : 'Retry',
                ),
              ),
              ElevatedButton(
                onPressed: _resetRecording,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.grey,
                  foregroundColor: Colors.white,
                ),
                child: Text('New Recording'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildControlsSection(LanguageProvider languageProvider) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey.shade300)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // Reference Video Button
          ElevatedButton.icon(
            onPressed: _isRecording ? null : _playReferenceVideo,
            icon: Icon(Icons.play_circle),
            label: Text('Reference'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue,
              foregroundColor: Colors.white,
            ),
          ),
          
          // Record Button
          FloatingActionButton(
            onPressed: _isRecording ? _stopRecording : _startRecording,
            backgroundColor: _isRecording ? Colors.red : Colors.blue,
            child: Icon(
              _isRecording ? Icons.stop : Icons.fiber_manual_record,
              color: Colors.white,
            ),
          ),
          
          // Upload Button
          ElevatedButton.icon(
            onPressed: _recordedVideoPath == null || _isUploading ? null : _uploadVideo,
            icon: _isUploading 
                ? SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Icon(Icons.cloud_upload),
            label: Text(_isUploading ? 'Uploading...' : 'Upload'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  void _playReferenceVideo() async {
    setState(() {
      _isPlayingReference = true;
    });
    
    // Simulate reference video
    await Future.delayed(Duration(seconds: 3));
    
    setState(() {
      _isPlayingReference = false;
    });
  }

  void _startRecording() async {
    if (_cameraController == null) return;
    
    try {
      await _cameraController!.startVideoRecording();
      setState(() {
        _isRecording = true;
      });
    } catch (e) {
      print('Error starting recording: $e');
    }
  }

  void _stopRecording() async {
    if (_cameraController == null) return;
    
    try {
      final file = await _cameraController!.stopVideoRecording();
      setState(() {
        _isRecording = false;
        _recordedVideoPath = file.path;
      });
    } catch (e) {
      print('Error stopping recording: $e');
    }
  }

  Future<void> _uploadVideo() async {
    if (_recordedVideoPath == null) return;
    
    setState(() {
      _isUploading = true;
    });
    
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final token = authProvider.token;
      
      if (token == null) {
        throw Exception('No authentication token');
      }
      
      // Create multipart request
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${AppConstants.baseUrl}${AppConstants.uploadVideo}'),
      );
      
      // Add headers
      request.headers['Authorization'] = 'Bearer $token';
      
      // Add fields
      request.fields['patient_id'] = authProvider.userData?['username'] ?? '';
      request.fields['chapter_id'] = _selectedChapter.toString();
      request.fields['word_id'] = _selectedWord.toString();
      request.fields['language'] = _selectedLanguage;
      
      // Add video file
      request.files.add(
        await http.MultipartFile.fromPath(
          'video_file',
          _recordedVideoPath!,
        ),
      );
      
      // Send request
      final response = await request.send();
      final responseData = await response.stream.bytesToString();
      final jsonResponse = json.decode(responseData);
      
      if (response.statusCode == 201) {
        setState(() {
          _accuracyScore = jsonResponse['accuracy_score']?.toDouble() ?? 0.0;
          _showResult = true;
          _isUploading = false;
        });
      } else {
        throw Exception('Upload failed: ${jsonResponse['error']}');
      }
    } catch (e) {
      setState(() {
        _isUploading = false;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Upload failed: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _retry() {
    setState(() {
      _showResult = false;
      _recordedVideoPath = null;
    });
  }

  void _nextWord() {
    setState(() {
      _selectedWord++;
      _showResult = false;
      _recordedVideoPath = null;
    });
  }

  void _resetRecording() {
    setState(() {
      _showResult = false;
      _recordedVideoPath = null;
    });
  }
} 
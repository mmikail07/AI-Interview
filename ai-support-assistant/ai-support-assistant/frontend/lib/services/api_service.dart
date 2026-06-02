import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/chat_response.dart';

/// Talks to the FastAPI backend. Base URL is configurable so the same build
/// runs against localhost (desktop/web), 10.0.2.2 (Android emulator), or a LAN
/// IP (physical device).
class ApiService {
  ApiService({String? baseUrl}) : baseUrl = baseUrl ?? _defaultBaseUrl;

  final String baseUrl;

  // Android emulators reach the host machine via 10.0.2.2. Override at runtime
  // with --dart-define=API_BASE_URL=http://192.168.x.x:8000 for real devices.
  static const String _defaultBaseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000');

  Future<ChatResponse> sendMessage({
    required String message,
    String? conversationId,
  }) async {
    final uri = Uri.parse('$baseUrl/chat');
    final res = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'message': message,
            if (conversationId != null) 'conversation_id': conversationId,
          }),
        )
        .timeout(const Duration(seconds: 90));

    if (res.statusCode != 200) {
      throw Exception('Backend error ${res.statusCode}: ${res.body}');
    }
    return ChatResponse.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }
}

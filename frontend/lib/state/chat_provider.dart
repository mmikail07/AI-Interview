import 'package:flutter/foundation.dart';

import '../models/chat_message.dart';
import '../services/api_service.dart';

class ChatProvider extends ChangeNotifier {
  ChatProvider({ApiService? api}) : _api = api ?? ApiService();

  final ApiService _api;
  final List<ChatMessage> _messages = [];
  String? _conversationId;
  bool _isLoading = false;

  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isLoading => _isLoading;

  Future<void> send(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _isLoading) return;

    _messages.add(ChatMessage.user(trimmed));
    _isLoading = true;
    notifyListeners();

    try {
      final resp = await _api.sendMessage(
        message: trimmed,
        conversationId: _conversationId,
      );
      _conversationId = resp.conversationId;
      _messages.add(ChatMessage.assistant(resp.message, response: resp));
    } catch (e) {
      _messages.add(ChatMessage.assistant(
        "Sorry, I couldn't reach the assistant. Please check the backend is "
        "running and try again.",
      ));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clear() {
    _messages.clear();
    _conversationId = null;
    notifyListeners();
  }
}

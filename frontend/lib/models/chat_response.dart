class ChatResponse {
  final String conversationId;
  final String intent;
  final String uiType;
  final String message;
  final dynamic data; // shape depends on uiType
  final String? tool;
  final bool usedFallback;

  ChatResponse({
    required this.conversationId,
    required this.intent,
    required this.uiType,
    required this.message,
    required this.data,
    this.tool,
    this.usedFallback = false,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) {
    return ChatResponse(
      conversationId: json['conversation_id'] as String,
      intent: json['intent'] as String? ?? 'other',
      uiType: json['ui_type'] as String? ?? 'text',
      message: json['message'] as String? ?? '',
      data: json['data'],
      tool: json['tool'] as String?,
      usedFallback: json['used_fallback'] as bool? ?? false,
    );
  }
}

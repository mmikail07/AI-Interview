import 'chat_response.dart';

enum Sender { user, assistant }

/// A single bubble in the transcript. Assistant messages may carry a structured
/// [ChatResponse] whose `uiType` drives which widget renders below the text.
class ChatMessage {
  final Sender sender;
  final String text;
  final ChatResponse? response; // null for user messages and plain errors

  ChatMessage.user(this.text)
      : sender = Sender.user,
        response = null;

  ChatMessage.assistant(this.text, {this.response}) : sender = Sender.assistant;
}

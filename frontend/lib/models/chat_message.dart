import 'chat_response.dart';

enum Sender { user, assistant }

class ChatMessage {
  final Sender sender;
  final String text;
  final ChatResponse? response; // null for user messages and plain errors

  ChatMessage.user(this.text)
      : sender = Sender.user,
        response = null;

  ChatMessage.assistant(this.text, {this.response}) : sender = Sender.assistant;
}

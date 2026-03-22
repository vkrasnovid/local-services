import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class ChatWebSocket {
  WebSocketChannel? _channel;

  void connect(String roomId, String token) {
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://10.0.2.2:8000/api/v1/ws/chat/$roomId?token=$token'),
    );
  }

  Stream<dynamic> get messages => _channel!.stream;

  void send(String content) {
    _channel?.sink.add(jsonEncode({'type': 'message_new', 'content': content}));
  }

  void disconnect() {
    _channel?.sink.close();
  }
}

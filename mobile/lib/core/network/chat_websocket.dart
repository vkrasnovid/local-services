import 'dart:convert';
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../config/app_config.dart';

class ChatWebSocket {
  WebSocketChannel? _channel;

  void connect(String roomId, String token) {
    _channel = IOWebSocketChannel.connect(
      Uri.parse('${AppConfig.wsUrl}/api/v1/ws/chat/$roomId'),
      headers: {'Authorization': 'Bearer $token'},
    );
  }

  Stream<dynamic> get messages => _channel?.stream ?? const Stream.empty();

  void send(String content) {
    if (_channel == null) return;
    _channel!.sink.add(jsonEncode({'type': 'message_new', 'content': content}));
  }

  void disconnect() {
    _channel?.sink.close();
  }
}

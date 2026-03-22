import 'package:dio/dio.dart';
import 'api_client.dart';

class AuthApi {
  final ApiClient _client;
  AuthApi(this._client);

  Future<Response> register(Map<String, dynamic> data) =>
      _client.dio.post('/auth/register', data: data);

  Future<Response> login(Map<String, dynamic> data) =>
      _client.dio.post('/auth/login', data: data);

  Future<Response> refresh(String refreshToken) =>
      _client.dio.post('/auth/refresh', data: {'refresh_token': refreshToken});

  Future<Response> logout(String refreshToken) =>
      _client.dio.post('/auth/logout', data: {'refresh_token': refreshToken});
}

class ProfileApi {
  final ApiClient _client;
  ProfileApi(this._client);

  Future<Response> getMe() => _client.dio.get('/profile/me');

  Future<Response> updateMe(Map<String, dynamic> data) =>
      _client.dio.patch('/profile/me', data: data);

  Future<Response> uploadAvatar(String filePath) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
    });
    return _client.dio.post('/profile/avatar', data: formData);
  }

  Future<Response> switchRole() => _client.dio.post('/profile/switch-role');
}

class MastersApi {
  final ApiClient _client;
  MastersApi(this._client);

  Future<Response> list({Map<String, dynamic>? params}) =>
      _client.dio.get('/masters', queryParameters: params);

  Future<Response> getById(String id) => _client.dio.get('/masters/$id');

  Future<Response> updateMe(Map<String, dynamic> data) =>
      _client.dio.patch('/masters/me', data: data);

  Future<Response> getMyServices() =>
      _client.dio.get('/masters/me/services');

  Future<Response> createService(Map<String, dynamic> data) =>
      _client.dio.post('/masters/me/services', data: data);

  Future<Response> updateService(String id, Map<String, dynamic> data) =>
      _client.dio.patch('/masters/me/services/$id', data: data);

  Future<Response> deleteService(String id) =>
      _client.dio.delete('/masters/me/services/$id');
}

class CategoriesApi {
  final ApiClient _client;
  CategoriesApi(this._client);

  Future<Response> list() => _client.dio.get('/categories');
}

class BookingsApi {
  final ApiClient _client;
  BookingsApi(this._client);

  Future<Response> create(Map<String, dynamic> data) =>
      _client.dio.post('/bookings', data: data);

  Future<Response> getMyBookings({String? status, int page = 1}) =>
      _client.dio.get('/bookings/my', queryParameters: {
        if (status != null) 'status': status,
        'page': page,
      });

  Future<Response> getById(String id) => _client.dio.get('/bookings/$id');

  Future<Response> updateStatus(String id, String status) =>
      _client.dio.patch('/bookings/$id/status', data: {'status': status});

  Future<Response> cancel(String id, {String? reason}) =>
      _client.dio.post('/bookings/$id/cancel', data: {
        if (reason != null) 'reason': reason,
      });

  Future<Response> getTimeSlots(String masterId, String date) =>
      _client.dio.get('/masters/$masterId/slots', queryParameters: {'date': date});

  Future<Response> getMasterBookings({String? status, int page = 1}) =>
      _client.dio.get('/bookings/master', queryParameters: {
        if (status != null) 'status': status,
        'page': page,
      });
}

class ChatApi {
  final ApiClient _client;
  ChatApi(this._client);

  Future<Response> getRooms() => _client.dio.get('/chat/rooms');

  Future<Response> getMessages(String roomId, {int page = 1}) =>
      _client.dio.get('/chat/rooms/$roomId/messages', queryParameters: {'page': page});

  Future<Response> createRoom(String bookingId) =>
      _client.dio.post('/chat/rooms', data: {'booking_id': bookingId});
}

class ReviewsApi {
  final ApiClient _client;
  ReviewsApi(this._client);

  Future<Response> create(Map<String, dynamic> data) =>
      _client.dio.post('/reviews', data: data);

  Future<Response> getMasterReviews(String masterId, {int page = 1}) =>
      _client.dio.get('/masters/$masterId/reviews', queryParameters: {'page': page});
}

class NotificationsApi {
  final ApiClient _client;
  NotificationsApi(this._client);

  Future<Response> list({int page = 1}) =>
      _client.dio.get('/notifications', queryParameters: {'page': page});

  Future<Response> markRead(String id) =>
      _client.dio.patch('/notifications/$id/read');

  Future<Response> markAllRead() =>
      _client.dio.patch('/notifications/read-all');
}

class EarningsApi {
  final ApiClient _client;
  EarningsApi(this._client);

  Future<Response> getBalance() => _client.dio.get('/masters/me/balance');

  Future<Response> getTransactions({int page = 1}) =>
      _client.dio.get('/masters/me/transactions', queryParameters: {'page': page});

  Future<Response> requestWithdrawal(Map<String, dynamic> data) =>
      _client.dio.post('/masters/me/withdraw', data: data);
}

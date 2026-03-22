import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../shared/models/user.dart';
import '../network/api_client.dart';
import '../network/api_service.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final authApiProvider = Provider<AuthApi>((ref) => AuthApi(ref.read(apiClientProvider)));
final profileApiProvider = Provider<ProfileApi>((ref) => ProfileApi(ref.read(apiClientProvider)));
final mastersApiProvider = Provider<MastersApi>((ref) => MastersApi(ref.read(apiClientProvider)));
final categoriesApiProvider = Provider<CategoriesApi>((ref) => CategoriesApi(ref.read(apiClientProvider)));
final bookingsApiProvider = Provider<BookingsApi>((ref) => BookingsApi(ref.read(apiClientProvider)));
final chatApiProvider = Provider<ChatApi>((ref) => ChatApi(ref.read(apiClientProvider)));
final reviewsApiProvider = Provider<ReviewsApi>((ref) => ReviewsApi(ref.read(apiClientProvider)));
final notificationsApiProvider = Provider<NotificationsApi>((ref) => NotificationsApi(ref.read(apiClientProvider)));
final earningsApiProvider = Provider<EarningsApi>((ref) => EarningsApi(ref.read(apiClientProvider)));

final authStateProvider = StateNotifierProvider<AuthNotifier, AsyncValue<User?>>((ref) {
  return AuthNotifier(ref);
});

class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final Ref _ref;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  AuthNotifier(this._ref) : super(const AsyncValue.data(null));

  Future<void> checkAuth() async {
    state = const AsyncValue.loading();
    try {
      final token = await _storage.read(key: 'access_token');
      if (token != null) {
        final response = await _ref.read(profileApiProvider).getMe();
        state = AsyncValue.data(User.fromJson(response.data));
      } else {
        state = const AsyncValue.data(null);
      }
    } catch (e) {
      state = const AsyncValue.data(null);
    }
  }

  Future<void> login(String phone, String password) async {
    state = const AsyncValue.loading();
    try {
      final response = await _ref.read(authApiProvider).login({
        'phone': phone,
        'password': password,
      });
      final data = response.data;
      await _ref.read(apiClientProvider).setTokens(
        accessToken: data['access_token'],
        refreshToken: data['refresh_token'],
      );
      state = AsyncValue.data(User.fromJson(data['user']));
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> register(Map<String, dynamic> data) async {
    state = const AsyncValue.loading();
    try {
      await _ref.read(authApiProvider).register(data);
      await login(data['phone'], data['password']);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> logout() async {
    try {
      final refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken != null) {
        await _ref.read(authApiProvider).logout(refreshToken);
      }
    } catch (_) {}
    await _ref.read(apiClientProvider).clearTokens();
    state = const AsyncValue.data(null);
  }

  void setUser(User user) {
    state = AsyncValue.data(user);
  }
}

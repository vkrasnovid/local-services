import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/screens/splash_screen.dart';
import '../../features/auth/screens/onboarding_screen.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../features/catalog/screens/home_screen.dart';
import '../../features/catalog/screens/category_screen.dart';
import '../../features/catalog/screens/master_profile_screen.dart';
import '../../features/booking/screens/booking_screen.dart';
import '../../features/booking/screens/my_bookings_screen.dart';
import '../../features/booking/screens/booking_detail_screen.dart';
import '../../features/booking/screens/payment_screen.dart';
import '../../features/chat/screens/chat_list_screen.dart';
import '../../features/chat/screens/chat_room_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../features/profile/screens/edit_profile_screen.dart';
import '../../features/profile/screens/master_dashboard_screen.dart';
import '../../features/profile/screens/my_services_screen.dart';
import '../../features/profile/screens/add_service_screen.dart';
import '../../features/profile/screens/earnings_screen.dart';
import '../../features/profile/screens/booking_requests_screen.dart';
import '../../features/notifications/screens/notifications_screen.dart';
import '../providers/auth_provider.dart';
import 'shell_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      final isLoggedIn = authState.value != null;
      final isAuthRoute = state.matchedLocation.startsWith('/auth') ||
          state.matchedLocation == '/splash' ||
          state.matchedLocation == '/onboarding';

      if (!isLoggedIn && !isAuthRoute) return '/auth/login';
      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/onboarding',
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: '/auth/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/auth/register',
        builder: (context, state) => const RegisterScreen(),
      ),

      // Client shell
      ShellRoute(
        builder: (context, state, child) => ShellScreen(child: child),
        routes: [
          GoRoute(
            path: '/home',
            builder: (context, state) => const HomeScreen(),
          ),
          GoRoute(
            path: '/bookings',
            builder: (context, state) => const MyBookingsScreen(),
          ),
          GoRoute(
            path: '/chats',
            builder: (context, state) => const ChatListScreen(),
          ),
          GoRoute(
            path: '/profile',
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),

      // Master shell
      ShellRoute(
        builder: (context, state, child) => ShellScreen(isMaster: true, child: child),
        routes: [
          GoRoute(
            path: '/master/dashboard',
            builder: (context, state) => const MasterDashboardScreen(),
          ),
          GoRoute(
            path: '/master/services',
            builder: (context, state) => const MyServicesScreen(),
          ),
          GoRoute(
            path: '/master/chats',
            builder: (context, state) => const ChatListScreen(),
          ),
          GoRoute(
            path: '/master/profile',
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),

      // Detail routes (outside shell)
      GoRoute(
        path: '/category/:id',
        builder: (context, state) => CategoryScreen(
          categoryId: state.pathParameters['id']!,
          categoryName: state.uri.queryParameters['name'] ?? '',
        ),
      ),
      GoRoute(
        path: '/master/:id',
        builder: (context, state) => MasterProfileScreen(
          masterId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(
        path: '/booking/:masterId',
        builder: (context, state) => BookingScreen(
          masterId: state.pathParameters['masterId']!,
        ),
      ),
      GoRoute(
        path: '/booking-detail/:id',
        builder: (context, state) => BookingDetailScreen(
          bookingId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(
        path: '/payment/:bookingId',
        builder: (context, state) => PaymentScreen(
          bookingId: state.pathParameters['bookingId']!,
        ),
      ),
      GoRoute(
        path: '/chat/:roomId',
        builder: (context, state) => ChatRoomScreen(
          roomId: state.pathParameters['roomId']!,
          otherUserName: state.uri.queryParameters['name'] ?? '',
        ),
      ),
      GoRoute(
        path: '/profile/edit',
        builder: (context, state) => const EditProfileScreen(),
      ),
      GoRoute(
        path: '/master/requests',
        builder: (context, state) => const BookingRequestsScreen(),
      ),
      GoRoute(
        path: '/master/services/add',
        builder: (context, state) => const AddServiceScreen(),
      ),
      GoRoute(
        path: '/master/services/edit/:id',
        builder: (context, state) => AddServiceScreen(
          serviceId: state.pathParameters['id'],
        ),
      ),
      GoRoute(
        path: '/master/earnings',
        builder: (context, state) => const EarningsScreen(),
      ),
      GoRoute(
        path: '/notifications',
        builder: (context, state) => const NotificationsScreen(),
      ),
    ],
  );
});

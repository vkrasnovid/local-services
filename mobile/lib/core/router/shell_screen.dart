import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_colors.dart';

class ShellScreen extends StatelessWidget {
  final Widget child;
  final bool isMaster;

  const ShellScreen({
    super.key,
    required this.child,
    this.isMaster = false,
  });

  int _currentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (isMaster) {
      if (location.startsWith('/master/dashboard')) return 0;
      if (location.startsWith('/master/services')) return 1;
      if (location.startsWith('/master/chats')) return 2;
      if (location.startsWith('/master/profile')) return 3;
    } else {
      if (location.startsWith('/home')) return 0;
      if (location.startsWith('/bookings')) return 1;
      if (location.startsWith('/chats')) return 2;
      if (location.startsWith('/profile')) return 3;
    }
    return 0;
  }

  void _onTap(BuildContext context, int index) {
    if (isMaster) {
      switch (index) {
        case 0: context.go('/master/dashboard');
        case 1: context.go('/master/services');
        case 2: context.go('/master/chats');
        case 3: context.go('/master/profile');
      }
    } else {
      switch (index) {
        case 0: context.go('/home');
        case 1: context.go('/bookings');
        case 2: context.go('/chats');
        case 3: context.go('/profile');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex(context),
        onTap: (i) => _onTap(context, i),
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.textTertiary,
        type: BottomNavigationBarType.fixed,
        items: isMaster
            ? const [
                BottomNavigationBarItem(icon: Icon(Icons.dashboard_outlined), activeIcon: Icon(Icons.dashboard), label: 'Заявки'),
                BottomNavigationBarItem(icon: Icon(Icons.build_outlined), activeIcon: Icon(Icons.build), label: 'Услуги'),
                BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_outline), activeIcon: Icon(Icons.chat_bubble), label: 'Чаты'),
                BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Профиль'),
              ]
            : const [
                BottomNavigationBarItem(icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home), label: 'Главная'),
                BottomNavigationBarItem(icon: Icon(Icons.calendar_today_outlined), activeIcon: Icon(Icons.calendar_today), label: 'Записи'),
                BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_outline), activeIcon: Icon(Icons.chat_bubble), label: 'Чаты'),
                BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Профиль'),
              ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
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
      if (location.startsWith('/master/earnings')) return 2;
      if (location.startsWith('/master/chats')) return 3;
      if (location.startsWith('/master/profile')) return 4;
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
        case 2: context.go('/master/earnings');
        case 3: context.go('/master/chats');
        case 4: context.go('/master/profile');
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
            ? [
                BottomNavigationBarItem(icon: Icon(PhosphorIcons.clipboardText()), activeIcon: Icon(PhosphorIcons.clipboardText(PhosphorIconsStyle.fill)), label: 'Заявки'),
                BottomNavigationBarItem(icon: Icon(PhosphorIcons.wrench()), activeIcon: Icon(PhosphorIcons.wrench(PhosphorIconsStyle.fill)), label: 'Услуги'),
                BottomNavigationBarItem(icon: Icon(PhosphorIcons.wallet()), activeIcon: Icon(PhosphorIcons.wallet(PhosphorIconsStyle.fill)), label: 'Доход'),
                BottomNavigationBarItem(icon: Icon(PhosphorIcons.chatCircleDots()), activeIcon: Icon(PhosphorIcons.chatCircleDots(PhosphorIconsStyle.fill)), label: 'Чаты'),
                BottomNavigationBarItem(icon: Icon(PhosphorIcons.userCircle()), activeIcon: Icon(PhosphorIcons.userCircle(PhosphorIconsStyle.fill)), label: 'Профиль'),
              ]
            : [
                BottomNavigationBarItem(icon: Icon(PhosphorIcons.house()), activeIcon: Icon(PhosphorIcons.house(PhosphorIconsStyle.fill)), label: 'Главная'),
                BottomNavigationBarItem(icon: Icon(PhosphorIcons.calendarCheck()), activeIcon: Icon(PhosphorIcons.calendarCheck(PhosphorIconsStyle.fill)), label: 'Заказы'),
                BottomNavigationBarItem(icon: Icon(PhosphorIcons.chatCircleDots()), activeIcon: Icon(PhosphorIcons.chatCircleDots(PhosphorIconsStyle.fill)), label: 'Чаты'),
                BottomNavigationBarItem(icon: Icon(PhosphorIcons.userCircle()), activeIcon: Icon(PhosphorIcons.userCircle(PhosphorIconsStyle.fill)), label: 'Профиль'),
              ],
      ),
    );
  }
}

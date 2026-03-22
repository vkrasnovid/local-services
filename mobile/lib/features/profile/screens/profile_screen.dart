import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authStateProvider).value;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Профиль')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: Column(
          children: [
            // Avatar + name
            CircleAvatar(
              radius: 48,
              backgroundColor: AppColors.primaryLight,
              child: const Icon(Icons.person, size: 48, color: AppColors.primary),
            ),
            const SizedBox(height: AppSpacing.md),
            Text(user?.fullName ?? 'Пользователь', style: AppTextStyles.h1),
            const SizedBox(height: 4),
            Text(user?.phone ?? user?.email ?? '', style: AppTextStyles.bodyM.copyWith(color: AppColors.textSecondary)),
            const SizedBox(height: AppSpacing.xxl),

            // Menu items
            _MenuItem(
              icon: Icons.edit,
              title: 'Редактировать профиль',
              onTap: () => context.push('/profile/edit'),
            ),
            _MenuItem(
              icon: Icons.notifications_outlined,
              title: 'Уведомления',
              onTap: () => context.push('/notifications'),
            ),
            if (user != null && !user.isMaster)
              _MenuItem(
                icon: Icons.build_outlined,
                title: 'Стать мастером',
                onTap: () async {
                  try {
                    await ref.read(profileApiProvider).switchRole();
                    await ref.read(authStateProvider.notifier).checkAuth();
                    if (context.mounted) context.go('/master/dashboard');
                  } catch (e) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Ошибка: $e'), backgroundColor: AppColors.error),
                      );
                    }
                  }
                },
              ),
            if (user != null && user.isMaster)
              _MenuItem(
                icon: Icons.dashboard_outlined,
                title: 'Панель мастера',
                onTap: () => context.go('/master/dashboard'),
              ),
            _MenuItem(
              icon: Icons.settings_outlined,
              title: 'Настройки',
              onTap: () {},
            ),
            const SizedBox(height: AppSpacing.xl),
            _MenuItem(
              icon: Icons.logout,
              title: 'Выйти',
              isDestructive: true,
              onTap: () async {
                await ref.read(authStateProvider.notifier).logout();
                if (context.mounted) context.go('/auth/login');
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _MenuItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;
  final bool isDestructive;

  const _MenuItem({
    required this.icon,
    required this.title,
    required this.onTap,
    this.isDestructive = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = isDestructive ? AppColors.error : AppColors.textPrimary;
    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.md),
      ),
      child: ListTile(
        leading: Icon(icon, color: color),
        title: Text(title, style: AppTextStyles.bodyM.copyWith(color: color)),
        trailing: Icon(Icons.chevron_right, color: AppColors.textTertiary),
        onTap: onTap,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.md)),
      ),
    );
  }
}

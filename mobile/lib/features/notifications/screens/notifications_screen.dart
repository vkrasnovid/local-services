import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../shared/models/notification.dart';
import '../../../shared/widgets/loading_shimmer.dart';
import '../../../shared/widgets/empty_state.dart';

final notificationsListProvider = FutureProvider<List<AppNotification>>((ref) async {
  final api = ref.read(notificationsApiProvider);
  final response = await api.list();
  final items = response.data['items'] as List;
  return items.map((e) => AppNotification.fromJson(e)).toList();
});

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationsListProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Уведомления'),
        actions: [
          TextButton(
            onPressed: () async {
              await ref.read(notificationsApiProvider).markAllRead();
              ref.invalidate(notificationsListProvider);
            },
            child: Text('Прочитать все', style: AppTextStyles.bodyM.copyWith(color: AppColors.primary)),
          ),
        ],
      ),
      body: notifications.when(
        data: (list) {
          if (list.isEmpty) {
            return const EmptyState(
              icon: Icons.notifications_none,
              title: 'Нет уведомлений',
            );
          }
          return RefreshIndicator(
            color: AppColors.primary,
            onRefresh: () async => ref.invalidate(notificationsListProvider),
            child: ListView.builder(
              itemCount: list.length,
              itemBuilder: (context, index) {
                final n = list[index];
                return _NotificationTile(notification: n);
              },
            ),
          );
        },
        loading: () => const Padding(
          padding: EdgeInsets.all(AppSpacing.base),
          child: LoadingShimmer(height: 72),
        ),
        error: (e, _) => Center(child: Text('Ошибка: $e')),
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  final AppNotification notification;

  const _NotificationTile({required this.notification});

  IconData get _icon => switch (notification.type) {
        'booking_new' => Icons.calendar_today,
        'booking_confirmed' => Icons.check_circle,
        'booking_cancelled' => Icons.cancel,
        'message' => Icons.chat_bubble,
        'review' => Icons.star,
        'reminder' => Icons.alarm,
        _ => Icons.notifications,
      };

  @override
  Widget build(BuildContext context) {
    return Container(
      color: notification.isRead ? null : AppColors.primaryLight.withValues(alpha: 0.3),
      child: ListTile(
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: AppColors.primaryLight,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(_icon, color: AppColors.primary, size: 20),
        ),
        title: Text(notification.title, style: AppTextStyles.bodyMBold),
        subtitle: Text(notification.body, style: AppTextStyles.caption, maxLines: 2, overflow: TextOverflow.ellipsis),
        trailing: Text(Formatters.timeAgo(notification.createdAt), style: AppTextStyles.caption),
      ),
    );
  }
}

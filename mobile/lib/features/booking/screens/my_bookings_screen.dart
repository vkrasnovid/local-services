import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../shared/models/booking.dart';
import '../../../shared/widgets/status_badge.dart';
import '../../../shared/widgets/loading_shimmer.dart';
import '../../../shared/widgets/empty_state.dart';

final myBookingsProvider = FutureProvider<List<Booking>>((ref) async {
  final api = ref.read(bookingsApiProvider);
  final response = await api.getMyBookings();
  final items = response.data['items'] as List;
  return items.map((e) => Booking.fromJson(e)).toList();
});

class MyBookingsScreen extends ConsumerWidget {
  const MyBookingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookings = ref.watch(myBookingsProvider);

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          title: const Text('Мои записи'),
          bottom: const TabBar(
            labelColor: AppColors.primary,
            unselectedLabelColor: AppColors.textSecondary,
            indicatorColor: AppColors.primary,
            tabs: [
              Tab(text: 'Активные'),
              Tab(text: 'История'),
            ],
          ),
        ),
        body: bookings.when(
          data: (list) {
            final active = list.where((b) => b.isActive).toList();
            final history = list.where((b) => !b.isActive).toList();
            return TabBarView(
              children: [
                _BookingList(
                  bookings: active,
                  emptyMessage: 'Нет активных записей',
                  emptyIcon: Icons.calendar_today,
                  onRefresh: () async => ref.invalidate(myBookingsProvider),
                ),
                _BookingList(
                  bookings: history,
                  emptyMessage: 'История пуста',
                  emptyIcon: Icons.history,
                  onRefresh: () async => ref.invalidate(myBookingsProvider),
                ),
              ],
            );
          },
          loading: () => const Padding(
            padding: EdgeInsets.all(AppSpacing.base),
            child: LoadingShimmer(),
          ),
          error: (e, _) => Center(child: Text('Ошибка: $e')),
        ),
      ),
    );
  }
}

class _BookingList extends StatelessWidget {
  final List<Booking> bookings;
  final String emptyMessage;
  final IconData emptyIcon;
  final Future<void> Function() onRefresh;

  const _BookingList({
    required this.bookings,
    required this.emptyMessage,
    required this.emptyIcon,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    if (bookings.isEmpty) {
      return EmptyState(icon: emptyIcon, title: emptyMessage);
    }
    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: onRefresh,
      child: ListView.builder(
        padding: const EdgeInsets.all(AppSpacing.base),
        itemCount: bookings.length,
        itemBuilder: (context, index) {
          final booking = bookings[index];
          return _BookingCard(booking: booking);
        },
      ),
    );
  }
}

class _BookingCard extends StatelessWidget {
  final Booking booking;

  const _BookingCard({required this.booking});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/booking-detail/${booking.id}'),
      child: Container(
        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          boxShadow: const [BoxShadow(color: Color(0x0F000000), blurRadius: 3, offset: Offset(0, 1))],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 20,
                  backgroundColor: AppColors.primaryLight,
                  child: const Icon(Icons.person, color: AppColors.primary, size: 20),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(booking.masterName ?? 'Мастер', style: AppTextStyles.bodyMBold),
                      Text(booking.serviceName ?? 'Услуга', style: AppTextStyles.caption),
                    ],
                  ),
                ),
                StatusBadge(status: booking.status),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                const Icon(Icons.calendar_today, size: 14, color: AppColors.textSecondary),
                const SizedBox(width: 6),
                Text(booking.slotDate ?? '', style: AppTextStyles.bodyM),
                const SizedBox(width: AppSpacing.base),
                const Icon(Icons.access_time, size: 14, color: AppColors.textSecondary),
                const SizedBox(width: 6),
                Text(booking.slotStartTime ?? '', style: AppTextStyles.bodyM),
                const Spacer(),
                Text(Formatters.price(booking.price), style: AppTextStyles.bodyMBold),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

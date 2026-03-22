import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../shared/models/booking.dart';
import '../../../shared/widgets/loading_shimmer.dart';
import '../../../shared/widgets/empty_state.dart';

final masterBookingsProvider = FutureProvider<List<Booking>>((ref) async {
  final api = ref.read(bookingsApiProvider);
  final response = await api.getMasterBookings(status: 'pending');
  final items = response.data['items'] as List;
  return items.map((e) => Booking.fromJson(e)).toList();
});

class MasterDashboardScreen extends ConsumerWidget {
  const MasterDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookings = ref.watch(masterBookingsProvider);
    final user = ref.watch(authStateProvider).value;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.primary,
          onRefresh: () async => ref.invalidate(masterBookingsProvider),
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.base),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Привет, ${user?.firstName ?? ''}!', style: AppTextStyles.h1),
                      const SizedBox(height: AppSpacing.xl),
                      // Stats row
                      Row(
                        children: [
                          _StatCard(title: 'Сегодня', value: '0 ₽', icon: Icons.today),
                          const SizedBox(width: AppSpacing.md),
                          _StatCard(title: 'Месяц', value: '0 ₽', icon: Icons.calendar_month),
                          const SizedBox(width: AppSpacing.md),
                          _StatCard(title: 'Заявки', value: '0', icon: Icons.inbox),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.xl),
                      // Quick actions
                      Row(
                        children: [
                          _QuickAction(
                            icon: Icons.list_alt,
                            label: 'Заявки',
                            onTap: () => context.push('/master/requests'),
                          ),
                          const SizedBox(width: AppSpacing.md),
                          _QuickAction(
                            icon: Icons.monetization_on_outlined,
                            label: 'Заработок',
                            onTap: () => context.push('/master/earnings'),
                          ),
                          const SizedBox(width: AppSpacing.md),
                          _QuickAction(
                            icon: Icons.add_circle_outline,
                            label: 'Услуга',
                            onTap: () => context.push('/master/services/add'),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.xl),
                      Text('Новые заявки', style: AppTextStyles.h2),
                    ],
                  ),
                ),
              ),
              bookings.when(
                data: (list) {
                  if (list.isEmpty) {
                    return const SliverToBoxAdapter(
                      child: EmptyState(
                        icon: Icons.inbox_outlined,
                        title: 'Нет новых заявок',
                        subtitle: 'Заявки от клиентов появятся здесь',
                      ),
                    );
                  }
                  return SliverPadding(
                    padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
                    sliver: SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) {
                          final booking = list[index];
                          return _PendingBookingCard(booking: booking, ref: ref);
                        },
                        childCount: list.length,
                      ),
                    ),
                  );
                },
                loading: () => const SliverToBoxAdapter(
                  child: Padding(
                    padding: EdgeInsets.all(AppSpacing.base),
                    child: LoadingShimmer(),
                  ),
                ),
                error: (e, _) => SliverToBoxAdapter(child: Center(child: Text('Ошибка: $e'))),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  const _StatCard({required this.title, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          boxShadow: const [BoxShadow(color: Color(0x0F000000), blurRadius: 3, offset: Offset(0, 1))],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 20, color: AppColors.primary),
            const SizedBox(height: AppSpacing.sm),
            Text(value, style: AppTextStyles.h3),
            Text(title, style: AppTextStyles.caption),
          ],
        ),
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _QuickAction({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(AppSpacing.md),
          decoration: BoxDecoration(
            color: AppColors.primaryLight,
            borderRadius: BorderRadius.circular(AppRadius.md),
          ),
          child: Column(
            children: [
              Icon(icon, color: AppColors.primary, size: 24),
              const SizedBox(height: 4),
              Text(label, style: AppTextStyles.captionBold.copyWith(color: AppColors.primary)),
            ],
          ),
        ),
      ),
    );
  }
}

class _PendingBookingCard extends StatelessWidget {
  final Booking booking;
  final WidgetRef ref;

  const _PendingBookingCard({required this.booking, required this.ref});

  @override
  Widget build(BuildContext context) {
    return Container(
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
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(booking.clientName ?? 'Клиент', style: AppTextStyles.bodyMBold),
                    Text(booking.serviceName ?? 'Услуга', style: AppTextStyles.caption),
                  ],
                ),
              ),
              Text(Formatters.price(booking.price), style: AppTextStyles.h3),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          Row(
            children: [
              const Icon(Icons.calendar_today, size: 14, color: AppColors.textSecondary),
              const SizedBox(width: 4),
              Text(booking.slotDate ?? '', style: AppTextStyles.caption),
              const SizedBox(width: AppSpacing.base),
              const Icon(Icons.access_time, size: 14, color: AppColors.textSecondary),
              const SizedBox(width: 4),
              Text(booking.slotStartTime ?? '', style: AppTextStyles.caption),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () async {
                    await ref.read(bookingsApiProvider).cancel(booking.id);
                    ref.invalidate(masterBookingsProvider);
                  },
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.error,
                    side: const BorderSide(color: AppColors.error),
                  ),
                  child: const Text('Отклонить'),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: ElevatedButton(
                  onPressed: () async {
                    await ref.read(bookingsApiProvider).updateStatus(booking.id, 'confirmed');
                    ref.invalidate(masterBookingsProvider);
                  },
                  child: const Text('Принять'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

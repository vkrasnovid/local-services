import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../shared/models/booking.dart';
import '../../../shared/widgets/loading_shimmer.dart';
import '../../../shared/widgets/empty_state.dart';

final allMasterBookingsProvider = FutureProvider<List<Booking>>((ref) async {
  final api = ref.read(bookingsApiProvider);
  final response = await api.getMasterBookings();
  final items = response.data['items'] as List;
  return items.map((e) => Booking.fromJson(e)).toList();
});

class BookingRequestsScreen extends ConsumerWidget {
  const BookingRequestsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookings = ref.watch(allMasterBookingsProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Заявки')),
      body: bookings.when(
        data: (list) {
          if (list.isEmpty) {
            return const EmptyState(
              icon: Icons.inbox_outlined,
              title: 'Нет заявок',
            );
          }
          return RefreshIndicator(
            color: AppColors.primary,
            onRefresh: () async => ref.invalidate(allMasterBookingsProvider),
            child: ListView.builder(
              padding: const EdgeInsets.all(AppSpacing.base),
              itemCount: list.length,
              itemBuilder: (context, index) {
                final booking = list[index];
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
                          Text(booking.clientName ?? 'Клиент', style: AppTextStyles.bodyMBold),
                          const Spacer(),
                          Text(booking.statusLabel, style: AppTextStyles.captionBold.copyWith(
                            color: booking.isPending ? AppColors.warning : AppColors.textSecondary,
                          )),
                        ],
                      ),
                      Text(booking.serviceName ?? '', style: AppTextStyles.caption),
                      const SizedBox(height: AppSpacing.sm),
                      Row(
                        children: [
                          Text('${booking.slotDate ?? ''} ${booking.slotStartTime ?? ''}', style: AppTextStyles.bodyM),
                          const Spacer(),
                          Text(Formatters.price(booking.price), style: AppTextStyles.bodyMBold),
                        ],
                      ),
                      if (booking.isPending) ...[
                        const SizedBox(height: AppSpacing.md),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton(
                                onPressed: () async {
                                  await ref.read(bookingsApiProvider).cancel(booking.id);
                                  ref.invalidate(allMasterBookingsProvider);
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
                                  ref.invalidate(allMasterBookingsProvider);
                                },
                                child: const Text('Принять'),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                );
              },
            ),
          );
        },
        loading: () => const Padding(
          padding: EdgeInsets.all(AppSpacing.base),
          child: LoadingShimmer(),
        ),
        error: (e, _) => Center(child: Text('Ошибка: $e')),
      ),
    );
  }
}

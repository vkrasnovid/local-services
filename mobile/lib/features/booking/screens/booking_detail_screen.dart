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
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/loading_shimmer.dart';

final bookingDetailProvider = FutureProvider.family<Booking, String>((ref, id) async {
  final api = ref.read(bookingsApiProvider);
  final response = await api.getById(id);
  return Booking.fromJson(response.data);
});

class BookingDetailScreen extends ConsumerWidget {
  final String bookingId;

  const BookingDetailScreen({super.key, required this.bookingId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookingAsync = ref.watch(bookingDetailProvider(bookingId));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Детали записи')),
      body: bookingAsync.when(
        data: (booking) => SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.base),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Status
              Center(child: StatusBadge(status: booking.status)),
              const SizedBox(height: AppSpacing.xl),

              // Info card
              Container(
                padding: const EdgeInsets.all(AppSpacing.base),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(AppRadius.md),
                  boxShadow: const [BoxShadow(color: Color(0x0F000000), blurRadius: 3, offset: Offset(0, 1))],
                ),
                child: Column(
                  children: [
                    _row('Мастер', booking.masterName ?? 'Мастер'),
                    _row('Услуга', booking.serviceName ?? 'Услуга'),
                    if (booking.serviceDuration != null)
                      _row('Длительность', Formatters.duration(booking.serviceDuration!)),
                    if (booking.slotDate != null)
                      _row('Дата', booking.slotDate!),
                    if (booking.slotStartTime != null)
                      _row('Время', '${booking.slotStartTime} — ${booking.slotEndTime ?? ''}'),
                    if (booking.address != null)
                      _row('Адрес', booking.address!),
                    if (booking.isOnline)
                      _row('Формат', 'Онлайн'),
                    const Divider(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Итого', style: AppTextStyles.h3),
                        Text(Formatters.price(booking.price), style: AppTextStyles.h2.copyWith(color: AppColors.primary)),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.xl),

              // Actions
              if (booking.chatRoomId != null)
                AppButton(
                  label: 'Написать мастеру',
                  isOutlined: true,
                  icon: Icons.chat_bubble_outline,
                  onPressed: () => context.push('/chat/${booking.chatRoomId}?name=${Uri.encodeComponent(booking.masterName ?? '')}'),
                ),
              const SizedBox(height: AppSpacing.md),
              if (booking.isActive)
                AppButton(
                  label: 'Отменить запись',
                  isOutlined: true,
                  icon: Icons.close,
                  onPressed: () => _showCancelDialog(context, ref, booking),
                ),
            ],
          ),
        ),
        loading: () => const Padding(
          padding: EdgeInsets.all(AppSpacing.base),
          child: LoadingShimmer(itemCount: 2),
        ),
        error: (e, _) => Center(child: Text('Ошибка: $e')),
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: AppTextStyles.bodyM.copyWith(color: AppColors.textSecondary)),
          Flexible(child: Text(value, style: AppTextStyles.bodyMBold, textAlign: TextAlign.end)),
        ],
      ),
    );
  }

  void _showCancelDialog(BuildContext context, WidgetRef ref, Booking booking) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Отменить запись?'),
        content: const Text('Вы уверены, что хотите отменить эту запись?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Нет'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ref.read(bookingsApiProvider).cancel(booking.id);
                ref.invalidate(bookingDetailProvider(bookingId));
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Ошибка: $e'), backgroundColor: AppColors.error),
                  );
                }
              }
            },
            child: const Text('Да, отменить', style: TextStyle(color: AppColors.error)),
          ),
        ],
      ),
    );
  }
}

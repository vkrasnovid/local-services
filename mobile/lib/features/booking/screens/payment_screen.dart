import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../shared/widgets/app_button.dart';

class PaymentScreen extends ConsumerStatefulWidget {
  final String bookingId;

  const PaymentScreen({super.key, required this.bookingId});

  @override
  ConsumerState<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends ConsumerState<PaymentScreen> {
  bool _processing = true;
  bool _success = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _processPayment();
  }

  Future<void> _processPayment() async {
    setState(() {
      _processing = true;
      _errorMessage = null;
    });

    try {
      final bookingsApi = ref.read(bookingsApiProvider);
      await bookingsApi.pay(widget.bookingId);

      if (mounted) {
        HapticFeedback.mediumImpact();
        setState(() {
          _processing = false;
          _success = true;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _processing = false;
          _success = false;
          _errorMessage = e.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_processing) {
      return Scaffold(
        backgroundColor: AppColors.background,
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(color: AppColors.primary),
              const SizedBox(height: AppSpacing.xl),
              Text('Обработка платежа...', style: AppTextStyles.bodyL),
            ],
          ),
        ),
      );
    }

    if (_success) {
      return Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.xxl),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: const BoxDecoration(
                    color: AppColors.successLight,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.check, size: 48, color: AppColors.success),
                ),
                const SizedBox(height: AppSpacing.xl),
                Text('Заказ оформлен!', style: AppTextStyles.h1),
                const SizedBox(height: AppSpacing.md),
                Text(
                  'Мастер подтвердит бронь в течение 30 минут',
                  style: AppTextStyles.bodyL.copyWith(color: AppColors.textSecondary),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.xxxl),
                AppButton(
                  label: 'На главную',
                  onPressed: () => context.go('/home'),
                ),
                const SizedBox(height: AppSpacing.md),
                AppButton(
                  label: 'Мои записи',
                  isOutlined: true,
                  onPressed: () => context.go('/bookings'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.xxl),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 64, color: AppColors.error),
              const SizedBox(height: AppSpacing.base),
              Text('Оплата не прошла', style: AppTextStyles.h2),
              if (_errorMessage != null) ...[
                const SizedBox(height: AppSpacing.sm),
                Text(
                  _errorMessage!,
                  style: AppTextStyles.bodyM.copyWith(color: AppColors.textSecondary),
                  textAlign: TextAlign.center,
                ),
              ],
              const SizedBox(height: AppSpacing.xl),
              AppButton(
                label: 'Попробовать снова',
                onPressed: _processPayment,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

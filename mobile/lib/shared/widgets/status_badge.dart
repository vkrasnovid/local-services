import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class StatusBadge extends StatelessWidget {
  final String status;

  const StatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final (label, bg, fg) = _statusData(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: AppTextStyles.captionBold.copyWith(color: fg),
      ),
    );
  }

  (String, Color, Color) _statusData(String status) {
    return switch (status) {
      'pending' => ('Ожидает', AppColors.warningLight, AppColors.warning),
      'confirmed' => ('Подтверждён', AppColors.infoLight, AppColors.info),
      'in_progress' => ('В процессе', AppColors.infoLight, AppColors.info),
      'completed' => ('Завершён', AppColors.successLight, AppColors.success),
      'cancelled' => ('Отменён', AppColors.errorLight, AppColors.error),
      _ => (status, AppColors.background, AppColors.textSecondary),
    };
  }
}

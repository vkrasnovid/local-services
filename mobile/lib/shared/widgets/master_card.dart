import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/utils/formatters.dart';
import '../../shared/models/master.dart';

class MasterCard extends StatelessWidget {
  final Master master;
  final VoidCallback? onTap;
  final bool isHorizontal;

  const MasterCard({
    super.key,
    required this.master,
    this.onTap,
    this.isHorizontal = false,
  });

  @override
  Widget build(BuildContext context) {
    if (isHorizontal) return _buildHorizontalCard();
    return _buildVerticalCard();
  }

  Widget _buildVerticalCard() {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0F000000),
              blurRadius: 3,
              offset: Offset(0, 1),
            ),
          ],
        ),
        child: Row(
          children: [
            _avatar(64),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(master.user.fullName, style: AppTextStyles.h3),
                      ),
                      if (master.isVerified)
                        const Icon(Icons.verified, size: 16, color: AppColors.success),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    [master.category?.name, master.user.city]
                        .where((e) => e != null)
                        .join(' · '),
                    style: AppTextStyles.caption,
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(Icons.star, size: 14, color: AppColors.accent),
                      const SizedBox(width: 2),
                      Text(
                        Formatters.rating(master.ratingAvg),
                        style: AppTextStyles.captionBold.copyWith(color: AppColors.textPrimary),
                      ),
                      Text(' (${master.ratingCount})', style: AppTextStyles.caption),
                    ],
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                if (master.priceFrom != null)
                  Text(
                    'от ${Formatters.price(master.priceFrom!)}',
                    style: AppTextStyles.bodyMBold,
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHorizontalCard() {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 160,
        margin: const EdgeInsets.only(right: AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0F000000),
              blurRadius: 3,
              offset: Offset(0, 1),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Stack(
              children: [
                ClipRRect(
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(AppRadius.md)),
                  child: master.user.avatarUrl != null
                      ? CachedNetworkImage(
                          imageUrl: master.user.avatarUrl!,
                          height: 100,
                          width: 160,
                          fit: BoxFit.cover,
                          placeholder: (_, __) => Container(
                            height: 100,
                            color: AppColors.background,
                          ),
                          errorWidget: (_, __, ___) => Container(
                            height: 100,
                            color: AppColors.background,
                            child: const Icon(Icons.person, size: 40, color: AppColors.textTertiary),
                          ),
                        )
                      : Container(
                          height: 100,
                          width: 160,
                          color: AppColors.primaryLight,
                          child: const Icon(Icons.person, size: 40, color: AppColors.primary),
                        ),
                ),
                Positioned(
                  top: 6,
                  right: 6,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(AppRadius.xs),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.star, size: 12, color: AppColors.accent),
                        const SizedBox(width: 2),
                        Text(
                          Formatters.rating(master.ratingAvg),
                          style: AppTextStyles.captionBold.copyWith(color: Colors.white),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            Padding(
              padding: const EdgeInsets.all(AppSpacing.sm),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    master.user.fullName,
                    style: AppTextStyles.h3,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    master.category?.name ?? '',
                    style: AppTextStyles.caption,
                    maxLines: 1,
                  ),
                  const SizedBox(height: 4),
                  if (master.priceFrom != null)
                    Text(
                      'от ${Formatters.price(master.priceFrom!)}',
                      style: AppTextStyles.bodyMBold,
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _avatar(double size) {
    if (master.user.avatarUrl != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(size / 2),
        child: CachedNetworkImage(
          imageUrl: master.user.avatarUrl!,
          width: size,
          height: size,
          fit: BoxFit.cover,
          placeholder: (_, __) => _placeholderAvatar(size),
          errorWidget: (_, __, ___) => _placeholderAvatar(size),
        ),
      );
    }
    return _placeholderAvatar(size);
  }

  Widget _placeholderAvatar(double size) {
    return Container(
      width: size,
      height: size,
      decoration: const BoxDecoration(
        color: AppColors.primaryLight,
        shape: BoxShape.circle,
      ),
      child: Icon(Icons.person, size: size * 0.5, color: AppColors.primary),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../shared/models/master.dart';
import '../../../shared/widgets/rating_stars.dart';
import '../../../shared/widgets/loading_shimmer.dart';
import '../../../shared/widgets/error_view.dart';

final masterDetailProvider = FutureProvider.family<Master, String>((ref, id) async {
  final api = ref.read(mastersApiProvider);
  final response = await api.getById(id);
  return Master.fromJson(response.data);
});

class MasterProfileScreen extends ConsumerWidget {
  final String masterId;

  const MasterProfileScreen({super.key, required this.masterId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final masterAsync = ref.watch(masterDetailProvider(masterId));

    return Scaffold(
      backgroundColor: AppColors.background,
      body: masterAsync.when(
        data: (master) => _MasterProfileContent(master: master),
        loading: () => const SafeArea(
          child: Padding(
            padding: EdgeInsets.all(AppSpacing.base),
            child: LoadingShimmer(itemCount: 5),
          ),
        ),
        error: (e, _) => ErrorView(
          message: 'Ошибка загрузки профиля',
          onRetry: () => ref.invalidate(masterDetailProvider(masterId)),
        ),
      ),
    );
  }
}

class _MasterProfileContent extends StatelessWidget {
  final Master master;

  const _MasterProfileContent({required this.master});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        CustomScrollView(
          slivers: [
            // Hero header
            SliverAppBar(
              expandedHeight: 220,
              pinned: true,
              backgroundColor: AppColors.secondary,
              leading: IconButton(
                icon: const Icon(Icons.arrow_back, color: Colors.white),
                onPressed: () => Navigator.of(context).pop(),
              ),
              flexibleSpace: FlexibleSpaceBar(
                background: master.user.avatarUrl != null
                    ? CachedNetworkImage(
                        imageUrl: master.user.avatarUrl!,
                        fit: BoxFit.cover,
                        placeholder: (_, __) => Container(color: AppColors.secondary),
                        errorWidget: (_, __, ___) => Container(
                          color: AppColors.secondary,
                          child: const Icon(Icons.person, size: 80, color: Colors.white30),
                        ),
                      )
                    : Container(
                        color: AppColors.secondary,
                        child: const Icon(Icons.person, size: 80, color: Colors.white30),
                      ),
              ),
            ),

            SliverToBoxAdapter(
              child: Container(
                decoration: const BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(AppRadius.lg)),
                ),
                transform: Matrix4.translationValues(0, -20, 0),
                padding: const EdgeInsets.fromLTRB(AppSpacing.base, AppSpacing.xl, AppSpacing.base, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Name & verification
                    Row(
                      children: [
                        Expanded(child: Text(master.user.fullName, style: AppTextStyles.h1)),
                        if (master.isVerified)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppColors.successLight,
                              borderRadius: BorderRadius.circular(AppRadius.xs),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.verified, size: 14, color: AppColors.success),
                                const SizedBox(width: 4),
                                Text('Проверен', style: AppTextStyles.captionBold.copyWith(color: AppColors.success)),
                              ],
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    if (master.category != null)
                      Text(master.category!.name, style: AppTextStyles.bodyM.copyWith(color: AppColors.textSecondary)),
                    if (master.user.city != null || master.district != null) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(Icons.location_on_outlined, size: 16, color: AppColors.textSecondary),
                          const SizedBox(width: 4),
                          Text(
                            [master.user.city, master.district].where((e) => e != null).join(', '),
                            style: AppTextStyles.bodyM.copyWith(color: AppColors.textSecondary),
                          ),
                        ],
                      ),
                    ],

                    // Rating
                    const SizedBox(height: AppSpacing.md),
                    Row(
                      children: [
                        RatingStars(rating: master.ratingAvg, size: 18),
                        const SizedBox(width: 8),
                        Text(Formatters.rating(master.ratingAvg), style: AppTextStyles.h3),
                        const SizedBox(width: 4),
                        Text('(${master.ratingCount} отзывов)', style: AppTextStyles.bodyM.copyWith(color: AppColors.textSecondary)),
                      ],
                    ),

                    // About
                    if (master.description != null) ...[
                      const SizedBox(height: AppSpacing.xl),
                      Text('О мастере', style: AppTextStyles.h2),
                      const SizedBox(height: AppSpacing.sm),
                      Text(master.description!, style: AppTextStyles.bodyL),
                    ],

                    // Services
                    if (master.services != null && master.services!.isNotEmpty) ...[
                      const SizedBox(height: AppSpacing.xl),
                      Text('Услуги', style: AppTextStyles.h2),
                      const SizedBox(height: AppSpacing.md),
                      ...master.services!.map((service) => Container(
                        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: BoxDecoration(
                          color: AppColors.background,
                          borderRadius: BorderRadius.circular(AppRadius.sm),
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(service.name, style: AppTextStyles.h3),
                                  const SizedBox(height: 2),
                                  if (service.description != null)
                                    Text(service.description!, style: AppTextStyles.caption, maxLines: 2, overflow: TextOverflow.ellipsis),
                                  const SizedBox(height: 4),
                                  Row(
                                    children: [
                                      const Icon(Icons.access_time, size: 14, color: AppColors.textSecondary),
                                      const SizedBox(width: 4),
                                      Text(Formatters.duration(service.durationMinutes), style: AppTextStyles.caption),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: AppSpacing.md),
                            Text(Formatters.price(service.price), style: AppTextStyles.h3),
                          ],
                        ),
                      )),
                    ],

                    // Portfolio
                    if (master.portfolio != null && master.portfolio!.isNotEmpty) ...[
                      const SizedBox(height: AppSpacing.xl),
                      Text('Портфолио', style: AppTextStyles.h2),
                      const SizedBox(height: AppSpacing.md),
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 3,
                          crossAxisSpacing: 4,
                          mainAxisSpacing: 4,
                        ),
                        itemCount: master.portfolio!.length,
                        itemBuilder: (context, index) {
                          return ClipRRect(
                            borderRadius: BorderRadius.circular(AppRadius.sm),
                            child: CachedNetworkImage(
                              imageUrl: master.portfolio![index].imageUrl,
                              fit: BoxFit.cover,
                              placeholder: (_, __) => Container(color: AppColors.divider),
                              errorWidget: (_, __, ___) => Container(
                                color: AppColors.divider,
                                child: const Icon(Icons.image, color: AppColors.textTertiary),
                              ),
                            ),
                          );
                        },
                      ),
                    ],

                    // Reviews preview
                    if (master.reviewsPreview != null && master.reviewsPreview!.isNotEmpty) ...[
                      const SizedBox(height: AppSpacing.xl),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Отзывы', style: AppTextStyles.h2),
                          TextButton(
                            onPressed: () {},
                            child: Text('Все (${master.ratingCount})', style: AppTextStyles.bodyM.copyWith(color: AppColors.primary)),
                          ),
                        ],
                      ),
                      ...master.reviewsPreview!.map((review) => Container(
                        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: BoxDecoration(
                          color: AppColors.background,
                          borderRadius: BorderRadius.circular(AppRadius.sm),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(review.clientName ?? 'Клиент', style: AppTextStyles.bodyMBold),
                                const Spacer(),
                                Text(Formatters.timeAgo(review.createdAt), style: AppTextStyles.caption),
                              ],
                            ),
                            const SizedBox(height: 4),
                            RatingStars(rating: review.rating.toDouble(), size: 14),
                            if (review.text != null) ...[
                              const SizedBox(height: 8),
                              Text(review.text!, style: AppTextStyles.bodyM),
                            ],
                            if (review.masterReply != null) ...[
                              const SizedBox(height: 8),
                              Container(
                                padding: const EdgeInsets.all(AppSpacing.sm),
                                decoration: BoxDecoration(
                                  color: AppColors.surface,
                                  borderRadius: BorderRadius.circular(AppRadius.xs),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Ответ мастера', style: AppTextStyles.captionBold),
                                    const SizedBox(height: 4),
                                    Text(review.masterReply!, style: AppTextStyles.bodyM),
                                  ],
                                ),
                              ),
                            ],
                          ],
                        ),
                      )),
                    ],

                    // Work hours
                    if (master.workHours != null) ...[
                      const SizedBox(height: AppSpacing.xl),
                      Text('Рабочие часы', style: AppTextStyles.h2),
                      const SizedBox(height: AppSpacing.md),
                      ..._buildWorkHours(master.workHours!),
                    ],

                    const SizedBox(height: 100),
                  ],
                ),
              ),
            ),
          ],
        ),

        // Bottom bar
        Positioned(
          left: 0,
          right: 0,
          bottom: 0,
          child: Container(
            padding: EdgeInsets.fromLTRB(AppSpacing.base, AppSpacing.md, AppSpacing.base, MediaQuery.of(context).padding.bottom + AppSpacing.md),
            decoration: const BoxDecoration(
              color: AppColors.surface,
              boxShadow: [BoxShadow(color: Color(0x1A000000), blurRadius: 8, offset: Offset(0, -2))],
            ),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {},
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(0, 48),
                      side: const BorderSide(color: AppColors.secondary),
                    ),
                    child: const Text('Написать'),
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  flex: 2,
                  child: ElevatedButton(
                    onPressed: () => context.push('/booking/${master.id}'),
                    style: ElevatedButton.styleFrom(minimumSize: const Size(0, 48)),
                    child: const Text('Заказать'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  static const _dayNames = {
    'mon': 'Пн',
    'tue': 'Вт',
    'wed': 'Ср',
    'thu': 'Чт',
    'fri': 'Пт',
    'sat': 'Сб',
    'sun': 'Вс',
  };

  List<Widget> _buildWorkHours(Map<String, dynamic> hours) {
    return _dayNames.entries.map((entry) {
      final data = hours[entry.key];
      final value = data != null ? '${data['start']} — ${data['end']}' : 'выходной';
      return Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Row(
          children: [
            SizedBox(width: 40, child: Text(entry.value, style: AppTextStyles.bodyM)),
            Text(value, style: AppTextStyles.bodyM.copyWith(
              color: data != null ? AppColors.textPrimary : AppColors.textTertiary,
            )),
          ],
        ),
      );
    }).toList();
  }
}

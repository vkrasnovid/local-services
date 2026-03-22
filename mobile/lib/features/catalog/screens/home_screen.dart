import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../shared/models/master.dart';
import '../../../shared/models/category.dart' as cat;
import '../../../shared/widgets/master_card.dart';
import '../../../shared/widgets/loading_shimmer.dart';
import '../../../shared/widgets/error_view.dart';

final categoriesProvider = FutureProvider<List<cat.Category>>((ref) async {
  final api = ref.read(categoriesApiProvider);
  final response = await api.list();
  final items = response.data['items'] as List;
  return items.map((e) => cat.Category.fromJson(e)).toList();
});

final featuredMastersProvider = FutureProvider<List<Master>>((ref) async {
  final api = ref.read(mastersApiProvider);
  final response = await api.list(params: {'sort_by': 'rating', 'page_size': 10});
  final items = response.data['items'] as List;
  return items.map((e) => Master.fromJson(e)).toList();
});

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final categories = ref.watch(categoriesProvider);
    final masters = ref.watch(featuredMastersProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.primary,
          onRefresh: () async {
            ref.invalidate(categoriesProvider);
            ref.invalidate(featuredMastersProvider);
          },
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.base),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Location + notification
                      Row(
                        children: [
                          const Icon(Icons.location_on_outlined, size: 20, color: AppColors.primary),
                          const SizedBox(width: 4),
                          Text('Москва', style: AppTextStyles.bodyMBold),
                          const Spacer(),
                          IconButton(
                            icon: const Icon(Icons.notifications_outlined),
                            onPressed: () => context.push('/notifications'),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.md),
                      // Search bar
                      GestureDetector(
                        onTap: () {},
                        child: Container(
                          height: 48,
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          decoration: BoxDecoration(
                            color: AppColors.surface,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: AppColors.divider),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.search, color: AppColors.textTertiary),
                              const SizedBox(width: 12),
                              Text(
                                'Поиск мастеров и услуг',
                                style: AppTextStyles.bodyM.copyWith(color: AppColors.textTertiary),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Categories
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 100,
                  child: categories.when(
                    data: (cats) => ListView.builder(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
                      itemCount: cats.length,
                      itemBuilder: (context, index) {
                        final c = cats[index];
                        return _CategoryChip(
                          name: c.name,
                          icon: c.icon,
                          onTap: () => context.push('/category/${c.id}?name=${Uri.encodeComponent(c.name)}'),
                        );
                      },
                    ),
                    loading: () => const Center(child: CircularProgressIndicator(color: AppColors.primary)),
                    error: (e, _) => Center(child: Text('Ошибка загрузки', style: AppTextStyles.caption)),
                  ),
                ),
              ),

              // Top masters header
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(AppSpacing.base, AppSpacing.lg, AppSpacing.base, AppSpacing.md),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Топ мастера', style: AppTextStyles.h2),
                      TextButton(
                        onPressed: () {},
                        child: Text('Все', style: AppTextStyles.bodyM.copyWith(color: AppColors.primary)),
                      ),
                    ],
                  ),
                ),
              ),

              // Horizontal master cards
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 210,
                  child: masters.when(
                    data: (list) => ListView.builder(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
                      itemCount: list.length,
                      itemBuilder: (context, index) {
                        return MasterCard(
                          master: list[index],
                          isHorizontal: true,
                          onTap: () => context.push('/master/${list[index].id}'),
                        );
                      },
                    ),
                    loading: () => const Center(child: CircularProgressIndicator(color: AppColors.primary)),
                    error: (e, _) => ErrorView(message: 'Ошибка загрузки', onRetry: () => ref.invalidate(featuredMastersProvider)),
                  ),
                ),
              ),

              // Recommended header
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(AppSpacing.base, AppSpacing.lg, AppSpacing.base, AppSpacing.md),
                  child: Text('Рекомендуем', style: AppTextStyles.h2),
                ),
              ),

              // Vertical master list
              masters.when(
                data: (list) => SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
                  sliver: SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) => MasterCard(
                        master: list[index],
                        onTap: () => context.push('/master/${list[index].id}'),
                      ),
                      childCount: list.length,
                    ),
                  ),
                ),
                loading: () => const SliverToBoxAdapter(
                  child: Padding(
                    padding: EdgeInsets.symmetric(horizontal: AppSpacing.base),
                    child: LoadingShimmer(),
                  ),
                ),
                error: (_, __) => const SliverToBoxAdapter(child: SizedBox()),
              ),

              const SliverToBoxAdapter(child: SizedBox(height: 20)),
            ],
          ),
        ),
      ),
    );
  }
}

class _CategoryChip extends StatelessWidget {
  final String name;
  final String icon;
  final VoidCallback onTap;

  const _CategoryChip({
    required this.name,
    required this.icon,
    required this.onTap,
  });

  static const _categoryColors = {
    'Уборка': Color(0xFF4CAF50),
    'Ремонт': Color(0xFFFF9800),
    'Красота': Color(0xFFE91E63),
    'Авто': Color(0xFF2196F3),
    'IT': Color(0xFF9C27B0),
    'Репетиторы': Color(0xFF00BCD4),
  };

  @override
  Widget build(BuildContext context) {
    final color = _categoryColors[name] ?? AppColors.textSecondary;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 72,
        margin: const EdgeInsets.only(right: AppSpacing.md),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: Center(
                child: Text(icon, style: const TextStyle(fontSize: 24)),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              name,
              style: AppTextStyles.caption,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}

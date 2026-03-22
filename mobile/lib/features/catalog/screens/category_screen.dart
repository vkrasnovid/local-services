import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../shared/models/master.dart';
import '../../../shared/widgets/master_card.dart';
import '../../../shared/widgets/loading_shimmer.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../../shared/widgets/error_view.dart';

final categoryMastersProvider = FutureProvider.family<List<Master>, String>((ref, categoryId) async {
  final api = ref.read(mastersApiProvider);
  final response = await api.list(params: {'category_id': categoryId, 'sort_by': 'rating'});
  final items = response.data['items'] as List;
  return items.map((e) => Master.fromJson(e)).toList();
});

class CategoryScreen extends ConsumerWidget {
  final String categoryId;
  final String categoryName;

  const CategoryScreen({
    super.key,
    required this.categoryId,
    required this.categoryName,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final masters = ref.watch(categoryMastersProvider(categoryId));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: Text(categoryName)),
      body: Column(
        children: [
          // Filter chips
          SizedBox(
            height: 50,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base, vertical: AppSpacing.sm),
              children: [
                _FilterChip(label: 'По рейтингу', isSelected: true),
                _FilterChip(label: 'По цене ↑'),
                _FilterChip(label: 'По цене ↓'),
                _FilterChip(label: 'Рейтинг 4+'),
              ],
            ),
          ),
          Expanded(
            child: masters.when(
              data: (list) {
                if (list.isEmpty) {
                  return const EmptyState(
                    icon: Icons.search_off,
                    title: 'Мастера не найдены',
                    subtitle: 'По вашим фильтрам ничего не найдено',
                  );
                }
                return RefreshIndicator(
                  color: AppColors.primary,
                  onRefresh: () async => ref.invalidate(categoryMastersProvider(categoryId)),
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
                    itemCount: list.length,
                    itemBuilder: (context, index) => MasterCard(
                      master: list[index],
                      onTap: () => context.push('/master/${list[index].id}'),
                    ),
                  ),
                );
              },
              loading: () => const Padding(
                padding: EdgeInsets.all(AppSpacing.base),
                child: LoadingShimmer(),
              ),
              error: (e, _) => ErrorView(
                message: 'Ошибка загрузки',
                onRetry: () => ref.invalidate(categoryMastersProvider(categoryId)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;

  const _FilterChip({required this.label, this.isSelected = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(right: AppSpacing.sm),
      child: Chip(
        label: Text(
          label,
          style: AppTextStyles.captionBold.copyWith(
            color: isSelected ? Colors.white : AppColors.textPrimary,
          ),
        ),
        backgroundColor: isSelected ? AppColors.primary : AppColors.surface,
        side: BorderSide(color: isSelected ? AppColors.primary : AppColors.divider),
        padding: const EdgeInsets.symmetric(horizontal: 4),
      ),
    );
  }
}

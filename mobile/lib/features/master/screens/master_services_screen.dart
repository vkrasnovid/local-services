import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../shared/models/service.dart';
import '../../../shared/widgets/loading_shimmer.dart';
import '../../../shared/widgets/empty_state.dart';

final myServicesProvider = FutureProvider<List<Service>>((ref) async {
  final api = ref.read(mastersApiProvider);
  final response = await api.getMyServices();
  final items = response.data['items'] as List;
  return items.map((e) => Service.fromJson(e)).toList();
});

class MyServicesScreen extends ConsumerWidget {
  const MyServicesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final services = ref.watch(myServicesProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Мои услуги')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/master/services/add'),
        backgroundColor: AppColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: services.when(
        data: (list) {
          if (list.isEmpty) {
            return EmptyState(
              icon: Icons.build_outlined,
              title: 'Нет услуг',
              subtitle: 'Добавьте свою первую услугу',
              buttonLabel: 'Добавить',
              onButtonPressed: () => context.push('/master/services/add'),
            );
          }
          return RefreshIndicator(
            color: AppColors.primary,
            onRefresh: () async => ref.invalidate(myServicesProvider),
            child: ListView.builder(
              padding: const EdgeInsets.all(AppSpacing.base),
              itemCount: list.length,
              itemBuilder: (context, index) {
                final svc = list[index];
                return Container(
                  margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(AppRadius.md),
                    boxShadow: const [BoxShadow(color: Color(0x0F000000), blurRadius: 3, offset: Offset(0, 1))],
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(svc.name, style: AppTextStyles.h3),
                            const SizedBox(height: 2),
                            Text(
                              '${Formatters.duration(svc.durationMinutes)} · ${Formatters.price(svc.price)}',
                              style: AppTextStyles.bodyM.copyWith(color: AppColors.textSecondary),
                            ),
                          ],
                        ),
                      ),
                      Switch(
                        value: svc.isActive,
                        onChanged: (val) async {
                          await ref.read(mastersApiProvider).updateService(svc.id, {'is_active': val});
                          ref.invalidate(myServicesProvider);
                        },
                        activeColor: AppColors.primary,
                      ),
                      IconButton(
                        icon: const Icon(Icons.edit, size: 20, color: AppColors.textSecondary),
                        onPressed: () => context.push('/master/services/edit/${svc.id}'),
                      ),
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

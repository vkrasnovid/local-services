import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../shared/models/master.dart';
import '../../../shared/models/service.dart';
import '../../../shared/widgets/app_button.dart';
import '../../catalog/screens/master_profile_screen.dart';

class BookingScreen extends ConsumerStatefulWidget {
  final String masterId;

  const BookingScreen({super.key, required this.masterId});

  @override
  ConsumerState<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends ConsumerState<BookingScreen> {
  int _step = 0; // 0=service, 1=date/time, 2=confirm
  Service? _selectedService;
  DateTime _selectedDate = DateTime.now();
  String? _selectedSlotId;
  String? _selectedSlotTime;
  final _notesController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _createBooking() async {
    if (_selectedService == null || _selectedSlotId == null) return;
    setState(() => _isLoading = true);

    try {
      final api = ref.read(bookingsApiProvider);
      final response = await api.create({
        'master_id': widget.masterId,
        'service_id': _selectedService!.id,
        'slot_id': _selectedSlotId,
        'notes': _notesController.text,
      });
      final bookingId = response.data['id'] as String;
      if (mounted) {
        HapticFeedback.mediumImpact();
        context.go('/payment/$bookingId');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Ошибка: $e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final masterAsync = ref.watch(masterDetailProvider(widget.masterId));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(['Выбор услуги', 'Дата и время', 'Подтверждение'][_step]),
      ),
      body: masterAsync.when(
        data: (master) => Column(
          children: [
            // Step indicator
            Padding(
              padding: const EdgeInsets.all(AppSpacing.base),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(3, (i) => Container(
                  width: i <= _step ? 10 : 8,
                  height: i <= _step ? 10 : 8,
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: i <= _step ? AppColors.primary : AppColors.divider,
                  ),
                )),
              ),
            ),
            Expanded(
              child: _step == 0
                  ? _buildServiceStep(master)
                  : _step == 1
                      ? _buildDateStep()
                      : _buildConfirmStep(master),
            ),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator(color: AppColors.primary)),
        error: (e, _) => Center(child: Text('Ошибка загрузки: $e')),
      ),
    );
  }

  Widget _buildServiceStep(Master master) {
    final services = master.services ?? [];
    return Column(
      children: [
        // Master mini header
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
          child: Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: AppColors.primaryLight,
                child: const Icon(Icons.person, color: AppColors.primary),
              ),
              const SizedBox(width: AppSpacing.sm),
              Text(master.user.fullName, style: AppTextStyles.bodyMBold),
              const Spacer(),
              Row(
                children: [
                  const Icon(Icons.star, size: 14, color: AppColors.accent),
                  const SizedBox(width: 2),
                  Text(Formatters.rating(master.ratingAvg), style: AppTextStyles.captionBold),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.base),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
            itemCount: services.length,
            itemBuilder: (context, index) {
              final svc = services[index];
              final isSelected = _selectedService?.id == svc.id;
              return GestureDetector(
                onTap: () => setState(() => _selectedService = svc),
                child: Container(
                  margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: isSelected ? AppColors.primaryLight : AppColors.surface,
                    borderRadius: BorderRadius.circular(AppRadius.md),
                    border: Border.all(
                      color: isSelected ? AppColors.primary : AppColors.divider,
                      width: isSelected ? 2 : 1,
                    ),
                  ),
                  child: Row(
                    children: [
                      Radio<String>(
                        value: svc.id,
                        groupValue: _selectedService?.id,
                        onChanged: (v) => setState(() => _selectedService = svc),
                        activeColor: AppColors.primary,
                      ),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(svc.name, style: AppTextStyles.h3),
                            if (svc.description != null)
                              Text(svc.description!, style: AppTextStyles.caption, maxLines: 2),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                const Icon(Icons.access_time, size: 14, color: AppColors.textSecondary),
                                const SizedBox(width: 4),
                                Text(Formatters.duration(svc.durationMinutes), style: AppTextStyles.caption),
                              ],
                            ),
                          ],
                        ),
                      ),
                      Text(Formatters.price(svc.price), style: AppTextStyles.h3),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(AppSpacing.base),
          child: AppButton(
            label: 'Далее',
            onPressed: _selectedService != null ? () => setState(() => _step = 1) : null,
          ),
        ),
      ],
    );
  }

  Widget _buildDateStep() {
    return Column(
      children: [
        // Date selector
        SizedBox(
          height: 80,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
            itemCount: 14,
            itemBuilder: (context, index) {
              final date = DateTime.now().add(Duration(days: index));
              final isSelected = _selectedDate.day == date.day &&
                  _selectedDate.month == date.month;
              return GestureDetector(
                onTap: () => setState(() {
                  _selectedDate = date;
                  _selectedSlotId = null;
                  _selectedSlotTime = null;
                }),
                child: Container(
                  width: 56,
                  margin: const EdgeInsets.only(right: AppSpacing.sm),
                  decoration: BoxDecoration(
                    color: isSelected ? AppColors.primary : AppColors.surface,
                    borderRadius: BorderRadius.circular(AppRadius.md),
                    border: Border.all(color: isSelected ? AppColors.primary : AppColors.divider),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        DateFormat('EE', 'ru').format(date),
                        style: AppTextStyles.caption.copyWith(
                          color: isSelected ? Colors.white : AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${date.day}',
                        style: AppTextStyles.h2.copyWith(
                          color: isSelected ? Colors.white : AppColors.textPrimary,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        const SizedBox(height: AppSpacing.xl),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text('Доступное время', style: AppTextStyles.h3),
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        Expanded(
          child: GridView.builder(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              childAspectRatio: 2.2,
              crossAxisSpacing: 8,
              mainAxisSpacing: 8,
            ),
            itemCount: 12,
            itemBuilder: (context, index) {
              final hour = 9 + index;
              final time = '${hour.toString().padLeft(2, '0')}:00';
              final slotId = 'slot-$index';
              final isSelected = _selectedSlotId == slotId;
              return GestureDetector(
                onTap: () => setState(() {
                  _selectedSlotId = slotId;
                  _selectedSlotTime = time;
                }),
                child: Container(
                  decoration: BoxDecoration(
                    color: isSelected ? AppColors.primary : AppColors.surface,
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                    border: Border.all(color: isSelected ? AppColors.primary : AppColors.divider),
                  ),
                  child: Center(
                    child: Text(
                      time,
                      style: AppTextStyles.bodyMBold.copyWith(
                        color: isSelected ? Colors.white : AppColors.textPrimary,
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(AppSpacing.base),
          child: AppButton(
            label: 'Далее',
            onPressed: _selectedSlotId != null ? () => setState(() => _step = 2) : null,
          ),
        ),
      ],
    );
  }

  Widget _buildConfirmStep(Master master) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.base),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Summary card
          Container(
            padding: const EdgeInsets.all(AppSpacing.base),
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
                    CircleAvatar(
                      radius: 20,
                      backgroundColor: AppColors.primaryLight,
                      child: const Icon(Icons.person, color: AppColors.primary, size: 20),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Text(master.user.fullName, style: AppTextStyles.bodyMBold),
                  ],
                ),
                const Divider(height: 24),
                _infoRow('Услуга', _selectedService?.name ?? ''),
                _infoRow('Длительность', Formatters.duration(_selectedService?.durationMinutes ?? 0)),
                _infoRow('Дата', DateFormat('d MMMM yyyy', 'ru').format(_selectedDate)),
                _infoRow('Время', _selectedSlotTime ?? ''),
                const Divider(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Итого', style: AppTextStyles.h3),
                    Text(
                      Formatters.price(_selectedService?.price ?? 0),
                      style: AppTextStyles.h2.copyWith(color: AppColors.primary),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          TextFormField(
            controller: _notesController,
            maxLines: 3,
            decoration: const InputDecoration(
              hintText: 'Комментарий для мастера',
              alignLabelWithHint: true,
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          Text(
            'Нажимая «Оплатить», вы соглашаетесь с условиями оферты',
            style: AppTextStyles.caption,
          ),
          const SizedBox(height: AppSpacing.base),
          AppButton(
            label: 'Оплатить ${Formatters.price(_selectedService?.price ?? 0)}',
            isLoading: _isLoading,
            onPressed: _createBooking,
          ),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: AppTextStyles.bodyM.copyWith(color: AppColors.textSecondary)),
          Text(value, style: AppTextStyles.bodyMBold),
        ],
      ),
    );
  }
}

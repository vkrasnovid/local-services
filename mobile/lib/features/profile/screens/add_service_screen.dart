import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/utils/validators.dart';
import '../../../shared/widgets/app_button.dart';
import 'my_services_screen.dart';

class AddServiceScreen extends ConsumerStatefulWidget {
  final String? serviceId;

  const AddServiceScreen({super.key, this.serviceId});

  @override
  ConsumerState<AddServiceScreen> createState() => _AddServiceScreenState();
}

class _AddServiceScreenState extends ConsumerState<AddServiceScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _priceController = TextEditingController();
  final _durationController = TextEditingController();
  bool _isLoading = false;

  bool get isEditing => widget.serviceId != null;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _priceController.dispose();
    _durationController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);

    try {
      final data = {
        'name': _nameController.text.trim(),
        'description': _descriptionController.text.trim(),
        'price': double.parse(_priceController.text),
        'duration_minutes': int.parse(_durationController.text),
      };

      final api = ref.read(mastersApiProvider);
      if (isEditing) {
        await api.updateService(widget.serviceId!, data);
      } else {
        await api.createService(data);
      }

      ref.invalidate(myServicesProvider);
      if (mounted) Navigator.pop(context);
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
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: Text(isEditing ? 'Редактировать услугу' : 'Новая услуга')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _nameController,
                validator: Validators.required,
                decoration: const InputDecoration(hintText: 'Название услуги'),
              ),
              const SizedBox(height: AppSpacing.md),
              TextFormField(
                controller: _descriptionController,
                maxLines: 3,
                decoration: const InputDecoration(hintText: 'Описание'),
              ),
              const SizedBox(height: AppSpacing.md),
              TextFormField(
                controller: _priceController,
                keyboardType: TextInputType.number,
                validator: Validators.price,
                decoration: const InputDecoration(hintText: 'Цена (₽)', suffixText: '₽'),
              ),
              const SizedBox(height: AppSpacing.md),
              TextFormField(
                controller: _durationController,
                keyboardType: TextInputType.number,
                validator: Validators.required,
                decoration: const InputDecoration(hintText: 'Длительность (мин)', suffixText: 'мин'),
              ),
              const SizedBox(height: AppSpacing.xxl),
              AppButton(
                label: isEditing ? 'Сохранить' : 'Добавить',
                isLoading: _isLoading,
                onPressed: _save,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

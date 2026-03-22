class Service {
  final String id;
  final String? masterId;
  final String name;
  final String? description;
  final double price;
  final int durationMinutes;
  final bool isActive;

  Service({
    required this.id,
    this.masterId,
    required this.name,
    this.description,
    required this.price,
    required this.durationMinutes,
    this.isActive = true,
  });

  factory Service.fromJson(Map<String, dynamic> json) {
    return Service(
      id: json['id'] as String,
      masterId: json['master_id'] as String?,
      name: json['name'] as String,
      description: json['description'] as String?,
      price: (json['price'] as num).toDouble(),
      durationMinutes: json['duration_minutes'] as int,
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'description': description,
    'price': price,
    'duration_minutes': durationMinutes,
  };
}

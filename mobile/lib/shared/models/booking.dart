class Booking {
  final String id;
  final String clientId;
  final String masterId;
  final String serviceId;
  final String? slotId;
  final String status;
  final double price;
  final String? address;
  final bool isOnline;
  final String? cancelReason;
  final String? cancelledBy;
  final DateTime createdAt;
  final DateTime? updatedAt;
  // Expanded fields
  final String? masterName;
  final String? masterAvatarUrl;
  final String? serviceName;
  final int? serviceDuration;
  final String? slotDate;
  final String? slotStartTime;
  final String? slotEndTime;
  final String? clientName;
  final String? chatRoomId;

  Booking({
    required this.id,
    required this.clientId,
    required this.masterId,
    required this.serviceId,
    this.slotId,
    required this.status,
    required this.price,
    this.address,
    this.isOnline = false,
    this.cancelReason,
    this.cancelledBy,
    required this.createdAt,
    this.updatedAt,
    this.masterName,
    this.masterAvatarUrl,
    this.serviceName,
    this.serviceDuration,
    this.slotDate,
    this.slotStartTime,
    this.slotEndTime,
    this.clientName,
    this.chatRoomId,
  });

  bool get isPending => status == 'pending';
  bool get isConfirmed => status == 'confirmed';
  bool get isCompleted => status == 'completed';
  bool get isCancelled => status == 'cancelled';
  bool get isActive => status == 'pending' || status == 'confirmed' || status == 'in_progress';

  String get statusLabel => switch (status) {
    'pending' => 'Ожидает',
    'confirmed' => 'Подтверждён',
    'in_progress' => 'В процессе',
    'completed' => 'Завершён',
    'cancelled' => 'Отменён',
    _ => status,
  };

  factory Booking.fromJson(Map<String, dynamic> json) {
    return Booking(
      id: json['id'] as String,
      clientId: json['client_id'] as String,
      masterId: json['master_id'] as String,
      serviceId: json['service_id'] as String,
      slotId: json['slot_id'] as String?,
      status: json['status'] as String,
      price: (json['price'] as num).toDouble(),
      address: json['address'] as String?,
      isOnline: json['is_online'] as bool? ?? false,
      cancelReason: json['cancel_reason'] as String?,
      cancelledBy: json['cancelled_by'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: json['updated_at'] != null ? DateTime.parse(json['updated_at'] as String) : null,
      masterName: json['master_name'] as String?,
      masterAvatarUrl: json['master_avatar_url'] as String?,
      serviceName: json['service_name'] as String?,
      serviceDuration: json['service_duration'] as int?,
      slotDate: json['slot_date'] as String?,
      slotStartTime: json['slot_start_time'] as String?,
      slotEndTime: json['slot_end_time'] as String?,
      clientName: json['client_name'] as String?,
      chatRoomId: json['chat_room_id'] as String?,
    );
  }
}

class TimeSlot {
  final String id;
  final String date;
  final String startTime;
  final String endTime;
  final bool isBooked;

  TimeSlot({
    required this.id,
    required this.date,
    required this.startTime,
    required this.endTime,
    this.isBooked = false,
  });

  factory TimeSlot.fromJson(Map<String, dynamic> json) {
    return TimeSlot(
      id: json['id'] as String,
      date: json['date'] as String,
      startTime: json['start_time'] as String,
      endTime: json['end_time'] as String,
      isBooked: json['is_booked'] as bool? ?? false,
    );
  }
}

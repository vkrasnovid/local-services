class Review {
  final String id;
  final String? bookingId;
  final String? clientId;
  final String? clientName;
  final String? clientAvatar;
  final String? masterId;
  final int rating;
  final String? text;
  final String? masterReply;
  final DateTime createdAt;

  Review({
    required this.id,
    this.bookingId,
    this.clientId,
    this.clientName,
    this.clientAvatar,
    this.masterId,
    required this.rating,
    this.text,
    this.masterReply,
    required this.createdAt,
  });

  factory Review.fromJson(Map<String, dynamic> json) {
    return Review(
      id: json['id'] as String,
      bookingId: json['booking_id'] as String?,
      clientId: json['client_id'] as String?,
      clientName: json['client_name'] as String?,
      clientAvatar: json['client_avatar'] as String?,
      masterId: json['master_id'] as String?,
      rating: json['rating'] as int,
      text: json['text'] as String?,
      masterReply: json['master_reply'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

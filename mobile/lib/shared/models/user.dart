class User {
  final String id;
  final String? phone;
  final String? email;
  final String firstName;
  final String? lastName;
  final String role;
  final String? city;
  final String? avatarUrl;
  final DateTime? createdAt;

  User({
    required this.id,
    this.phone,
    this.email,
    required this.firstName,
    this.lastName,
    required this.role,
    this.city,
    this.avatarUrl,
    this.createdAt,
  });

  String get fullName => [firstName, lastName].where((e) => e != null && e.isNotEmpty).join(' ');
  bool get isMaster => role == 'master';
  bool get isAdmin => role == 'admin';

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      phone: json['phone'] as String?,
      email: json['email'] as String?,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String?,
      role: json['role'] as String,
      city: json['city'] as String?,
      avatarUrl: json['avatar_url'] as String?,
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'phone': phone,
    'email': email,
    'first_name': firstName,
    'last_name': lastName,
    'role': role,
    'city': city,
    'avatar_url': avatarUrl,
  };
}

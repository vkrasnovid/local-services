import 'category.dart';
import 'service.dart';
import 'review.dart';

class MasterUser {
  final String id;
  final String firstName;
  final String? lastName;
  final String? avatarUrl;
  final String? city;

  MasterUser({
    required this.id,
    required this.firstName,
    this.lastName,
    this.avatarUrl,
    this.city,
  });

  String get fullName => [firstName, lastName].where((e) => e != null && e.isNotEmpty).join(' ');

  factory MasterUser.fromJson(Map<String, dynamic> json) {
    return MasterUser(
      id: json['id'] as String,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String?,
      avatarUrl: json['avatar_url'] as String?,
      city: json['city'] as String?,
    );
  }
}

class Master {
  final String id;
  final MasterUser user;
  final Category? category;
  final String? description;
  final String? district;
  final double ratingAvg;
  final int ratingCount;
  final String verificationStatus;
  final bool isAvailable;
  final double? priceFrom;
  final int? servicesCount;
  final Map<String, dynamic>? workHours;
  final List<Service>? services;
  final List<PortfolioImage>? portfolio;
  final List<Review>? reviewsPreview;

  Master({
    required this.id,
    required this.user,
    this.category,
    this.description,
    this.district,
    this.ratingAvg = 0,
    this.ratingCount = 0,
    this.verificationStatus = 'pending',
    this.isAvailable = true,
    this.priceFrom,
    this.servicesCount,
    this.workHours,
    this.services,
    this.portfolio,
    this.reviewsPreview,
  });

  bool get isVerified => verificationStatus == 'verified';

  factory Master.fromJson(Map<String, dynamic> json) {
    return Master(
      id: json['id'] as String,
      user: MasterUser.fromJson(json['user'] as Map<String, dynamic>),
      category: json['category'] != null
          ? Category.fromJson(json['category'] as Map<String, dynamic>)
          : null,
      description: json['description'] as String?,
      district: json['district'] as String?,
      ratingAvg: (json['rating_avg'] as num?)?.toDouble() ?? 0,
      ratingCount: json['rating_count'] as int? ?? 0,
      verificationStatus: json['verification_status'] as String? ?? 'pending',
      isAvailable: json['is_available'] as bool? ?? true,
      priceFrom: (json['price_from'] as num?)?.toDouble(),
      servicesCount: json['services_count'] as int?,
      workHours: json['work_hours'] as Map<String, dynamic>?,
      services: (json['services'] as List<dynamic>?)
          ?.map((e) => Service.fromJson(e as Map<String, dynamic>))
          .toList(),
      portfolio: (json['portfolio'] as List<dynamic>?)
          ?.map((e) => PortfolioImage.fromJson(e as Map<String, dynamic>))
          .toList(),
      reviewsPreview: (json['reviews_preview'] as List<dynamic>?)
          ?.map((e) => Review.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class PortfolioImage {
  final String id;
  final String imageUrl;
  final int sortOrder;

  PortfolioImage({
    required this.id,
    required this.imageUrl,
    this.sortOrder = 0,
  });

  factory PortfolioImage.fromJson(Map<String, dynamic> json) {
    return PortfolioImage(
      id: json['id'] as String,
      imageUrl: json['image_url'] as String,
      sortOrder: json['sort_order'] as int? ?? 0,
    );
  }
}

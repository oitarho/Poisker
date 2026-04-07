class PublicUserProfileDto {
  final String id;
  final String? fullName;
  final bool isPhoneVerified;
  final double rating;
  final int reviewsCount;

  PublicUserProfileDto({
    required this.id,
    required this.fullName,
    required this.isPhoneVerified,
    required this.rating,
    required this.reviewsCount,
  });

  factory PublicUserProfileDto.fromJson(Map<String, dynamic> json) {
    return PublicUserProfileDto(
      id: json['id'] as String,
      fullName: json['full_name'] as String?,
      isPhoneVerified: json['is_phone_verified'] as bool? ?? false,
      rating: (json['rating'] as num? ?? 0).toDouble(),
      reviewsCount: (json['reviews_count'] as num? ?? 0).toInt(),
    );
  }
}


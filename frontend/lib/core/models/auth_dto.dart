import '../api/auth_tokens.dart';

class AuthResponseDto {
  final AuthTokens tokens;
  final UserProfileDto user;

  AuthResponseDto({required this.tokens, required this.user});

  factory AuthResponseDto.fromJson(Map<String, dynamic> json) {
    return AuthResponseDto(
      tokens: AuthTokens.fromJson(json['tokens'] as Map<String, dynamic>),
      user: UserProfileDto.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}

class UserProfileDto {
  final String id;
  final String email;
  final String? fullName;
  final String? phoneNumber;
  final bool isEmailVerified;
  final bool isPhoneVerified;
  final double rating;
  final int reviewsCount;

  UserProfileDto({
    required this.id,
    required this.email,
    required this.fullName,
    required this.phoneNumber,
    required this.isEmailVerified,
    required this.isPhoneVerified,
    required this.rating,
    required this.reviewsCount,
  });

  factory UserProfileDto.fromJson(Map<String, dynamic> json) {
    return UserProfileDto(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String?,
      phoneNumber: json['phone_number'] as String?,
      isEmailVerified: json['is_email_verified'] as bool? ?? false,
      isPhoneVerified: json['is_phone_verified'] as bool? ?? false,
      rating: (json['rating'] as num? ?? 0).toDouble(),
      reviewsCount: (json['reviews_count'] as num? ?? 0).toInt(),
    );
  }
}


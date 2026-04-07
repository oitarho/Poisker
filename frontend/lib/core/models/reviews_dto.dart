class ReviewDto {
  final String id;
  final String reviewerId;
  final String targetUserId;
  final String? listingId;
  final int rating;
  final String? text;
  final String createdAt;

  ReviewDto({
    required this.id,
    required this.reviewerId,
    required this.targetUserId,
    required this.listingId,
    required this.rating,
    required this.text,
    required this.createdAt,
  });

  factory ReviewDto.fromJson(Map<String, dynamic> json) {
    return ReviewDto(
      id: json['id'] as String,
      reviewerId: json['reviewer_id'] as String,
      targetUserId: json['target_user_id'] as String,
      listingId: json['listing_id'] as String?,
      rating: (json['rating'] as num).toInt(),
      text: json['text'] as String?,
      createdAt: json['created_at'] as String,
    );
  }
}

class ReviewListDto {
  final List<ReviewDto> items;
  ReviewListDto(this.items);

  factory ReviewListDto.fromJson(Map<String, dynamic> json) {
    final items = (json['items'] as List<dynamic>? ?? const [])
        .map((e) => ReviewDto.fromJson(e as Map<String, dynamic>))
        .toList();
    return ReviewListDto(items);
  }
}


import '../api/url_utils.dart';

class ListingPhotoDto {
  final String id;
  final String key;
  final String url;
  final String? contentType;
  final int sortOrder;

  ListingPhotoDto({
    required this.id,
    required this.key,
    required this.url,
    required this.contentType,
    required this.sortOrder,
  });

  factory ListingPhotoDto.fromJson(Map<String, dynamic> json) {
    return ListingPhotoDto(
      id: json['id'] as String,
      key: json['key'] as String,
      url: absolutizeMediaUrl(json['url'] as String),
      contentType: json['content_type'] as String?,
      sortOrder: (json['sort_order'] as num? ?? 0).toInt(),
    );
  }
}

class ListingDto {
  final String id;
  final String kind;
  final String status;
  final String title;
  final String description;
  final double price;
  final String locationId;
  final String categoryId;
  final String ownerId;
  final int viewsCount;
  final int favoritesCount;
  final double boostScore;
  final List<ListingPhotoDto> photos;

  ListingDto({
    required this.id,
    required this.kind,
    required this.status,
    required this.title,
    required this.description,
    required this.price,
    required this.locationId,
    required this.categoryId,
    required this.ownerId,
    required this.viewsCount,
    required this.favoritesCount,
    required this.boostScore,
    required this.photos,
  });

  factory ListingDto.fromJson(Map<String, dynamic> json) {
    final photosJson = (json['photos'] as List<dynamic>? ?? const []);
    return ListingDto(
      id: json['id'] as String,
      kind: json['kind'] as String,
      status: json['status'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      price: (json['price'] as num).toDouble(),
      locationId: json['location_id'] as String,
      categoryId: json['category_id'] as String,
      ownerId: json['owner_id'] as String,
      viewsCount: (json['views_count'] as num? ?? 0).toInt(),
      favoritesCount: (json['favorites_count'] as num? ?? 0).toInt(),
      boostScore: (json['boost_score'] as num? ?? 0).toDouble(),
      photos: photosJson.map((e) => ListingPhotoDto.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }
}


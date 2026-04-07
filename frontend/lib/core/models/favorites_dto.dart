import 'listing_dto.dart';

class FavoritesListDto {
  final List<ListingDto> items;
  FavoritesListDto(this.items);

  factory FavoritesListDto.fromJson(Map<String, dynamic> json) {
    final items = (json['items'] as List<dynamic>? ?? const [])
        .map((e) => ListingDto.fromJson(e as Map<String, dynamic>))
        .toList();
    return FavoritesListDto(items);
  }
}


class LocationDto {
  final String id;
  final String name;
  final String type;
  final String? parentId;
  final double? latitude;
  final double? longitude;

  LocationDto({
    required this.id,
    required this.name,
    required this.type,
    required this.parentId,
    required this.latitude,
    required this.longitude,
  });

  factory LocationDto.fromJson(Map<String, dynamic> json) {
    return LocationDto(
      id: json['id'] as String,
      name: json['name'] as String,
      type: json['type'] as String,
      parentId: json['parent_id'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
    );
  }
}

class LocationListDto {
  final List<LocationDto> items;
  LocationListDto(this.items);

  factory LocationListDto.fromJson(Map<String, dynamic> json) {
    final items = (json['items'] as List<dynamic>? ?? const [])
        .map((e) => LocationDto.fromJson(e as Map<String, dynamic>))
        .toList();
    return LocationListDto(items);
  }
}


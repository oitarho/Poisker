class CategoryDto {
  final String id;
  final String name;
  final String slug;
  final String scope;
  final String? parentId;

  CategoryDto({
    required this.id,
    required this.name,
    required this.slug,
    required this.scope,
    required this.parentId,
  });

  factory CategoryDto.fromJson(Map<String, dynamic> json) {
    return CategoryDto(
      id: json['id'] as String,
      name: json['name'] as String,
      slug: json['slug'] as String,
      scope: json['scope'] as String,
      parentId: json['parent_id'] as String?,
    );
  }
}

class CategoryListDto {
  final List<CategoryDto> items;
  CategoryListDto(this.items);

  factory CategoryListDto.fromJson(Map<String, dynamic> json) {
    final items = (json['items'] as List<dynamic>? ?? const [])
        .map((e) => CategoryDto.fromJson(e as Map<String, dynamic>))
        .toList();
    return CategoryListDto(items);
  }
}


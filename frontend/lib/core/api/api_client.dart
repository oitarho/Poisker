import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import '../storage/token_store.dart';
import 'auth_tokens.dart';
import '../models/auth_dto.dart';
import '../models/listing_dto.dart';
import 'dart:typed_data';

import '../models/categories_dto.dart';
import '../models/locations_dto.dart';
import '../models/public_user_dto.dart';
import '../models/chats_dto.dart';
import 'package:http_parser/http_parser.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);
}

class ApiClient {
  final TokenStore _tokenStore;
  ApiClient(this._tokenStore);

  Uri _uri(String path, [Map<String, String>? query]) {
    final base = AppConfig.apiBaseUrl;
    final p = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$base$p').replace(queryParameters: query);
  }

  Future<Map<String, String>> _headers({bool auth = true}) async {
    final h = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (auth) {
      final tokens = await _tokenStore.load();
      if (tokens != null && tokens.accessToken.isNotEmpty) {
        h['Authorization'] = 'Bearer ${tokens.accessToken}';
      }
    }
    return h;
  }

  Future<http.Response> _raw(
    String method,
    String path, {
    Map<String, String>? query,
    Map<String, dynamic>? body,
    bool auth = true,
    bool _retrying = false,
  }) async {
    final uri = _uri(path, query);
    final headers = await _headers(auth: auth);
    final encoded = body == null ? null : jsonEncode(body);

    http.Response resp;
    switch (method) {
      case 'GET':
        resp = await http.get(uri, headers: headers);
        break;
      case 'POST':
        resp = await http.post(uri, headers: headers, body: encoded);
        break;
      case 'PATCH':
        resp = await http.patch(uri, headers: headers, body: encoded);
        break;
      case 'DELETE':
        resp = await http.delete(uri, headers: headers);
        break;
      default:
        throw ArgumentError('Unsupported method: $method');
    }

    if (auth && resp.statusCode == 401 && !_retrying) {
      final ok = await _tryRefresh();
      if (ok) {
        return _raw(method, path,
            query: query, body: body, auth: auth, _retrying: true);
      }
    }
    return resp;
  }

  Future<bool> _tryRefresh() async {
    final tokens = await _tokenStore.load();
    if (tokens == null || tokens.refreshToken.isEmpty) return false;
    try {
      final resp = await http.post(
        _uri('/api/v1/auth/refresh'),
        headers: await _headers(auth: false),
        body: jsonEncode({'refresh_token': tokens.refreshToken}),
      );
      final json = _decode(resp);
      final newTokens = AuthTokens.fromJson(json);
      await _tokenStore.save(newTokens);
      return true;
    } catch (_) {
      await _tokenStore.clear();
      return false;
    }
  }

  Future<Map<String, dynamic>> getJson(String path,
      {Map<String, String>? query, bool auth = true}) async {
    final resp = await _raw('GET', path, query: query, auth: auth);
    return _decode(resp);
  }

  Future<Map<String, dynamic>> postJson(String path, Map<String, dynamic> body,
      {bool auth = true}) async {
    final resp = await _raw('POST', path, body: body, auth: auth);
    return _decode(resp);
  }

  Future<Map<String, dynamic>> patchJson(String path, Map<String, dynamic> body,
      {bool auth = true}) async {
    final resp = await _raw('PATCH', path, body: body, auth: auth);
    return _decode(resp);
  }

  Future<Map<String, dynamic>> deleteJson(String path, {bool auth = true}) async {
    final resp = await _raw('DELETE', path, auth: auth);
    return _decode(resp);
  }

  Map<String, dynamic> _decode(http.Response resp) {
    final text = resp.body;
    final json = text.isEmpty ? <String, dynamic>{} : jsonDecode(text) as Map<String, dynamic>;
    if (resp.statusCode >= 200 && resp.statusCode < 300) return json;
    final msg = (json['error']?['message'] ?? json['message'] ?? 'Request failed').toString();
    throw ApiException(resp.statusCode, msg);
  }

  Future<AuthResponseDto> login(String email, String password) async {
    final json = await postJson('/api/v1/auth/login', {'email': email, 'password': password},
        auth: false);
    final dto = AuthResponseDto.fromJson(json);
    await _tokenStore.save(dto.tokens);
    return dto;
  }

  Future<AuthResponseDto> register(
      {required String email,
      required String password,
      String? fullName,
      String? phoneNumber}) async {
    final json = await postJson('/api/v1/auth/register', {
      'email': email,
      'password': password,
      'full_name': fullName,
      'phone_number': phoneNumber,
    }, auth: false);
    final dto = AuthResponseDto.fromJson(json);
    await _tokenStore.save(dto.tokens);
    return dto;
  }

  Future<UserProfileDto> getMyProfile() async {
    final json = await getJson('/api/v1/users/me', auth: true);
    return UserProfileDto.fromJson(json);
  }

  Future<UserProfileDto> updateMyProfile({String? fullName, String? phoneNumber}) async {
    final json = await patchJson('/api/v1/users/me', {
      if (fullName != null) 'full_name': fullName,
      if (phoneNumber != null) 'phone_number': phoneNumber,
    }, auth: true);
    return UserProfileDto.fromJson(json);
  }

  Future<List<ListingDto>> listActiveListings({int limit = 20, int offset = 0}) async {
    final json = await getJson('/api/v1/listings',
        query: {'limit': '$limit', 'offset': '$offset'}, auth: false);
    final items = (json['items'] as List<dynamic>? ?? const []);
    return items.map((e) => ListingDto.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<ListingDto>> searchListings({
    String q = '*',
    String? kind,
    String? categoryId,
    String? locationId,
    double? minPrice,
    double? maxPrice,
    int limit = 20,
    int offset = 0,
  }) async {
    final qp = <String, String>{
      'q': q,
      'limit': '$limit',
      'offset': '$offset',
      if (kind != null) 'kind': kind,
      if (categoryId != null) 'category_id': categoryId,
      if (locationId != null) 'location_id': locationId,
      if (minPrice != null) 'min_price': '$minPrice',
      if (maxPrice != null) 'max_price': '$maxPrice',
    };
    final json = await getJson('/api/v1/search', query: qp, auth: false);
    final items = (json['items'] as List<dynamic>? ?? const []);
    return items.map((e) => ListingDto.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ListingDto> getListing(String listingId) async {
    final json = await getJson('/api/v1/listings/$listingId', auth: false);
    return ListingDto.fromJson(json);
  }

  Future<void> favorite(String listingId) async {
    await postJson('/api/v1/favorites/$listingId', {}, auth: true);
  }

  Future<void> unfavorite(String listingId) async {
    await deleteJson('/api/v1/favorites/$listingId', auth: true);
  }

  Future<PublicUserProfileDto> getPublicUser(String userId) async {
    final json = await getJson('/api/v1/users/$userId/public', auth: false);
    return PublicUserProfileDto.fromJson(json);
  }

  Future<LocationDto> getLocation(String id) async {
    final json = await getJson('/api/v1/locations/$id', auth: false);
    return LocationDto.fromJson(json);
  }

  Future<CategoryDto> getCategory(String id) async {
    final json = await getJson('/api/v1/categories/$id', auth: false);
    return CategoryDto.fromJson(json);
  }

  Future<LocationListDto> searchLocations(String q) async {
    final json = await getJson('/api/v1/locations/search', query: {'q': q}, auth: false);
    return LocationListDto.fromJson(json);
  }

  Future<CategoryListDto> listRootCategories({String? kind}) async {
    final json = await getJson('/api/v1/categories',
        query: {if (kind != null) 'kind': kind}, auth: false);
    return CategoryListDto.fromJson(json);
  }

  Future<CategoryListDto> listChildCategories(String parentId, {String? kind}) async {
    final json = await getJson('/api/v1/categories/$parentId/children',
        query: {if (kind != null) 'kind': kind}, auth: false);
    return CategoryListDto.fromJson(json);
  }

  Future<LocationListDto> listRootLocations() async {
    final json = await getJson('/api/v1/locations/roots', auth: false);
    return LocationListDto.fromJson(json);
  }

  Future<Map<String, dynamic>> uploadListingPhotoBytes({
    required String listingId,
    required Uint8List bytes,
    required String filename,
    required String contentType,
    int orderIndex = 0,
  }) async {
    final tokens = await _tokenStore.load();
    if (tokens == null) {
      throw ApiException(401, 'Not authenticated');
    }
    final uri = _uri('/api/v1/listings/$listingId/photos', {'order_index': '$orderIndex'});
    final req = http.MultipartRequest('POST', uri);
    req.headers['Authorization'] = 'Bearer ${tokens.accessToken}';
    req.files.add(http.MultipartFile.fromBytes(
      'file',
      bytes,
      filename: filename,
      contentType: MediaType.parse(contentType),
    ));
    // http doesn't let setting contentType without http_parser; backend will still use UploadFile.content_type.
    final streamed = await req.send();
    final resp = await http.Response.fromStream(streamed);
    return _decode(resp);
  }

  Future<ConversationDto> startConversation(String listingId) async {
    final json = await postJson('/api/v1/chats/conversations', {'listing_id': listingId}, auth: true);
    return ConversationDto.fromJson(json);
  }

  Future<ConversationListDto> listMyConversations() async {
    final json = await getJson('/api/v1/chats/conversations', auth: true);
    return ConversationListDto.fromJson(json);
  }

  Future<ConversationSummaryListDto> listMyConversationsSummary() async {
    final json = await getJson('/api/v1/chats/conversations/summary', auth: true);
    return ConversationSummaryListDto.fromJson(json);
  }

  Future<MessageListDto> getMessages(String conversationId, {int limit = 50}) async {
    final json = await getJson('/api/v1/chats/conversations/$conversationId/messages',
        query: {'limit': '$limit'}, auth: true);
    return MessageListDto.fromJson(json);
  }

  Future<MessageDto> sendMessage(String conversationId, String body) async {
    final json = await postJson('/api/v1/chats/conversations/$conversationId/messages', {'body': body}, auth: true);
    return MessageDto.fromJson(json);
  }

  Future<void> markRead(String conversationId) async {
    await postJson('/api/v1/chats/conversations/$conversationId/read', {}, auth: true);
  }

  Future<ListingDto> createListing({
    required String kind,
    required String title,
    required String description,
    required double price,
    required String locationId,
    required String categoryId,
    String status = 'draft',
  }) async {
    final json = await postJson('/api/v1/listings', {
      'kind': kind,
      'title': title,
      'description': description,
      'price': price,
      'location_id': locationId,
      'category_id': categoryId,
      'status': status,
    }, auth: true);
    return ListingDto.fromJson(json);
  }

  Future<void> logout() async {
    await _tokenStore.clear();
  }
}


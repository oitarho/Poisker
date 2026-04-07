import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../api/auth_tokens.dart';

class TokenStore {
  static const _kTokens = 'poisker.tokens';

  Future<AuthTokens?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_kTokens);
    if (raw == null || raw.isEmpty) return null;
    final json = jsonDecode(raw) as Map<String, dynamic>;
    return AuthTokens.fromJson(json);
  }

  Future<void> save(AuthTokens tokens) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kTokens, jsonEncode(tokens.toJson()));
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kTokens);
  }
}


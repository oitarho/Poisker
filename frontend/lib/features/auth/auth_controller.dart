import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/providers.dart';

sealed class AuthState {
  const AuthState();
}

class AuthUnknown extends AuthState {
  const AuthUnknown();
}

class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();
}

class AuthAuthenticated extends AuthState {
  const AuthAuthenticated();
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref.watch(apiClientProvider));
});

class AuthController extends StateNotifier<AuthState> {
  final ApiClient _api;
  AuthController(this._api) : super(const AuthUnknown()) {
    _init();
  }

  Future<void> _init() async {
    // If tokens exist, validate via /users/me (will refresh if needed).
    try {
      await _api.getMyProfile();
      state = const AuthAuthenticated();
    } catch (_) {
      state = const AuthUnauthenticated();
    }
  }

  Future<void> login(String email, String password) async {
    await _api.login(email, password);
    state = const AuthAuthenticated();
  }

  Future<void> register(
      {required String email,
      required String password,
      String? fullName,
      String? phoneNumber}) async {
    await _api.register(
        email: email, password: password, fullName: fullName, phoneNumber: phoneNumber);
    state = const AuthAuthenticated();
  }

  Future<void> logout() async {
    await _api.logout();
    state = const AuthUnauthenticated();
  }
}


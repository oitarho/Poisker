import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/auth_controller.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/register_screen.dart';
import '../features/chats/chat_details_screen.dart';
import '../features/chats/chat_list_screen.dart';
import '../features/favorites/favorites_screen.dart';
import '../features/home/home_feed_screen.dart';
import '../features/listings/create_listing_screen.dart';
import '../features/listings/listing_details_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/reviews/reviews_screen.dart';
import '../features/splash/splash_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authControllerProvider);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: _GoRouterRefresh(ref),
    redirect: (context, state) {
      final loc = state.matchedLocation;
      final authed = auth is AuthAuthenticated;

      if (loc == '/splash') {
        if (auth is AuthUnknown) return null;
        return authed ? '/home' : '/login';
      }
      if (!authed && (loc.startsWith('/home') || loc.startsWith('/profile') || loc.startsWith('/favorites') || loc.startsWith('/chats'))) {
        return '/login';
      }
      if (authed && (loc == '/login' || loc == '/register')) {
        return '/home';
      }
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (c, s) => const SplashScreen()),
      GoRoute(path: '/login', builder: (c, s) => const LoginScreen()),
      GoRoute(path: '/register', builder: (c, s) => const RegisterScreen()),
      GoRoute(path: '/home', builder: (c, s) => const HomeFeedScreen()),
      GoRoute(
        path: '/listing/:id',
        builder: (c, s) => ListingDetailsScreen(listingId: s.pathParameters['id']!),
      ),
      GoRoute(path: '/create', builder: (c, s) => const CreateListingScreen()),
      GoRoute(path: '/profile', builder: (c, s) => const ProfileScreen()),
      GoRoute(path: '/favorites', builder: (c, s) => const FavoritesScreen()),
      GoRoute(path: '/chats', builder: (c, s) => const ChatListScreen()),
      GoRoute(
        path: '/chats/:id',
        builder: (c, s) => ChatDetailsScreen(conversationId: s.pathParameters['id']!),
      ),
      GoRoute(
        path: '/users/:id/reviews',
        builder: (c, s) => ReviewsScreen(userId: s.pathParameters['id']!),
      ),
    ],
    errorBuilder: (c, s) => Scaffold(
      appBar: AppBar(title: const Text('Poisker')),
      body: Center(child: Text(s.error.toString())),
    ),
  );
});

class _GoRouterRefresh extends ChangeNotifier {
  _GoRouterRefresh(this.ref) {
    ref.listen<AuthState>(authControllerProvider, (_, __) => notifyListeners());
  }
  final Ref ref;
}


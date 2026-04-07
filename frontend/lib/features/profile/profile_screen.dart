import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/auth_dto.dart';
import '../../core/providers.dart';
import '../auth/auth_controller.dart';

final myProfileProvider = FutureProvider<UserProfileDto>((ref) async {
  final api = ref.watch(apiClientProvider);
  return api.getMyProfile();
});

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(myProfileProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            onPressed: () async {
              await ref.read(authControllerProvider.notifier).logout();
              if (context.mounted) context.go('/login');
            },
            icon: const Icon(Icons.logout),
          )
        ],
      ),
      body: SafeArea(
        child: profileAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Failed to load profile'),
                const SizedBox(height: 8),
                Text(e.toString(), style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () => ref.invalidate(myProfileProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
          data: (p) => _ProfileView(profile: p),
        ),
      ),
    );
  }
}

class _ProfileView extends ConsumerStatefulWidget {
  final UserProfileDto profile;
  const _ProfileView({required this.profile});

  @override
  ConsumerState<_ProfileView> createState() => _ProfileViewState();
}

class _ProfileViewState extends ConsumerState<_ProfileView> {
  late final TextEditingController _fullName;
  late final TextEditingController _phone;
  String? _error;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _fullName = TextEditingController(text: widget.profile.fullName ?? '');
    _phone = TextEditingController(text: widget.profile.phoneNumber ?? '');
  }

  @override
  void dispose() {
    _fullName.dispose();
    _phone.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      await api.updateMyProfile(
        fullName: _fullName.text.trim().isEmpty ? null : _fullName.text.trim(),
        phoneNumber: _phone.text.trim().isEmpty ? null : _phone.text.trim(),
      );
      ref.invalidate(myProfileProvider);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.profile;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(p.email, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _pill('Email verified: ${p.isEmailVerified ? "yes" : "no"}'),
            _pill('Phone verified: ${p.isPhoneVerified ? "yes" : "no"}'),
            _pill('Rating: ${p.rating.toStringAsFixed(2)}'),
            _pill('Reviews: ${p.reviewsCount}'),
          ],
        ),
        const SizedBox(height: 16),
        TextField(controller: _fullName, decoration: const InputDecoration(labelText: 'Full name')),
        const SizedBox(height: 12),
        TextField(controller: _phone, decoration: const InputDecoration(labelText: 'Phone (+7...)')),
        const SizedBox(height: 12),
        if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
        const SizedBox(height: 12),
        FilledButton(
          onPressed: _saving ? null : _save,
          child: Text(_saving ? 'Saving...' : 'Save'),
        ),
      ],
    );
  }
}

Widget _pill(String text) {
  return Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
    decoration: BoxDecoration(
      color: Colors.black.withOpacity(0.05),
      borderRadius: BorderRadius.circular(999),
    ),
    child: Text(text),
  );
}


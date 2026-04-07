import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/chats_dto.dart';
import '../../core/providers.dart';

final conversationsProvider = FutureProvider<ConversationSummaryListDto>((ref) async {
  final api = ref.watch(apiClientProvider);
  return api.listMyConversationsSummary();
});

class ChatListScreen extends ConsumerWidget {
  const ChatListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncConvs = ref.watch(conversationsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Chats')),
      body: SafeArea(
        child: asyncConvs.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Failed to load chats'),
                const SizedBox(height: 8),
                Text(e.toString(), style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () => ref.invalidate(conversationsProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
          data: (dto) {
            if (dto.items.isEmpty) return const Center(child: Text('No chats yet'));
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: dto.items.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, i) {
                final c = dto.items[i];
                return ListTile(
                  leading: c.unread
                      ? const Icon(Icons.mark_chat_unread, color: Colors.blue)
                      : const Icon(Icons.chat_bubble_outline),
                  title: Text('Chat ${c.id.substring(0, 8)}'),
                  subtitle: Text(c.unread ? 'Unread messages' : 'No unread'),
                  onTap: () => context.go('/chats/${c.id}'),
                );
              },
            );
          },
        ),
      ),
    );
  }
}


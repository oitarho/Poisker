import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/listing_dto.dart';
import '../../core/models/categories_dto.dart';
import '../../core/models/locations_dto.dart';
import '../../core/providers.dart';

final _feedQueryProvider = StateProvider<_FeedQuery>((ref) => const _FeedQuery());

final listingsFeedProvider = FutureProvider<List<ListingDto>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final q = ref.watch(_feedQueryProvider);
  return api.searchListings(
    q: q.query.isEmpty ? '*' : q.query,
    kind: q.kind,
    categoryId: q.categoryId,
    locationId: q.locationId,
    limit: 20,
    offset: 0,
  );
});

class _FeedQuery {
  final String query;
  final String? kind;
  final String? categoryId;
  final String? locationId;
  const _FeedQuery({this.query = '', this.kind, this.categoryId, this.locationId});

  _FeedQuery copyWith({String? query, String? kind, String? categoryId, String? locationId, bool clearKind = false, bool clearCategory = false, bool clearLocation = false}) {
    return _FeedQuery(
      query: query ?? this.query,
      kind: clearKind ? null : (kind ?? this.kind),
      categoryId: clearCategory ? null : (categoryId ?? this.categoryId),
      locationId: clearLocation ? null : (locationId ?? this.locationId),
    );
  }
}

class HomeFeedScreen extends ConsumerWidget {
  const HomeFeedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final feedAsync = ref.watch(listingsFeedProvider);
    final feedQuery = ref.watch(_feedQueryProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Poisker'),
        actions: [
          IconButton(onPressed: () => context.go('/favorites'), icon: const Icon(Icons.favorite)),
          IconButton(onPressed: () => context.go('/chats'), icon: const Icon(Icons.chat_bubble)),
          IconButton(onPressed: () => context.go('/profile'), icon: const Icon(Icons.person)),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/create'),
        child: const Icon(Icons.add),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: TextField(
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search),
                  hintText: 'Search listings',
                  border: OutlineInputBorder(),
                ),
                onChanged: (v) {
                  ref.read(_feedQueryProvider.notifier).state =
                      feedQuery.copyWith(query: v.trim());
                },
              ),
            ),
            _FiltersRow(query: feedQuery),
            const Divider(height: 1),
            Expanded(
              child: feedAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Failed to load listings'),
                const SizedBox(height: 8),
                Text(e.toString(), style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () => ref.invalidate(listingsFeedProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
          data: (items) {
            if (items.isEmpty) {
              return const Center(child: Text('No listings yet'));
            }
            return RefreshIndicator(
              onRefresh: () async => ref.invalidate(listingsFeedProvider),
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: items.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (context, i) {
                  final l = items[i];
                  return ListTile(
                    title: Text(l.title),
                    subtitle: Text('${l.price.toStringAsFixed(0)} ₽ • ${l.kind}'),
                    onTap: () => context.go('/listing/${l.id}'),
                  );
                },
              ),
            );
          },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FiltersRow extends ConsumerWidget {
  final _FeedQuery query;
  const _FiltersRow({required this.query});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          FilterChip(
            label: Text(query.kind ?? 'Kind'),
            selected: query.kind != null,
            onSelected: (_) async {
              final selected = await showModalBottomSheet<String>(
                context: context,
                builder: (c) => _KindPicker(initial: query.kind),
              );
              if (selected == null) return;
              ref.read(_feedQueryProvider.notifier).state =
                  selected == 'any' ? query.copyWith(clearKind: true) : query.copyWith(kind: selected);
            },
          ),
          const SizedBox(width: 8),
          FilterChip(
            label: Text(query.categoryId == null ? 'Category' : 'Category selected'),
            selected: query.categoryId != null,
            onSelected: (_) async {
              final selected = await showModalBottomSheet<String>(
                context: context,
                builder: (c) => _CategoryPicker(kind: query.kind),
              );
              if (selected == null) return;
              ref.read(_feedQueryProvider.notifier).state =
                  selected == 'any' ? query.copyWith(clearCategory: true) : query.copyWith(categoryId: selected);
            },
          ),
          const SizedBox(width: 8),
          FilterChip(
            label: Text(query.locationId == null ? 'Location' : 'Location selected'),
            selected: query.locationId != null,
            onSelected: (_) async {
              final selected = await showModalBottomSheet<String>(
                context: context,
                isScrollControlled: true,
                builder: (c) => const _LocationSearchPicker(),
              );
              if (selected == null) return;
              ref.read(_feedQueryProvider.notifier).state =
                  selected == 'any' ? query.copyWith(clearLocation: true) : query.copyWith(locationId: selected);
            },
          ),
        ],
      ),
    );
  }
}

class _KindPicker extends StatelessWidget {
  final String? initial;
  const _KindPicker({this.initial});
  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(title: const Text('Any'), onTap: () => Navigator.pop(context, 'any')),
          ListTile(title: const Text('product'), onTap: () => Navigator.pop(context, 'product')),
          ListTile(title: const Text('service'), onTap: () => Navigator.pop(context, 'service')),
        ],
      ),
    );
  }
}

class _CategoryPicker extends ConsumerWidget {
  final String? kind;
  const _CategoryPicker({this.kind});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ref.watch(apiClientProvider);
    return SafeArea(
      child: FutureBuilder<CategoryListDto>(
        future: api.listRootCategories(kind: kind),
        builder: (context, snap) {
          if (!snap.hasData) {
            if (snap.hasError) return Padding(padding: const EdgeInsets.all(16), child: Text(snap.error.toString()));
            return const Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator());
          }
          final items = snap.data!.items;
          return ListView(
            shrinkWrap: true,
            children: [
              ListTile(title: const Text('Any'), onTap: () => Navigator.pop(context, 'any')),
              for (final c in items)
                ListTile(title: Text(c.name), onTap: () => Navigator.pop(context, c.id)),
            ],
          );
        },
      ),
    );
  }
}

class _LocationSearchPicker extends ConsumerStatefulWidget {
  const _LocationSearchPicker();
  @override
  ConsumerState<_LocationSearchPicker> createState() => _LocationSearchPickerState();
}

class _LocationSearchPickerState extends ConsumerState<_LocationSearchPicker> {
  final _q = TextEditingController();
  LocationListDto? _results;
  String? _error;
  bool _loading = false;

  @override
  void dispose() {
    _q.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final res = _q.text.trim().isEmpty ? await api.listRootLocations() : await api.searchLocations(_q.text.trim());
      setState(() => _results = res);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    return Padding(
      padding: EdgeInsets.only(bottom: bottom),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _q,
                      decoration: const InputDecoration(labelText: 'Search location', border: OutlineInputBorder()),
                      onSubmitted: (_) => _search(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(onPressed: _loading ? null : _search, icon: const Icon(Icons.search)),
                ],
              ),
            ),
            if (_error != null) Padding(padding: const EdgeInsets.all(12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
            Flexible(
              child: ListView(
                shrinkWrap: true,
                children: [
                  ListTile(title: const Text('Any'), onTap: () => Navigator.pop(context, 'any')),
                  ...?_results?.items.map((l) => ListTile(title: Text(l.name), subtitle: Text(l.type), onTap: () => Navigator.pop(context, l.id))),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}


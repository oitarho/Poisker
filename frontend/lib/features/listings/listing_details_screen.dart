import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/categories_dto.dart';
import '../../core/models/listing_dto.dart';
import '../../core/models/locations_dto.dart';
import '../../core/models/public_user_dto.dart';
import '../../core/providers.dart';

final listingDetailsProvider =
    FutureProvider.family<_ListingDetailsVm, String>((ref, listingId) async {
  final api = ref.watch(apiClientProvider);
  final listing = await api.getListing(listingId);
  final seller = await api.getPublicUser(listing.ownerId);
  final loc = await api.getLocation(listing.locationId);
  final cat = await api.getCategory(listing.categoryId);
  return _ListingDetailsVm(listing: listing, seller: seller, location: loc, category: cat);
});

class _ListingDetailsVm {
  final ListingDto listing;
  final PublicUserProfileDto seller;
  final LocationDto location;
  final CategoryDto category;
  _ListingDetailsVm({
    required this.listing,
    required this.seller,
    required this.location,
    required this.category,
  });
}

class ListingDetailsScreen extends ConsumerWidget {
  final String listingId;
  const ListingDetailsScreen({super.key, required this.listingId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncVm = ref.watch(listingDetailsProvider(listingId));

    return Scaffold(
      appBar: AppBar(title: const Text('Listing')),
      body: SafeArea(
        child: asyncVm.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Failed to load listing'),
                const SizedBox(height: 8),
                Text(e.toString(), style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () => ref.invalidate(listingDetailsProvider(listingId)),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
          data: (vm) => _ListingDetailsView(vm: vm),
        ),
      ),
    );
  }
}

class _ListingDetailsView extends ConsumerStatefulWidget {
  final _ListingDetailsVm vm;
  const _ListingDetailsView({required this.vm});

  @override
  ConsumerState<_ListingDetailsView> createState() => _ListingDetailsViewState();
}

class _ListingDetailsViewState extends ConsumerState<_ListingDetailsView> {
  bool _favBusy = false;
  bool _favorited = false; // MVP: we don't query favorites state yet
  String? _favError;

  Future<void> _toggleFavorite() async {
    setState(() {
      _favBusy = true;
      _favError = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      if (_favorited) {
        await api.unfavorite(widget.vm.listing.id);
      } else {
        await api.favorite(widget.vm.listing.id);
      }
      setState(() => _favorited = !_favorited);
    } catch (e) {
      setState(() => _favError = e.toString());
    } finally {
      if (mounted) setState(() => _favBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = widget.vm.listing;
    final seller = widget.vm.seller;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (l.photos.isNotEmpty)
          SizedBox(
            height: 220,
            child: PageView(
              children: [
                for (final p in l.photos)
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.network(p.url, fit: BoxFit.cover),
                  ),
              ],
            ),
          )
        else
          Container(
            height: 180,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.05),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text('No photos'),
          ),
        const SizedBox(height: 12),
        Text(l.title, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        Text('${l.price.toStringAsFixed(0)} ₽', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Text('${widget.vm.category.name} • ${widget.vm.location.name}'),
        const SizedBox(height: 12),
        Text(l.description),
        const SizedBox(height: 16),
        const Divider(),
        ListTile(
          title: Text(seller.fullName ?? 'Seller'),
          subtitle: Text('Rating: ${seller.rating.toStringAsFixed(2)} • Reviews: ${seller.reviewsCount}'),
          trailing: TextButton(
            onPressed: () => context.go('/users/${seller.id}/reviews'),
            child: const Text('Reviews'),
          ),
        ),
        const SizedBox(height: 12),
        if (_favError != null) Text(_favError!, style: const TextStyle(color: Colors.red)),
        Row(
          children: [
            Expanded(
              child: FilledButton.icon(
                onPressed: _favBusy ? null : _toggleFavorite,
                icon: Icon(_favorited ? Icons.favorite : Icons.favorite_border),
                label: Text(_favorited ? 'Favorited' : 'Favorite'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: FilledButton.icon(
                onPressed: () async {
                  final api = ref.read(apiClientProvider);
                  try {
                    final conv = await api.startConversation(l.id);
                    if (context.mounted) context.go('/chats/${conv.id}');
                  } catch (e) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(e.toString())),
                    );
                  }
                },
                icon: const Icon(Icons.chat_bubble),
                label: const Text('Contact'),
              ),
            ),
          ],
        )
      ],
    );
  }
}


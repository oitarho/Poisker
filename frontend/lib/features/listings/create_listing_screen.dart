import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mime/mime.dart';

import '../../core/models/categories_dto.dart';
import '../../core/models/locations_dto.dart';
import '../../core/providers.dart';

class CreateListingScreen extends ConsumerStatefulWidget {
  const CreateListingScreen({super.key});

  @override
  ConsumerState<CreateListingScreen> createState() => _CreateListingScreenState();
}

class _CreateListingScreenState extends ConsumerState<CreateListingScreen> {
  final _title = TextEditingController();
  final _description = TextEditingController();
  final _price = TextEditingController();
  String _kind = 'product';
  String? _categoryId;
  String? _categoryName;
  String? _locationId;
  String? _locationName;
  bool _submitting = false;
  String? _error;
  final List<_PickedPhoto> _photos = [];
  final _picker = ImagePicker();

  @override
  void dispose() {
    _title.dispose();
    _description.dispose();
    _price.dispose();
    super.dispose();
  }

  Future<void> _pickPhotos() async {
    final imgs = await _picker.pickMultiImage(imageQuality: 85);
    if (imgs.isEmpty) return;
    for (final x in imgs) {
      final bytes = await x.readAsBytes();
      _photos.add(_PickedPhoto(name: x.name, bytes: bytes));
    }
    if (mounted) setState(() {});
  }

  Future<void> _pickCategory() async {
    final api = ref.read(apiClientProvider);
    final dto = await api.listRootCategories(kind: _kind);
    final id = await showModalBottomSheet<String>(
      context: context,
      builder: (c) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            for (final cat in dto.items)
              ListTile(
                title: Text(cat.name),
                onTap: () => Navigator.pop(c, cat.id),
              ),
          ],
        ),
      ),
    );
    if (id == null) return;
    final cat = dto.items.firstWhere((e) => e.id == id);
    setState(() {
      _categoryId = id;
      _categoryName = cat.name;
    });
  }

  Future<void> _pickLocation() async {
    final id = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      builder: (c) => const _LocationPicker(),
    );
    if (id == null) return;
    final api = ref.read(apiClientProvider);
    final loc = await api.getLocation(id);
    setState(() {
      _locationId = id;
      _locationName = loc.name;
    });
  }

  Future<void> _submit({required String status}) async {
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final title = _title.text.trim();
      final desc = _description.text.trim();
      final price = double.tryParse(_price.text.trim()) ?? -1;
      if (title.isEmpty || desc.isEmpty) throw Exception('Fill title and description');
      if (price < 0) throw Exception('Invalid price');
      if (_categoryId == null) throw Exception('Select category');
      if (_locationId == null) throw Exception('Select location');

      final api = ref.read(apiClientProvider);
      final listing = await api.createListing(
        kind: _kind,
        title: title,
        description: desc,
        price: price,
        categoryId: _categoryId!,
        locationId: _locationId!,
        status: status,
      );

      // Upload photos after creation.
      for (var i = 0; i < _photos.length; i++) {
        final p = _photos[i];
        final mime = lookupMimeType(p.name) ?? 'image/jpeg';
        await api.uploadListingPhotoBytes(
          listingId: listing.id,
          bytes: p.bytes,
          filename: p.name,
          contentType: mime,
          orderIndex: i,
        );
      }

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(status == 'pending' ? 'Submitted for moderation' : 'Saved as draft')),
        );
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create listing')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            DropdownButtonFormField<String>(
              value: _kind,
              items: const [
                DropdownMenuItem(value: 'product', child: Text('Product')),
                DropdownMenuItem(value: 'service', child: Text('Service')),
              ],
              onChanged: _submitting
                  ? null
                  : (v) => setState(() {
                        _kind = v ?? 'product';
                        _categoryId = null;
                        _categoryName = null;
                      }),
              decoration: const InputDecoration(labelText: 'Kind'),
            ),
            const SizedBox(height: 12),
            TextField(controller: _title, decoration: const InputDecoration(labelText: 'Title')),
            const SizedBox(height: 12),
            TextField(
              controller: _description,
              decoration: const InputDecoration(labelText: 'Description'),
              maxLines: 5,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _price,
              decoration: const InputDecoration(labelText: 'Price'),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 12),
            ListTile(
              title: const Text('Category'),
              subtitle: Text(_categoryName ?? 'Select'),
              trailing: const Icon(Icons.chevron_right),
              onTap: _submitting ? null : _pickCategory,
            ),
            ListTile(
              title: const Text('Location'),
              subtitle: Text(_locationName ?? 'Select'),
              trailing: const Icon(Icons.chevron_right),
              onTap: _submitting ? null : _pickLocation,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _submitting ? null : _pickPhotos,
                    icon: const Icon(Icons.photo),
                    label: Text('Add photos (${_photos.length})'),
                  ),
                ),
              ],
            ),
            if (_photos.isNotEmpty) ...[
              const SizedBox(height: 12),
              SizedBox(
                height: 88,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: _photos.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (context, i) {
                    final p = _photos[i];
                    return Stack(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(10),
                          child: Image.memory(p.bytes, width: 88, height: 88, fit: BoxFit.cover),
                        ),
                        Positioned(
                          right: 0,
                          top: 0,
                          child: IconButton(
                            onPressed: _submitting
                                ? null
                                : () => setState(() => _photos.removeAt(i)),
                            icon: const Icon(Icons.close, size: 18),
                          ),
                        )
                      ],
                    );
                  },
                ),
              )
            ],
            const SizedBox(height: 12),
            if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _submitting ? null : () => _submit(status: 'draft'),
                    child: Text(_submitting ? '...' : 'Save draft'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: _submitting ? null : () => _submit(status: 'pending'),
                    child: Text(_submitting ? '...' : 'Submit'),
                  ),
                ),
              ],
            )
          ],
        ),
      ),
    );
  }
}

class _PickedPhoto {
  final String name;
  final Uint8List bytes;
  _PickedPhoto({required this.name, required this.bytes});
}

class _LocationPicker extends ConsumerStatefulWidget {
  const _LocationPicker();
  @override
  ConsumerState<_LocationPicker> createState() => _LocationPickerState();
}

class _LocationPickerState extends ConsumerState<_LocationPicker> {
  final _q = TextEditingController();
  LocationListDto? _results;
  String? _error;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _loadRoots();
  }

  Future<void> _loadRoots() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final res = await api.listRootLocations();
      setState(() => _results = res);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _search() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final res = _q.text.trim().isEmpty
          ? await api.listRootLocations()
          : await api.searchLocations(_q.text.trim());
      setState(() => _results = res);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _q.dispose();
    super.dispose();
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
            if (_loading) const Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator()),
            Flexible(
              child: ListView(
                shrinkWrap: true,
                children: [
                  for (final l in _results?.items ?? const [])
                    ListTile(
                      title: Text(l.name),
                      subtitle: Text(l.type),
                      onTap: () => Navigator.pop(context, l.id),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}


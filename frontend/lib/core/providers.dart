import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api/api_client.dart';
import 'storage/token_store.dart';

final tokenStoreProvider = Provider<TokenStore>((ref) => TokenStore());
final apiClientProvider =
    Provider<ApiClient>((ref) => ApiClient(ref.watch(tokenStoreProvider)));


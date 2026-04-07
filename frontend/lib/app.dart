import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/ui/theme.dart';
import 'routing/router.dart';

class PoiskerApp extends ConsumerWidget {
  const PoiskerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'Poisker',
      theme: buildLightTheme(),
      routerConfig: router,
    );
  }
}


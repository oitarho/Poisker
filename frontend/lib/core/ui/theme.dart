import 'package:flutter/material.dart';

ThemeData buildLightTheme() {
  final base = ThemeData.light(useMaterial3: true);
  return base.copyWith(
    colorScheme: base.colorScheme.copyWith(
      primary: const Color(0xFF1E88E5),
      secondary: const Color(0xFF43A047),
    ),
    appBarTheme: const AppBarTheme(centerTitle: true),
  );
}


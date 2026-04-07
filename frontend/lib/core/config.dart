class AppConfig {
  // For Android emulator use: http://10.0.2.2:8000
  // For local web use: http://localhost:8000
  static const apiBaseUrl = String.fromEnvironment(
    'POISKER_API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
}


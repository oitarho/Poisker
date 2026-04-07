import '../config.dart';

String absolutizeMediaUrl(String urlOrPath) {
  if (urlOrPath.startsWith('http://') || urlOrPath.startsWith('https://')) {
    return urlOrPath;
  }
  if (!urlOrPath.startsWith('/')) {
    return '${AppConfig.apiBaseUrl}/$urlOrPath';
  }
  return '${AppConfig.apiBaseUrl}$urlOrPath';
}


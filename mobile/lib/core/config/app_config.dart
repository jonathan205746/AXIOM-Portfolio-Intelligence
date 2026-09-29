// App Configuration
class AppConfig {
  static const String appName = 'PARHARIQ AI';
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://api.parhariq.example.com/api/v1',
  );
  static const String webBaseUrl = String.fromEnvironment(
    'WEB_BASE_URL',
    defaultValue: 'https://parhariq.example.com',
  );

  // Token configuration
  static const int accessTokenExpiryMinutes = 30;
  static const int refreshTokenExpiryDays = 30;

  // Feature flags
  static const bool enableBiometricAuth = true;
  static const bool enableAnalytics = false;
}

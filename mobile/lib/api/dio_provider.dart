// Dio Provider with Auth Interceptors
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:parhariq/core/config/app_config.dart';
import 'package:parhariq/auth/auth_state.dart';
import 'package:parhariq/api/api_client.dart';
import 'package:parhariq/api/api_models.dart';

class AuthInterceptor extends Interceptor {
  final Ref ref;

  AuthInterceptor(this.ref);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final authState = ref.read(authStateProvider);
    if (authState.isAuthenticated && authState.accessToken != null) {
      options.headers['Authorization'] = 'Bearer ${authState.accessToken}';
    }
    options.headers['X-Request-ID'] = DateTime.now().millisecondsSinceEpoch.toString();
    super.onRequest(options, handler);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      final authState = ref.read(authStateProvider);
      if (authState.isAuthenticated && authState.refreshToken != null) {
        try {
          // Attempt token refresh
          final dio = Dio();
          final response = await dio.post(
            '${AppConfig.apiBaseUrl}/auth/refresh',
            data: {'refresh_token': authState.refreshToken},
          );
          if (response.statusCode == 200) {
            final tokenResponse = TokenResponse.fromJson(response.data);
            await ref.read(authStateProvider.notifier).updateTokens(tokenResponse);

            // Retry original request
            final opts = Options(
              method: err.requestOptions.method,
              headers: {
                ...err.requestOptions.headers,
                'Authorization': 'Bearer ${tokenResponse.accessToken}',
              },
            );
            final retryResponse = await dio.request(
              err.requestOptions.uri.toString(),
              options: opts,
              data: err.requestOptions.data,
              queryParameters: err.requestOptions.queryParameters,
            );
            return handler.resolve(retryResponse);
          }
        } catch (_) {
          // Refresh failed, logout
          await ref.read(authStateProvider.notifier).logout();
        }
      } else {
        await ref.read(authStateProvider.notifier).logout();
      }
    }
    super.onError(err, handler);
  }
}

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: AppConfig.apiBaseUrl,
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  ));

  dio.interceptors.add(AuthInterceptor(ref));
  dio.interceptors.add(LogInterceptor(
    requestBody: true,
    responseBody: true,
    requestHeader: true,
    responseHeader: false,
  ));

  return dio;
});

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.watch(dioProvider), baseUrl: AppConfig.apiBaseUrl);
});

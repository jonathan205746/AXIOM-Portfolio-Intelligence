// API Client - Manual Dio Implementation
import 'package:dio/dio.dart';
import 'package:parhariq/api/api_models.dart';

class ApiClient {
  final Dio _dio;
  final String baseUrl;

  ApiClient(this._dio, {required this.baseUrl});

  // Auth endpoints
  Future<TokenResponse> login(LoginRequest request) async {
    final response = await _dio.post(
      '$baseUrl/auth/login',
      data: request.toJson(),
    );
    return TokenResponse.fromJson(response.data);
  }

  Future<TokenResponse> register(RegisterRequest request) async {
    final response = await _dio.post(
      '$baseUrl/auth/register',
      data: request.toJson(),
    );
    return TokenResponse.fromJson(response.data);
  }

  Future<TokenResponse> refreshToken(RefreshTokenRequest request) async {
    final response = await _dio.post(
      '$baseUrl/auth/refresh',
      data: request.toJson(),
    );
    return TokenResponse.fromJson(response.data);
  }

  Future<MessageResponse> logout(RefreshTokenRequest request) async {
    final response = await _dio.post(
      '$baseUrl/auth/logout',
      data: request.toJson(),
    );
    return MessageResponse.fromJson(response.data);
  }

  Future<UserResponse> getCurrentUser() async {
    final response = await _dio.get('$baseUrl/auth/me');
    return UserResponse.fromJson(response.data);
  }

  Future<MessageResponse> requestPasswordReset(PasswordResetRequest request) async {
    final response = await _dio.post(
      '$baseUrl/auth/password-reset/request',
      data: request.toJson(),
    );
    return MessageResponse.fromJson(response.data);
  }

  Future<MessageResponse> confirmPasswordReset(PasswordResetConfirm request) async {
    final response = await _dio.post(
      '$baseUrl/auth/password-reset/confirm',
      data: request.toJson(),
    );
    return MessageResponse.fromJson(response.data);
  }

  Future<MessageResponse> deleteAccount(AccountDeletionRequest request) async {
    final response = await _dio.delete(
      '$baseUrl/auth/account',
      data: request.toJson(),
    );
    return MessageResponse.fromJson(response.data);
  }

  // Portfolio endpoints
  Future<List<PortfolioResponse>> listPortfolios() async {
    final response = await _dio.get('$baseUrl/portfolios');
    return (response.data as List)
        .map((e) => PortfolioResponse.fromJson(e))
        .toList();
  }

  Future<PortfolioResponse> createPortfolio(PortfolioCreate request) async {
    final response = await _dio.post(
      '$baseUrl/portfolios',
      data: request.toJson(),
    );
    return PortfolioResponse.fromJson(response.data);
  }

  Future<PortfolioResponse> getPortfolio(int portfolioId) async {
    final response = await _dio.get('$baseUrl/portfolios/$portfolioId');
    return PortfolioResponse.fromJson(response.data);
  }

  Future<void> deletePortfolio(int portfolioId) async {
    await _dio.delete('$baseUrl/portfolios/$portfolioId');
  }

  // Holdings endpoints
  Future<List<HoldingResponse>> listHoldings(int portfolioId) async {
    final response = await _dio.get('$baseUrl/portfolios/$portfolioId/holdings');
    return (response.data as List)
        .map((e) => HoldingResponse.fromJson(e))
        .toList();
  }

  Future<HoldingResponse> addHolding(int portfolioId, HoldingCreate request) async {
    final response = await _dio.post(
      '$baseUrl/portfolios/$portfolioId/holdings',
      data: request.toJson(),
    );
    return HoldingResponse.fromJson(response.data);
  }

  Future<void> removeHolding(int holdingId) async {
    await _dio.delete('$baseUrl/holdings/$holdingId');
  }

  // Analysis endpoints
  Future<AnalysisResponse> runAnalysis(int portfolioId, AnalysisRequest request) async {
    final response = await _dio.post(
      '$baseUrl/portfolios/$portfolioId/analysis',
      data: request.toJson(),
    );
    return AnalysisResponse.fromJson(response.data);
  }

  // History endpoints
  Future<List<HistoryResponse>> getHistory(int portfolioId, int limit) async {
    final response = await _dio.get(
      '$baseUrl/portfolios/$portfolioId/history',
      queryParameters: {'limit': limit},
    );
    return (response.data as List)
        .map((e) => HistoryResponse.fromJson(e))
        .toList();
  }

  // Benchmark endpoints
  Future<BenchmarkResponse> getBenchmark(int portfolioId) async {
    final response = await _dio.get('$baseUrl/portfolios/$portfolioId/benchmark');
    return BenchmarkResponse.fromJson(response.data);
  }

  // Health check
  Future<Map<String, dynamic>> healthCheck() async {
    final response = await _dio.get('$baseUrl/health');
    return response.data;
  }
}

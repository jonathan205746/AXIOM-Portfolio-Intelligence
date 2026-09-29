// API Models - Manual JSON Serialization
class LoginRequest {
  final String username;
  final String password;

  LoginRequest({required this.username, required this.password});

  factory LoginRequest.fromJson(Map<String, dynamic> json) {
    return LoginRequest(
      username: json['username'] as String,
      password: json['password'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'username': username,
    'password': password,
  };
}

class RegisterRequest {
  final String username;
  final String email;
  final String password;

  RegisterRequest({required this.username, required this.email, required this.password});

  factory RegisterRequest.fromJson(Map<String, dynamic> json) {
    return RegisterRequest(
      username: json['username'] as String,
      email: json['email'] as String,
      password: json['password'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'username': username,
    'email': email,
    'password': password,
  };
}

class TokenResponse {
  final String accessToken;
  final String tokenType;
  final int expiresIn;
  final String refreshToken;
  final UserResponse user;

  TokenResponse({
    required this.accessToken,
    required this.tokenType,
    required this.expiresIn,
    required this.refreshToken,
    required this.user,
  });

  factory TokenResponse.fromJson(Map<String, dynamic> json) {
    return TokenResponse(
      accessToken: json['access_token'] as String,
      tokenType: json['token_type'] as String,
      expiresIn: json['expires_in'] as int,
      refreshToken: json['refresh_token'] as String,
      user: UserResponse.fromJson(json['user'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() => {
    'access_token': accessToken,
    'token_type': tokenType,
    'expires_in': expiresIn,
    'refresh_token': refreshToken,
    'user': user.toJson(),
  };
}

class UserResponse {
  final int id;
  final String username;
  final String email;
  final String createdAt;

  UserResponse({
    required this.id,
    required this.username,
    required this.email,
    required this.createdAt,
  });

  factory UserResponse.fromJson(Map<String, dynamic> json) {
    return UserResponse(
      id: json['id'] as int,
      username: json['username'] as String,
      email: json['email'] as String,
      createdAt: json['created_at'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'username': username,
    'email': email,
    'created_at': createdAt,
  };
}

class RefreshTokenRequest {
  final String refreshToken;

  RefreshTokenRequest({required this.refreshToken});

  factory RefreshTokenRequest.fromJson(Map<String, dynamic> json) {
    return RefreshTokenRequest(refreshToken: json['refresh_token'] as String);
  }

  Map<String, dynamic> toJson() => {
    'refresh_token': refreshToken,
  };
}

class PasswordResetRequest {
  final String username;
  final String email;

  PasswordResetRequest({required this.username, required this.email});

  factory PasswordResetRequest.fromJson(Map<String, dynamic> json) {
    return PasswordResetRequest(
      username: json['username'] as String,
      email: json['email'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'username': username,
    'email': email,
  };
}

class PasswordResetConfirm {
  final String username;
  final String email;
  final String code;
  final String newPassword;

  PasswordResetConfirm({
    required this.username,
    required this.email,
    required this.code,
    required this.newPassword,
  });

  factory PasswordResetConfirm.fromJson(Map<String, dynamic> json) {
    return PasswordResetConfirm(
      username: json['username'] as String,
      email: json['email'] as String,
      code: json['code'] as String,
      newPassword: json['new_password'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'username': username,
    'email': email,
    'code': code,
    'new_password': newPassword,
  };
}

class AccountDeletionRequest {
  final String password;
  final String confirmation;

  AccountDeletionRequest({required this.password, this.confirmation = 'DELETE'});

  factory AccountDeletionRequest.fromJson(Map<String, dynamic> json) {
    return AccountDeletionRequest(
      password: json['password'] as String,
      confirmation: json['confirmation'] as String? ?? 'DELETE',
    );
  }

  Map<String, dynamic> toJson() => {
    'password': password,
    'confirmation': confirmation,
  };
}

class PortfolioCreate {
  final String name;
  final String description;
  final String currency;

  PortfolioCreate({required this.name, this.description = '', this.currency = 'USD'});

  factory PortfolioCreate.fromJson(Map<String, dynamic> json) {
    return PortfolioCreate(
      name: json['name'] as String,
      description: json['description'] as String? ?? '',
      currency: json['currency'] as String? ?? 'USD',
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'description': description,
    'currency': currency,
  };
}

class PortfolioResponse {
  final int id;
  final int userId;
  final String name;
  final String description;
  final String currency;
  final String createdAt;

  PortfolioResponse({
    required this.id,
    required this.userId,
    required this.name,
    required this.description,
    required this.currency,
    required this.createdAt,
  });

  factory PortfolioResponse.fromJson(Map<String, dynamic> json) {
    return PortfolioResponse(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      name: json['name'] as String,
      description: json['description'] as String,
      currency: json['currency'] as String,
      createdAt: json['created_at'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'user_id': userId,
    'name': name,
    'description': description,
    'currency': currency,
    'created_at': createdAt,
  };
}

class HoldingCreate {
  final String ticker;
  final double quantity;
  final double buyPrice;
  final String buyCurrency;
  final String? buyDate;

  HoldingCreate({
    required this.ticker,
    required this.quantity,
    required this.buyPrice,
    this.buyCurrency = 'USD',
    this.buyDate,
  });

  factory HoldingCreate.fromJson(Map<String, dynamic> json) {
    return HoldingCreate(
      ticker: json['ticker'] as String,
      quantity: (json['quantity'] as num).toDouble(),
      buyPrice: (json['buy_price'] as num).toDouble(),
      buyCurrency: json['buy_currency'] as String? ?? 'USD',
      buyDate: json['buy_date'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'ticker': ticker,
    'quantity': quantity,
    'buy_price': buyPrice,
    'buy_currency': buyCurrency,
    'buy_date': buyDate,
  };
}

class HoldingResponse {
  final int id;
  final int portfolioId;
  final String ticker;
  final String displayName;
  final String exchange;
  final double quantity;
  final double buyPrice;
  final String buyCurrency;
  final String buyDate;
  final String createdAt;

  HoldingResponse({
    required this.id,
    required this.portfolioId,
    required this.ticker,
    required this.displayName,
    required this.exchange,
    required this.quantity,
    required this.buyPrice,
    required this.buyCurrency,
    required this.buyDate,
    required this.createdAt,
  });

  factory HoldingResponse.fromJson(Map<String, dynamic> json) {
    return HoldingResponse(
      id: json['id'] as int,
      portfolioId: json['portfolio_id'] as int,
      ticker: json['ticker'] as String,
      displayName: json['display_name'] as String,
      exchange: json['exchange'] as String,
      quantity: (json['quantity'] as num).toDouble(),
      buyPrice: (json['buy_price'] as num).toDouble(),
      buyCurrency: json['buy_currency'] as String,
      buyDate: json['buy_date'] as String,
      createdAt: json['created_at'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'portfolio_id': portfolioId,
    'ticker': ticker,
    'display_name': displayName,
    'exchange': exchange,
    'quantity': quantity,
    'buy_price': buyPrice,
    'buy_currency': buyCurrency,
    'buy_date': buyDate,
    'created_at': createdAt,
  };
}

class AnalysisRequest {
  final int portfolioId;
  final double alpha;
  final double portfolioValue;
  final bool useLlm;

  AnalysisRequest({
    required this.portfolioId,
    this.alpha = 0.6,
    this.portfolioValue = 100000,
    this.useLlm = true,
  });

  factory AnalysisRequest.fromJson(Map<String, dynamic> json) {
    return AnalysisRequest(
      portfolioId: json['portfolio_id'] as int,
      alpha: (json['alpha'] as num?)?.toDouble() ?? 0.6,
      portfolioValue: (json['portfolio_value'] as num?)?.toDouble() ?? 100000,
      useLlm: json['use_llm'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
    'portfolio_id': portfolioId,
    'alpha': alpha,
    'portfolio_value': portfolioValue,
    'use_llm': useLlm,
  };
}

class AnalysisResponse {
  final List<String> tickers;
  final Map<String, String> displayNames;
  final Map<String, dynamic> optResult;
  final Map<String, dynamic> baseline;
  final Map<String, double> finalWeights;
  final Map<String, Map<String, double>> weightChanges;
  final Map<String, double> sentimentScores;
  final Map<String, dynamic> riskReport;
  final Map<String, dynamic> healthScore;
  final double selectedCap;
  final List<Map<String, dynamic>> adaptiveCandidates;
  final List<Map<String, dynamic>> recommendations;
  final Map<String, List<double>> frontier;

  AnalysisResponse({
    required this.tickers,
    required this.displayNames,
    required this.optResult,
    required this.baseline,
    required this.finalWeights,
    required this.weightChanges,
    required this.sentimentScores,
    required this.riskReport,
    required this.healthScore,
    required this.selectedCap,
    required this.adaptiveCandidates,
    required this.recommendations,
    required this.frontier,
  });

  factory AnalysisResponse.fromJson(Map<String, dynamic> json) {
    return AnalysisResponse(
      tickers: (json['tickers'] as List).cast<String>(),
      displayNames: (json['display_names'] as Map).cast<String, String>(),
      optResult: json['opt_result'] as Map<String, dynamic>,
      baseline: json['baseline'] as Map<String, dynamic>,
      finalWeights: (json['final_weights'] as Map).cast<String, double>(),
      weightChanges: (json['weight_changes'] as Map).map(
        (k, v) => MapEntry(k, (v as Map).cast<String, double>()),
      ),
      sentimentScores: (json['sentiment_scores'] as Map).cast<String, double>(),
      riskReport: json['risk_report'] as Map<String, dynamic>,
      healthScore: json['health_score'] as Map<String, dynamic>,
      selectedCap: (json['selected_cap'] as num).toDouble(),
      adaptiveCandidates: (json['adaptive_candidates'] as List)
          .map((e) => e as Map<String, dynamic>)
          .toList(),
      recommendations: (json['recommendations'] as List)
          .map((e) => e as Map<String, dynamic>)
          .toList(),
      frontier: (json['frontier'] as Map).map(
        (k, v) => MapEntry(k, (v as List).cast<double>()),
      ),
    );
  }

  Map<String, dynamic> toJson() => {
    'tickers': tickers,
    'display_names': displayNames,
    'opt_result': optResult,
    'baseline': baseline,
    'final_weights': finalWeights,
    'weight_changes': weightChanges,
    'sentiment_scores': sentimentScores,
    'risk_report': riskReport,
    'health_score': healthScore,
    'selected_cap': selectedCap,
    'adaptive_candidates': adaptiveCandidates,
    'recommendations': recommendations,
    'frontier': frontier,
  };
}

class HistoryResponse {
  final int id;
  final int portfolioId;
  final String runDate;
  final double? alphaUsed;
  final double? sharpeRatio;
  final double? expectedReturn;
  final double? volatility;
  final List<String> tickers;
  final Map<String, dynamic> optResult;
  final Map<String, double> sentimentScores;
  final List<Map<String, dynamic>> recommendations;
  final Map<String, dynamic> riskReport;

  HistoryResponse({
    required this.id,
    required this.portfolioId,
    required this.runDate,
    this.alphaUsed,
    this.sharpeRatio,
    this.expectedReturn,
    this.volatility,
    required this.tickers,
    required this.optResult,
    required this.sentimentScores,
    required this.recommendations,
    required this.riskReport,
  });

  factory HistoryResponse.fromJson(Map<String, dynamic> json) {
    return HistoryResponse(
      id: json['id'] as int,
      portfolioId: json['portfolio_id'] as int,
      runDate: json['run_date'] as String,
      alphaUsed: (json['alpha_used'] as num?)?.toDouble(),
      sharpeRatio: (json['sharpe_ratio'] as num?)?.toDouble(),
      expectedReturn: (json['expected_return'] as num?)?.toDouble(),
      volatility: (json['volatility'] as num?)?.toDouble(),
      tickers: (json['tickers'] as List).cast<String>(),
      optResult: json['opt_result'] as Map<String, dynamic>,
      sentimentScores: (json['sentiment_scores'] as Map).cast<String, double>(),
      recommendations: (json['recommendations'] as List)
          .map((e) => e as Map<String, dynamic>)
          .toList(),
      riskReport: json['risk_report'] as Map<String, dynamic>,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'portfolio_id': portfolioId,
    'run_date': runDate,
    'alpha_used': alphaUsed,
    'sharpe_ratio': sharpeRatio,
    'expected_return': expectedReturn,
    'volatility': volatility,
    'tickers': tickers,
    'opt_result': optResult,
    'sentiment_scores': sentimentScores,
    'recommendations': recommendations,
    'risk_report': riskReport,
  };
}

class BenchmarkResponse {
  final List<String> dates;
  final List<double> portfolio;
  final List<double> spy;

  BenchmarkResponse({
    required this.dates,
    required this.portfolio,
    required this.spy,
  });

  factory BenchmarkResponse.fromJson(Map<String, dynamic> json) {
    return BenchmarkResponse(
      dates: (json['dates'] as List).cast<String>(),
      portfolio: (json['portfolio'] as List).cast<double>(),
      spy: (json['spy'] as List).cast<double>(),
    );
  }

  Map<String, dynamic> toJson() => {
    'dates': dates,
    'portfolio': portfolio,
    'spy': spy,
  };
}

class MessageResponse {
  final String message;

  MessageResponse({required this.message});

  factory MessageResponse.fromJson(Map<String, dynamic> json) {
    return MessageResponse(message: json['message'] as String);
  }

  Map<String, dynamic> toJson() => {
    'message': message,
  };
}

class ErrorResponse {
  final String detail;

  ErrorResponse({required this.detail});

  factory ErrorResponse.fromJson(Map<String, dynamic> json) {
    return ErrorResponse(detail: json['detail'] as String);
  }

  Map<String, dynamic> toJson() => {
    'detail': detail,
  };
}

// Authentication State Management
import 'dart:convert';
import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:encrypt/encrypt.dart';
import 'package:parhariq/api/api_models.dart';

class AuthState {
  final bool isAuthenticated;
  final UserResponse? user;
  final String? accessToken;
  final String? refreshToken;
  final DateTime? accessTokenExpiry;

  const AuthState({
    this.isAuthenticated = false,
    this.user,
    this.accessToken,
    this.refreshToken,
    this.accessTokenExpiry,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    UserResponse? user,
    String? accessToken,
    String? refreshToken,
    DateTime? accessTokenExpiry,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      user: user ?? this.user,
      accessToken: accessToken ?? this.accessToken,
      refreshToken: refreshToken ?? this.refreshToken,
      accessTokenExpiry: accessTokenExpiry ?? this.accessTokenExpiry,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'isAuthenticated': isAuthenticated,
      'user': user?.toJson(),
      'accessToken': accessToken,
      'refreshToken': refreshToken,
      'accessTokenExpiry': accessTokenExpiry?.toIso8601String(),
    };
  }

  factory AuthState.fromJson(Map<String, dynamic> json) {
    return AuthState(
      isAuthenticated: json['isAuthenticated'] ?? false,
      user: json['user'] != null ? UserResponse.fromJson(json['user']) : null,
      accessToken: json['accessToken'],
      refreshToken: json['refreshToken'],
      accessTokenExpiry: json['accessTokenExpiry'] != null
          ? DateTime.parse(json['accessTokenExpiry'])
          : null,
    );
  }
}

class SecureStorage {
  static const _storageKey = 'axiom_auth_data';
  late final Encrypter _encrypter;
  late final IV _iv;
  String? _filePath;

  SecureStorage() {
    final key = Key.fromUtf8('axiom_mobile_app_key_32_chars!!');
    _encrypter = Encrypter(AES(key, mode: AESMode.cbc));
    _iv = IV.fromLength(16);
  }

  Future<void> _init() async {
    if (_filePath != null) return;
    final dir = await getApplicationDocumentsDirectory();
    _filePath = '${dir.path}/$_storageKey.enc';
  }

  Future<void> write(AuthState state) async {
    await _init();
    final jsonString = json.encode(state.toJson());
    final encrypted = _encrypter.encrypt(jsonString, iv: _iv);
    final file = File(_filePath!);
    await file.writeAsString(encrypted.base64);
  }

  Future<AuthState?> read() async {
    await _init();
    final file = File(_filePath!);
    if (!await file.exists()) return null;
    try {
      final encryptedString = await file.readAsString();
      final encrypted = Encrypted.fromBase64(encryptedString);
      final decrypted = _encrypter.decrypt(encrypted, iv: _iv);
      return AuthState.fromJson(json.decode(decrypted));
    } catch (_) {
      return null;
    }
  }

  Future<void> delete() async {
    await _init();
    final file = File(_filePath!);
    if (await file.exists()) {
      await file.delete();
    }
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final SecureStorage _secureStorage;

  AuthNotifier(this._secureStorage) : super(const AuthState()) {
    _loadStoredAuth();
  }

  Future<void> _loadStoredAuth() async {
    final stored = await _secureStorage.read();
    if (stored != null && stored.isAuthenticated) {
      state = stored;
    }
  }

  Future<void> login(TokenResponse response) async {
    final expiry = DateTime.now().add(Duration(seconds: response.expiresIn));
    final state = AuthState(
      isAuthenticated: true,
      user: response.user,
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
      accessTokenExpiry: expiry,
    );
    await _secureStorage.write(state);
    this.state = state;
  }

  Future<void> logout() async {
    await _secureStorage.delete();
    state = const AuthState();
  }

  Future<void> updateTokens(TokenResponse response) async {
    final expiry = DateTime.now().add(Duration(seconds: response.expiresIn));
    final newState = state.copyWith(
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
      accessTokenExpiry: expiry,
    );
    await _secureStorage.write(newState);
    state = newState;
  }

  bool get isTokenExpired {
    if (state.accessTokenExpiry == null) return true;
    return DateTime.now().isAfter(state.accessTokenExpiry!.subtract(const Duration(minutes: 5)));
  }
}

final secureStorageProvider = Provider<SecureStorage>((ref) {
  return SecureStorage();
});

final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.watch(secureStorageProvider));
});

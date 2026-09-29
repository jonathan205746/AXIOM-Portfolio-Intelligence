// PARHARIQ Mobile App - Main Entry Point
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:parhariq/core/config/app_config.dart';
import 'package:parhariq/core/theme/app_theme.dart';
import 'package:parhariq/core/router/app_router.dart';

void main() {
  runApp(const ProviderScope(child: ParhariqApp()));
}

class ParhariqApp extends ConsumerWidget {
  const ParhariqApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    final theme = ref.watch(appThemeProvider);

    return MaterialApp.router(
      title: AppConfig.appName,
      theme: theme,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}

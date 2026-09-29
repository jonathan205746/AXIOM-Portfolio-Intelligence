// App Router Configuration - GoRouter v14
import 'package:go_router/go_router.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:parhariq/features/auth/presentation/screens/login_screen.dart';
import 'package:parhariq/features/auth/presentation/screens/register_screen.dart';
import 'package:parhariq/features/portfolio/presentation/screens/portfolio_list_screen.dart';
import 'package:parhariq/features/portfolio/presentation/screens/portfolio_detail_screen.dart';
import 'package:parhariq/features/analysis/presentation/screens/analysis_screen.dart';
import 'package:parhariq/features/history/presentation/screens/history_screen.dart';
import 'package:parhariq/features/settings/presentation/screens/settings_screen.dart';
import 'package:parhariq/features/settings/presentation/screens/account_deletion_screen.dart';
import 'package:parhariq/auth/auth_state.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register';
      final isPublicRoute = state.matchedLocation == '/splash' ||
          state.matchedLocation == '/privacy' ||
          state.matchedLocation == '/terms' ||
          state.matchedLocation == '/responsible-use';

      if (!isLoggedIn && !isAuthRoute && !isPublicRoute) {
        return '/login';
      }
      if (isLoggedIn && isAuthRoute) {
        return '/dashboard';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (context, state) => const PortfolioListScreen(),
      ),
      GoRoute(
        path: '/portfolio/:id',
        builder: (context, state) {
          final portfolioId = int.parse(state.pathParameters['id']!);
          return PortfolioDetailScreen(portfolioId: portfolioId);
        },
      ),
      GoRoute(
        path: '/portfolio/:id/analysis',
        builder: (context, state) {
          final portfolioId = int.parse(state.pathParameters['id']!);
          return AnalysisScreen(portfolioId: portfolioId);
        },
      ),
      GoRoute(
        path: '/history',
        builder: (context, state) => const HistoryScreen(),
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsScreen(),
      ),
      GoRoute(
        path: '/settings/delete-account',
        builder: (context, state) => const AccountDeletionScreen(),
      ),
      GoRoute(
        path: '/privacy',
        builder: (context, state) => const PrivacyPolicyScreen(),
      ),
      GoRoute(
        path: '/terms',
        builder: (context, state) => const TermsScreen(),
      ),
      GoRoute(
        path: '/responsible-use',
        builder: (context, state) => const ResponsibleUseScreen(),
      ),
    ],
  );
});

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.analytics_outlined,
              size: 80,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 24),
            Text(
              'AXIOM',
              style: Theme.of(context).textTheme.displayLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              'Portfolio Intelligence',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
            const SizedBox(height: 48),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}

// Placeholder screens for static pages
class PrivacyPolicyScreen extends StatelessWidget {
  const PrivacyPolicyScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Privacy Policy')),
        body: const Center(child: Text('Privacy Policy content here')),
      );
}

class TermsScreen extends StatelessWidget {
  const TermsScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Terms of Service')),
        body: const Center(child: Text('Terms of Service content here')),
      );
}

class ResponsibleUseScreen extends StatelessWidget {
  const ResponsibleUseScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Responsible Use')),
        body: const Center(child: Text('Responsible Use content here')),
      );
}

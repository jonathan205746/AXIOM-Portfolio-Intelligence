// Portfolio List Screen
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:dio/dio.dart';
import 'package:parhariq/api/api_models.dart';
import 'package:parhariq/api/dio_provider.dart';
import 'package:parhariq/features/portfolio/presentation/widgets/create_portfolio_dialog.dart';

class PortfolioListScreen extends ConsumerStatefulWidget {
  const PortfolioListScreen({super.key});

  @override
  ConsumerState<PortfolioListScreen> createState() => _PortfolioListScreenState();
}

class _PortfolioListScreenState extends ConsumerState<PortfolioListScreen> {
  List<PortfolioResponse> _portfolios = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadPortfolios();
  }

  Future<void> _loadPortfolios() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final apiClient = ref.read(apiClientProvider);
      _portfolios = await apiClient.listPortfolios();
    } on DioException catch (e) {
      _errorMessage = e.response?.data['detail'] ?? 'Failed to load portfolios';
    } catch (e) {
      _errorMessage = 'An unexpected error occurred';
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _handleCreatePortfolio() async {
    final result = await showDialog<PortfolioCreate>(
      context: context,
      builder: (context) => const CreatePortfolioDialog(),
    );

    if (result != null) {
      setState(() => _isLoading = true);
      try {
        final apiClient = ref.read(apiClientProvider);
        final portfolio = await apiClient.createPortfolio(result);
        setState(() {
          _portfolios.insert(0, portfolio);
          _isLoading = false;
        });
        if (mounted) {
          context.push('/portfolio/${portfolio.id}');
        }
      } catch (e) {
        setState(() => _isLoading = false);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to create portfolio: $e')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Portfolios'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _handleCreatePortfolio,
            tooltip: 'Create Portfolio',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadPortfolios,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.error_outline,
                        size: 64,
                        color: theme.colorScheme.error,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _errorMessage!,
                        style: theme.textTheme.bodyLarge?.copyWith(
                          color: theme.colorScheme.error,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadPortfolios,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : _portfolios.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.folder_open,
                            size: 80,
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'No Portfolios Yet',
                            style: theme.textTheme.headlineSmall,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Create your first portfolio to get started',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
                          const SizedBox(height: 24),
                          ElevatedButton.icon(
                            onPressed: _handleCreatePortfolio,
                            icon: const Icon(Icons.add),
                            label: const Text('Create Portfolio'),
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _loadPortfolios,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _portfolios.length,
                        itemBuilder: (context, index) {
                          final portfolio = _portfolios[index];
                          return _PortfolioCard(
                            portfolio: portfolio,
                            onTap: () => context.push('/portfolio/${portfolio.id}'),
                          );
                        },
                      ),
                    ),
    );
  }
}

class _PortfolioCard extends StatelessWidget {
  final PortfolioResponse portfolio;
  final VoidCallback onTap;

  const _PortfolioCard({
    required this.portfolio,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      Icons.account_balance_wallet,
                      color: theme.colorScheme.onPrimaryContainer,
                      size: 28,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          portfolio.name,
                          style: theme.textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (portfolio.description.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            portfolio.description,
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                  Icon(
                    Icons.chevron_right,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Chip(
                    label: Text(portfolio.currency),
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Created ${_formatDate(portfolio.createdAt)}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(String dateString) {
    try {
      final date = DateTime.parse(dateString);
      return '${date.day}/${date.month}/${date.year}';
    } catch (_) {
      return dateString;
    }
  }
}

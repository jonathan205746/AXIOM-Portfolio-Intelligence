// Portfolio Detail Screen
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:dio/dio.dart';
import 'package:parhariq/api/api_models.dart';
import 'package:parhariq/api/dio_provider.dart';
import 'package:parhariq/features/portfolio/presentation/widgets/add_holding_dialog.dart';
import 'package:parhariq/features/analysis/presentation/screens/analysis_screen.dart';

class PortfolioDetailScreen extends ConsumerStatefulWidget {
  final int portfolioId;

  const PortfolioDetailScreen({super.key, required this.portfolioId});

  @override
  ConsumerState<PortfolioDetailScreen> createState() => _PortfolioDetailScreenState();
}

class _PortfolioDetailScreenState extends ConsumerState<PortfolioDetailScreen> {
  PortfolioResponse? _portfolio;
  List<HoldingResponse> _holdings = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadPortfolio();
  }

  Future<void> _loadPortfolio() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final apiClient = ref.read(apiClientProvider);
      final results = await Future.wait([
        apiClient.getPortfolio(widget.portfolioId),
        apiClient.listHoldings(widget.portfolioId),
      ]);
      _portfolio = results[0] as PortfolioResponse;
      _holdings = results[1] as List<HoldingResponse>;
    } on DioException catch (e) {
      _errorMessage = e.response?.data['detail'] ?? 'Failed to load portfolio';
    } catch (e) {
      _errorMessage = 'An unexpected error occurred';
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _handleAddHolding() async {
    final result = await showDialog<HoldingCreate>(
      context: context,
      builder: (context) => const AddHoldingDialog(),
    );

    if (result != null) {
      setState(() => _isLoading = true);
      try {
        final apiClient = ref.read(apiClientProvider);
        final holding = await apiClient.addHolding(widget.portfolioId, result);
        setState(() {
          _holdings.insert(0, holding);
          _isLoading = false;
        });
      } catch (e) {
        setState(() => _isLoading = false);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to add holding: $e')),
          );
        }
      }
    }
  }

  Future<void> _handleRunAnalysis() async {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => AnalysisScreen(portfolioId: widget.portfolioId),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(_portfolio?.name ?? 'Portfolio'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _handleAddHolding,
            tooltip: 'Add Holding',
          ),
          IconButton(
            icon: const Icon(Icons.analytics),
            onPressed: _handleRunAnalysis,
            tooltip: 'Run Analysis',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadPortfolio,
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
                        onPressed: _loadPortfolio,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : _portfolio == null
                  ? const Center(child: Text('Portfolio not found'))
                  : RefreshIndicator(
                      onRefresh: _loadPortfolio,
                      child: SingleChildScrollView(
                        physics: const AlwaysScrollableScrollPhysics(),
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _PortfolioSummaryCard(portfolio: _portfolio!),
                            const SizedBox(height: 24),
                            _HoldingsSection(
                              holdings: _holdings,
                              onAddHolding: _handleAddHolding,
                            ),
                            const SizedBox(height: 24),
                            _ActionButtons(
                              onRunAnalysis: _handleRunAnalysis,
                              onViewHistory: () => context.push('/history'),
                            ),
                          ],
                        ),
                      ),
                    ),
    );
  }
}

class _PortfolioSummaryCard extends StatelessWidget {
  final PortfolioResponse portfolio;

  const _PortfolioSummaryCard({required this.portfolio});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
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
                        style: theme.textTheme.headlineSmall?.copyWith(
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
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
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

class _HoldingsSection extends StatelessWidget {
  final List<HoldingResponse> holdings;
  final VoidCallback onAddHolding;

  const _HoldingsSection({
    required this.holdings,
    required this.onAddHolding,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Holdings (${holdings.length})',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            TextButton.icon(
              onPressed: onAddHolding,
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Add Holding'),
            ),
          ],
        ),
const SizedBox(height: 12),
holdings.isEmpty
    ? Card(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: Column(
              children: [
                Icon(
                  Icons.inventory_2_outlined,
                  size: 48,
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                const SizedBox(height: 12),
                Text(
                  'No Holdings Yet',
                  style: theme.textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  'Add your first stock holding to get started',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: onAddHolding,
                  icon: const Icon(Icons.add),
                  label: const Text('Add Holding'),
                ),
              ],
            ),
          ),
        )
      )
    : ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: holdings.length,
        separatorBuilder: (_, _) => const SizedBox(height: 8),
        itemBuilder: (context, index) {
          final holding = holdings[index];
          return _HoldingCard(holding: holding);
        },
      ),
        ],
      );
  }
}

class _HoldingCard extends StatelessWidget {
  final HoldingResponse holding;

  const _HoldingCard({required this.holding});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final investedValue = holding.quantity * holding.buyPrice;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: theme.colorScheme.primaryContainer,
                  child: Text(
                    holding.displayName[0].toUpperCase(),
                    style: TextStyle(
                      color: theme.colorScheme.onPrimaryContainer,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        holding.displayName,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        '${holding.ticker} (${holding.exchange})',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '${holding.buyCurrency} ${investedValue.toStringAsFixed(2)}',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '${holding.quantity} shares @ ${holding.buyCurrency} ${holding.buyPrice.toStringAsFixed(2)}',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Chip(
                  label: Text('Buy: ${_formatDate(holding.buyDate)}'),
                  backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
          ],
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

class _ActionButtons extends StatelessWidget {
  final VoidCallback onRunAnalysis;
  final VoidCallback onViewHistory;

  const _ActionButtons({
    required this.onRunAnalysis,
    required this.onViewHistory,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: FilledButton.icon(
            onPressed: onRunAnalysis,
            icon: const Icon(Icons.analytics),
            label: const Text('Run Analysis'),
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: OutlinedButton.icon(
            onPressed: onViewHistory,
            icon: const Icon(Icons.history),
            label: const Text('History'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ),
      ],
    );
  }
}

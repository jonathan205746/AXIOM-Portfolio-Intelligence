// Analysis Screen
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:parhariq/api/api_models.dart';
import 'package:parhariq/api/dio_provider.dart';
import 'package:parhariq/features/analysis/presentation/widgets/analysis_results.dart';

class AnalysisScreen extends ConsumerStatefulWidget {
  final int portfolioId;

  const AnalysisScreen({super.key, required this.portfolioId});

  @override
  ConsumerState<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends ConsumerState<AnalysisScreen> {
  AnalysisResponse? _analysis;
  bool _isLoading = false;
  bool _useLlm = true;
  double _alpha = 0.6;
  double _portfolioValue = 100000;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _runAnalysis();
  }

  Future<void> _runAnalysis() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final apiClient = ref.read(apiClientProvider);
      _analysis = await apiClient.runAnalysis(
        widget.portfolioId,
        AnalysisRequest(
          portfolioId: widget.portfolioId,
          alpha: _alpha,
          portfolioValue: _portfolioValue,
          useLlm: _useLlm,
        ),
      );
    } on DioException catch (e) {
      _errorMessage = e.response?.data['detail'] ?? 'Analysis failed';
    } catch (e) {
      _errorMessage = 'An unexpected error occurred';
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _showSettingsDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Analysis Settings'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SwitchListTile(
              title: const Text('Use AI Commentary'),
              subtitle: const Text('Include LLM-generated research commentary'),
              value: _useLlm,
              onChanged: (value) => setState(() => _useLlm = value),
            ),
            ListTile(
              title: const Text('Alpha (Risk Preference)'),
              subtitle: Text(_alpha.toStringAsFixed(1)),
              trailing: SizedBox(
                width: 200,
                child: Slider(
                  value: _alpha,
                  min: 0.0,
                  max: 1.0,
                  divisions: 10,
                  label: _alpha.toStringAsFixed(1),
                  onChanged: (value) => setState(() => _alpha = value),
                ),
              ),
            ),
            ListTile(
              title: const Text('Portfolio Value'),
              subtitle: Text('\$${_portfolioValue.toStringAsFixed(0)}'),
              trailing: SizedBox(
                width: 200,
                child: Slider(
                  value: _portfolioValue,
                  min: 1000,
                  max: 1000000,
                  divisions: 999,
                  label: '\$${_portfolioValue.toStringAsFixed(0)}',
                  onChanged: (value) => setState(() => _portfolioValue = value),
                ),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              _runAnalysis();
            },
            child: const Text('Run Analysis'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Portfolio Analysis'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: _showSettingsDialog,
            tooltip: 'Settings',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _runAnalysis,
            tooltip: 'Re-run Analysis',
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
                        onPressed: _runAnalysis,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : _analysis == null
                  ? const Center(child: Text('No analysis available'))
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: AnalysisResults(analysis: _analysis!),
                    ),
    );
  }
}

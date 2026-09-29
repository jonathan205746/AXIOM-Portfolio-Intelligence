// Analysis Results Widget
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:parhariq/api/api_models.dart';

class AnalysisResults extends StatelessWidget {
  final AnalysisResponse analysis;

  const AnalysisResults({super.key, required this.analysis});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _OptimizationSummary(analysis: analysis),
        const SizedBox(height: 24),
        _EfficientFrontierChart(analysis: analysis),
        const SizedBox(height: 24),
        _AllocationChart(analysis: analysis),
        const SizedBox(height: 24),
        _WeightChangesTable(analysis: analysis),
        const SizedBox(height: 24),
        _RiskMetricsCard(analysis: analysis),
        const SizedBox(height: 24),
        _HealthScoreCard(analysis: analysis),
        if (analysis.recommendations.isNotEmpty) ...[
          const SizedBox(height: 24),
          _RecommendationsSection(analysis: analysis),
        ],
        if (analysis.sentimentScores.isNotEmpty) ...[
          const SizedBox(height: 24),
          _SentimentSection(analysis: analysis),
        ],
      ],
    );
  }
}

class _OptimizationSummary extends StatelessWidget {
  final AnalysisResponse analysis;

  const _OptimizationSummary({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final opt = analysis.optResult;
    final baseline = analysis.baseline;

    final sharpe = (opt['sharpe_ratio'] as num?)?.toDouble() ?? 0.0;
    final expectedReturn = (opt['expected_return'] as num?)?.toDouble() ?? 0.0;
    final volatility = (opt['volatility'] as num?)?.toDouble() ?? 0.0;

    final baselineSharpe = (baseline['sharpe_ratio'] as num?)?.toDouble() ?? 0.0;
    final baselineReturn = (baseline['expected_return'] as num?)?.toDouble() ?? 0.0;
    final baselineVol = (baseline['volatility'] as num?)?.toDouble() ?? 0.0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Optimization Results',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _MetricCard(
                    label: 'Sharpe Ratio',
                    value: sharpe.toStringAsFixed(3),
                    baseline: baselineSharpe.toStringAsFixed(3),
                    isGood: sharpe > baselineSharpe,
                    icon: Icons.trending_up,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MetricCard(
                    label: 'Expected Return',
                    value: '${(expectedReturn * 100).toStringAsFixed(2)}%',
                    baseline: '${(baselineReturn * 100).toStringAsFixed(2)}%',
                    isGood: expectedReturn > baselineReturn,
                    icon: Icons.percent,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MetricCard(
                    label: 'Volatility',
                    value: '${(volatility * 100).toStringAsFixed(2)}%',
                    baseline: '${(baselineVol * 100).toStringAsFixed(2)}%',
                    isGood: volatility < baselineVol,
                    icon: Icons.show_chart,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _MetricCard(
                    label: 'Health Score',
                    value: analysis.healthScore['score']?.toStringAsFixed(1) ?? 'N/A',
                    baseline: '',
                    isGood: ((analysis.healthScore['score'] as num?) ?? 0) > 70,
                    icon: Icons.favorite,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MetricCard(
                    label: 'Selected Cap',
                    value: '${analysis.selectedCap.toStringAsFixed(1)}%',
                    baseline: '',
                    isGood: true,
                    icon: Icons.tune,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final String baseline;
  final bool isGood;
  final IconData icon;

  const _MetricCard({
    required this.label,
    required this.value,
    required this.baseline,
    required this.isGood,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 20, color: theme.colorScheme.primary),
              const SizedBox(width: 8),
              Text(
                label,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: isGood ? theme.colorScheme.primary : theme.colorScheme.error,
            ),
          ),
          if (baseline.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              'Baseline: $baseline',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _EfficientFrontierChart extends StatelessWidget {
  final AnalysisResponse analysis;

  const _EfficientFrontierChart({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final frontier = analysis.frontier;
    final opt = analysis.optResult;

    final volatility = (frontier['volatility'] as List<dynamic>?)?.cast<double>() ?? [];
    final returns = (frontier['return'] as List<dynamic>?)?.cast<double>() ?? [];
    final optimalVol = (opt['volatility'] as num?)?.toDouble() ?? 0.0;
    final optimalReturn = (opt['expected_return'] as num?)?.toDouble() ?? 0.0;

    if (volatility.isEmpty || returns.isEmpty) {
      return const SizedBox.shrink();
    }

    final spots = List.generate(
      volatility.length,
      (i) => FlSpot(volatility[i] * 100, returns[i] * 100),
    );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Efficient Frontier',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 250,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: true,
                    horizontalInterval: 2,
                    verticalInterval: 2,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: theme.colorScheme.outlineVariant,
                      strokeWidth: 0.5,
                    ),
                    getDrawingVerticalLine: (value) => FlLine(
                      color: theme.colorScheme.outlineVariant,
                      strokeWidth: 0.5,
                    ),
                  ),
                  titlesData: FlTitlesData(
                    show: true,
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 30,
                        interval: 2,
                        getTitlesWidget: (value, meta) => Text(
                          '${value.toInt()}%',
                          style: theme.textTheme.bodySmall,
                        ),
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        interval: 2,
                        reservedSize: 40,
                        getTitlesWidget: (value, meta) => Text(
                          '${value.toInt()}%',
                          style: theme.textTheme.bodySmall,
                        ),
                      ),
                    ),
                  ),
                  borderData: FlBorderData(
                    show: true,
                    border: Border.all(color: theme.colorScheme.outlineVariant),
                  ),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      color: theme.colorScheme.primary,
                      barWidth: 3,
                      isStrokeCapRound: true,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        color: theme.colorScheme.primary.withValues(alpha: 0.1),
                      ),
                    ),
                  ],
                  minX: volatility.reduce((a, b) => a < b ? a : b) * 100 - 1,
                  maxX: volatility.reduce((a, b) => a > b ? a : b) * 100 + 1,
                  minY: returns.reduce((a, b) => a < b ? a : b) * 100 - 1,
                  maxY: returns.reduce((a, b) => a > b ? a : b) * 100 + 1,
                  lineTouchData: LineTouchData(
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipItems: (touchedSpots) {
                        return touchedSpots.map((spot) {
                          return LineTooltipItem(
                            'Vol: ${spot.x.toStringAsFixed(2)}%\nRet: ${spot.y.toStringAsFixed(2)}%',
                            TextStyle(color: theme.colorScheme.onSurface),
                          );
                        }).toList();
                      },
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  'Optimal Portfolio',
                  style: theme.textTheme.bodyMedium,
                ),
              ],
            ),
            if (optimalVol > 0 && optimalReturn > 0) ...[
              const SizedBox(height: 4),
              Text(
                'Vol: ${(optimalVol * 100).toStringAsFixed(2)}% | Ret: ${(optimalReturn * 100).toStringAsFixed(2)}%',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _AllocationChart extends StatelessWidget {
  final AnalysisResponse analysis;

  const _AllocationChart({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final weights = analysis.finalWeights;
    final displayNames = analysis.displayNames;

    if (weights.isEmpty) return const SizedBox.shrink();

    final sections = weights.entries.map((entry) {
      final name = displayNames[entry.key] ?? entry.key;
      return PieChartSectionData(
        value: entry.value * 100,
        title: '$name\n${(entry.value * 100).toStringAsFixed(1)}%',
        radius: 80,
        titleStyle: theme.textTheme.bodySmall?.copyWith(
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      );
    }).toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Optimal Allocation',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 250,
              child: PieChart(
                PieChartData(
                  sections: sections,
                  centerSpaceRadius: 40,
                  sectionsSpace: 2,
                  startDegreeOffset: -90,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WeightChangesTable extends StatelessWidget {
  final AnalysisResponse analysis;

  const _WeightChangesTable({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final changes = analysis.weightChanges;

    if (changes.isEmpty) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Weight Changes',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: const [
                  DataColumn(label: Text('Ticker')),
                  DataColumn(label: Text('Change'), numeric: true),
                  DataColumn(label: Text('Direction'), numeric: true),
                ],
                rows: changes.entries.map((entry) {
                  final change = (entry.value['change'] as num?)?.toDouble() ?? 0.0;
                  final direction = change > 0 ? '↑ Increase' : change < 0 ? '↓ Decrease' : '→ Unchanged';
                  final color = change > 0
                      ? Colors.green
                      : change < 0
                          ? Colors.red
                          : theme.colorScheme.onSurfaceVariant;

                  return DataRow(
                    cells: [
                      DataCell(Text(entry.key)),
                      DataCell(Text('${(change * 100).toStringAsFixed(2)}%')),
                      DataCell(
                        Text(
                          direction,
                          style: TextStyle(color: color, fontWeight: FontWeight.w500),
                        ),
                      ),
                    ],
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RiskMetricsCard extends StatelessWidget {
  final AnalysisResponse analysis;

  const _RiskMetricsCard({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final risk = analysis.riskReport;

    if (risk.isEmpty) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Risk Metrics',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            _RiskMetricRow(
              label: 'Portfolio Beta',
              value: _formatValue(risk['portfolio_beta']),
            ),
            _RiskMetricRow(
              label: 'Max Drawdown',
              value: _formatPercent(risk['max_drawdown']),
            ),
            _RiskMetricRow(
              label: 'VaR (95%)',
              value: _formatPercent(risk['var_95']),
            ),
            _RiskMetricRow(
              label: 'CVaR (95%)',
              value: _formatPercent(risk['cvar_95']),
            ),
            _RiskMetricRow(
              label: 'Skewness',
              value: _formatValue(risk['skewness']),
            ),
            _RiskMetricRow(
              label: 'Kurtosis',
              value: _formatValue(risk['kurtosis']),
            ),
          ],
        ),
      ),
    );
  }

  String _formatValue(dynamic value) {
    if (value == null) return 'N/A';
    if (value is num) return value.toStringAsFixed(3);
    return value.toString();
  }

  String _formatPercent(dynamic value) {
    if (value == null) return 'N/A';
    if (value is num) return '${(value * 100).toStringAsFixed(2)}%';
    return value.toString();
  }
}

class _RiskMetricRow extends StatelessWidget {
  final String label;
  final String value;

  const _RiskMetricRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: theme.textTheme.bodyMedium),
          Text(
            value,
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w600,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }
}

class _HealthScoreCard extends StatelessWidget {
  final AnalysisResponse analysis;

  const _HealthScoreCard({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final health = analysis.healthScore;

    if (health.isEmpty) return const SizedBox.shrink();

    final score = (health['score'] as num?)?.toDouble() ?? 0.0;
    final color = score >= 80
        ? Colors.green
        : score >= 60
            ? Colors.orange
            : Colors.red;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.health_and_safety, color: color, size: 28),
                const SizedBox(width: 12),
                Text(
                  'Portfolio Health Score',
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: Column(
                    children: [
                      Text(
                        score.toStringAsFixed(0),
                        style: theme.textTheme.displayMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: color,
                        ),
                      ),
                      Text(
                        '/ 100',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  flex: 2,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      LinearProgressIndicator(
                        value: score / 100,
                        backgroundColor: theme.colorScheme.surfaceContainerHighest,
                        valueColor: AlwaysStoppedAnimation<Color>(color),
                        minHeight: 12,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _getHealthLabel(score),
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: color,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _getHealthLabel(double score) {
    if (score >= 80) return 'Excellent - Well diversified, low risk';
    if (score >= 60) return 'Good - Moderate diversification';
    if (score >= 40) return 'Fair - Some concentration risk';
    return 'Poor - High concentration risk';
  }
}

class _RecommendationsSection extends StatelessWidget {
  final AnalysisResponse analysis;

  const _RecommendationsSection({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'AI Research Commentary',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            ...analysis.recommendations.map((rec) {
              final ticker = rec['ticker'] as String? ?? '';
              final recommendation = rec['recommendation'] as String? ?? '';
              final rationale = rec['rationale'] as String? ?? '';

              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: theme.colorScheme.outlineVariant),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 16,
                            backgroundColor: theme.colorScheme.primaryContainer,
                            child: Text(
                              ticker[0].toUpperCase(),
                              style: TextStyle(
                                color: theme.colorScheme.onPrimaryContainer,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Text(
                            ticker,
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        recommendation,
                        style: theme.textTheme.bodyMedium,
                      ),
                      if (rationale.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(
                          rationale,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _SentimentSection extends StatelessWidget {
  final AnalysisResponse analysis;

  const _SentimentSection({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sentiments = analysis.sentimentScores;

    if (sentiments.isEmpty) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'News Sentiment',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            ...sentiments.entries.map((entry) {
              final score = entry.value;
              final color = score > 0.1
                  ? Colors.green
                  : score < -0.1
                      ? Colors.red
                      : Colors.orange;

              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 16,
                      backgroundColor: theme.colorScheme.primaryContainer,
                      child: Text(
                        entry.key[0].toUpperCase(),
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
                          Text(entry.key, style: theme.textTheme.bodyMedium),
                          const SizedBox(height: 4),
                          LinearProgressIndicator(
                            value: (score + 1) / 2,
                            backgroundColor: theme.colorScheme.surfaceContainerHighest,
                            valueColor: AlwaysStoppedAnimation<Color>(color),
                            minHeight: 6,
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ],
                      ),
                    ),
const SizedBox(width: 12),
                    Text(
                      score.toStringAsFixed(2),
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: color,
                        fontFamily: 'monospace',
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

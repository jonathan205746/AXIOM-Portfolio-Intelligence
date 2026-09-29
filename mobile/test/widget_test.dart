// This is a basic Flutter widget test.
//
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:parhariq/main.dart';

void main() {
  testWidgets('PARHARIQ AI app loads', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: ParhariqApp()));

    // Verify that the splash screen loads
    expect(find.text('PARHARIQ'), findsOneWidget);
    expect(find.text('Portfolio Intelligence'), findsOneWidget);
  });
}
// Add Holding Dialog
import 'package:flutter/material.dart';
import 'package:parhariq/api/api_models.dart';

class AddHoldingDialog extends StatefulWidget {
  const AddHoldingDialog({super.key});

  @override
  State<AddHoldingDialog> createState() => _AddHoldingDialogState();
}

class _AddHoldingDialogState extends State<AddHoldingDialog> {
  final _formKey = GlobalKey<FormState>();
  final _tickerController = TextEditingController();
  final _quantityController = TextEditingController();
  final _buyPriceController = TextEditingController();
  String _buyCurrency = 'USD';
  DateTime? _buyDate;

  @override
  void dispose() {
    _tickerController.dispose();
    _quantityController.dispose();
    _buyPriceController.dispose();
    super.dispose();
  }

  Future<void> _selectDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime.now(),
    );
    if (date != null) {
      setState(() => _buyDate = date);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add Holding'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _tickerController,
                decoration: const InputDecoration(
                  labelText: 'Ticker Symbol',
                  hintText: 'e.g., AAPL, TCS.NS',
                  helperText: 'Use .NS suffix for Indian stocks (e.g., TCS.NS)',
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter a ticker symbol';
                  }
                  return null;
                },
                autofocus: true,
                textCapitalization: TextCapitalization.characters,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _quantityController,
                decoration: const InputDecoration(
                  labelText: 'Quantity',
                  hintText: 'e.g., 10',
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter quantity';
                  }
                  final qty = double.tryParse(value);
                  if (qty == null || qty <= 0) {
                    return 'Please enter a valid positive number';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _buyPriceController,
                decoration: InputDecoration(
                  labelText: 'Buy Price ($_buyCurrency)',
                  hintText: 'e.g., 150.00',
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter buy price';
                  }
                  final price = double.tryParse(value);
                  if (price == null || price <= 0) {
                    return 'Please enter a valid positive number';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: _buyCurrency,
                decoration: const InputDecoration(
                  labelText: 'Currency',
                ),
                items: const [
                  DropdownMenuItem(value: 'USD', child: Text('USD - US Dollar')),
                  DropdownMenuItem(value: 'INR', child: Text('INR - Indian Rupee')),
                ],
                onChanged: (value) => setState(() => _buyCurrency = value!),
              ),
              const SizedBox(height: 16),
              ListTile(
                title: Text(_buyDate == null
                    ? 'Buy Date (Optional)'
                    : 'Buy Date: ${_buyDate!.day}/${_buyDate!.month}/${_buyDate!.year}'),
                leading: const Icon(Icons.calendar_today),
                onTap: _selectDate,
                trailing: _buyDate != null
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () => setState(() => _buyDate = null),
                      )
                    : null,
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () {
            if (_formKey.currentState!.validate()) {
              Navigator.pop(
                context,
                HoldingCreate(
                  ticker: _tickerController.text.trim().toUpperCase(),
                  quantity: double.parse(_quantityController.text),
                  buyPrice: double.parse(_buyPriceController.text),
                  buyCurrency: _buyCurrency,
                  buyDate: _buyDate?.toIso8601String().split('T')[0],
                ),
              );
            }
          },
          child: const Text('Add'),
        ),
      ],
    );
  }
}

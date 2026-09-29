// Create Portfolio Dialog
import 'package:flutter/material.dart';
import 'package:parhariq/api/api_models.dart';

class CreatePortfolioDialog extends StatefulWidget {
  const CreatePortfolioDialog({super.key});

  @override
  State<CreatePortfolioDialog> createState() => _CreatePortfolioDialogState();
}

class _CreatePortfolioDialogState extends State<CreatePortfolioDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  String _currency = 'USD';

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create Portfolio'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Portfolio Name',
                  hintText: 'e.g., My Retirement Portfolio',
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter a name';
                  }
                  return null;
                },
                autofocus: true,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _descriptionController,
                decoration: const InputDecoration(
                  labelText: 'Description (Optional)',
                  hintText: 'Brief description of this portfolio',
                ),
                maxLines: 3,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: _currency,
                decoration: const InputDecoration(
                  labelText: 'Currency',
                ),
                items: const [
                  DropdownMenuItem(value: 'USD', child: Text('USD - US Dollar')),
                  DropdownMenuItem(value: 'INR', child: Text('INR - Indian Rupee')),
                ],
                onChanged: (value) => setState(() => _currency = value!),
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
                PortfolioCreate(
                  name: _nameController.text.trim(),
                  description: _descriptionController.text.trim(),
                  currency: _currency,
                ),
              );
            }
          },
          child: const Text('Create'),
        ),
      ],
    );
  }
}

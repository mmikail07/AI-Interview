import 'package:flutter/material.dart';

/// Renders the `order_status` payload with a vertical progress trail.
class OrderStatusWidget extends StatelessWidget {
  const OrderStatusWidget({super.key, required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final steps = (data['steps'] as List?) ?? const [];
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.local_shipping_outlined, color: Color(0xFF1565C0)),
                const SizedBox(width: 8),
                Text('Order ${data['order_id']}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                const Spacer(),
                Text(data['eta'] != null ? 'ETA ${data['eta']}' : '',
                    style: const TextStyle(color: Colors.black54)),
              ],
            ),
            const SizedBox(height: 4),
            Text('${data['status']}  •  ${data['carrier'] ?? ''}',
                style: const TextStyle(color: Colors.black54, fontSize: 13)),
            const Divider(height: 20),
            ...steps.map((s) {
              final step = s as Map<String, dynamic>;
              final done = step['done'] == true;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Icon(done ? Icons.check_circle : Icons.radio_button_unchecked,
                        size: 20, color: done ? Colors.green : Colors.black26),
                    const SizedBox(width: 10),
                    Text(step['label']?.toString() ?? '',
                        style: TextStyle(
                            color: done ? Colors.black87 : Colors.black45,
                            fontWeight: done ? FontWeight.w600 : FontWeight.normal)),
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

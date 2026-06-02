import 'package:flutter/material.dart';

/// A flexible key/value info card reused by refund, complaint, and escalation
/// UI types. Each gets its own icon + accent so they remain visually distinct
/// while sharing one implementation (extensibility without widget sprawl).
class InfoCardWidget extends StatelessWidget {
  const InfoCardWidget({
    super.key,
    required this.data,
    required this.icon,
    required this.accent,
    required this.fields,
  });

  final Map<String, dynamic> data;
  final IconData icon;
  final Color accent;

  /// Ordered list of (label, jsonKey) pairs to display.
  final List<MapEntry<String, String>> fields;

  factory InfoCardWidget.refund(Map<String, dynamic> data) => InfoCardWidget(
        data: data,
        icon: Icons.assignment_return_outlined,
        accent: const Color(0xFF6A1B9A),
        fields: const [
          MapEntry('Refund ID', 'refund_id'),
          MapEntry('Order', 'order_id'),
          MapEntry('Status', 'status'),
          MapEntry('Reason', 'reason'),
          MapEntry('Expected (days)', 'expected_days'),
        ],
      );

  factory InfoCardWidget.complaint(Map<String, dynamic> data) => InfoCardWidget(
        data: data,
        icon: Icons.report_problem_outlined,
        accent: const Color(0xFFC62828),
        fields: const [
          MapEntry('Ticket', 'ticket_id'),
          MapEntry('Summary', 'summary'),
          MapEntry('Priority', 'priority'),
          MapEntry('Status', 'status'),
        ],
      );

  factory InfoCardWidget.escalation(Map<String, dynamic> data) => InfoCardWidget(
        data: data,
        icon: Icons.support_agent_outlined,
        accent: const Color(0xFF00695C),
        fields: const [
          MapEntry('Case', 'case_id'),
          MapEntry('Topic', 'topic'),
          MapEntry('Status', 'status'),
          MapEntry('Queue position', 'queue_position'),
          MapEntry('Est. wait (min)', 'estimated_wait_minutes'),
        ],
      );

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: accent),
            const SizedBox(height: 10),
            ...fields
                .where((f) => data[f.value] != null)
                .map((f) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SizedBox(
                            width: 130,
                            child: Text(f.key,
                                style: const TextStyle(color: Colors.black54, fontSize: 13)),
                          ),
                          Expanded(
                            child: Text('${data[f.value]}',
                                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                          ),
                        ],
                      ),
                    )),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

class FlightWidget extends StatelessWidget {
  const FlightWidget({super.key, required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final flights = (data['flights'] as List?) ?? const [];
    if (flights.isEmpty) {
      return const Padding(
        padding: EdgeInsets.all(12),
        child: Text('No flights matched that route.', style: TextStyle(color: Colors.black54)),
      );
    }
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: flights.length,
      itemBuilder: (context, i) {
        final f = flights[i] as Map<String, dynamic>;
        final stops = (f['stops'] as num?)?.toInt() ?? 0;
        return Card(
          margin: const EdgeInsets.symmetric(vertical: 5),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            leading: const CircleAvatar(child: Icon(Icons.flight_takeoff)),
            title: Text(f['airline']?.toString() ?? 'Airline',
                style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text('${f['origin']} → ${f['destination']}  •  ${f['duration']}  •  '
                '${stops == 0 ? 'Non-stop' : '$stops stop'}'),
            trailing: Text('\$${f['price']}',
                style: const TextStyle(
                    fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF1565C0))),
          ),
        );
      },
    );
  }
}

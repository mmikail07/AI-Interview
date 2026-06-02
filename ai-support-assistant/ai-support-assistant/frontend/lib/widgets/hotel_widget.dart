import 'package:flutter/material.dart';

/// Renders the `hotel_list` payload as a real, structured list of hotel cards.
/// Each card uses Image (network placeholder), Text for name/price/rating, and
/// a star indicator — per the task's HotelWidget requirement.
class HotelWidget extends StatelessWidget {
  const HotelWidget({super.key, required this.data});

  /// Expects: { location, count, hotels: [ {name, price, rating, image, location} ] }
  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final hotels = (data['hotels'] as List?) ?? const [];
    final location = data['location'] ?? '';

    if (hotels.isEmpty) {
      return _emptyState('No hotels matched. Try a higher price or a different city.');
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8, left: 4),
          child: Text('${hotels.length} hotels in $location',
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        ),
        ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: hotels.length,
          itemBuilder: (context, i) => _HotelCard(hotel: hotels[i] as Map<String, dynamic>),
        ),
      ],
    );
  }

  Widget _emptyState(String msg) => Padding(
        padding: const EdgeInsets.all(12),
        child: Text(msg, style: const TextStyle(color: Colors.black54)),
      );
}

class _HotelCard extends StatelessWidget {
  const _HotelCard({required this.hotel});

  final Map<String, dynamic> hotel;

  @override
  Widget build(BuildContext context) {
    final name = hotel['name']?.toString() ?? 'Unknown hotel';
    final price = hotel['price'];
    final rating = (hotel['rating'] as num?)?.toDouble() ?? 0.0;
    final image = hotel['image']?.toString();

    return Card(
      clipBehavior: Clip.antiAlias,
      margin: const EdgeInsets.symmetric(vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      elevation: 1.5,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _image(image),
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name,
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 6),
                Row(
                  children: [
                    _StarRating(rating: rating),
                    const SizedBox(width: 6),
                    Text(rating.toStringAsFixed(1),
                        style: const TextStyle(color: Colors.black54, fontSize: 13)),
                    const Spacer(),
                    Text('\$$price',
                        style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1565C0))),
                    const Text(' /night', style: TextStyle(color: Colors.black45, fontSize: 12)),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _image(String? url) {
    const double h = 140;
    if (url == null || url.isEmpty) return _placeholder(h);
    return Image.network(
      url,
      height: h,
      width: double.infinity,
      fit: BoxFit.cover,
      // Works fully offline: any network failure shows the local placeholder.
      errorBuilder: (_, __, ___) => _placeholder(h),
      loadingBuilder: (ctx, child, progress) =>
          progress == null ? child : _placeholder(h, loading: true),
    );
  }

  Widget _placeholder(double h, {bool loading = false}) => Container(
        height: h,
        width: double.infinity,
        color: const Color(0xFFE8EaED),
        child: Center(
          child: loading
              ? const SizedBox(
                  width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.hotel, size: 40, color: Colors.black26),
        ),
      );
}

class _StarRating extends StatelessWidget {
  const _StarRating({required this.rating});
  final double rating;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(5, (i) {
        final filled = i < rating.round();
        return Icon(filled ? Icons.star : Icons.star_border,
            size: 16, color: const Color(0xFFF6A609));
      }),
    );
  }
}

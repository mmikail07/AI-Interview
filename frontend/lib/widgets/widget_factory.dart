import 'package:flutter/material.dart';

import '../models/chat_response.dart';
import 'flight_widget.dart';
import 'hotel_widget.dart';
import 'info_card_widget.dart';
import 'order_status_widget.dart';

class WidgetFactory {
  static Widget? build(ChatResponse response) {
    final data = response.data;
    if (data is! Map) return null;
    final map = Map<String, dynamic>.from(data);

    switch (response.uiType) {
      case 'hotel_list':
        return HotelWidget(data: map);
      case 'flight_list':
        return FlightWidget(data: map);
      case 'order_status':
        return OrderStatusWidget(data: map);
      case 'refund_status':
        return InfoCardWidget.refund(map);
      case 'complaint_ack':
        return InfoCardWidget.complaint(map);
      case 'escalation':
        return InfoCardWidget.escalation(map);
      case 'text':
      default:
        return null;
    }
  }
}

import 'package:intl/intl.dart';

class Formatters {
  Formatters._();

  static String price(double amount) {
    final formatter = NumberFormat.currency(
      locale: 'ru_RU',
      symbol: '₽',
      decimalDigits: 0,
    );
    return formatter.format(amount);
  }

  static String date(DateTime date) {
    return DateFormat('d MMMM yyyy', 'ru').format(date);
  }

  static String dateShort(DateTime date) {
    return DateFormat('d MMM', 'ru').format(date);
  }

  static String time(DateTime date) {
    return DateFormat('HH:mm').format(date);
  }

  static String dateTime(DateTime date) {
    return DateFormat('d MMMM, HH:mm', 'ru').format(date);
  }

  static String timeAgo(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);
    if (diff.inMinutes < 1) return 'только что';
    if (diff.inMinutes < 60) return '${diff.inMinutes} мин назад';
    if (diff.inHours < 24) return '${diff.inHours} ч назад';
    if (diff.inDays < 7) return '${diff.inDays} дн назад';
    return dateShort(date);
  }

  static String rating(double rating) {
    return rating.toStringAsFixed(1);
  }

  static String duration(int minutes) {
    if (minutes < 60) return '$minutes мин';
    final h = minutes ~/ 60;
    final m = minutes % 60;
    if (m == 0) return '$h ч';
    return '$h ч $m мин';
  }

  static String phone(String phone) {
    if (phone.length < 11) return phone;
    return '+${phone[1]} (${phone.substring(2, 5)}) ${phone.substring(5, 8)}-${phone.substring(8, 10)}-${phone.substring(10)}';
  }
}

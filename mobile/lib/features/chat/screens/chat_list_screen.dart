import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../shared/models/chat.dart';
import '../../../shared/widgets/loading_shimmer.dart';
import '../../../shared/widgets/empty_state.dart';

final chatRoomsProvider = FutureProvider<List<ChatRoom>>((ref) async {
  final api = ref.read(chatApiProvider);
  final response = await api.getRooms();
  final items = response.data['items'] as List;
  return items.map((e) => ChatRoom.fromJson(e)).toList();
});

class ChatListScreen extends ConsumerWidget {
  const ChatListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rooms = ref.watch(chatRoomsProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Чаты')),
      body: rooms.when(
        data: (list) {
          if (list.isEmpty) {
            return const EmptyState(
              icon: Icons.chat_bubble_outline,
              title: 'Нет чатов',
              subtitle: 'Чаты появятся после бронирования услуги',
            );
          }
          return RefreshIndicator(
            color: AppColors.primary,
            onRefresh: () async => ref.invalidate(chatRoomsProvider),
            child: ListView.builder(
              itemCount: list.length,
              itemBuilder: (context, index) {
                final room = list[index];
                return _ChatRoomTile(room: room);
              },
            ),
          );
        },
        loading: () => const Padding(
          padding: EdgeInsets.all(AppSpacing.base),
          child: LoadingShimmer(height: 72),
        ),
        error: (e, _) => Center(child: Text('Ошибка: $e')),
      ),
    );
  }
}

class _ChatRoomTile extends StatelessWidget {
  final ChatRoom room;

  const _ChatRoomTile({required this.room});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: () => context.push('/chat/${room.id}?name=${Uri.encodeComponent(room.otherUserName ?? '')}'),
      leading: CircleAvatar(
        radius: 24,
        backgroundColor: AppColors.primaryLight,
        child: const Icon(Icons.person, color: AppColors.primary),
      ),
      title: Text(room.otherUserName ?? 'Собеседник', style: AppTextStyles.bodyMBold),
      subtitle: room.lastMessage != null
          ? Text(
              room.lastMessage!,
              style: AppTextStyles.caption,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            )
          : null,
      trailing: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (room.lastMessageAt != null)
            Text(Formatters.timeAgo(room.lastMessageAt!), style: AppTextStyles.caption),
          if (room.unreadCount > 0) ...[
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: const BoxDecoration(
                color: AppColors.primary,
                shape: BoxShape.circle,
              ),
              child: Text(
                '${room.unreadCount}',
                style: AppTextStyles.captionBold.copyWith(color: Colors.white),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

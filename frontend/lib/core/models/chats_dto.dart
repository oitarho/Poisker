class ConversationDto {
  final String id;
  final String listingId;
  final String ownerUserId;
  final String interestedUserId;

  ConversationDto({
    required this.id,
    required this.listingId,
    required this.ownerUserId,
    required this.interestedUserId,
  });

  factory ConversationDto.fromJson(Map<String, dynamic> json) {
    return ConversationDto(
      id: json['id'] as String,
      listingId: json['listing_id'] as String,
      ownerUserId: json['owner_user_id'] as String,
      interestedUserId: json['interested_user_id'] as String,
    );
  }
}

class ConversationListDto {
  final List<ConversationDto> items;
  ConversationListDto(this.items);

  factory ConversationListDto.fromJson(Map<String, dynamic> json) {
    final items = (json['items'] as List<dynamic>? ?? const [])
        .map((e) => ConversationDto.fromJson(e as Map<String, dynamic>))
        .toList();
    return ConversationListDto(items);
  }
}

class ConversationSummaryDto {
  final String id;
  final String listingId;
  final String otherUserId;
  final String? lastMessageAt;
  final String? lastReadAt;
  final bool unread;

  ConversationSummaryDto({
    required this.id,
    required this.listingId,
    required this.otherUserId,
    required this.lastMessageAt,
    required this.lastReadAt,
    required this.unread,
  });

  factory ConversationSummaryDto.fromJson(Map<String, dynamic> json) {
    return ConversationSummaryDto(
      id: json['id'] as String,
      listingId: json['listing_id'] as String,
      otherUserId: json['other_user_id'] as String,
      lastMessageAt: json['last_message_at'] as String?,
      lastReadAt: json['last_read_at'] as String?,
      unread: json['unread'] as bool? ?? false,
    );
  }
}

class ConversationSummaryListDto {
  final List<ConversationSummaryDto> items;
  ConversationSummaryListDto(this.items);

  factory ConversationSummaryListDto.fromJson(Map<String, dynamic> json) {
    final items = (json['items'] as List<dynamic>? ?? const [])
        .map((e) => ConversationSummaryDto.fromJson(e as Map<String, dynamic>))
        .toList();
    return ConversationSummaryListDto(items);
  }
}

class MessageDto {
  final String id;
  final String conversationId;
  final String senderId;
  final String body;
  final String createdAt;

  MessageDto({
    required this.id,
    required this.conversationId,
    required this.senderId,
    required this.body,
    required this.createdAt,
  });

  factory MessageDto.fromJson(Map<String, dynamic> json) {
    return MessageDto(
      id: json['id'] as String,
      conversationId: json['conversation_id'] as String,
      senderId: json['sender_id'] as String,
      body: json['body'] as String,
      createdAt: json['created_at'] as String,
    );
  }
}

class MessageListDto {
  final List<MessageDto> items;
  MessageListDto(this.items);

  factory MessageListDto.fromJson(Map<String, dynamic> json) {
    final items = (json['items'] as List<dynamic>? ?? const [])
        .map((e) => MessageDto.fromJson(e as Map<String, dynamic>))
        .toList();
    return MessageListDto(items);
  }
}


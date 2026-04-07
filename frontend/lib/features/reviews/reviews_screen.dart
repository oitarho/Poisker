import 'package:flutter/material.dart';

class ReviewsScreen extends StatelessWidget {
  final String userId;
  const ReviewsScreen({super.key, required this.userId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reviews')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text('User reviews for $userId (MVP placeholder: wire to /api/v1/reviews/users/{id})'),
        ),
      ),
    );
  }
}


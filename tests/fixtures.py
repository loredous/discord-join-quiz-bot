MINIMAL_QUIZ_CONFIG = {
    "quizzes": [
        {
            "guild_ids": 111,
            "welcome_text": "Hello {mention}",
            "quiz_base_channel_id": 1,
            "log_channel_id": 2,
            "success_role_id": 10,
            "banish_role_id": 20,
            "moderator_banish_role_id": 30,
            "success_text": "Welcome!",
            "fail_text": "You failed.",
            "fail_actions": ["kick", "banish", "ban"],
            "timeout_action": "kick",
            "questions": [
                {
                    "order": 1,
                    "text": "Do you agree?",
                    "timeout": 60,
                    "timeout_text": "Too slow",
                    "fail_count": 1,
                    "answers": [
                        {"text": "Yes", "correct": True},
                        {"text": "No"},
                    ],
                }
            ],
        }
    ]
}

from fixtures import MINIMAL_QUIZ_CONFIG

from quiz_config import QuizList


def test_moderator_banish_role_id_parsed_when_present() -> None:
    quiz_list = QuizList.parse_obj(MINIMAL_QUIZ_CONFIG)
    quiz = quiz_list.quizzes[0]
    assert quiz.moderator_banish_role_id == 30


def test_moderator_banish_role_id_defaults_to_none_when_absent() -> None:
    config = {
        "quizzes": [
            {
                **MINIMAL_QUIZ_CONFIG["quizzes"][0],
            }
        ]
    }
    del config["quizzes"][0]["moderator_banish_role_id"]

    quiz_list = QuizList.parse_obj(config)
    assert quiz_list.quizzes[0].moderator_banish_role_id is None

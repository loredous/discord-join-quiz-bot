from pydantic import BaseModel, validator
from typing import Optional, List, Union
from enum import Enum
from hashlib import md5

class Action(Enum):
    KICK = 1
    BAN = 2
    NOTHING = 3

class Answer(BaseModel):
    text: str
    id: str = ""
    correct: bool = False
    post_text: Optional[str]

    @validator('id', pre=True, always=True)
    def set_default_id(cls, v, *, values, **kwargs):
        return v or md5(values['text'].encode()).hexdigest()
        

class Question(BaseModel):
    order: int
    text: str
    timeout: int = 300
    timeout_text: str
    timeout_audit: str = "Timed out on a question"
    fail_count: int = 1
    fail_audit: str = "Failed a question"
    randomize_answers: bool = False
    answers: List[Answer]

    def get_answer_by_id(self, answer_id: str):
        ans = [answer for answer in self.answers if answer.id == answer_id]
        if ans:
            return ans[0]

class QuizConfig(BaseModel):
    guild_ids: Union[ int, List[int] ]
    welcome_text: str
    quiz_base_channel_id: int
    log_channel_id: Optional[int]
    success_role_id: int
    success_text: Optional[str]
    questions: List[Question]
    fail_action: Action = Action.KICK
    timeout_action: Action = Action.KICK
    fail_text: Optional[str]

    @validator('fail_action','timeout_action', pre=True)
    def set_action_by_string(cls, v, *, values, **kwargs):
        if isinstance(v, str):
            return Action[v.upper()]

class QuizList(BaseModel):
    quizzes: List[QuizConfig]

    def get_quiz_by_guild(self, guild_id):
        for quiz in self.quizzes:
            if isinstance(quiz.guild_ids,int):
                if quiz.guild_ids == guild_id:
                    return quiz
            if isinstance(quiz.guild_ids, list):
                if guild_id in quiz.guild_ids:
                    return quiz

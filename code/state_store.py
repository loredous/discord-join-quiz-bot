import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('StateStore')

STATE_VERSION = 1


def save_state(quizees: dict, state_path: str):
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = {
        "version": STATE_VERSION,
        "quizees": {
            str(guild_id): {
                str(member_id): {
                    "count": data["count"],
                    "last_quiz": data["last_quiz"].isoformat(),
                }
                for member_id, data in members.items()
            }
            for guild_id, members in quizees.items()
        },
    }
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as tmp_file:
            json.dump(serialized, tmp_file)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def load_state(state_path: str) -> dict:
    path = Path(state_path)
    if not path.is_file():
        return {}
    try:
        with open(path, 'r') as state_file:
            raw = json.load(state_file)
    except Exception:
        logger.exception(f'Failed to load state file [{state_path}]; starting with empty state.')
        return {}
    quizees = {}
    for guild_id, members in raw.get("quizees", {}).items():
        quizees[int(guild_id)] = {
            int(member_id): {
                "count": data["count"],
                "last_quiz": datetime.fromisoformat(data["last_quiz"]),
            }
            for member_id, data in members.items()
        }
    return quizees

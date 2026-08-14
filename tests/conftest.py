from pathlib import Path

import pytest
import yaml
from fixtures import MINIMAL_QUIZ_CONFIG

__all__ = ["MINIMAL_QUIZ_CONFIG", "quiz_config_file"]


@pytest.fixture
def quiz_config_file(tmp_path: Path) -> Path:
    config_path = tmp_path / "quiz_config.yaml"
    config_path.write_text(yaml.safe_dump(MINIMAL_QUIZ_CONFIG))
    return config_path

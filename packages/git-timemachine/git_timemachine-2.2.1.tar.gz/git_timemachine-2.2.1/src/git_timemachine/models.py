from datetime import datetime
from pathlib import Path
from typing import Optional, Type, TypeVar

import yaml
from pydantic import BaseModel, Field

T = TypeVar('T', bound='BaseModel')


class BaseConfig(BaseModel):
    _path: Path

    @classmethod
    def load(cls: Type[T], path: Path) -> T:
        with path.open('r', encoding='utf-8') as f:
            config = cls.model_validate(yaml.safe_load(f))
            config._path = path

            return config

    def save(self, path: Path = None) -> None:
        if path is None:
            path = self._path

        path.write_text(yaml.dump(self.model_dump(), sort_keys=False), encoding='utf-8')


class Config(BaseConfig):
    max_daily_commits: int = Field(default=5, gt=0)
    min_seconds_increased: int = Field(default=600, gt=0)
    max_seconds_increased: int = Field(default=3600, gt=0)
    update_check_interval: int = Field(default=1, gt=0)


class States(BaseConfig):
    last_commit_time: datetime = Field(default_factory=datetime.now)
    last_update_check: Optional[datetime] = datetime.now()

import os
from dataclasses import dataclass
from datetime import datetime

from croniter import croniter


@dataclass
class SynchronisationConfigItem:
    type: str
    local: str
    remote: str
    cron: str
    uuid: str = None


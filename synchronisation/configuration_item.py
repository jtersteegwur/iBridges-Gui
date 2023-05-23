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

    def validate_cron_localpath(self):
        local_valid = os.path.exists(self.local)
        cron_valid = croniter.is_valid(self.cron)
        return cron_valid and local_valid

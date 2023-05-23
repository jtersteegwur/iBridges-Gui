import datetime
from dataclasses import dataclass


@dataclass
class SynchronisationStatusEvent:
    start_date: datetime.datetime
    end_date: datetime.datetime
    source: str
    destination: str
    status: str
    bytes: int


@dataclass
class SynchronisationStatusReport:
    uuid: str
    config_id: str
    events: list[SynchronisationStatusEvent]
    start_date: datetime.datetime  # cached - calculated based on events
    end_date: datetime.datetime  # cached - calculated based on events
    total_files_processed: int  # cached - calculated based on events
    total_files_processed_succesfully: int  # cached - calculated based on events
    total_bytes_processed: int  # cached - calculated based on events

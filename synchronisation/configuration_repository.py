from synchronisation.configuration_item import SynchronisationConfigItem
from datetime import datetime
from croniter import croniter
from utils import utils
import os
import json
import uuid

DEFAULT_EMPTY_SYNCHRONISATION_CONFIG = {
    'comment': "this file is programmatically controlled by ibridges, modification by hand might "
               "result in undefined behavior",
    'configurations': []}


class ConfigRepository:
    def __init__(self, config_path: str = None):
        if config_path is None:
            ibridges_path: utils.LocalPath = utils.LocalPath(os.path.join('~', '.ibridges')).expanduser()
            config_path = ibridges_path.joinpath("synchronisation.json")

        self.config_path = config_path
        self.config_data = []
        if os.path.isfile(config_path):
            with open(self.config_path, "r") as file_obj:
                try:
                    load = json.load(file_obj)
                    configurations_ = load['configurations']
                    for configuration in configurations_:
                        add_me = SynchronisationConfigItem(uuid=configuration["uuid"],
                                                           type=configuration["type"],
                                                           local=configuration["local"],
                                                           remote=configuration["remote"],
                                                           cron=configuration["cron"])
                        self.config_data.append(add_me)
                except (json.JSONDecodeError, KeyError) as err:
                    raise ValueError(f"Error loading {self.config_path}, please fix or remove it.", err)
        else:
            with open(self.config_path, "x") as file_obj:
                default_config = DEFAULT_EMPTY_SYNCHRONISATION_CONFIG
                json.dump(default_config, file_obj, indent=6)

        self.observers = []

    def add_config(self, item: SynchronisationConfigItem):
        item.uuid = str(uuid.uuid4())
        self.config_data.append(item)
        self.notify_config_changed()

    def update_config(self, item: SynchronisationConfigItem):
        for index, config_item in enumerate(self.config_data):
            if config_item.uuid == item.uuid:
                self.config_data[index] = item
                self.notify_config_changed()
                return

    def delete_config(self, item: SynchronisationConfigItem):
        for index, config_item in enumerate(self.config_data):
            if config_item.uuid == item.uuid:
                del self.config_data[index]
                self.notify_config_changed()
                return

    def get_all_cron_datetimes(self, config_uuid=None):
        if config_uuid is None:
            return [(config.uuid, croniter.next(croniter(config.cron))) for config in self.config_data]
        else:
            return [(config_uuid, croniter.next(croniter(self.get_by_id(config_uuid).cron)))]

    def len(self):
        return len(self.config_data)

    def get_by_index(self, index: int):
        if index < 0 or index >= len(self.config_data):
            logging.error("invalid index!")
            return None
        else:
            return self.config_data[index]

    def get_by_id(self, id: str):
        for index, config_item in enumerate(self.config_data):
            if config_item.uuid == id:
                return self.config_data[index]

    def attach_obverver(self, observer):
        self.observers.append(observer)

    def detach_obverver(self, observer):
        self.observers.remove(observer)

    def notify_config_changed(self):
        self.write_current_config_to_file()
        for obs in self.observers:
            obs()

    def write_current_config_to_file(self):
        with open(self.config_path, "r") as file_obj:
            data = json.load(file_obj)
        data['configurations'] = [blah.__dict__ for blah in self.config_data]
        with open(self.config_path, "w") as file_obj:
            json.dump(data, file_obj, indent=6)

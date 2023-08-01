from yaml import safe_load as yaml_to_py_dict
from yaml import safe_dump as py_dict_to_yaml
from typing import Any

class Loader():
    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        

    def _save(self, config_dict: dict):
        with open(self.config_file_path, "w") as config_file:
            config_file.write(py_dict_to_yaml(config_dict))


    def _load(self) -> dict[str, Any]:
        with open(self.config_file_path, "r") as config_file:
            if config_file.read() and config_file.readable():
                config_file.seek(0)
                config: dict = yaml_to_py_dict(config_file.read())
                return config
            else:
                return {}


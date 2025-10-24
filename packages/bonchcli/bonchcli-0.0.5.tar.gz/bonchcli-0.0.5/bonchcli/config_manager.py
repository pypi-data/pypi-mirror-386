from dataclasses import dataclass
import os
import pathlib

from tomlkit import comment, parse
from tomlkit import document
from tomlkit import nl
from tomlkit import table


@dataclass
class Config:
    mail: str
    password: str


class ConfigManager:
    def __init__(self):
        self.home_path = str(pathlib.Path.home())
        self.path_config_file = pathlib.Path(f"{self.home_path}/.config/bonchcli/bonchcli.conf")
        self.path_config_dir = pathlib.Path(f"{self.home_path}/.config/bonchcli")

    def write_config(self, config: Config) -> None:
        doc = document()

        doc.add(comment("Всем салам братья!"))
        doc.add(nl())

        auth = table()
        auth.add("mail", config.mail)
        auth.add("password", config.password)
        doc.add("auth", auth)
        doc.add(nl())

        toml = doc.as_string()

        with open(self.path_config_file, "w") as file:
            file.write(toml)

    def read_config(self) -> Config:
        with open(self.path_config_file) as file:
           config = parse(file.read())

        return Config(
            config["auth"]["mail"],
            config["auth"]["password"]
        )

    def check_validity_config(self):
        "Check validity of the config"

        with open(self.path_config_file) as file:
           config = parse(file.read())

        try:
            config["auth"]["mail"],
            config["auth"]["password"]
        except:
            return False

        return True

    def create_config_file(self):
        pathlib.Path.mkdir(self.path_config_dir, mode=0o700, exist_ok=True)
        pathlib.Path.touch(self.path_config_file, mode=400, exist_ok=True)

    def is_config_exists(self) -> bool:
        if os.path.isdir(self.path_config_dir) and os.path.isfile(self.path_config_dir):
            return True
        else:
            return False


cm = ConfigManager()

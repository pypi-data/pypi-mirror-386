# pylint: disable=C0114

import os
from smart_open import open
from csvpath import CsvPaths
from csvpath.util.box import Box
from ..file_writers import DataFileWriter
from .sftp_config import SftpConfig


class SftpDataWriter(DataFileWriter):
    @property
    def _config(self):
        config = Box().get(Box.CSVPATHS_CONFIG)
        if config is None:
            #
            # if none, we may not be in a context closely tied to a CsvPaths.
            # e.g. FP. so we create a new csvpaths just for the config. it will
            # be identical to any csvpaths in this project unless the other
            # csvpaths were long-lived and had programmatic changes.
            #
            config = CsvPaths().config
            Box().add(Box.CSVPATHS_CONFIG, config)
        return config

    def load_if(self) -> None:
        if self.sink is None:
            config = self._config
            c = SftpConfig(config)
            self.sink = open(
                self.path,
                self.mode,
                newline="",
                transport_params={
                    "connect_kwargs": {
                        "username": c.username,
                        "password": c.password,
                        "look_for_keys": False,
                        "allow_agent": False,
                    }
                },
            )

    def write(self, data) -> None:
        """
        config = self._config
        c = SftpConfig(config)
        with open(
            self.path,
            self.mode,
            newline="",
            transport_params={
                "connect_kwargs": {
                    "username": c.username,
                    "password": c.password,
                    "look_for_keys": False,
                    "allow_agent": False,
                }
            },
        ) as sink:
            sink.write(data)
        """
        if self.is_binary and not isinstance(data, bytes):
            data = data.encode(self.encoding)
        self.sink.write(data)

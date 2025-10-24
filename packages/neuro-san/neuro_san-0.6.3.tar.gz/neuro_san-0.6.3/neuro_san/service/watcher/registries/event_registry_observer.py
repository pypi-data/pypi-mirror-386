
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT

from typing import Tuple

import logging

from pathlib import Path

from watchdog.observers import Observer

from neuro_san.service.watcher.registries.registry_change_handler import RegistryChangeHandler
from neuro_san.service.watcher.registries.registry_observer import RegistryObserver


class EventRegistryObserver(RegistryObserver):
    """
    Observer class for manifest file and its directory.
    """

    def __init__(self, manifest_path: str):
        self.manifest_path: str = str(Path(manifest_path).resolve())
        self.registry_path: str = str(Path(self.manifest_path).parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.observer: Observer = Observer()
        self.event_handler: RegistryChangeHandler = RegistryChangeHandler()

    def start(self):
        """
        Start running observer
        """
        self.observer.schedule(self.event_handler, path=self.registry_path, recursive=True)
        self.observer.start()
        self.logger.info("Registry watchdog started on: %s for manifest %s",
                         self.registry_path, self.manifest_path)

    def reset_event_counters(self) -> Tuple[int, int, int]:
        """
        Reset event counters and return current counters.
        """
        return self.event_handler.reset_event_counters()

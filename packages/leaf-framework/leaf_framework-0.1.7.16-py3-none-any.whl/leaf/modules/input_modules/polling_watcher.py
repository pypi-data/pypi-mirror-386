from abc import abstractmethod
import threading
import time
import logging

from typing import Optional
from typing import Callable
from typing import List
from typing import Dict
from typing import Any

from leaf.utility.logger.logger_utils import get_logger
from leaf.modules.input_modules.event_watcher import EventWatcher
from leaf_register.metadata import MetadataManager
from leaf.error_handler.error_holder import ErrorHolder

logger = get_logger(__name__, log_file="input_module.log")


class PollingWatcher(EventWatcher):
    """
    A base class for watchers that perform periodic polling
    to check for events like start, stop, or measurement.

    It supports callback registration and background polling.
    """

    def __init__(
        self,
        interval: int,
        metadata_manager: MetadataManager,
        callbacks: Optional[List[Callable[[str, Any], None]]] = None,
        error_holder: Optional[ErrorHolder] = None
    ) -> None:
        """
        Initialize the PollingWatcher.

        Args:
            interval (int): Polling interval in seconds.
            metadata_manager (MetadataManager): Equipment metadata manager.
            callbacks (Optional[List[Callable]]): List of event callbacks.
            error_holder (Optional[ErrorHolder]): Central error tracker.
        """
        super().__init__(metadata_manager, 
                         callbacks=callbacks, 
                         error_holder=error_holder)

        self._interval: int = interval
        self._thread: Optional[threading.Thread] = None
        self._term_map = {
            self.start_message: metadata_manager.experiment.start,
            self.stop_message: metadata_manager.experiment.stop,
            self.measurement_message: metadata_manager.experiment.measurement
        }

    def start_message(self, data: Any) -> None:
        """Dispatch start message to callbacks."""
        self._dispatch_callback(self._term_map[self.start_message], data)

    def stop_message(self, data: Any) -> None:
        """Dispatch stop message to callbacks."""
        self._dispatch_callback(self._term_map[self.stop_message], data)

    def measurement_message(self, data: Any) -> None:
        """Dispatch measurement message to callbacks."""
        self._dispatch_callback(self._term_map[self.measurement_message], data)

    @abstractmethod
    def _fetch_data(self) -> Dict[str, Optional[dict]]:
        """
        Abstract method that should be overridden to fetch
        polling data for 'start', 'stop', and 'measurement'.

        Returns:
            dict: A dictionary with optional data for each type.
        """
        pass

    def _poll(self) -> None:
        """Background loop for fetching data and dispatching events."""
        while self._running:
            data = self._fetch_data()

            if data.get("measurement") is not None:
                self.measurement_message(data["measurement"])

            if data.get("start") is not None:
                self.start_message(data["start"])

            if data.get("stop") is not None:
                self.stop_message(data["stop"])

            time.sleep(self._interval)

    def start(self) -> None:
        """
        Start the watcher and begin polling in a background thread.
        Also triggers the initialization event.
        """
        logger.info("Starting PollingWatcher...")
        if self._running:
            logger.warning("PollingWatcher already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._poll, 
                                        daemon=True)
        self._thread.start()

        super().start()

    def stop(self) -> None:
        """
        Stop the watcher and wait for the background thread to exit.
        """
        logger.info("Stopping PollingWatcher...")
        if not self._running:
            logger.warning("PollingWatcher is not running.")
            return

        self._running = False
        if self._thread:
            self._thread.join()
        logger.info("PollingWatcher stopped.")

from typing import Optional, Any

from leaf.modules.phase_modules.control import ControlPhase
from leaf_register.metadata import MetadataManager
from leaf.error_handler.error_holder import ErrorHolder
from leaf.error_handler.exceptions import InterpreterError

class StartPhase(ControlPhase):
    """
    A ControlPhase responsible for starting the process by transmitting
    the necessary actions and setting the running status. Inherits from
    ControlPhase.
    """

    def __init__(
        self,
        metadata_manager: MetadataManager,
        error_holder: Optional[ErrorHolder] = None,
    ) -> None:
        """
        Initialize the StartPhase with metadata manager and error holder.

        Args:
            metadata_manager (MetadataManager): Manages metadata associated with the phase.
            error_holder (Optional[ErrorHolder]): Optional, an error holder to manage phase errors.
        """
        term_builder = metadata_manager.experiment.start
        super().__init__(
            term_builder, metadata_manager=metadata_manager, 
            error_holder=error_holder
        )

    def update(self, data: Any) -> list:
        """
        Update the StartPhase by transmitting actions to set the equipment as running.

        Args:
            data (Any): Data to be transmitted.

        Returns:
            list: A list of tuples containing the action terms and data.
        """
        if self._interpreter is not None:
            try:
                data = self._interpreter.metadata(data)
            except Exception as ex:
                leaf_exp = InterpreterError(ex)
                self._handle_exception(leaf_exp)
                data = []
            
        data = super().update(data)
        data += [(self._metadata_manager.running(), True)]
        data += [(self._metadata_manager.experiment.stop(), None)]
        return data

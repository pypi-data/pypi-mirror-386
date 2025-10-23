"""Remote Control capability."""
from __future__ import annotations

import secsgem.secs

from .capability import Capability
from .collection_event import CollectionEventId
from .handler import GemHandler
from .remote_command import RemoteCommand, RemoteCommandId


class RemoteControlCapability(GemHandler, Capability):
    """Remote Control capability on GEM equipment."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize capability."""
        super().__init__(*args, **kwargs)

        self._remote_commands: dict[int | str | RemoteCommandId, RemoteCommand] = {
            RemoteCommandId.START.value: RemoteCommand(
                RemoteCommandId.START,
                "Start",
                [],
                CollectionEventId.CMD_START_DONE.value),
            RemoteCommandId.STOP.value: RemoteCommand(
                RemoteCommandId.STOP,
                "Stop",
                [],
                CollectionEventId.CMD_STOP_DONE.value),
        }

    @property
    def remote_commands(self) -> dict[int | str | RemoteCommandId, RemoteCommand]:
        """Get list of the remote commands.

        Returns:
            Remote command list

        """
        return self._remote_commands

    def _on_s02f41(self,
                   handler: secsgem.secs.SecsHandler,
                   message: secsgem.common.Message) -> secsgem.secs.SecsStreamFunction | None:
        """Handle Stream 2, Function 41, host command send.

        The remote command handing differs from usual stream function handling, because we send the ack with later
        completion first.
        Then we run the actual remote command callback and signal success with the matching collection event.

        Args:
            handler: handler the message was received on
            message: complete message received

        """
        del handler  # unused parameters

        function = self.settings.streams_functions.decode(message)

        rcmd_name = function.RCMD.get()
        pre_check_func = getattr(self, f"{rcmd_name}_pre_check", None)
        if pre_check_func:
            if not pre_check_func():
                return self.stream_function(2, 42)({
                    "HCACK": secsgem.secs.data_items.HCACK.CANT_PERFORM_NOW, "PARAMS": []
                })

        rcmd_callback_name = "rcmd_" + rcmd_name

        if rcmd_name not in self._remote_commands:
            self._logger.info("remote command %s not registered", rcmd_name)
            return self.stream_function(2, 42)({"HCACK": secsgem.secs.data_items.HCACK.INVALID_COMMAND, "PARAMS": []})

        if rcmd_callback_name not in self._callback_handler:
            self._logger.warning("callback for remote command %s not available", rcmd_name)
            return self.stream_function(2, 42)({"HCACK": secsgem.secs.data_items.HCACK.INVALID_COMMAND, "PARAMS": []})

        for param in function.PARAMS:
            if param.CPNAME.get() not in self._remote_commands[rcmd_name].params:
                self._logger.warning("parameter %s for remote command %s not available", param.CPNAME.get(), rcmd_name)
                return self.stream_function(2, 42)({
                    "HCACK": secsgem.secs.data_items.HCACK.PARAMETER_INVALID, "PARAMS": []
                })

        self.send_response(self.stream_function(2, 42)({
            "HCACK": secsgem.secs.data_items.HCACK.ACK_FINISH_LATER, "PARAMS": []
        }), message.header.system)

        callback = getattr(self._callback_handler, rcmd_callback_name)

        kwargs = {}
        for param in function.PARAMS.get():
            kwargs[param["CPNAME"]] = param["CPVAL"]

        callback(**kwargs)

        self.trigger_collection_events([self._remote_commands[rcmd_name].ce_finished])

        return None

    def _on_rcmd_START(self):  # noqa: N802 pylint: disable=invalid-name
        self._logger.warning("remote command START not implemented, this is required for GEM compliance")

    def _on_rcmd_STOP(self):  # noqa: N802 pylint: disable=invalid-name
        self._logger.warning("remote command STOP not implemented, this is required for GEM compliance")

"""Secs I over TCP settings class."""
from __future__ import annotations

import enum

import secsgem.common
import secsgem.secsi


class SecsITcpConnectMode(enum.Enum):
    """Secs I over TCP connect mode (client or server)."""

    CLIENT = 1
    SERVER = 2

    def __repr__(self) -> str:
        """String representation of object."""
        return "Client" if self == self.CLIENT else "Server"


class SecsITcpSettings(secsgem.secsi.SecsISettings):
    """Settings for Secs I over TCP connection.

    These attributes can be initialized in the constructor and accessed as property.

    Example:
        >>> import secsgem.secsitcp
        >>>
        >>> settings = secsgem.secsitcp.SecsITcpSettings(device_type=secsgem.common.DeviceType.EQUIPMENT)
        >>> settings.device_type
        <DeviceType.EQUIPMENT: 0>
        >>> settings.address
        '127.0.0.1'

    """

    def __init__(self, **kwargs) -> None:
        """Initialize settings."""
        super().__init__(**kwargs)

        self._connect_mode = kwargs.get("connect_mode", SecsITcpConnectMode.CLIENT)
        self._address = kwargs.get("address", "127.0.0.1")
        self._port = kwargs.get("port", 5000)

    @property
    def connect_mode(self) -> SecsITcpConnectMode:
        """Secs I over TCP connect mode.

        Default: SecsITcpConnectMode.CLIENT
        """
        return self._connect_mode

    @property
    def address(self) -> str:
        """Remote (client) or local (server) IP address.

        Default: "127.0.0.1"
        """
        return self._address

    @property
    def port(self) -> int:  # type: ignore[override]
        """TCP port of remote host.

        Default: 5000
        """
        return self._port

    def create_protocol(self) -> secsgem.common.Protocol:
        """Protocol class for this configuration."""
        from ..secsi.protocol import SecsIProtocol  # pylint: disable=import-outside-toplevel

        return SecsIProtocol(self)

    def create_connection(self) -> secsgem.common.Connection:
        """Connection class for this configuration."""
        if self.connect_mode == SecsITcpConnectMode.CLIENT:
            return secsgem.common.TcpClientConnection(self)
        return secsgem.common.TcpServerConnection(self)

    @property
    def name(self) -> str:
        """Name of this configuration."""
        return f"HSMS-{self.connect_mode}_{self.address}:{self.port}"

    def generate_thread_name(self, functionality: str) -> str:
        """Generate a unique thread name for this configuration and a provided functionality.

        Args:
            functionality: name of the functionality to generate thread name for

        Returns:
            generated thread name

        """
        return f"secsgem_SECSITCP_{functionality}_{self.connect_mode}_{self.address}:{self.port}"

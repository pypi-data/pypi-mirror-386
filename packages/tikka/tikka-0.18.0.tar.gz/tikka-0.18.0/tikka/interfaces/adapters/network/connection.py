# Copyright 2021 Vincent Texier <vit@free.fr>
#
# This software is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import abc

from tikka.interfaces.entities.Server import ServerInterface


class ConnectionInterface(abc.ABC):
    """
    ConnectionInterface class
    """

    url: str = ""

    @abc.abstractmethod
    def connect(self, server: ServerInterface) -> None:
        """
        Start connection from server

        :param server: Node instance
        :return:
        """
        raise NotImplementedError

    @abc.abstractmethod
    def disconnect(self) -> None:
        """
        Close connection

        :return:
        """
        raise NotImplementedError

    @abc.abstractmethod
    def is_connected(self) -> bool:
        """
        Return True if connection is active or OK.

        :return:
        """
        raise NotImplementedError


class NetworkConnectionError(ConnectionError):
    """
    NetworkConnectionError class
    """

    def __init__(self):
        super().__init__("Network connection error")

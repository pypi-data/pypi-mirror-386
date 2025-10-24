
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

from typing import Dict

from janus import Queue

from leaf_common.asyncio.asyncio_executor_pool import AsyncioExecutorPool

from neuro_san.internals.chat.async_collating_queue import AsyncCollatingQueue
from neuro_san.internals.network_providers.agent_network_storage import AgentNetworkStorage
from neuro_san.internals.network_providers.expiring_agent_network_storage import ExpiringAgentNetworkStorage
from neuro_san.service.utils.server_status import ServerStatus


class ServerContext:
    """
    Class that contains global-ish state for each instance of a server.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.server_status: ServerStatus = None
        self.executor_pool = AsyncioExecutorPool(reuse_mode=True)
        self.queues: Queue[AsyncCollatingQueue] = Queue()

        # Dictionary is string key (describing scope) to AgentNetworkStorage grouping.
        self.network_storage_dict: Dict[str, AgentNetworkStorage] = {
            "protected": AgentNetworkStorage(),
            "public": AgentNetworkStorage(),
            "temp": ExpiringAgentNetworkStorage()
        }

    def get_executor_pool(self) -> AsyncioExecutorPool:
        """
        :return: The AsyncioExecutorPool
        """
        return self.executor_pool

    def set_server_status(self, server_status: ServerStatus):
        """
        Sets the server status
        """
        self.server_status = server_status

    def get_server_status(self) -> ServerStatus:
        """
        :return: The ServerStatus
        """
        return self.server_status

    def get_network_storage_dict(self) -> Dict[str, AgentNetworkStorage]:
        """
        :return: The Network Storage dictionary
        """
        return self.network_storage_dict

    def get_queues(self) -> Queue[AsyncCollatingQueue]:
        """
        :return: The janus Queue of queues for temporary agent deployment
        """
        return self.queues

    def no_queues(self):
        """
        Resets the queues to None as a signal to other parts of code base
        that we don't need Reservationists
        """
        self.queues = None

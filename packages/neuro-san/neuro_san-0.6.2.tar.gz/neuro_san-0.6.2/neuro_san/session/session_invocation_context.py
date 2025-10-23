
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
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict

from copy import copy
import functools

from leaf_common.asyncio.asyncio_executor import AsyncioExecutor
from leaf_common.asyncio.asyncio_executor_pool import AsyncioExecutorPool
from leaf_server_common.logging.logging_setup import setup_extra_logging_fields

from neuro_san.interfaces.reservationist import Reservationist
from neuro_san.internals.chat.async_collating_queue import AsyncCollatingQueue
from neuro_san.internals.interfaces.async_agent_session_factory import AsyncAgentSessionFactory
from neuro_san.internals.interfaces.context_type_toolbox_factory import ContextTypeToolboxFactory
from neuro_san.internals.interfaces.context_type_llm_factory import ContextTypeLlmFactory
from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.journals.message_journal import MessageJournal
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.origination import Origination


# pylint: disable=too-many-instance-attributes
class SessionInvocationContext(InvocationContext):
    """
    Implementation of InvocationContext which encapsulates specific policy classes that pertain to
    a single invocation of an AgentSession, whether by way of a
    service call or library call.
    """

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def __init__(self, async_session_factory: AsyncAgentSessionFactory,
                 async_executors_pool: AsyncioExecutorPool,
                 llm_factory: ContextTypeLlmFactory,
                 toolbox_factory: ContextTypeToolboxFactory = None,
                 metadata: Dict[str, str] = None,
                 reservationist: Reservationist = None):
        """
        Constructor

        :param async_session_factory: The AsyncAgentSessionFactory to use
                        when connecting with external agents.
        :param async_executors_pool: pool of AsyncioExecutors to use for obtaining
                         an executor instance to use for this context;
        :param llm_factory: The ContextTypeLlmFactory instance
        :param toolbox_factory: The ContextTypeToolboxFactory instance
        :param metadata: A grpc metadata of key/value pairs to be inserted into
                         the header. Default is None. Preferred format is a
                         dictionary of string keys to string values.
        :param reservationist: The Reservationist instance to use.
        """

        self.async_session_factory: AsyncAgentSessionFactory = async_session_factory
        self.async_executors_pool: AsyncioExecutorPool = async_executors_pool
        # Get an async executor to run all tasks for this session instance:
        self.asyncio_executor: AsyncioExecutor = self.async_executors_pool.get_executor()
        self.origination: Origination = Origination()
        self.queue: AsyncCollatingQueue = AsyncCollatingQueue()
        self.journal: Journal = MessageJournal(self.queue)
        self.metadata: Dict[str, str] = metadata
        self.request_reporting: Dict[str, Any] = {}
        self.llm_factory: ContextTypeLlmFactory = llm_factory
        self.toolbox_factory: ContextTypeToolboxFactory = toolbox_factory
        self.reservationist: Reservationist = reservationist

    def start(self):
        """
        Starts the active components of this invocation context.
        Do this separately from constructor for more control.
        Currently, we only start internal AsyncioExecutor.
        It could be already running, but starting it twice is allowed.
        """
        # Wrap it up into a single function with no parameters
        # for easier handling downstream.
        logging_setup: Callable = functools.partial(setup_extra_logging_fields, metadata_dict=self.metadata)
        self.asyncio_executor.start()
        # Run logging setup as event-loop initialization step -
        # make sure it is finished before we start to use this AsyncioExecutor instance.
        self.asyncio_executor.initialize(logging_setup)

    def get_async_session_factory(self) -> AsyncAgentSessionFactory:
        """
        :return: The AsyncAgentSessionFactory associated with the invocation
        """
        return self.async_session_factory

    def get_asyncio_executor(self) -> AsyncioExecutor:
        """
        :return: The AsyncioExecutor associated with the invocation
        """
        return self.asyncio_executor

    def get_origination(self) -> Origination:
        """
        :return: The Origination instance carrying state about tool instantation
                during the course of the AgentSession.
        """
        return self.origination

    def get_journal(self) -> Journal:
        """
        :return: The Journal instance that allows message reporting
                during the course of the AgentSession.
        """
        return self.journal

    def get_queue(self) -> AsyncCollatingQueue:
        """
        :return: The AsyncCollatingQueue instance via which messages are streamed to the
                AgentSession mechanics
        """
        return self.queue

    def get_metadata(self) -> Dict[str, str]:
        """
        :return: The metadata to pass along with any request
        """
        return self.metadata

    def close(self):
        """
        Release resources owned by this context
        """
        if self.asyncio_executor is not None:
            self.async_executors_pool.return_executor(self.asyncio_executor)
            self.asyncio_executor = None
        if self.queue is not None:
            self.queue.close()

    def get_request_reporting(self) -> Dict[str, Any]:
        """
        :return: The request reporting dictionary
        """
        return self.request_reporting

    def get_llm_factory(self) -> ContextTypeLlmFactory:
        """
        :return: The ContextTypeLlmFactory instance for the session
        """
        return self.llm_factory

    def get_toolbox_factory(self) -> ContextTypeToolboxFactory:
        """
        :return: The ContextTypeToolboxFactory instance for the session
        """
        return self.toolbox_factory

    def get_reservationist(self) -> Reservationist:
        """
        :return: The Reservationist instance for the session
        """
        return self.reservationist

    def reset(self):
        """
        Resets the instance for a subsequent use for another exchange with the agent network.
        """
        # Origination needs to be reset so that origin information can match up
        # with what is in the chat_context. If we do not reset this, then library calls
        # to DirectAgentSession do not properly carry forward any memory of the conversation
        # in subsequent interactions with the same network.
        self.origination.reset()

    def safe_shallow_copy(self) -> SessionInvocationContext:
        """
        Makes a safe shallow copy of the invocation context.
        Generally used with direct sessions.
        """

        invocation_context: SessionInvocationContext = copy(self)

        # We need a different queue in order for direct sessions to call external agents
        # with direct sessions.
        invocation_context.queue: AsyncCollatingQueue = AsyncCollatingQueue()

        return invocation_context

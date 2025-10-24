
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

from typing import Any
from typing import Dict
from typing import Iterator

import contextlib
import copy
import json
import uuid

from janus import Queue

from leaf_common.asyncio.asyncio_executor import AsyncioExecutor
from leaf_common.asyncio.asyncio_executor_pool import AsyncioExecutorPool
from leaf_common.utils.atomic_counter import AtomicCounter

from leaf_server_common.server.request_logger import RequestLogger

from neuro_san.interfaces.reservationist import Reservationist
from neuro_san.internals.chat.async_collating_queue import AsyncCollatingQueue
from neuro_san.internals.graph.registry.agent_network import AgentNetwork
from neuro_san.internals.interfaces.agent_network_provider import AgentNetworkProvider
from neuro_san.internals.interfaces.context_type_toolbox_factory import ContextTypeToolboxFactory
from neuro_san.internals.interfaces.context_type_llm_factory import ContextTypeLlmFactory
from neuro_san.internals.run_context.factory.master_toolbox_factory import MasterToolboxFactory
from neuro_san.internals.run_context.factory.master_llm_factory import MasterLlmFactory
from neuro_san.service.generic.agent_server_logging import AgentServerLogging
from neuro_san.service.generic.chat_message_converter import ChatMessageConverter
from neuro_san.service.generic.service_agent_reservationist import ServiceAgentReservationist
from neuro_san.service.usage.usage_logger_factory import UsageLoggerFactory
from neuro_san.service.usage.wrapped_usage_logger import WrappedUsageLogger
from neuro_san.service.utils.server_context import ServerContext
from neuro_san.session.direct_agent_session import DirectAgentSession
from neuro_san.session.external_agent_session_factory import ExternalAgentSessionFactory
from neuro_san.session.session_invocation_context import SessionInvocationContext

# A list of methods to not log requests for
# Some of these can be way too chatty
DO_NOT_LOG_REQUESTS = [
]


# pylint: disable=too-many-instance-attributes
class AgentService:
    """
    A base implementation of the Neuro-San Agent Service,
    independent of target transport protocol.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self,
                 request_logger: RequestLogger,
                 security_cfg: Dict[str, Any],
                 agent_name: str,
                 agent_network_provider: AgentNetworkProvider,
                 server_logging: AgentServerLogging,
                 server_context: ServerContext):
        """
        Set the gRPC interface up for health checking so that the service
        will be opened to callers when the mesh sees it operational, if this
        is not done the mesh will treat the service instance as non functional

        :param request_logger: The instance of the RequestLogger that helps
                    keep track of stats
        :param security_cfg: A dictionary of parameters used to
                        secure the TLS and the authentication of the gRPC
                        connection.  Supplying this implies use of a secure
                        GRPC Channel.  If None, uses insecure channel.
        :param agent_name: The agent name for the service
        :param agent_network_provider: The AgentNetworkProvider to use for the session.
        :param server_logging: An AgentServerLogging instance initialized so that
                        spawned asyncrhonous threads can also properly initialize
                        their logging.
        :param server_context: The ServerContext containing global-ish state
        """
        self.request_logger = request_logger
        self.security_cfg = security_cfg
        self.server_logging: AgentServerLogging = server_logging

        self.agent_network_provider: AgentNetworkProvider = agent_network_provider
        self.agent_name: str = agent_name
        self.request_counter = AtomicCounter()

        # Stuff needed for ServiceAgentReservationist
        self.queues: Queue[AsyncCollatingQueue] = server_context.get_queues()

        agent_network: AgentNetwork = self.agent_network_provider.get_agent_network()
        config: Dict[str, Any] = agent_network.get_config()
        self.llm_factory: ContextTypeLlmFactory = MasterLlmFactory.create_llm_factory(config)
        self.toolbox_factory: ContextTypeToolboxFactory = MasterToolboxFactory.create_toolbox_factory(config)
        self.async_executor_pool: AsyncioExecutorPool = server_context.get_executor_pool()
        # Load once
        self.llm_factory.load()
        self.toolbox_factory.load()

    def get_request_count(self) -> int:
        """
        :return: The number of currently active requests
        """
        return self.request_counter.get_count()

    def function(self, request_dict: Dict[str, Any],
                 request_metadata: Dict[str, Any],
                 context: Any) \
            -> Dict[str, Any]:
        """
        Allows a client to get the outward-facing function for the agent
        served by this service.

        :param request_dict: a FunctionRequest dictionary
        :param request_metadata: request metadata
        :param context: a service request context object
        :return: a FunctionResponse dictionary
        """
        self.request_counter.increment()
        request_log = None
        log_marker: str = "function request"
        service_logging_dict: Dict[str, str] = {
            "request_id": f"server-{uuid.uuid4()}"
        }
        if "Function" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.Function",
                                                            log_marker, context,
                                                            service_logging_dict)

        # Get the metadata to forward on to another service
        metadata: Dict[str, str] = copy.copy(service_logging_dict)
        metadata.update(request_metadata)

        # Delegate to Direct*Session
        agent_network: AgentNetwork = self.agent_network_provider.get_agent_network()
        session = DirectAgentSession(agent_network=agent_network,
                                     invocation_context=None,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        response_dict = session.function(request_dict)

        if request_log is not None:
            self.request_logger.finish_request(f"{self.agent_name}.Function", log_marker, request_log)

        self.request_counter.decrement()
        return response_dict

    def connectivity(self, request_dict: Dict[str, Any],
                     request_metadata: Dict[str, Any],
                     context: Any) \
            -> Dict[str, Any]:
        """
        Allows a client to get connectivity information for the agent
        served by this service.

        :param request_dict: a ChatRequest dictionary
        :param request_metadata: request metadata
        :param context: a service request context object
        :return: a ConnectivityResponse dictionary
        """
        self.request_counter.increment()
        request_log = None
        log_marker: str = "connectivity request"
        service_logging_dict: Dict[str, str] = {
            "request_id": f"server-{uuid.uuid4()}"
        }
        if "Connectivity" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.Connectivity",
                                                            log_marker, context,
                                                            service_logging_dict)

        # Get the metadata to forward on to another service
        metadata: Dict[str, str] = copy.copy(service_logging_dict)
        metadata.update(request_metadata)

        # Delegate to Direct*Session
        agent_network: AgentNetwork = self.agent_network_provider.get_agent_network()
        session = DirectAgentSession(agent_network=agent_network,
                                     invocation_context=None,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        response_dict = session.connectivity(request_dict)

        if request_log is not None:
            self.request_logger.finish_request(f"{self.agent_name}.Connectivity", log_marker, request_log)

        self.request_counter.decrement()
        return response_dict

    # pylint: disable=too-many-locals
    def streaming_chat(self, request_dict: Dict[str, Any],
                       request_metadata: Dict[str, Any],
                       context: Any) \
            -> Iterator[Dict[str, Any]]:
        """
        Initiates or continues the agent chat with the session_id
        context in the request.

        :param request_dict: a ChatRequest dictionary
        :param request_metadata: request metadata
        :param context: a service request context object
        :return: an iterator for (eventually) returned responses dictionaries
        """
        self.request_counter.increment()
        request_log = None
        user_text: str = request_dict.get("user_message", {}).get("text", "")
        log_marker = f"'{user_text}'"
        service_logging_dict: Dict[str, str] = {
            "request_id": f"server-{uuid.uuid4()}"
        }
        if "StreamingChat" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.StreamingChat",
                                                            log_marker, context,
                                                            service_logging_dict)

        # Get the metadata to forward on to another service
        metadata: Dict[str, str] = copy.copy(service_logging_dict)
        metadata.update(request_metadata)
        if metadata.get("request_id") is None:
            metadata["request_id"] = service_logging_dict.get("request_id")

        # Create a reservationist
        reservationist: Reservationist = None
        if self.queues is not None:
            reservationist = ServiceAgentReservationist()
            self.queues.sync_q.put(reservationist.get_queue())

        # Prepare
        factory = ExternalAgentSessionFactory(use_direct=False)
        invocation_context = SessionInvocationContext(
            factory,
            self.async_executor_pool,
            self.llm_factory,
            self.toolbox_factory,
            metadata,
            reservationist)
        invocation_context.start()

        # Set up logging inside async thread
        # Prefer any request_id from the client over what we generated on the server.
        executor: AsyncioExecutor = invocation_context.get_asyncio_executor()
        _ = executor.submit(None, self.server_logging.setup_logging, metadata, metadata.get("request_id"))

        # Delegate to Direct*Session
        agent_network: AgentNetwork = self.agent_network_provider.get_agent_network()
        session = DirectAgentSession(agent_network=agent_network,
                                     invocation_context=invocation_context,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        # Get our args in order to pass to grpc-free session level
        response_dict_iterator: Iterator[Dict[str, Any]] = session.streaming_chat(request_dict)

        # See if we want to put the request dict in the response
        chat_filter_dict: Dict[str, Any] = {}
        chat_filter_dict = request_dict.get("chat_filter", chat_filter_dict)
        chat_filter_type: str = chat_filter_dict.get("chat_filter_type", "MINIMAL")

        try:
            for response_dict in response_dict_iterator:
                # Prepare chat message for output:
                response_dict = ChatMessageConverter().to_dict(response_dict)
                # Do not return the request when the filter is MINIMAL
                if chat_filter_type != "MINIMAL":
                    response_dict["request"] = request_dict
                yield response_dict
        finally:
            # Put iterator cleanup logic in "finally" part of try-except block;
            # this way we guarantee that underlying response_dict_iterator will be closed
            # whether we finish consuming its data stream normally
            # OR we are interrupted downstream
            # and have special "GeneratorExit" exception delivered to us.
            request_reporting: Dict[str, Any] = invocation_context.get_request_reporting()
            # Properly close our iterator:
            if response_dict_iterator is not None:
                with contextlib.suppress(Exception):
                    response_dict_iterator.close()
            # Ensure that our SessionInvocationContext is always closed,
            # even if iterator is interrupted.
            invocation_context.close()
            invocation_context = None

        # Maybe report token accounting to a UsageLogger
        token_dict: Dict[str, Any] = request_reporting.get("token_accounting")
        if token_dict is not None:
            usage_logger: WrappedUsageLogger = UsageLoggerFactory.create_usage_logger()
            usage_logger.synchronous_log_usage(token_dict, request_metadata)

        # Iterator has finally signaled that there are no more responses to be had.
        # Log that we are done.
        if request_log is not None:
            reporting: str = None
            if request_reporting is not None:
                reporting = json.dumps(request_reporting, indent=4, sort_keys=False)
            request_log.metrics("Request reporting: %s", reporting)
            self.request_logger.finish_request(f"{self.agent_name}.StreamingChat", log_marker, request_log)

        self.request_counter.decrement()

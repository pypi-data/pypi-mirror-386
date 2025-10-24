
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

from leaf_common.time.timeout import Timeout

from neuro_san.client.direct_agent_session_factory import DirectAgentSessionFactory
from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.session.http_service_agent_session import HttpServiceAgentSession


# pylint: disable=too-many-arguments,too-many-positional-arguments
class AgentSessionFactory:
    """
    Factory class for agent sessions.
    """

    def create_session(self, session_type: str,
                       agent_name: str,
                       hostname: str = None,
                       port: int = None,
                       use_direct: bool = False,
                       metadata: Dict[str, str] = None,
                       connect_timeout_in_seconds: float = None) -> AgentSession:
        """
        :param session_type: The type of session to create
        :param agent_name: The name of the agent to use for the session.
        :param hostname: The name of the host to connect to (if applicable)
        :param port: The port on the host to connect to (if applicable)
        :param use_direct: When True, will use a Direct session for
                    external agents that would reside on the same server.
        :param metadata: A grpc metadata of key/value pairs to be inserted into
                         the header. Default is None. Preferred format is a
                         dictionary of string keys to string values.
        :param connect_timeout_in_seconds: A timeout in seconds after which attempts
                        to reach a server will stop. By default this is None,
                        meaning sessions will try forever.
        """
        session: AgentSession = None

        umbrella_timeout: Timeout = None
        if connect_timeout_in_seconds is not None:
            umbrella_timeout = Timeout()
            umbrella_timeout.set_limit_in_seconds(connect_timeout_in_seconds)

        # Incorrectly flagged as destination of Trust Boundary Violation 1
        #   Reason: This is the place where the session_type enforced-string argument is
        #           actually checked for positive use.
        if session_type == "direct":
            factory = DirectAgentSessionFactory()
            session = factory.create_session(agent_name, use_direct=use_direct,
                                             metadata=metadata, umbrella_timeout=umbrella_timeout)
        elif session_type in ("http", "https"):

            # If there is no port really specified, use the default port
            use_port = port
            if port is None:
                use_port = AgentSession.DEFAULT_PORT

            security_cfg: Dict[str, Any] = None
            if session_type == "https":
                # For now, to get the https scheme
                security_cfg = {}
            session = HttpServiceAgentSession(host=hostname, port=use_port, agent_name=agent_name,
                                              security_cfg=security_cfg, metadata=metadata,
                                              timeout_in_seconds=connect_timeout_in_seconds)
        else:
            # Incorrectly flagged as destination of Trust Boundary Violation 2
            #   Reason: This is the place where the session_type enforced-string argument is
            #           actually checked for negative use.
            raise ValueError(f"session_type {session_type} is not understood")

        return session


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
from typing import Generator

import asyncio
import json

from aiohttp import ClientPayloadError
from aiohttp import ClientOSError
from aiohttp import ClientSession
from aiohttp import ClientTimeout

from neuro_san.interfaces.async_agent_session import AsyncAgentSession
from neuro_san.session.abstract_http_service_agent_session import AbstractHttpServiceAgentSession


class AsyncHttpServiceAgentSession(AbstractHttpServiceAgentSession, AsyncAgentSession):
    """
    Implementation of AsyncAgentSession that talks to an HTTP service.
    """

    async def function(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the FunctionRequest
                    protobufs structure. Has the following keys:
                        <None>
        :return: A dictionary version of the FunctionResponse
                    protobufs structure. Has the following keys:
                "function" - the dictionary description of the function
        """
        path: str = self.get_request_path("function")
        result_dict: Dict[str, Any] = None
        try:
            timeout: ClientTimeout = None
            if self.timeout_in_seconds is not None:
                timeout = ClientTimeout(self.timeout_in_seconds)

            async with ClientSession(headers=self.get_headers(),
                                     timeout=timeout
                                     ) as session:
                async with session.get(path, json=request_dict) as response:
                    result_dict = await response.json()
                    return result_dict
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ValueError(self.help_message(path)) from exc

    async def connectivity(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the ConnectivityRequest
                    protobufs structure. Has the following keys:
                        <None>
        :return: A dictionary version of the ConnectivityResponse
                    protobufs structure. Has the following keys:
                "connectivity_info" - the list of connectivity descriptions for
                                    each node in the agent network the service
                                    wants the client ot know about.
        """
        path: str = self.get_request_path("connectivity")
        result_dict: Dict[str, Any] = None
        try:
            timeout: ClientTimeout = None
            if self.timeout_in_seconds is not None:
                timeout = ClientTimeout(self.timeout_in_seconds)
            async with ClientSession(headers=self.get_headers(),
                                     timeout=timeout
                                     ) as session:
                async with session.get(path, json=request_dict) as response:
                    result_dict = await response.json()
                    return result_dict
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ValueError(self.help_message(path)) from exc

    async def streaming_chat(self, request_dict: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        :param request_dict: A dictionary version of the ChatRequest
                    protobufs structure. Has the following keys:
            "user_message" - A ChatMessage dict representing the user input to the chat stream
            "chat_context" - A ChatContext dict representing the state of the previous conversation
                            (if any)
        :return: An iterator of dictionary versions of the ChatResponse
                    protobufs structure. Has the following keys:
            "response"      - An optional ChatMessage dictionary.  See chat.proto for details.

            Note that responses to the chat input might be numerous and will come as they
            are produced until the system decides there are no more messages to be sent.
        """
        separator: bytes = b"\n"
        max_chunk_size: int = 64 * 1024
        path: str = self.get_request_path("streaming_chat")
        try:
            timeout: ClientTimeout = None
            if self.streaming_timeout_in_seconds is not None:
                timeout = ClientTimeout(self.streaming_timeout_in_seconds)
            async with ClientSession(headers=self.get_headers(),
                                     timeout=timeout
                                     ) as session:
                async with session.post(path, json=request_dict) as response:
                    # Check for successful response status
                    response.raise_for_status()

                    # Iterate over the content stream as it comes in.
                    # Note: We used to iterate over lines with the simpler:
                    #           async for line in response.content:
                    #               ... blah blah ...
                    #       but that could fail with ValueError("Chunk too big")
                    #       if a single line was too long.
                    accumulator: bytes = b""
                    async for data in response.content.iter_chunked(max_chunk_size):

                        # Concatenate data as it comes in
                        accumulator += data

                        # Try to find our line separator
                        index: int = accumulator.find(separator)
                        while index >= 0:

                            # Grab a single line
                            line: bytes = accumulator[:index]
                            unicode_line = line.decode("utf-8")
                            if unicode_line.strip():    # Skip empty lines

                                # We have a line with something in it.
                                # Decode and yield as a dictionary
                                result_dict = json.loads(unicode_line)
                                yield result_dict

                            # Remove the previous line from the accumulator
                            accumulator = accumulator[index + len(separator):]

                            # Allow for case of multiple lines in one chunk
                            index = accumulator.find(separator)

                    # If there is anything left in the accumulator, yield it
                    if len(accumulator) > 0:
                        result_dict = json.loads(accumulator.decode("utf-8"))
                        yield result_dict

        except (asyncio.TimeoutError, ClientOSError, ClientPayloadError) as exc:
            # Pass on a couple of asserts that are known to represent
            # real problems that a client has to deal with.
            # We figure this is OK for streaming_chat() because normally
            # in order to get to using streaming_chat() clients will most
            # often call function() first, and that will have the blanket
            # helpful asserts for the newly initiated.
            raise exc

        except Exception as exc:  # pylint: disable=broad-exception-caught
            # Assume the newly initiated need some more help.
            raise ValueError(self.help_message(path)) from exc

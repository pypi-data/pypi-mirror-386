
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
from typing import List

import uuid

from aiohttp.client_exceptions import ClientConnectionError

from langchain_core.messages.base import BaseMessage

from leaf_common.parsers.field_extractor import FieldExtractor

from neuro_san.internals.graph.activations.argument_assigner import ArgumentAssigner
from neuro_san.internals.graph.activations.calling_activation import CallingActivation
from neuro_san.internals.graph.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.graph.interfaces.callable_activation import CallableActivation
from neuro_san.internals.interfaces.async_agent_session_factory import AsyncAgentSessionFactory
from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.run_context.interfaces.run import Run
from neuro_san.internals.run_context.interfaces.run_context import RunContext


class BranchActivation(CallingActivation, CallableActivation):
    """
    A CallingActivation subclass which can also be a CallableActivation.
    Thus, instances are able to be branch nodes in the tool call graph.
    Leaf nodes in the call graph are also these guys, they just happen to
    not call anyone else.
    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(self, parent_run_context: RunContext,
                 factory: AgentToolFactory,
                 arguments: Dict[str, Any],
                 agent_tool_spec: Dict[str, Any],
                 sly_data: Dict[str, Any]):
        """
        Constructor

        :param parent_run_context: The parent RunContext (if any) to pass
                             down its resources to a new RunContext created by
                             this call.
        :param factory: The AgentToolFactory used to create tools
        :param arguments: A dictionary of the tool function arguments passed in
        :param agent_tool_spec: The dictionary describing the JSON agent tool
                            to be used by the instance
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be an empty dictionary.
        """
        super().__init__(parent_run_context, factory, agent_tool_spec, sly_data)
        self.arguments: Dict[str, Any] = arguments

    def get_assignments(self) -> str:
        """
        :return: The string prompt for assigning values to the arguments to the agent.
        """
        # Get the properties of the function
        extractor: FieldExtractor = FieldExtractor()
        empty: Dict[str, Any] = {}

        agent_spec: Dict[str, Any] = self.get_agent_tool_spec()

        # Properties describe the function arguments
        properties: Dict[str, Any] = extractor.get_field(agent_spec, "function.parameters.properties", empty)

        assigner = ArgumentAssigner(properties)
        # The assigner will skip any arguments that the value is None.
        assignments: List[str] = assigner.assign(self.arguments)

        # Start to build a single assignments string, with one sentence for each property
        # listed (exception for name and description).
        assignments_str: str = "\n".join(assignments)
        return assignments_str

    def get_command(self) -> str:
        """
        :return: A string describing the objective of the component.
        """
        agent_spec: Dict[str, Any] = self.get_agent_tool_spec()

        # The command will be combined with assignments (arguments from an upstream agent)
        # to direct the agent toward a specific task.
        # Optional: if omitted, the agent will choose an action based on the assignments
        # and the list of available tools.
        return agent_spec.get("command")

    async def integrate_callable_response(self, run: Run, messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        :param run: The Run for the prescriptor (if any)
        :param messages: A current list of messages for the component.
        :return: An updated list of messages after this operation is done.
                This default implementation is just a pass-through of the messages argument.
        """
        new_messages: List[BaseMessage] = messages

        callable_tool_names: List[str] = self.get_callable_tool_names(self.agent_tool_spec)
        if callable_tool_names is None:
            # If there are no callable_tool_names, then there is no action from the
            # callable class to integrate
            return new_messages

        while run.requires_action():
            # The tool we just called requires more information
            new_run: Run = await self.make_tool_function_calls(run)
            new_run = await self.run_context.wait_on_run(new_run, self.journal)
            new_messages = await self.run_context.get_response()

        return new_messages

    async def build(self) -> BaseMessage:
        """
        Main entry point to the class.

        :return: A BaseMessage produced during this process.
        """

        assignments: str = self.get_assignments()
        instructions: str = self.get_instructions()

        uuid_str: str = str(uuid.uuid4())
        component_name: str = self.get_name()
        unique_name: str = f"{uuid_str}_{component_name}"
        await self.create_resources(unique_name, instructions, None)

        # If there is command, combine it with assignment to be used as HumanMessage.
        command: str = self.get_command()
        if command:
            assignments = assignments + "\n" + command

        run: Run = await self.run_context.submit_message(assignments)
        run = await self.run_context.wait_on_run(run, self.journal)

        messages: List[BaseMessage] = await self.run_context.get_response()

        messages = await self.integrate_callable_response(run, messages)

        # Return the last message
        return messages[-1]

    def get_origin(self) -> List[Dict[str, Any]]:
        """
        :return: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with.
        """
        return self.run_context.get_origin()

    async def use_tool(self, tool_name: str, tool_args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
        """
        Experimental method to call a tool more directly from a subclass.

        NOTE: This method is not correctly reporting history or anything like that just yet.

        :param tool_name: The name of the tool to invoke
        :param tool_args: A dictionary of arguments to send to the tool.
        :param sly_data: private data dictionary to send to the tool.
        :return: A string representing the last received content text of the last message.
        """

        # Use the tool
        our_agent_spec: Dict[str, Any] = self.get_agent_tool_spec()
        callable_activation: CallableActivation = self.factory.create_agent_activation(self.run_context,
                                                                                       our_agent_spec,
                                                                                       tool_name,
                                                                                       sly_data,
                                                                                       tool_args)
        message: BaseMessage = None
        try:
            # DEF - need to integrate sly_data
            message = await callable_activation.build()

        except ClientConnectionError as exception:
            # There is a case where we could give a little more help.
            invocation_context: InvocationContext = self.run_context.get_invocation_context()
            async_factory: AsyncAgentSessionFactory = invocation_context.get_async_session_factory()
            if not async_factory.is_use_direct() and tool_name.startswith("/"):
                # Special case where we can give a hint about using direct
                raise ValueError(f"""
Attempt to call {tool_name} as an external agent network over http failed.
If you are getting this from the agent_cli command line, consider adding the --local_externals_direct
flag to your invocation.
""") from exception

            # Nope. Just a regular http connection failure given the tool_name. Can't help ya.
            raise exception

        # We got a message back, take the content as the return string
        return message.content

    async def use_reservation(self, reservation_id: str, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
        """
        Experimental method to call a reserved temporary network more directly from a subclass.

        NOTE: This method is not correctly reporting history or anything like that just yet.

        :param reservation_id: The string id of the reservation to invoke
        :param args: A dictionary of arguments to send to the reserved temporary network.
        :param sly_data: private data dictionary to send to the reserved temporary network.
        :return: A string representing the last received content text of the last message.
        """
        # DEF - for now just assume a local copy
        result: str = await self.use_tool(f"/{reservation_id}", args, sly_data)
        return result

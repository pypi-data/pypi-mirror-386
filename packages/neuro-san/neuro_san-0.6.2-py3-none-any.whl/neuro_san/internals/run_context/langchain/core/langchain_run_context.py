
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
from typing import Set
from typing import Tuple
from typing import Type
from typing import Union

import json
import traceback
import uuid

from copy import copy
from logging import Logger
from logging import getLogger

from pydantic_core import ValidationError

from langchain.agents.factory import create_agent
from langchain_classic.callbacks.tracers.logging import LoggingCallbackHandler
from langchain_core.agents import AgentFinish
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.system import SystemMessage
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables.base import Runnable
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_core.tools.base import BaseTool

from leaf_common.config.resolver_util import ResolverUtil

from neuro_san.internals.errors.error_detector import ErrorDetector
from neuro_san.internals.interfaces.async_agent_session_factory import AsyncAgentSessionFactory
from neuro_san.internals.interfaces.context_type_toolbox_factory import ContextTypeToolboxFactory
from neuro_san.internals.interfaces.context_type_llm_factory import ContextTypeLlmFactory
from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.journals.originating_journal import OriginatingJournal
from neuro_san.internals.messages.origination import Origination
from neuro_san.internals.messages.agent_message import AgentMessage
from neuro_san.internals.messages.agent_tool_result_message import AgentToolResultMessage
from neuro_san.internals.messages.base_message_dictionary_converter import BaseMessageDictionaryConverter
from neuro_san.internals.run_context.interfaces.agent_network_inspector import AgentNetworkInspector
from neuro_san.internals.run_context.interfaces.run import Run
from neuro_san.internals.run_context.interfaces.run_context import RunContext
from neuro_san.internals.run_context.interfaces.tool_caller import ToolCaller
from neuro_san.internals.run_context.langchain.core.langchain_openai_function_tool \
    import LangChainOpenAIFunctionTool
from neuro_san.internals.run_context.langchain.core.langchain_run import LangChainRun
from neuro_san.internals.run_context.langchain.journaling.journaling_callback_handler import JournalingCallbackHandler
from neuro_san.internals.run_context.langchain.mcp.langchain_mcp_adapter import LangChainMcpAdapter
from neuro_san.internals.run_context.langchain.token_counting.langchain_token_counter import LangChainTokenCounter
from neuro_san.internals.run_context.langchain.util.api_key_error_check import ApiKeyErrorCheck
from neuro_san.internals.run_context.utils.external_agent_parsing import ExternalAgentParsing
from neuro_san.internals.run_context.utils.external_tool_adapter import ExternalToolAdapter
from neuro_san.internals.run_context.langchain.llms.langchain_llm_resources import LangChainLlmResources


MINUTES: float = 60.0

# Lazily import specific errors from llm providers
API_ERROR_TYPES: Tuple[Type[Any], ...] = ResolverUtil.create_type_tuple([
                                            "openai.APIError",
                                            "anthropic.APIError",
                                            "langchain_google_genai.chat_models.ChatGoogleGenerativeAIError",
                                         ])


# pylint: disable=too-many-instance-attributes
class LangChainRunContext(RunContext):
    """
    LangChain implementation on RunContext interface supporting high-level LLM usage
    This ends up being useful:
        https://python.langchain.com/docs/modules/tools/tools_as_openai_functions/
    Note that "tools" can be just a list of OpenAI functions JSON.
    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(self, llm_config: Dict[str, Any],
                 parent_run_context: RunContext,
                 tool_caller: ToolCaller,
                 invocation_context: InvocationContext,
                 chat_context: Dict[str, Any]):
        """
        Constructor

        :param llm_config: The default llm_config to use as an overlay
                            for the tool-specific llm_config
        :param parent_run_context: The parent RunContext that is calling this one. Can be None.
        :param tool_caller: The tool caller to use
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.
        :param chat_context: A ChatContext dictionary that contains all the state necessary
                to carry on a previous conversation, possibly from a different server.
        """
        self.chat_history: List[BaseMessage] = []
        self.journal: OriginatingJournal = None
        self.llm_resources: LangChainLlmResources = None
        self.agent_chain: Runnable = None

        # This might get modified in create_resources() (for now)
        self.llm_config: Dict[str, Any] = llm_config
        self.run_id_base: str = str(uuid.uuid4())

        self.tools: List[BaseTool] = []
        self.error_detector: ErrorDetector = None
        self.recent_human_message: HumanMessage = None
        self.tool_caller: ToolCaller = tool_caller
        self.invocation_context: InvocationContext = invocation_context
        self.chat_context: Dict[str, Any] = chat_context
        self.origin: List[Dict[str, Any]] = []
        # Have we already created resources for this RunContext:
        self.resources_created: bool = False
        # Default logger
        self.logger: Logger = getLogger(self.__class__.__name__)

        parent_origin: List[Dict[str, Any]] = []
        if parent_run_context is not None:

            # Get other stuff from parent if not specified
            if self.invocation_context is None:
                self.invocation_context = parent_run_context.get_invocation_context()
            if self.chat_context is None:
                self.chat_context = parent_run_context.get_chat_context()
            parent_origin = parent_run_context.get_origin()

            # Initialize the origin.
            agent_name: str = tool_caller.get_name()
            origination: Origination = self.invocation_context.get_origination()
            self.origin = origination.add_spec_name_to_origin(parent_origin, agent_name)

        self.update_from_chat_context(self.chat_context)

        # Set up so local logging gives origin info.
        if self.origin is not None and len(self.origin) > 0:
            full_name: str = Origination.get_full_name_from_origin(self.origin)
            self.logger = getLogger(full_name)

        if self.invocation_context is not None:
            base_journal: Journal = self.invocation_context.get_journal()
            self.journal = OriginatingJournal(base_journal, self.origin, self.chat_history)

    async def create_resources(self, agent_name: str,
                               instructions: str,
                               assignments: str,
                               tool_names: List[str] = None):
        """
        Creates resources for later use within the RunContext instance.
        Results are stored as a member in this instance for future use.

        Note that even though this method is labeled as async, we don't
        really do any async method calls in here for this implementation.

        :param agent_name: String name of the agent
        :param instructions: string instructions that are used
                    to create the agent
        :param assignments: string assignments of function parameters that are used as input
        :param tool_names: The list of registered tool names to use.
                    Default is None implying no tool is to be called.
        """
        # DEF - Remove the arg if possible
        if self.resources_created:
            # Don't create RunContext resources twice -
            # we could possibly leak some run-time resources.
            return

        _ = agent_name

        full_name: str = Origination.get_full_name_from_origin(self.origin)
        agent_spec: Dict[str, Any] = self.tool_caller.get_agent_tool_spec()

        # Now that we have a name, we can create an ErrorDetector for the output.
        self.error_detector = ErrorDetector(full_name,
                                            error_formatter_name=agent_spec.get("error_formatter"),
                                            system_error_fragments=["Agent stopped"],
                                            agent_error_fragments=agent_spec.get("error_fragments"))

        if tool_names is not None:
            for tool_name in tool_names:
                tool: Union[BaseTool | List[BaseTool]] = await self._create_base_tool(tool_name)
                if tool is not None:
                    if isinstance(tool, List):
                        self.tools.extend(tool)
                    else:
                        self.tools.append(tool)

        prompt_template: ChatPromptTemplate = await self._create_prompt_template(instructions)

        self.agent_chain = self.create_agent_with_fallbacks(prompt_template)
        self.resources_created = True

    def create_agent_with_fallbacks(self, prompt_template: ChatPromptTemplate) -> Runnable:
        """
        Creates an agent with potential fallback llms to use.
        :param prompt_template: The ChatPromptTemplate to use for the agent
        :return: An Agent (Runnable)
        """
        # Initialize our return value
        agent: Runnable = None

        # Get the factory we will use
        llm_factory: ContextTypeLlmFactory = self.invocation_context.get_llm_factory()

        # Prepare a list of fallbacks.  By default, the llm_config itself is a single-entry fallback list.
        fallbacks: List[Dict[str, Any]] = [self.llm_config]
        fallbacks = self.llm_config.get("fallbacks", fallbacks)

        # Initialize a list of chain fallbacks. This may or may not get filled.
        chain_fallbacks: List[Runnable] = []

        # Go through the list of fallbacks in the config.
        for index, fallback in enumerate(fallbacks):

            # Create a model we might use.
            one_llm_resources: LangChainLlmResources = llm_factory.create_llm(fallback)
            one_agent: Runnable = self.create_agent(prompt_template, one_llm_resources.get_model())

            if index == 0:
                # The first agent is the one we want to be our main guy.
                agent = one_agent
                # For now. Could be problems with different providers w/ token counting.
                self.llm_resources = one_llm_resources
            else:
                # Anything later than the first guy is considered a fallback. Add it to the list.
                chain_fallbacks.append(one_agent)

        if len(chain_fallbacks) > 0:
            # Set up fallbacks.
            # See https://python.langchain.com/docs/how_to/tools_error/#tryexcept-tool-call
            agent = agent.with_fallbacks(chain_fallbacks)

        return agent

    def create_agent(self, prompt_template: ChatPromptTemplate, llm: BaseLanguageModel) -> Runnable:
        """
        Creates an agent.
        :param prompt_template: The ChatPromptTemplate to use for the agent
        :param llm: The BaseLanguageModel to use for the agent
        :return: An Agent (Runnable)
        """
        # Initialize our return value
        agent: Runnable = None

        # Determine how complex the meat of our agent chain will be
        meat: Runnable = llm
        if len(self.tools) > 0:
            meat = create_agent(model=llm, tools=self.tools)

        # This uses LangChain Expression Language (LCEL), which enables a functional, pipeline-style composition
        # using "|". Here, we pass `agent_scratchpad` in the input message, but since we don't explicitly assign it
        # to `intermediate_steps` (as done in the old `create_tool_calling_agent`), it remains unused by the prompt.
        #
        # In contrast, the old `create_tool_calling_agent` can be written in LCEL as
        # RunnablePassthrough | prompt | llm_with_tools | ToolsAgentOutputParser
        # where RunnablePassthrough `agent scratchpad` convert (AgentAction, tool output) tuples into ToolMessages.
        #
        # By skipping this step, our agent functions as a pure LLM-driven system with a defined role,
        # without tool invocation logic influencing its decision-making.

        agent = RunnablePassthrough() | prompt_template | meat

        return agent

    async def _create_base_tool(self, name: str) -> Union[BaseTool, List[BaseTool]]:
        """
        Create base tools for the agent to call.
        :param name: The name of the tool to create
        :return: The BaseTools associated with the name
        """

        inspector: AgentNetworkInspector = self.tool_caller.get_inspector()

        # Check our own local inspector. Most tools live in the neighborhood.
        agent_spec: Dict[str, Any] = inspector.get_agent_tool_spec(name)

        if agent_spec is None:
            return await self._create_external_tool(name)

        return await self._create_internal_tool(name, agent_spec)

    async def _create_external_tool(self, name: Union[str, Dict[str, Any]]) -> Union[BaseTool, List[BaseTool]]:
        """
        Create external agent/tool.
        :param name: The name of the external agent/tool
        :return: External agent as base tools
        """

        if not isinstance(name, (dict, str)):
            raise TypeError(f"Tools must be string or dict, got {type(name)}")

        # Handle MCP-based tool as external tool
        if ExternalAgentParsing.is_mcp_tool(name):
            return await self._create_mcp_tool(name)

        # See if the agent name given could reference an external agent.
        if not ExternalAgentParsing.is_external_agent(name):
            return None

        # Use the ExternalToolAdapter to get the function specification
        # from the service call to the external agent.
        # We should be able to use the same BaseTool for langchain integration
        # purposes as we do for any other tool, though.
        # Optimization:
        #   It's possible we might want to cache these results somehow to minimize
        #   network calls.
        session_factory: AsyncAgentSessionFactory = self.invocation_context.get_async_session_factory()
        adapter = ExternalToolAdapter(session_factory, name)
        try:
            function_json: Dict[str, Any] = await adapter.get_function_json(self.invocation_context)
            return self._create_function_tool(function_json, name)
        except ValueError as exception:
            # Could not reach the server for the external agent, so tell about it
            message: str = f"Agent/tool {name} was unreachable. Not including it as a tool.\n"
            message += str(exception)
            agent_message = AgentMessage(content=message)
            await self.journal.write_message(agent_message)
            self.logger.info(message)
            return None

    async def _create_internal_tool(self, name: str, agent_spec: Dict[str, Any]) -> BaseTool:
        """
        Create internal agent/tool.
        :param name: The name of the agent or coded tool
        :return: Agent as base tools
        """

        toolbox: str = agent_spec.get("toolbox")

        # Handle toolbox-based tools
        if toolbox:
            return await self._create_toolbox_tool(toolbox, agent_spec, name)

        # Handle coded tools
        function_json: Dict[str, Any] = agent_spec.get("function")
        if function_json is None:
            return None

        return self._create_function_tool(function_json, name)

    async def _create_mcp_tool(self, mcp_info: Union[str, Dict[str, Any]]) -> List[BaseTool]:
        """
        Create MCP tools from the provided MCP configuration.

        The configuration can be one of:
        - **String**: A URL to an MCP server.
        Valid values start with "https://mcp" or end with "/mcp" or "/mcp/".
        - **Dictionary**:
            - "server" (str): MCP server URL.
            - "tools" (List[str], optional): List of tool names to allow from the server.

        :param mcp_info: MCP server URL (string) or a configuration dictionary
        :return: A list of MCP tools as base tools
        """
        # By default, assume no allowed tools. This may get updated below or in the LangChainMcpAdadter.
        allowed_tools: List[str] = None
        if isinstance(mcp_info, str):
            server_url: str = mcp_info
        else:
            server_url = mcp_info.get("url")
            allowed_tools = mcp_info.get("tools")

        try:
            mcp_adapter = LangChainMcpAdapter()
            mcp_tools: List[BaseTool] = await mcp_adapter.get_mcp_tools(server_url, allowed_tools)

        # MCP errors are nested exceptions.
        except ExceptionGroup as nested_exception:
            # Could not reach the MCP server
            message: str = f"The URL {server_url} was unreachable. Not including it as a tool.\n"
            message += self.get_exception_details(nested_exception)
            agent_message = AgentMessage(content=message)
            await self.journal.write_message(agent_message)
            self.logger.info(message)
            return None

        # The allowed tools list might have been updated by the MCP adapter
        allowed_tools: List[str] = mcp_adapter.client_allowed_tools
        tool_names: List[str] = [tool.name for tool in mcp_tools]
        invalid_names: Set[str] = set(allowed_tools) - set(tool_names)
        # Check if there are invalid tool names in the list.
        if invalid_names:
            message = f"The following tools cannot be found in {server_url}: {invalid_names}"
            agent_message = AgentMessage(content=message)
            await self.journal.write_message(agent_message)
            self.logger.info(message)

        return mcp_tools

    def get_exception_details(self, exception, indent=0) -> str:
        """
        Recursively extract detailed information from nested exceptions.

        This function handles both regular exceptions and ExceptionGroup instances
        (introduced in Python 3.11) which can contain multiple nested exceptions.
        It creates a human-readable, hierarchical representation of all exceptions
        in the error chain.

        :param exception: The exception to analyze. Can be any Exception type,
                            including ExceptionGroup instances that contain multiple
                            nested exceptions.
        :parm indent: The current indentation level for formatting.
                                Each recursive call increases this by 1 to create
                                a visual hierarchy. Defaults to 0.

        :return: A formatted string containing the exception type, message, and
                any nested sub-exceptions with proper indentation to show the
                hierarchy. Each line ends with a newline character.

        Note:
            This function is particularly useful for debugging MCP (Model Context Protocol)
            errors and other complex exception scenarios where multiple errors can occur
            simultaneously and get wrapped in ExceptionGroup containers.
        """

        # Create indentation string based on current nesting level
        # Each level adds 2 spaces for visual hierarchy
        spaces: str = "  " * indent

        # Start building the message with exception type and description
        # Format: "ExceptionType: exception message"
        message: str = f"{spaces}{type(exception).__name__}: {exception}\n"

        # Check if this exception is an ExceptionGroup (Python 3.11+ feature)
        # ExceptionGroup can contain multiple exceptions that occurred simultaneously
        if isinstance(exception, ExceptionGroup):
            # Iterate through each sub-exception in the group
            for i, sub_exc in enumerate(exception.exceptions):
                # Add a header for each sub-exception with 1-based numbering
                message += f"{spaces}Sub-exception {i+1}:\n"

                # Recursively process the sub-exception with increased indentation
                # This handles cases where sub-exceptions might themselves be ExceptionGroups
                message += self.get_exception_details(sub_exc, indent + 1)

        return message

    async def _create_toolbox_tool(self, toolbox: str, agent_spec: Dict[str, Any], name: str) -> BaseTool:
        """Create tool from toolbox"""

        toolbox_factory: ContextTypeToolboxFactory = self.invocation_context.get_toolbox_factory()
        try:
            tool_from_toolbox = toolbox_factory.create_tool_from_toolbox(toolbox, agent_spec.get("args"), name)
            # If the tool from toolbox is base tool or list of base tool, return the tool as is
            # since tool's definition and args schema are predefined in these the class of the tool.
            if isinstance(tool_from_toolbox, BaseTool) or (
                isinstance(tool_from_toolbox, list) and
                all(isinstance(tool, BaseTool) for tool in tool_from_toolbox)
            ):
                return tool_from_toolbox

            # Otherwise, it is a shared coded tool.
            return self._create_function_tool(tool_from_toolbox, name)

        except ValueError as tool_creation_exception:
            # There are errors in tool creation process
            message: str = f"Failed to create Agent/tool '{name}': {tool_creation_exception}"
            agent_message = AgentMessage(content=message)
            await self.journal.write_message(agent_message)
            self.logger.info(message)
            return None

    def _create_function_tool(self, function_json: Dict[str, Any], name: str) -> BaseTool:
        """Create a function tool from JSON specification"""

        # In the case of external agents, if they report a name at all, they will
        # report something different that does not identify them as external.
        # Also, most internal agents do not have a name identifier on their functional
        # JSON, which is required.  Use the agent name we are using for look-up for that
        # regardless of intent.
        function_json["name"] = name

        return LangChainOpenAIFunctionTool.from_function_json(function_json, self.tool_caller)

    async def _create_prompt_template(self, instructions: str) -> ChatPromptTemplate:
        """
        Creates a ChatPromptTemplate given the generic instructions
        """
        # Assemble the prompt message list
        message_list: List[Tuple[str, str]] = []

        system_message = SystemMessage(instructions)
        if not self.chat_history:
            await self.journal.write_message(system_message)
        message_list.append(("system", instructions))

        # Fill out the rest of the prompt per the docs for create_tooling_agent()
        # Note we are not write_message()-ing the chat history because that is redundant
        # Unclear if we should somehow/someplace write_message() the agent_scratchpad at all.
        message_list.extend([
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(message_list)

        return prompt

    async def submit_message(self, user_message: str) -> Run:
        """
        Submits a message to the model used by this instance.

        Note that even though this method is labeled as async, we don't
        really do any async method calls in here for this implementation.

        :param user_message: The message to submit
        :return: The run which is processing the agent's message
        """
        # Contruct a human message out of the text of the user message
        # Don't add this to the chat history yet.
        try:
            self.recent_human_message = HumanMessage(user_message)
        except ValidationError as exception:
            full_name: str = Origination.get_full_name_from_origin(self.origin)
            message = f"ValidationError in {full_name} with message: {user_message}"
            raise ValueError(message) from exception

        # Create a run to return
        run = LangChainRun(self.run_id_base, self.chat_history)
        return run

    # pylint: disable=too-many-locals
    async def wait_on_run(self, run: Run, journal: Journal = None) -> Run:
        """
        Loops on the given run's status for model invokation.

        This truly is an asynchronous method.

        :param run: The run to wait on
        :param journal: The Journal which captures the "thinking" messages.
        :return: An potentially updated run
        """

        # Create an agent executor and invoke it with the most recent human message
        # as input.
        agent_spec: Dict[str, Any] = self.tool_caller.get_agent_tool_spec()

        verbose: Union[bool, str] = agent_spec.get("verbose", False)
        if isinstance(verbose, str):
            verbose = bool(verbose.lower() in ("true", "extra", "logging"))

        max_execution_seconds: float = agent_spec.get("max_execution_seconds", 2.0 * MINUTES)

        # Per advice from https://python.langchain.com/docs/how_to/migrate_agent/#max_iterations
        max_iterations: int = agent_spec.get("max_iterations", 20)
        recursion_limit: int = max_iterations * 2 + 1

        run: Run = LangChainRun(self.run_id_base, self.chat_history)

        # Chat history is updated in write_message() below, so to save on
        # some tokens, make a shallow copy of it here as we send it to the LLM
        previous_chat_history: List[BaseMessage] = copy(self.chat_history)

        inputs = {
            "chat_history": previous_chat_history,
            "input": self.recent_human_message.content
        }

        # Create the list of callbacks to pass when invoking
        parent_origin: List[Dict[str, Any]] = self.get_origin()
        base_journal: Journal = self.invocation_context.get_journal()
        origination: Origination = self.invocation_context.get_origination()
        callbacks: List[BaseCallbackHandler] = [
            JournalingCallbackHandler(self.journal, base_journal, parent_origin, origination)
        ]
        # Consult the agent spec for level of verbosity as it pertains to callbacks.
        agent_spec: Dict[str, Any] = self.tool_caller.get_agent_tool_spec()
        verbose: Union[bool, str] = agent_spec.get("verbose", False)
        if isinstance(verbose, str) and verbose.lower() in ("extra", "logging"):
            # This particular class adds a *lot* of very detailed messages
            # to the logs.  Add this because some people are interested in it.
            callbacks.append(LoggingCallbackHandler(self.logger))

        # Add callbacks as an invoke config
        invoke_config = {
            "configurable": {
                "session_id": run.get_id()
            },
            "callbacks": callbacks,
            "recursion_limit": recursion_limit
        }

        # Chat history is updated in write_message
        await self.journal.write_message(self.recent_human_message)

        # Attempt to count tokens/costs while invoking the agent.
        llm: BaseLanguageModel = self.llm_resources.get_model()
        token_counter = LangChainTokenCounter(llm, self.invocation_context, self.journal)
        await token_counter.count_tokens(self.ainvoke(inputs, invoke_config), max_execution_seconds)

        return run

    async def ainvoke(self, inputs: Dict[str, Any], invoke_config: Dict[str, Any]):
        """
        Set the agent in motion

        :param inputs: The inputs to the agent_executor
        :param invoke_config: The invoke_config to send to the agent_executor
        """
        chain_result: Union[Dict[str, Any], AgentFinish, AIMessage] = None
        retries: int = 3
        exception: Exception = None
        backtrace: str = None
        while chain_result is None and retries > 0:
            try:
                chain_result: Dict[str, Any] = await self.agent_chain.ainvoke(input=inputs, config=invoke_config)
            except API_ERROR_TYPES as api_error:
                backtrace = traceback.format_exc()
                message: str = None
                if not ApiKeyErrorCheck.check_for_internal_error(backtrace):
                    # Does not look like internal LLM stack error:
                    message = ApiKeyErrorCheck.check_for_api_key_exception(api_error)
                if message is not None:
                    raise ValueError(message) from api_error
                # Continue with regular retry logic:
                self.logger.warning("retrying from %s", api_error.__class__.__name__)
                retries = retries - 1
                exception = api_error
            except KeyError as key_error:
                self.logger.warning("retrying from KeyError")
                retries = retries - 1
                exception = key_error
                backtrace = traceback.format_exc()
            except ValueError as value_error:
                response = str(value_error)
                find_string = "An output parsing error occurred. " + \
                              "In order to pass this error back to the agent and have it try again, " + \
                              "pass `handle_parsing_errors=True` to the AgentExecutor. " + \
                              "This is the error: Could not parse LLM output: `"
                if response.startswith(find_string):
                    # Agent is returning good stuff, but langchain is erroring out over it.
                    # From: https://github.com/langchain-ai/langchain/issues/1358#issuecomment-1486132587
                    # Per thread consensus, this is hacky and there are better ways to go,
                    # but removes immediate impediments.
                    chain_result = {
                        "output": response.removeprefix(find_string).removesuffix("`")
                    }
                else:
                    self.logger.warning("retrying from ValueError")
                    retries = retries - 1
                    exception = value_error
                    backtrace = traceback.format_exc()

        output: str = self.parse_chain_result(chain_result, exception, backtrace)
        return_message: BaseMessage = AIMessage(output)

        # Chat history is updated in write_message
        await self.journal.write_message(return_message)

    def parse_chain_result(self, chain_result: Union[Dict[str, Any], AgentFinish, AIMessage],
                           exception: Exception, backtrace: str) -> str:
        """
        Parse the result from the langchain chain.

        :param chain_result: The result from invoking the agent chain.
                        Can be:
                        * An AgentFinish instance whose return_values can be any one of the following
                        * A dictionary whose keys might be:
                            "output" - the actual output to use
                            "messages" - effectively a chat history
                        * An AIMessage whose content is the output to use
        :param exception: Any exception that happened along the way
        :param backtrace: Any backtrace to the exception that happened along the way
        :return: A string value to return as the result of the run.
        """

        # Initialize our output.
        # The value here might morph a bit between types, but when we return
        # something we expect it to be a string.
        output: Union[str, List[Dict[str, Any]]] = None

        if chain_result is None and exception is not None:
            # We got an exception instead of a proper result. Say so.
            output = f"Agent stopped due to exception {exception}"
        else:
            # Set some stuff up for later
            backtrace = None
            ai_message: AIMessage = None

            # Handle the AgentFinish case.
            # The return_values from there contain our output whether in string or dict form.
            # ??? From what path does this come?
            if isinstance(chain_result, AgentFinish):
                chain_result = chain_result.return_values

            if isinstance(chain_result, Dict):
                # Normal return value from a chain is a dict.
                # The dict in question usually has chat history in a messages field.
                # We want the last AIMessage from that chat history.
                messages: List[BaseMessage] = chain_result.get("messages", [])
                for message in reversed(messages):
                    if isinstance(message, AIMessage):
                        ai_message = message
                        break

                if ai_message is None:
                    # We didn't find an AIMessage, so look for straight-up output key
                    output = chain_result.get("output")

            elif isinstance(chain_result, AIMessage):
                # Sometimes we get an AIMessage from a tool call.
                ai_message = chain_result

            if ai_message is not None:
                # We generally want the content of any single AIMessage we found from above
                output = ai_message.content

        # In general, output is a string. but output from Anthropic can either be
        # a single string or a list of content blocks.
        # If it is a list, "text" is a key of a dictionary which is the first element of
        # the list. For more details: https://python.langchain.com/docs/integrations/chat/anthropic/#content-blocks
        if isinstance(output, list):
            output = output[0].get("text", "")

        # See if we had some kind of error and format accordingly, if asked for.
        output = self.error_detector.handle_error(output, backtrace)
        return output

    async def get_response(self) -> List[BaseMessage]:
        """
        :return: The list of messages from the instance's thread.
        """
        # Not sure if this is the right thing, as this will be langchain-y stuff.
        return self.chat_history

    async def submit_tool_outputs(self, run: Run, tool_outputs: List[Dict[str, Any]]) -> Run:
        """
        :param run: The Run handling the execution of the agent
        :param tool_outputs: The tool outputs to submit
                The component dictionaries can have the following keys:
                    "origin"        A List of origin dictionaries indicating the origin of the run.
                    "output"        A string representing the output of the tool call
                    "sly_data"      Optional sly_data dictionary that might have returned from an external tool.
                    "tool_call_id"  The string id of the tool_call being executed
        :return: A potentially updated run handle
        """
        if tool_outputs is not None and len(tool_outputs) > 0:
            for tool_output in tool_outputs:
                tool_message: BaseMessage = self.parse_tool_output(tool_output)
                if tool_message is not None:
                    # Chat history is updated in write_message()
                    await self.journal.write_message(tool_message)

        # Create a run to return
        run = LangChainRun(self.run_id_base, self.chat_history)

        return run

    def parse_tool_output(self, tool_output: Dict[str, Any]) -> BaseMessage:
        """
        Parse a single tool_output dictionary for its results
        :return: A message representing the output from the tool.
        """

        # Get a Message for each output and add to the chat history.
        # Assuming dictionary
        tool_chat_list_string = tool_output.get("output", None)
        if tool_chat_list_string is None:
            # Dunno what to do with None tool output
            return None
        if isinstance(tool_chat_list_string, tuple):
            # Sometimes output comes back as a tuple.
            # The output we want is the first element of the tuple.
            tool_chat_list_string = tool_chat_list_string[0]

        tool_message: BaseMessage = None
        if isinstance(tool_chat_list_string, str):
            # Sometimes output comes back as a list.
            # The output we want is the first element of the list.
            tool_message = self.parse_tool_chat_list_string(tool_chat_list_string, tool_output.get("origin"))

        elif isinstance(tool_chat_list_string, BaseMessage):
            tool_message = AgentToolResultMessage(content=tool_chat_list_string.content,
                                                  tool_result_origin=tool_output.get("origin"))

        elif isinstance(tool_chat_list_string, list) and isinstance(tool_chat_list_string[-1], BaseMessage):
            # Always take the last element of the list as the answer to the tool output
            last_message: BaseMessage = tool_chat_list_string[-1]
            tool_message = AgentToolResultMessage(content=last_message.content,
                                                  tool_result_origin=tool_output.get("origin"))
        else:
            self.logger.warning("Dunno what to do with %s tool output %s",
                                str(tool_chat_list_string.__class__.__name__),
                                str(tool_chat_list_string))
            return None

        # Integrate any sly data
        tool_sly_data: Dict[str, Any] = tool_output.get("sly_data")
        if tool_sly_data and tool_sly_data != self.tool_caller.sly_data:
            # We have sly data from the tool output that is not the same as our own
            # and it has data in it.  Integrate that.
            # It's possible we might need to run a SlyDataRedactor against from_download.sly_data on this.
            self.tool_caller.sly_data.update(tool_sly_data)

        return tool_message

    def parse_tool_chat_list_string(self, tool_chat_list_string: str, origin: str) -> BaseMessage:
        """
        Parse a tool output string into a list of messages
        :param tool_chat_list_string: The string to parse
        :param origin: The origin of the tool
        :return: A list of messages representing the output from the tool.
        """

        # Remove bracketing quotes from within the string
        while (tool_chat_list_string[0] == '"' and tool_chat_list_string[-1] == '"') or \
              (tool_chat_list_string[0] == "'" and tool_chat_list_string[-1] == "'"):
            tool_chat_list_string = tool_chat_list_string[1:-1]

        # Remove escaping
        tool_chat_list_string = tool_chat_list_string.replace('\\"', '"')
        # Put back some escaping of double quotes in messages that are not json.
        # We have to do this because gpt-4o seems to not like json braces in its
        # input, but now we have to deal with the consequences in the output.
        # See ArgumentAssigner.get_args_value_as_string().
        tool_chat_list_string = tool_chat_list_string.replace('\\"', '\\\\\"')

        # Decode the JSON in that string now.
        tool_chat_list: List[Dict[str, Any]] = None
        try:
            tool_chat_list = json.loads(tool_chat_list_string)
        except json.decoder.JSONDecodeError as exception:
            self.logger.error("Exception: %s parsing %s", str(exception), str(tool_chat_list_string))
            raise exception

        # The tool_output seems to contain the entire chat history of
        # the call to the tool. For now just take the last one as the answer.
        tool_result_dict = tool_chat_list[-1]

        # Turn that guy into a BaseMessage
        # You might expect that this should be a ToolMessage, but making that
        # kind of conversion at this point runs into problems with OpenAI models
        # that process them.  So, to make things continue to work, report the
        # content as an AI message - as if the bot came up with the answer itself.
        tool_message = AgentToolResultMessage(content=tool_result_dict.get("content"),
                                              tool_result_origin=origin)

        return tool_message

    async def delete_resources(self, parent_run_context: RunContext = None):
        """
        Cleans up the service-side resources associated with this instance
        :param parent_run_context: A parent RunContext perhaps the same instance,
                        but perhaps not.  Default is None
        """

        # Release model related resources:
        if self.llm_resources:
            await self.llm_resources.delete_resources()

        self.tools = []
        self.chat_history = []
        self.agent_chain = None
        self.recent_human_message = None
        self.llm_resources = None
        self.journal = None

    def get_agent_tool_spec(self) -> Dict[str, Any]:
        """
        :return: the dictionary describing the data-driven agent
        """
        if self.tool_caller is None:
            return None

        return self.tool_caller.get_agent_tool_spec()

    def get_invocation_context(self) -> InvocationContext:
        """
        :return: The InvocationContext policy container that pertains to the invocation
                    of the agent.
        """
        return self.invocation_context

    def get_chat_context(self) -> Dict[str, Any]:
        """
        :return: A ChatContext dictionary that contains all the state necessary
                to carry on a previous conversation, possibly from a different server.
                Can be None when a new conversation has been started.
        """
        return self.chat_context

    def get_origin(self) -> List[Dict[str, Any]]:
        """
        :return: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with.
        """
        return self.origin

    def update_invocation_context(self, invocation_context: InvocationContext):
        """
        Update internal state based on the InvocationContext instance passed in.
        :param invocation_context: The context policy container that pertains to the invocation
        """
        self.invocation_context = invocation_context

        base_journal: Journal = self.invocation_context.get_journal()
        self.journal = OriginatingJournal(base_journal, self.origin, self.chat_history)

    def update_from_chat_context(self, chat_context: Dict[str, Any]):
        """
        :param chat_context: A ChatContext dictionary that contains all the state necessary
                to carry on a previous conversation, possibly from a different server.
        """
        self.chat_context = chat_context

        if self.chat_context is None:
            return

        # See if our origin appears in the chat histories.
        # If so, get ours from there.
        empty: List[Any] = []
        chat_histories: List[Dict[str, Any]] = self.chat_context.get("chat_histories", empty)
        our_origin_str: str = Origination.get_full_name_from_origin(self.origin)
        for one_chat_history in chat_histories:

            # See if the origin matches our own
            test_origin: List[Dict[str, Any]] = one_chat_history.get("origin", empty)
            test_origin_str: str = Origination.get_full_name_from_origin(test_origin)
            if test_origin_str != our_origin_str:
                continue

            one_messages: List[Dict[str, Any]] = one_chat_history.get("messages", empty)
            if not one_messages:
                # Empty list - Nothing to convert. Use default empty list.
                break

            converter = BaseMessageDictionaryConverter()
            self.chat_history = []
            for chat_message in one_messages:
                base_message: BaseMessage = converter.from_dict(chat_message)
                if base_message is not None:
                    self.chat_history.append(base_message)

            # Nothing left to search for
            break

    def get_journal(self) -> Journal:
        """
        :return: The Journal associated with the instance
        """
        return self.journal

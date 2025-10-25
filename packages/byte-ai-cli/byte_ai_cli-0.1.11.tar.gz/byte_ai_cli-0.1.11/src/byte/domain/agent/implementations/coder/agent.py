from typing import Type

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

from byte.domain.agent.implementations.base import Agent
from byte.domain.agent.implementations.coder.prompts import coder_prompt
from byte.domain.agent.nodes.assistant_node import AssistantNode
from byte.domain.agent.nodes.end_node import EndNode
from byte.domain.agent.nodes.lint_node import LintNode
from byte.domain.agent.nodes.parse_blocks_node import ParseBlocksNode
from byte.domain.agent.nodes.start_node import StartNode
from byte.domain.agent.schemas import AssistantContextSchema
from byte.domain.agent.state import CoderState
from byte.domain.edit_format.service.edit_format_service import EditFormatService
from byte.domain.llm.service.llm_service import LLMService


class CoderAgent(Agent):
	"""Domain service for the coder agent specialized in software development.

	Pure domain service that handles coding logic without UI concerns.
	Integrates with file context, memory, and development tools through
	the actor system for clean separation of concerns.
	"""

	edit_format: EditFormatService

	async def boot(self):
		self.edit_format = await self.make(EditFormatService)

	def get_state_class(self) -> Type[TypedDict]:  # pyright: ignore[reportInvalidTypeForm]
		"""Return coder-specific state class."""
		return CoderState

	async def build(self) -> CompiledStateGraph:
		"""Build and compile the coder agent graph with memory and tools."""

		# Create the state graph
		graph = StateGraph(self.get_state_class())

		# Add nodes
		graph.add_node("start_node", await self.make(StartNode, edit_format=self.edit_format))
		graph.add_node("assistant_node", await self.make(AssistantNode, goto="parse_blocks_node"))
		graph.add_node("parse_blocks_node", await self.make(ParseBlocksNode, edit_format=self.edit_format))
		graph.add_node("lint_node", await self.make(LintNode))
		graph.add_node("end_node", await self.make(EndNode))

		# Define edges
		graph.add_edge(START, "start_node")
		graph.add_edge("start_node", "assistant_node")
		graph.add_edge("assistant_node", "parse_blocks_node")

		graph.add_edge("lint_node", "end_node")
		graph.add_edge("end_node", END)

		checkpointer = await self.get_checkpointer()
		return graph.compile(checkpointer=checkpointer, debug=False)

	async def get_assistant_runnable(self) -> AssistantContextSchema:
		llm_service = await self.make(LLMService)
		main: BaseChatModel = llm_service.get_main_model()
		weak: BaseChatModel = llm_service.get_weak_model()

		# Create the assistant runnable with out any tools. So regardless it wont make a tool call even thou we have a tool node.
		return AssistantContextSchema(
			mode="main",
			prompt=coder_prompt,
			main=main,
			weak=weak,
			agent=self.__class__.__name__,
		)

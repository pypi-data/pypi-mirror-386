from textwrap import dedent

from langchain_core.prompts.chat import ChatPromptTemplate

cleaner_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			dedent(
				"""
				<role>
				You are an expert content distiller who extracts signal from noise.
				Transform verbose content into its essential form while preserving all critical information.
				</role>

				<rules>
				- Remove: marketing fluff, legal boilerplate, repetitive examples, excessive formatting
				- Preserve: technical details, version numbers, API signatures, configuration values, caveats
				- Restructure: group related concepts, use clear hierarchy, prefer lists over prose
				- Maintain: original terminology, code snippets, important warnings or notes
				- Prioritize: actionable information over background context
				</rules>

				<output_requirements>
				Return only the distilled content without meta-commentary.
				Use markdown structure (headers, lists, code blocks) when it improves clarity.
				Keep the output 30-70% of the original length while retaining 100% of the value.
				</output_requirements>
				"""
			),
		),
		(
			"user",
			dedent(
				"""[Skip to content](#getting-help)\n\n[![logo](../../assets/logo-letter.svg)](../.. "uv")\n\n\n\n\nuv\n\nGetting help\n\n\n\n\n\n\n\nInitializing search\n\n[uv](https://github.com/astral-sh/uv "Go to repository")\n\n[![logo](../../assets/logo-letter.svg)](../.. "uv")\nuv\n\n[uv](https://github.com/astral-sh/uv "Go to repository")\n\n* [Introduction](../..)\n* [Getting started](../)\n\n  Getting started\n  + [Installation](../installation/)\n  + [First steps](../first-steps/)\n  + [Features](../features/)\n  + Getting help\n\n	[Getting help](./)\n\n\n\n	Table of contents\n	- [Help menus](#help-menus)\n	- [Displaying verbose output](#displaying-verbose-output)\n	- [Viewing the version](#viewing-the-version)\n	- [Troubleshooting issues](#troubleshooting-issues)\n	- [Open an issue on GitHub](#open-an-issue-on-github)\n	- [Chat on Discord](#chat-on-discord)\n* [Guides](../../guides/)\n\n  Guides\n  + [Installing Python](../../guides/install-python/)\n  + [Running scripts](../../guides/scripts/)\n  + [Using tools](../../guides/tools/)\n  + [Working on projects](../../guides/projects/)\n  + [Publishing packages](../../guides/package/)\n  + [Migration](../../guides/migration/)\n\n	Migration\n	- [From pip to a uv project](../../guides/migration/pip-to-project/)\n  + [Integrations](../../guides/integration/)\n\n	Integrations\n	- [Docker](../../guides/integration/docker/)\n	- [Jupyter](../../guides/integration/jupyter/)\n	- [marimo](../../guides/integration/marimo/)\n	- [GitHub Actions](../../guides/integration/github/)\n	- [GitLab CI/CD](../../guides/integration/gitlab/)\n	- [Pre-commit](../../guides/integration/pre-commit/)\n	- [PyTorch](../../guides/integration/pytorch/)\n	- [FastAPI](../../guides/integration/fastapi/)\n	- [Alternative indexes](../../guides/integration/alternative-indexes/)\n	- [Dependency bots](../../guides/integration/dependency-bots/)\n	- [AWS Lambda](../../guides/integration/aws-lambda/)\n	- [Coiled](../../guides/integration/coiled/)\n* [Concepts](../../concepts/)\n\n  Concepts\n  + [Projects](../../concepts/projects/)\n\n	Projects\n	- [Structure and files](../../concepts/projects/layout/)\n	- [Creating projects](../../concepts/projects/init/)\n	- [Managing dependencies](../../concepts/projects/dependencies/)\n	- [Running commands](../../concepts/projects/run/)\n	- [Locking and syncing](../../concepts/projects/sync/)\n	- [Configuring projects](../../concepts/projects/config/)\n	- [Building distributions](../../concepts/projects/build/)\n	- [Using workspaces](../../concepts/projects/workspaces/)\n  + [Tools](../../concepts/tools/)\n  + [Python versions](../../concepts/python-versions/)\n  + [Configuration files](../../concepts/configuration-files/)\n  + [Package indexes](../../concepts/indexes/)\n  + [Resolution](../../concepts/resolution/)\n  + [Build backend](../../concepts/build-backend/)\n  + [Authentication](../../concepts/authentication/)\n\n	Authentication\n	- [The auth CLI](../../concepts/authentication/cli/)\n	- [HTTP credentials](../../concepts/authentication/http/)\n	- [Git credentials](../../concepts/authentication/git/)\n	- [TLS certificates](../../concepts/authentication/certificates/)\n	- [Third-party services](../../concepts/authentication/third-party/)\n  + [Caching](../../concepts/cache/)\n  + [Preview features](../../concepts/preview/)\n  + [The pip interface](../../pip/)\n\n	The pip interface\n	- [Using environments](../../pip/environments/)\n	- [Managing packages](../../pip/packages/)\n	- [Inspecting environments](../../pip/inspection/)\n	- [Declaring dependencies](../../pip/dependencies/)\n	- [Locking environments](../../pip/compile/)\n	- [Compatibility with pip](../../pip/compatibility/)\n* [Reference](../../reference/)\n\n  Reference\n  + [Commands](../../reference/cli/)\n  + [Settings](../../reference/settings/)\n  + [Environment variables](../../reference/environment/)\n  + [Installer options](../../reference/installer/)\n  + [Troubleshooting](../../reference/troubleshooting/)\n\n	Troubleshooting\n	- [Build failures](../../reference/troubleshooting/build-failures/)\n	- [Reproducible examples](../../reference/troubleshooting/reproducible-examples/)\n  + [Internals](../../reference/internals/)\n\n	Internals\n	- [Resolver](../../reference/internals/resolver/)\n  + [Benchmarks](../../reference/benchmarks/)\n  + [Policies](../../reference/policies/)\n\n	Policies\n	- [Versioning](../../reference/policies/versioning/)\n	- [Platform support](../../reference/policies/platforms/)\n	- [License](../../reference/policies/license/)\n\nTable of contents\n\n* [Help menus](#help-menus)\n* [Displaying verbose output](#displaying-verbose-output)\n* [Viewing the version](#viewing-the-version)\n* [Troubleshooting issues](#troubleshooting-issues)\n* [Open an issue on GitHub](#open-an-issue-on-github)\n* [Chat on Discord](#chat-on-discord)\n\n1. [Introduction](../..)\n2. [Getting started](../)\n\n[Getting help](#getting-help)\n=============================\n\n[Help menus](#help-menus)\n-------------------------\n\nThe `--help` flag can be used to view the help menu for a command, e.g., for `uv`:\n\n```\n$ uv --help\n```\n\nTo view the help menu for a specific command, e.g., for `uv init`:\n\n```\n$ uv init --help\n```\n\nWhen using the `--help` flag, uv displays a condensed help menu. To view a longer help menu for a\ncommand, use `uv help`:\n\n```\n$ uv help\n```\n\nTo view the long help menu for a specific command, e.g., for `uv init`:\n\n```\n$ uv help init\n```\n\nWhen using the long help menu, uv will attempt to use `less` or `more` to "page" the output so it is\nnot all displayed at once. To exit the pager, press `q`.\n\n[Displaying verbose output](#displaying-verbose-output)\n-------------------------------------------------------\n\nThe `-v` flag can be used to display verbose output for a command, e.g., for `uv sync`:\n\n```\n$ uv sync -v\n```\n\nThe `-v` flag can be repeated to increase verbosity, e.g.:\n\n```\n$ uv sync -vv\n```\n\nOften, the verbose output will include additional information about why uv is behaving in a certain\nway.\n\n[Viewing the version](#viewing-the-version)\n-------------------------------------------\n\nWhen seeking help, it\'s important to determine the version of uv that you\'re using — sometimes the\nproblem is already solved in a newer version.\n\nTo check the installed version:\n\n```\n$ uv self version\n```\n\nThe following are also valid:\n\n```\n$ uv --version	  # Same output as `uv self version`\n$ uv -V			 # Will not include the build commit and date\n```\n\nNote\n\nBefore uv 0.7.0, `uv version` was used instead of `uv self version`.\n\n[Troubleshooting issues](#troubleshooting-issues)\n-------------------------------------------------\n\nThe reference documentation contains a\n[troubleshooting guide](../../reference/troubleshooting/) for common issues.\n\n[Open an issue on GitHub](#open-an-issue-on-github)\n---------------------------------------------------\n\nThe [issue tracker](https://github.com/astral-sh/uv/issues) on GitHub is a good place to report bugs\nand request features. Make sure to search for similar issues first, as it is common for someone else\nto encounter the same problem.\n\n[Chat on Discord](#chat-on-discord)\n-----------------------------------\n\nAstral has a [Discord server](https://discord.com/invite/astral-sh), which is a great place to ask\nquestions, learn more about uv, and engage with other community members.\n\nSeptember 17, 2025\n\nBack to top\n\n\n[Previous\n\nFeatures](../features/)\n[Next\n\nIndex](../../guides/)\n\nMade with\n[Material for MkDocs Insiders](https://squidfunk.github.io/mkdocs-material/)\n\n\n\n![](https://cdn.usefathom.com/?h=https%3A%2F%2Fdocs.astral.sh&p=%2Fuv%2Fgetting-started%2Fhelp%2F&r=&sid=ESKBRHGN&qs=%7B%7D&cid=81931367)'"""
			),
		),
		(
			"assistant",
			dedent(
				"""
				# Getting Help with uv

				## Help Commands

				**Short help**: `uv --help` or `uv init --help`
				**Long help**: `uv help` or `uv help init` (uses pager, press `q` to exit)

				## Verbose Output

				Use `-v` flag for verbose output: `uv sync -v`
				Use `-vv` for more verbosity: `uv sync -vv`

				## Version Check

				```bash
				$ uv self version	# Full version with build info
				$ uv --version	   # Same as above
				$ uv -V			  # Short version only
				```

				Note: Before uv 0.7.0, use `uv version` instead of `uv self version`.

				## Getting Support

				- **Troubleshooting guide**: Check reference docs at `/reference/troubleshooting/`
				- **GitHub issues**: Search existing issues first at https://github.com/astral-sh/uv/issues
				- **Discord**: Join Astral's Discord server at https://discord.com/invite/astral-sh
				"""
			),
		),
		(
			"assistant",
			dedent(
				"""
				# LangChain MCP Adapters

				Lightweight wrapper making Anthropic Model Context Protocol (MCP) tools compatible with LangChain and LangGraph.

				## Installation

				```bash
				pip install langchain-mcp-adapters
				```

				## Quick Start

				**Create MCP Server** (`math_server.py`):
				```python
				from mcp.server.fastmcp import FastMCP

				mcp = FastMCP("Math")

				@mcp.tool()
				def add(a: int, b: int) -> int:
					return a + b

				if __name__ == "__main__":
					mcp.run(transport="stdio")
				```

				**Use in LangGraph Agent**:
				```python
				from mcp import ClientSession, StdioServerParameters
				from mcp.client.stdio import stdio_client
				from langchain_mcp_adapters.tools import load_mcp_tools
				from langgraph.prebuilt import create_react_agent

				server_params = StdioServerParameters(
					command="python",
					args=["/path/to/math_server.py"],
				)

				async with stdio_client(server_params) as (read, write):
					async with ClientSession(read, write) as session:
						await session.initialize()
						tools = await load_mcp_tools(session)
						agent = create_react_agent("openai:gpt-4.1", tools)
						response = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"})
				```

				## Multiple Servers

				**Connect to multiple MCP servers**:
				```python
				from langchain_mcp_adapters.client import MultiServerMCPClient

				client = MultiServerMCPClient({
					"math": {
						"command": "python",
						"args": ["/path/to/math_server.py"],
						"transport": "stdio",
					},
					"weather": {
						"url": "http://localhost:8000/mcp",
						"transport": "streamable_http",
					}
				})
				tools = await client.get_tools()
				agent = create_react_agent("openai:gpt-4.1", tools)
				```

				## Transports

				**Supported transports**: `stdio`, `streamable_http`, `sse`

				**Streamable HTTP example**:
				```python
				from mcp import ClientSession
				from mcp.client.streamable_http import streamablehttp_client

				async with streamablehttp_client("http://localhost:3000/mcp") as (read, write, _):
					async with ClientSession(read, write) as session:
						await session.initialize()
						tools = await load_mcp_tools(session)
				```

				## Headers (SSE/Streamable HTTP only)

				Pass authentication/custom headers:
				```python
				client = MultiServerMCPClient({
					"weather": {
						"transport": "streamable_http",
						"url": "http://localhost:8000/mcp",
						"headers": {
							"Authorization": "Bearer YOUR_TOKEN",
							"X-Custom-Header": "value"
						},
					}
				})
				```

				## LangGraph StateGraph

				```python
				from langgraph.graph import StateGraph, MessagesState, START
				from langgraph.prebuilt import ToolNode, tools_condition

				tools = await client.get_tools()
				model = init_chat_model("openai:gpt-4.1").bind_tools(tools)

				builder = StateGraph(MessagesState)
				builder.add_node("call_model", lambda state: {"messages": model.invoke(state["messages"])})
				builder.add_node("tools", ToolNode(tools))
				builder.add_edge(START, "call_model")
				builder.add_conditional_edges("call_model", tools_condition)
				builder.add_edge("tools", "call_model")
				graph = builder.compile()
				```

				## LangGraph API Server

				In `langgraph.json`:
				```json
				{
					"graphs": {
						"agent": "./graph.py:make_graph"
					}
				}
				```

				In `graph.py`:
				```python
				async def make_graph():
					client = MultiServerMCPClient({...})
					tools = await client.get_tools()
					return create_react_agent("openai:gpt-4.1", tools)
				```

				## Convert LangChain → FastMCP

				```python
				from langchain_core.tools import tool
				from langchain_mcp_adapters.tools import to_fastmcp
				from mcp.server.fastmcp import FastMCP

				@tool
				def add(a: int, b: int) -> int:
					return a + b

				mcp = FastMCP("Math", tools=[to_fastmcp(add)])
				```

				**License**: MIT
				**Repository**: https://github.com/langchain-ai/langchain-mcp-adapters
				**JS/TS version**: Available in langchainjs
				"""
			),
		),
		("placeholder", "{messages}"),
	]
)

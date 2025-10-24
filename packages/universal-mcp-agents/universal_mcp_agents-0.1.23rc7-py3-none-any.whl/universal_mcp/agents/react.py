from langchain.agents import create_agent
from langgraph.checkpoint.base import BaseCheckpointSaver
from loguru import logger
from rich import print
from universal_mcp.agentr.registry import AgentrRegistry
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolConfig, ToolFormat

from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.llm import load_chat_model
from universal_mcp.agents.utils import messages_to_list

DEVELOPER_PROMPT = """You are {name}.

You have access to various tools that can help you answer questions and complete tasks. When you need to use a tool:

1. Think about what information you need
2. Call the appropriate tool with the right parameters
3. Use the tool results to provide a comprehensive answer

Always explain your reasoning and be thorough in your responses. If you need to use multiple tools to answer a question completely, do so.

Adhere to the following instructions strictly:
{instructions}
"""


class ReactAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        memory: BaseCheckpointSaver | None = None,
        tools: ToolConfig | None = None,
        registry: ToolRegistry | None = None,
        max_iterations: int = 10,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instructions=instructions,
            model=model,
            memory=memory,
            **kwargs,
        )
        self.llm = load_chat_model(model)
        self.tools = tools or {}
        if "ui" not in self.tools:
            self.tools["ui"] = [
                "create_bar_chart",
                "create_line_chart",
                "create_pie_chart",
                "create_table",
                "http_get",
                "http_post",
                "http_put",
                "http_delete",
                "http_patch",
                "read_file",
                "web_search",
                "web_content",
            ]
        self.max_iterations = max_iterations
        self.registry = registry

    async def _build_graph(self):
        tools = []
        if self.tools:
            if not self.registry:
                raise ValueError("Tools are configured but no registry is provided")
            tools = await self.registry.export_tools(self.tools, ToolFormat.LANGCHAIN)
            logger.debug(tools)
        else:
            tools = []

        logger.debug(f"Initialized ReactAgent: name={self.name}, model={self.model}")
        return create_agent(
            self.llm,
            tools,
            system_prompt=self._build_system_message(),
            checkpointer=self.memory,
        )

    def _build_system_message(self):
        return DEVELOPER_PROMPT.format(name=self.name, instructions=self.instructions)


async def main():
    agent = ReactAgent(
        name="Universal React Agent",
        instructions="Be very concise in your answers.",
        model="azure/gpt-4o",
        tools={"google-mail": ["send_email"]},
        registry=AgentrRegistry(),
    )
    result = await agent.invoke("Send an email with the subject 'testing react agent' to manoj@agentr.dev")

    print(messages_to_list(result["messages"]))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

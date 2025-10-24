import asyncio
import json
import textwrap

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .constants import (
    DEFAULT_MAX_TOKENS,
    MAX_RETRY_ATTEMPTS,
    TOPIC_GRAPH_DEFAULT_MODEL,
    TOPIC_GRAPH_DEFAULT_TEMPERATURE,
    TOPIC_GRAPH_SUMMARY,
)
from .llm import LLMClient
from .metrics import trace
from .prompts import GRAPH_EXPANSION_PROMPT
from .schemas import GraphSubtopics
from .topic_model import TopicModel


def validate_graph_response(response_text: str) -> dict[str, Any] | None:
    """Clean and validate the JSON response for the graph from the LLM."""
    try:
        return json.loads(response_text)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Failed to parse the input string as JSON.\n{e}")
        return None


class GraphConfig(BaseModel):
    """Configuration for constructing a topic graph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    topic_prompt: str = Field(
        ..., min_length=1, description="The initial prompt to start the topic graph"
    )
    topic_system_prompt: str = Field(
        default="", description="System prompt for topic exploration and generation"
    )
    provider: str = Field(
        default="ollama",
        min_length=1,
        description="LLM provider (openai, anthropic, gemini, ollama)",
    )
    model_name: str = Field(
        default=TOPIC_GRAPH_DEFAULT_MODEL,
        min_length=1,
        description="The name of the model to be used",
    )
    temperature: float = Field(
        default=TOPIC_GRAPH_DEFAULT_TEMPERATURE,
        ge=0.0,
        le=2.0,
        description="Temperature for model generation",
    )
    degree: int = Field(default=3, ge=1, le=10, description="The branching factor of the graph")
    depth: int = Field(default=2, ge=1, le=5, description="The depth of the graph")
    base_url: str | None = Field(
        default=None,
        description="Base URL for API endpoint (e.g., custom OpenAI-compatible servers)",
    )


# Pydantic Models for strict data representation


class NodeModel(BaseModel):
    """Pydantic model for a node in the graph."""

    id: int
    topic: str
    children: list[int] = Field(default_factory=list)
    parents: list[int] = Field(default_factory=list)


class GraphModel(BaseModel):
    """Pydantic model for the entire topic graph."""

    nodes: dict[int, NodeModel]
    root_id: int


# Core graph implementation


class Node:
    """Represents a node in the Graph for runtime manipulation."""

    def __init__(self, topic: str, node_id: int):
        self.topic: str = topic
        self.id: int = node_id
        self.children: list[Node] = []
        self.parents: list[Node] = []

    def to_pydantic(self) -> NodeModel:
        """Converts the runtime Node to its Pydantic model representation."""
        return NodeModel(
            id=self.id,
            topic=self.topic,
            children=[child.id for child in self.children],
            parents=[parent.id for parent in self.parents],
        )


class Graph(TopicModel):
    """Represents the topic graph and manages its structure."""

    def __init__(self, **kwargs):
        try:
            self.config = GraphConfig.model_validate(kwargs)
        except Exception as e:
            raise ValueError(f"Invalid graph configuration: {str(e)}") from e  # noqa: TRY003

        # Initialize from config
        self.topic_prompt = self.config.topic_prompt
        self.model_system_prompt = self.config.topic_system_prompt
        self.provider = self.config.provider
        self.model_name = self.config.model_name
        self.temperature = self.config.temperature
        self.degree = self.config.degree
        self.depth = self.config.depth

        # Initialize LLM client
        llm_kwargs = {}
        if self.config.base_url:
            llm_kwargs["base_url"] = self.config.base_url

        self.llm_client = LLMClient(
            provider=self.provider,
            model_name=self.model_name,
            **llm_kwargs,
        )

        trace(
            "graph_created",
            {
                "provider": self.provider,
                "model_name": self.model_name,
                "degree": self.degree,
                "depth": self.depth,
            },
        )

        self.root: Node = Node(self.config.topic_prompt, 0)
        self.nodes: dict[int, Node] = {0: self.root}
        self._next_node_id: int = 1
        self.failed_generations: list[dict[str, Any]] = []

    def _wrap_text(self, text: str, width: int = 30) -> str:
        """Wrap text to a specified width."""
        return "\n".join(textwrap.wrap(text, width=width))

    def add_node(self, topic: str) -> Node:
        """Adds a new node to the graph."""
        node = Node(topic, self._next_node_id)
        self.nodes[node.id] = node
        self._next_node_id += 1
        return node

    def add_edge(self, parent_id: int, child_id: int) -> None:
        """Adds a directed edge from a parent to a child node, avoiding duplicates."""
        parent_node = self.nodes.get(parent_id)
        child_node = self.nodes.get(child_id)
        if parent_node and child_node:
            if child_node not in parent_node.children:
                parent_node.children.append(child_node)
            if parent_node not in child_node.parents:
                child_node.parents.append(parent_node)

    def to_pydantic(self) -> GraphModel:
        """Converts the runtime graph to its Pydantic model representation."""
        return GraphModel(
            nodes={node_id: node.to_pydantic() for node_id, node in self.nodes.items()},
            root_id=self.root.id,
        )

    def to_json(self) -> str:
        """Returns a JSON representation of the graph."""
        pydantic_model = self.to_pydantic()
        return pydantic_model.model_dump_json(indent=2)

    def save(self, save_path: str) -> None:
        """Save the topic graph to a file."""
        with open(save_path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def from_json(cls, json_path: str, params: dict) -> "Graph":
        """Load a topic graph from a JSON file."""
        with open(json_path) as f:
            data = json.load(f)

        graph_model = GraphModel(**data)
        graph = cls(**params)
        graph.nodes = {}

        # Create nodes
        for node_model in graph_model.nodes.values():
            node = Node(node_model.topic, node_model.id)
            graph.nodes[node.id] = node
            if node.id == graph_model.root_id:
                graph.root = node

        # Create edges
        for node_model in graph_model.nodes.values():
            for child_id in node_model.children:
                graph.add_edge(node_model.id, child_id)

        graph._next_node_id = max(graph.nodes.keys()) + 1
        return graph

    def visualize(self, save_path: str) -> None:
        """Visualize the graph and save it to a file."""
        try:
            from mermaid import Mermaid  # noqa: PLC0415
        except ImportError:
            print("Please install mermaid-py to visualize the graph: uv add mermaid-py")
            return

        graph_definition = "graph TD\n"
        for node in self.nodes.values():
            graph_definition += f'    {node.id}["{self._wrap_text(node.topic)}"]\n'

        for node in self.nodes.values():
            for child in node.children:
                graph_definition += f"    {node.id} --> {child.id}\n"

        mermaid = Mermaid(graph_definition)
        mermaid.to_svg(f"{save_path}.svg")

    async def build_async(self):
        """Builds the graph by iteratively calling the LLM to get subtopics and connections.

        Yields:
            dict: Progress events with event type and associated data
        """

        def _raise_if_build_failed():
            """Check if build failed completely and raise appropriate error."""
            if len(self.nodes) == 1 and self.failed_generations:
                # Surface the actual first error instead of a generic message
                first_error = self.failed_generations[0]["last_error"]
                raise RuntimeError(first_error)

        try:
            for depth in range(self.depth):
                leaf_nodes = [node for node in self.nodes.values() if not node.children]
                yield {"event": "depth_start", "depth": depth + 1, "leaf_count": len(leaf_nodes)}

                if leaf_nodes:
                    tasks = [
                        self.get_subtopics_and_connections(node, self.degree) for node in leaf_nodes
                    ]
                    results = await asyncio.gather(*tasks)

                    for node, (subtopics_added, connections_added) in zip(
                        leaf_nodes, results, strict=True
                    ):
                        yield {
                            "event": "node_expanded",
                            "node_topic": node.topic,
                            "subtopics_added": subtopics_added,
                            "connections_added": connections_added,
                        }

                yield {"event": "depth_complete", "depth": depth + 1}

            # Check if build was completely unsuccessful (only root node exists)
            _raise_if_build_failed()

            trace(
                "graph_built",
                {
                    "provider": self.provider,
                    "model_name": self.model_name,
                    "nodes_count": len(self.nodes),
                    "failed_generations": len(self.failed_generations),
                    "success": len(self.nodes) > 1,
                },
            )

            yield {
                "event": "build_complete",
                "nodes_count": len(self.nodes),
                "failed_generations": len(self.failed_generations),
            }

        except Exception as e:
            yield {"event": "error", "error": str(e)}
            raise

    async def get_subtopics_and_connections(  # noqa: PLR0912
        self, parent_node: Node, num_subtopics: int
    ) -> tuple[int, int]:
        """Generate subtopics and connections for a given node. Returns (subtopics_added, connections_added)."""
        subtopics_added = 0
        connections_added = 0
        graph_summary = (
            self.to_json()
            if len(self.nodes) <= TOPIC_GRAPH_SUMMARY
            else "Graph too large to display"
        )

        graph_prompt = GRAPH_EXPANSION_PROMPT.replace("{{current_graph_summary}}", graph_summary)
        graph_prompt = graph_prompt.replace("{{current_topic}}", parent_node.topic)
        graph_prompt = graph_prompt.replace("{{num_subtopics}}", str(num_subtopics))

        try:
            response = await self.llm_client.generate_async(
                prompt=graph_prompt,
                schema=GraphSubtopics,
                max_retries=MAX_RETRY_ATTEMPTS,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=self.temperature,
            )

            # Process structured response
            for subtopic_data in response.subtopics:
                new_node = self.add_node(subtopic_data.topic)
                self.add_edge(parent_node.id, new_node.id)
                subtopics_added += 1
                for connection_id in subtopic_data.connections:
                    if connection_id in self.nodes:
                        self.add_edge(connection_id, new_node.id)
                        connections_added += 1

            return subtopics_added, connections_added

        except Exception as e:
            last_error = str(e)
            # Check if it's an API key related error
            error_str = str(e).lower()
            if any(
                keyword in error_str
                for keyword in ["api_key", "api key", "authentication", "unauthorized"]
            ):
                error_msg = f"Authentication failed for provider '{self.provider}'. Please set the required API key environment variable."
                raise RuntimeError(error_msg) from e

            self.failed_generations.append(
                {"node_id": parent_node.id, "attempts": 1, "last_error": last_error}
            )
            return 0, 0  # No subtopics or connections added on failure
        else:
            return subtopics_added, connections_added

    def get_all_paths(self) -> list[list[str]]:
        """Returns all paths from the root to leaf nodes."""
        paths = []
        self._dfs_paths(self.root, [self.root.topic], paths)
        return paths

    def _dfs_paths(self, node: Node, current_path: list[str], paths: list[list[str]]) -> None:
        """Helper function for DFS traversal to find all paths."""
        if not node.children:
            paths.append(current_path)
            return

        for child in node.children:
            self._dfs_paths(child, current_path + [child.topic], paths)

    def _has_cycle_util(self, node: Node, visited: set[int], recursion_stack: set[int]) -> bool:
        """Utility function for cycle detection."""
        visited.add(node.id)
        recursion_stack.add(node.id)

        for child in node.children:
            if child.id not in visited:
                if self._has_cycle_util(child, visited, recursion_stack):
                    return True
            elif child.id in recursion_stack:
                return True

        recursion_stack.remove(node.id)
        return False

    def has_cycle(self) -> bool:
        """Checks if the graph contains a cycle."""
        visited: set[int] = set()
        recursion_stack: set[int] = set()
        for node_id in self.nodes:
            if node_id not in visited and self._has_cycle_util(
                self.nodes[node_id], visited, recursion_stack
            ):
                return True
        return False

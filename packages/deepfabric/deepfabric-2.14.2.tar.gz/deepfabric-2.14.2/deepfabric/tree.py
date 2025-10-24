import asyncio
import json
import time
import warnings

from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field

from .constants import (
    DEFAULT_MAX_TOKENS,
    MAX_RETRY_ATTEMPTS,
    TOPIC_TREE_DEFAULT_DEGREE,
    TOPIC_TREE_DEFAULT_DEPTH,
    TOPIC_TREE_DEFAULT_MODEL,
    TOPIC_TREE_DEFAULT_TEMPERATURE,
)
from .exceptions import TreeError
from .llm import LLMClient
from .metrics import trace
from .prompts import TreePromptBuilder
from .schemas import TopicList
from .topic_model import TopicModel

warnings.filterwarnings("ignore", message=".*Pydantic serializer warnings:.*")


UPPER_DEGREE = 50
UPPER_DEPTH = 10


class ValidationResult(TypedDict, total=False):
    valid: bool
    total_tree_paths: int
    total_requested_paths: int
    recommended_batch_size: int


class TreeConfig(BaseModel):
    """Configuration for constructing a topic tree."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    topic_prompt: str = Field(
        ..., min_length=1, description="The initial prompt to start the topic tree"
    )
    topic_system_prompt: str = Field(
        default="", description="System prompt for topic exploration and generation"
    )
    degree: int = Field(
        default=TOPIC_TREE_DEFAULT_DEGREE,
        ge=1,
        le=UPPER_DEGREE,
        description="The branching factor of the tree",
    )
    depth: int = Field(
        default=TOPIC_TREE_DEFAULT_DEPTH,
        ge=1,
        le=UPPER_DEPTH,
        description="The depth of the tree",
    )
    provider: str = Field(
        default="ollama",
        min_length=1,
        description="LLM provider (openai, anthropic, gemini, ollama)",
    )
    model_name: str = Field(
        default=TOPIC_TREE_DEFAULT_MODEL,
        min_length=1,
        description="The name of the model to be used",
    )
    temperature: float = Field(
        default=TOPIC_TREE_DEFAULT_TEMPERATURE,
        ge=0.0,
        le=2.0,
        description="Temperature for model generation",
    )
    base_url: str | None = Field(
        default=None,
        description="Base URL for API endpoint (e.g., custom OpenAI-compatible servers)",
    )


class TreeValidator:
    """TreeValidator validates and calculates unique paths in a tree structure."""

    def __init__(self, degree: int, depth: int):
        self.degree = degree
        self.depth = depth

    def calculate_paths(self) -> int:
        """Calculate total number of paths in the tree."""
        return self.degree**self.depth

    def validate_configuration(self, num_steps: int, batch_size: int) -> ValidationResult:
        """
        Validates the tree configuration and provides recommendations if invalid.

        Args:
            num_steps: Number of steps requested.
            batch_size: Batch size per step.

        Returns:
            A ValidationResult dict containing validity, totals, and recommendations.
        """
        total_requested_paths = num_steps * batch_size
        total_tree_paths = self.calculate_paths()

        print(f"Total tree paths available: {total_tree_paths}")
        print(f"Total requested paths: {total_requested_paths}")

        result: ValidationResult = {
            "valid": total_requested_paths <= total_tree_paths,
            "total_tree_paths": total_tree_paths,
            "total_requested_paths": total_requested_paths,
        }

        if not result["valid"]:
            print(
                "Requested paths (%d) exceed available tree paths (%d).",
                total_requested_paths,
                total_tree_paths,
            )
            result["recommended_batch_size"] = min(batch_size, total_tree_paths)

        return result


class Tree(TopicModel):
    """A class to represent and build a hierarchical topic tree."""

    def __init__(self, **kwargs):
        """Initialize the Tree with the given parameters."""
        try:
            self.config = TreeConfig.model_validate(kwargs)
        except Exception as e:
            raise TreeError(f"Invalid tree configuration: {str(e)}") from e  # noqa: TRY003

        # Initialize from config
        self.topic_prompt = self.config.topic_prompt
        self.model_system_prompt = self.config.topic_system_prompt
        self.degree = self.config.degree
        self.depth = self.config.depth
        self.temperature = self.config.temperature
        self.provider = self.config.provider
        self.model_name = self.config.model_name

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
            "tree_created",
            {
                "provider": self.provider,
                "model_name": self.model_name,
                "degree": self.degree,
                "depth": self.depth,
            },
        )

        # Derived attributes
        self.system_prompt = self.config.topic_system_prompt
        self.tree_paths: list[list[str]] = []
        self.failed_generations: list[dict[str, Any]] = []

    async def build_async(self, model_name: str | None = None):
        """Build the complete topic tree.

        Args:
            model_name: Optional model name to override the configured model

        Yields:
            dict: Progress events with event type and associated data
        """
        if model_name:
            self.model_name = model_name

        yield {
            "event": "build_start",
            "model_name": self.model_name,
            "depth": self.config.depth,
            "degree": self.config.degree,
        }

        def _raise_if_build_failed():
            """Check if build failed completely and raise appropriate error."""
            if len(self.tree_paths) == 0 and self.failed_generations:
                error_msg = f"Tree build failed completely: all {len(self.failed_generations)} generation attempts failed. No topic paths created."
                raise RuntimeError(error_msg)

        try:
            async for event in self._build_subtree_generator(
                [self.config.topic_prompt],
                self.config.topic_system_prompt,
                self.config.depth,
                self.config.degree,
                1,
            ):
                yield event

            # Check if build was completely unsuccessful (no paths generated)
            _raise_if_build_failed()

            trace(
                "tree_built",
                {
                    "provider": self.provider,
                    "model_name": self.model_name,
                    "total_paths": len(self.tree_paths),
                    "failed_generations": len(self.failed_generations),
                    "success": len(self.tree_paths) > 0,
                },
            )

            yield {
                "event": "build_complete",
                "total_paths": len(self.tree_paths),
                "failed_generations": len(self.failed_generations),
            }
        except Exception as e:
            yield {"event": "error", "error": str(e)}
            # Save partial results before re-raising
            if self.tree_paths:
                self.save("partial_tree.jsonl")
            raise

    def get_all_paths(self) -> list[list[str]]:
        """Returns all the paths in the topic model."""
        return self.tree_paths

    async def get_subtopics(
        self, system_prompt: str, node_path: list[str], num_subtopics: int
    ) -> list[str]:
        """Generate subtopics using structured generation."""

        # Determine domain based on system prompt or path content
        domain = self._detect_domain(system_prompt, node_path)

        prompt = TreePromptBuilder.build_expansion_prompt(
            topic_path=node_path,
            num_subtopics=num_subtopics,
            system_prompt=system_prompt if system_prompt else "",
            domain=domain,
        )

        try:
            # Generate structured subtopics using TopicList schema
            topic_response = await self.llm_client.generate_async(
                prompt=prompt,
                schema=TopicList,
                max_retries=MAX_RETRY_ATTEMPTS,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=self.temperature,
            )

            # Extract and validate subtopics
            subtopics = topic_response.subtopics
            if len(subtopics) >= num_subtopics:
                return subtopics[:num_subtopics]

            # If insufficient subtopics, pad with defaults
            while len(subtopics) < num_subtopics:
                subtopics.append(f"subtopic_{len(subtopics) + 1}_for_{node_path[-1]}")

            return subtopics[:num_subtopics]

        except Exception as e:
            # Log the failure and return default subtopics
            self.failed_generations.append(
                {
                    "node_path": node_path,
                    "error": str(e),
                    "timestamp": time.time(),
                }
            )

            # Generate default subtopics
            return [f"subtopic_{i + 1}_for_{node_path[-1]}" for i in range(num_subtopics)]

    def _detect_domain(self, system_prompt: str, node_path: list[str]) -> str:
        """Detect the appropriate domain for prompt examples based on context."""
        combined_text = f"{system_prompt} {' '.join(node_path)}".lower()

        if any(
            word in combined_text
            for word in ["math", "calculus", "algebra", "geometry", "equation"]
        ):
            return "educational"
        if any(
            word in combined_text
            for word in ["programming", "code", "software", "python", "algorithm"]
        ):
            return "technical"
        if any(
            word in combined_text
            for word in ["chat", "conversation", "talk", "friendly", "assistant"]
        ):
            return "conversational"
        return "general"

    async def _build_subtree_generator(
        self,
        node_path: list[str],
        system_prompt: str,
        total_depth: int,
        n_child: int,
        current_depth: int,
    ):
        """Recursively build a subtree of topics, yielding progress events.

        Args:
            node_path: Current path in the tree
            system_prompt: System prompt for topic generation
            total_depth: Maximum depth of the tree
            n_child: Number of child nodes per parent
            current_depth: Current depth in the tree

        Yields:
            dict: Progress events
        """
        yield {"event": "subtree_start", "node_path": node_path, "depth": current_depth}

        if current_depth > total_depth:
            self.tree_paths.append(node_path)
            yield {"event": "leaf_reached", "path": node_path}
            return

        subtopics = await self.get_subtopics(system_prompt, node_path, n_child)

        event = {
            "event": "subtopics_generated",
            "parent_path": node_path,
            "count": len(subtopics),
            "success": bool(subtopics),
        }

        # Include error information if generation failed
        if not event["success"] and self.failed_generations:
            # Get the most recent failure
            recent_failure = self.failed_generations[-1]
            event["error"] = recent_failure.get("error", "Unknown error")

        yield event

        if not subtopics:
            self.tree_paths.append(node_path)
            yield {"event": "leaf_reached", "path": node_path}
            return

        async def _collect_child_events(child_subtopic: str) -> list[dict[str, Any]]:
            child_path = node_path + [child_subtopic]
            events: list[dict[str, Any]] = []
            async for child_event in self._build_subtree_generator(
                child_path, system_prompt, total_depth, n_child, current_depth + 1
            ):
                events.append(child_event)
            return events

        tasks = [asyncio.create_task(_collect_child_events(subtopic)) for subtopic in subtopics]

        for child_events in await asyncio.gather(*tasks):
            for child_event in child_events:
                yield child_event

    def save(self, save_path: str) -> None:
        """Save the topic tree to a file."""
        with open(save_path, "w") as f:
            for path in self.tree_paths:
                f.write(json.dumps({"path": path}) + "\n")

        # Save failed generations if any
        if self.failed_generations:
            failed_path = save_path.replace(".jsonl", "_failed.jsonl")
            with open(failed_path, "w") as f:
                for failed in self.failed_generations:
                    f.write(json.dumps({"failed_generation": failed}) + "\n")

    def print_tree(self) -> None:
        """Print the topic tree in a readable format."""
        print("Topic Tree Structure:")
        for path in self.tree_paths:
            print(" -> ".join(path))

    def to_dict(self) -> dict[str, Any]:
        """Convert the topic tree to a dictionary representation.

        Returns:
            dict: Dictionary containing the tree structure and metadata
        """
        return {
            "tree_paths": self.tree_paths,
            "failed_generations": self.failed_generations,
            "config": {
                "topic_prompt": self.topic_prompt,
                "degree": self.degree,
                "depth": self.depth,
                "temperature": self.temperature,
                "provider": self.provider,
                "model_name": self.model_name,
            },
        }

    def from_dict_list(self, dict_list: list[dict[str, Any]]) -> None:
        """Construct the topic tree from a list of dictionaries.

        Args:
            dict_list (list[dict]): The list of dictionaries representing the topic tree.
        """
        # Clear existing data
        self.tree_paths = []
        self.failed_generations = []

        for d in dict_list:
            if "path" in d:
                self.tree_paths.append(d["path"])
            elif "failed_generation" in d:
                self.failed_generations.append(d["failed_generation"])

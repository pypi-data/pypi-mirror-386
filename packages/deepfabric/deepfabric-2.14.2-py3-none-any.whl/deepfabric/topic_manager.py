import asyncio
import traceback

from typing import TYPE_CHECKING

from .config import DeepFabricConfig
from .constants import (
    TOPIC_TREE_DEFAULT_DEGREE,
    TOPIC_TREE_DEFAULT_DEPTH,
    TOPIC_TREE_DEFAULT_TEMPERATURE,
)
from .exceptions import ConfigurationError
from .factory import create_topic_generator
from .graph import Graph
from .topic_model import TopicModel
from .tree import Tree
from .tui import get_graph_tui, get_tree_tui, get_tui
from .utils import read_topic_tree_from_jsonl

if TYPE_CHECKING:
    from .topic_model import TopicModel


def _ensure_not_running_loop(func_name: str) -> None:
    """Raise a helpful error if invoked from an active asyncio loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    if loop.is_running():
        msg = (
            f"{func_name} cannot be called from within an active event loop. "
            f"Use `{func_name}_async` instead."
        )
        raise RuntimeError(msg)


async def _process_graph_events(graph: Graph) -> dict | None:
    tui = get_graph_tui()
    tui_started = False

    final_event = None
    try:
        async for event in graph.build_async():
            if event["event"] == "depth_start":
                if not tui_started:
                    tui.start_building(graph.model_name, graph.depth, graph.degree)
                    tui_started = True
                depth = int(event["depth"]) if isinstance(event["depth"], str | int) else 0
                leaf_count = (
                    int(event.get("leaf_count", 0))
                    if isinstance(event.get("leaf_count", 0), str | int)
                    else 0
                )
                tui.start_depth_level(depth, leaf_count)
            elif event["event"] == "node_expanded":
                subtopics_added = (
                    int(event["subtopics_added"])
                    if isinstance(event["subtopics_added"], str | int)
                    else 0
                )
                connections_added = (
                    int(event.get("connections_added", 0))
                    if isinstance(event.get("connections_added", 0), str | int)
                    else 0
                )
                tui.complete_node_expansion(event["node_topic"], subtopics_added, connections_added)
            elif event["event"] == "depth_complete":
                depth = int(event["depth"]) if isinstance(event["depth"], str | int) else 0
                tui.complete_depth_level(depth)
            elif event["event"] == "build_complete":
                failed_generations = (
                    int(event.get("failed_generations", 0))
                    if isinstance(event.get("failed_generations", 0), str | int)
                    else 0
                )
                tui.finish_building(failed_generations)
                final_event = event
    except Exception as e:
        get_tui().error(f"Graph build failed: {str(e)}")
        raise
    else:
        return final_event


async def _process_tree_events(tree: Tree, debug: bool = False) -> dict | None:
    tui = get_tree_tui()

    final_event = None
    try:
        async for event in tree.build_async():
            if event["event"] == "build_start":
                depth = int(event["depth"]) if isinstance(event["depth"], str | int) else 0
                degree = int(event["degree"]) if isinstance(event["degree"], str | int) else 0
                tui.start_building(event["model_name"], depth, degree)
            elif event["event"] == "subtopics_generated":
                if not event["success"]:
                    tui.add_failure()
                    if debug and "error" in event:
                        get_tui().error(f"Debug: Tree generation failure - {event['error']}")
            elif event["event"] == "build_complete":
                total_paths = (
                    int(event["total_paths"]) if isinstance(event["total_paths"], str | int) else 0
                )
                failed_generations = (
                    int(event["failed_generations"])
                    if isinstance(event["failed_generations"], str | int)
                    else 0
                )
                tui.finish_building(total_paths, failed_generations)
                final_event = event

                if debug and failed_generations > 0 and hasattr(tree, "failed_generations"):
                    get_tui().error("\n🔍 Debug: Tree generation failures:")
                    for idx, failure in enumerate(tree.failed_generations, 1):
                        get_tui().error(
                            f"  [{idx}] Path: {' -> '.join(failure.get('node_path', []))}"
                        )
                        get_tui().error(f"      Error: {failure.get('error', 'Unknown error')}")
    except Exception as e:
        if debug:
            get_tui().error(f"🔍 Debug: Full traceback:\n{traceback.format_exc()}")
        get_tui().error(f"Tree build failed: {str(e)}")
        raise
    else:
        return final_event


def handle_graph_events(graph: Graph) -> dict | None:
    """
    Build graph with TUI progress.

    Args:
        graph: Graph object to build

    Returns:
        Final build event dictionary or None

    Raises:
        Exception: If graph build fails
    """
    _ensure_not_running_loop("handle_graph_events")
    return asyncio.run(_process_graph_events(graph))


async def handle_graph_events_async(graph: Graph) -> dict | None:
    return await _process_graph_events(graph)


def handle_tree_events(tree: Tree, debug: bool = False) -> dict | None:
    """
    Build tree with TUI progress.

    Args:
        tree: Tree object to build
        debug: Enable debug output

    Returns:
        Final build event dictionary or None

    Raises:
        Exception: If tree build fails
    """
    _ensure_not_running_loop("handle_tree_events")
    return asyncio.run(_process_tree_events(tree, debug=debug))


async def handle_tree_events_async(tree: Tree, debug: bool = False) -> dict | None:
    return await _process_tree_events(tree, debug=debug)


def load_or_build_topic_model(
    config: DeepFabricConfig,
    load_tree: str | None = None,
    load_graph: str | None = None,
    tree_overrides: dict | None = None,
    graph_overrides: dict | None = None,
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    debug: bool = False,
) -> TopicModel:
    """
    Load topic model from file or build new one.

    Args:
        config: DeepFabricConfig object
        load_tree: Path to existing tree JSONL file
        load_graph: Path to existing graph JSON file
        tree_overrides: Override parameters for tree
        graph_overrides: Override parameters for graph
        provider: LLM provider
        model: Model name
        base_url: Base URL for LLM API

    Returns:
        TopicModel (Tree or Graph)

    Raises:
        ConfigurationError: If loading or building fails
    """
    tui = get_tui()

    if load_tree:
        tui.info(f"Reading topic tree from JSONL file: {load_tree}")
        dict_list = read_topic_tree_from_jsonl(load_tree)

        final_provider = provider or "ollama"
        final_model = model or "mistral:latest"

        topic_model = Tree(
            topic_prompt="default",
            provider=final_provider,
            model_name=final_model,
            topic_system_prompt="",
            degree=TOPIC_TREE_DEFAULT_DEGREE,
            depth=TOPIC_TREE_DEFAULT_DEPTH,
            temperature=TOPIC_TREE_DEFAULT_TEMPERATURE,
            base_url=base_url,
        )
        topic_model.from_dict_list(dict_list)
        return topic_model

    if load_graph:
        tui.info(f"Reading topic graph from JSON file: {load_graph}")
        graph_params = config.get_topic_graph_params(**(graph_overrides or {}))
        return Graph.from_json(load_graph, graph_params)

    # Build new topic model
    topic_model = create_topic_generator(
        config, tree_overrides=tree_overrides, graph_overrides=graph_overrides
    )

    # Build with appropriate event handler
    if isinstance(topic_model, Graph):
        handle_graph_events(topic_model)
    elif isinstance(topic_model, Tree):
        handle_tree_events(topic_model, debug=debug)

    return topic_model


def save_topic_model(
    topic_model: TopicModel,
    config: DeepFabricConfig,
    save_tree: str | None = None,
    save_graph: str | None = None,
) -> None:
    """
    Save topic model to file.

    Args:
        topic_model: TopicModel to save (Tree or Graph)
        config: DeepFabricConfig object
        save_tree: Override path for saving tree
        save_graph: Override path for saving graph

    Raises:
        ConfigurationError: If saving fails
    """
    tui = get_tui()

    if isinstance(topic_model, Tree):
        try:
            tree_save_path = (
                save_tree
                or (config.topic_tree.save_as if config.topic_tree else None)
                or "topic_tree.jsonl"
            )
            topic_model.save(tree_save_path)
            tui.success(f"Topic tree saved to {tree_save_path}")
            tui.info(f"Total paths: {len(topic_model.tree_paths)}")
        except Exception as e:
            raise ConfigurationError(f"Error saving topic tree: {str(e)}") from e

    elif isinstance(topic_model, Graph):
        try:
            graph_save_path = (
                save_graph
                or (config.topic_graph.save_as if config.topic_graph else None)
                or "topic_graph.json"
            )
            topic_model.save(graph_save_path)
            tui.success(f"Topic graph saved to {graph_save_path}")
        except Exception as e:
            raise ConfigurationError(f"Error saving topic graph: {str(e)}") from e

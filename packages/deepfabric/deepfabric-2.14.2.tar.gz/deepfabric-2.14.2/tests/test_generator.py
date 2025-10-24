from unittest.mock import AsyncMock, MagicMock, patch

import pytest  # type: ignore

from deepfabric.exceptions import DataSetGeneratorError
from deepfabric.generator import Dataset, DataSetGenerator


@pytest.fixture
def engine_args():
    return {
        "instructions": "Test instructions",
        "generation_system_prompt": "Test system prompt",
        "dataset_system_prompt": "Test dataset system prompt",
        "provider": "openai",
        "model_name": "test-model",
        "prompt_template": None,
        "example_data": None,
        "temperature": 0.7,
        "max_retries": 3,
        "default_batch_size": 5,
        "default_num_examples": 3,
        "request_timeout": 30,
        "sys_msg": True,
    }


@pytest.fixture
def data_engine(engine_args):
    with patch("deepfabric.generator.LLMClient"):
        return DataSetGenerator(**engine_args)


def test_engine_initialization(engine_args):
    with patch("deepfabric.generator.LLMClient"):
        engine = DataSetGenerator(**engine_args)
    assert engine.config.instructions == engine_args["instructions"]
    assert engine.config.generation_system_prompt == engine_args["generation_system_prompt"]
    assert engine.config.model_name == engine_args["model_name"]
    assert isinstance(engine.dataset, Dataset)
    assert engine.failed_samples == []


def test_create_data_no_steps(data_engine):
    with pytest.raises(DataSetGeneratorError, match="positive"):
        data_engine.create_data(num_steps=0)


def test_create_data_success(data_engine):
    # Mock the generate method on the data_engine's llm_client instance
    from deepfabric.schemas import ChatMessage, ChatTranscript  # noqa: PLC0415

    data_engine.llm_client.generate_async = AsyncMock(
        return_value=ChatTranscript(
            messages=[
                ChatMessage(role="user", content="example"),
                ChatMessage(role="assistant", content="response"),
            ]
        )
    )

    topic_tree = MagicMock()
    topic_tree.tree_paths = [
        "path1",
        "path2",
        "path3",
        "path4",
        "path5",
        "path6",
        "path7",
        "path8",
        "path9",
        "path10",
    ]
    topic_tree.get_all_paths.return_value = [[p] for p in topic_tree.tree_paths]

    # Define a constant for the expected number of samples
    expected_num_samples = 10

    # Generate the data
    dataset = data_engine.create_data(num_steps=1, batch_size=10, topic_model=topic_tree)

    # Assert that the dataset contains exactly the expected number of samples
    assert len(dataset.samples) == expected_num_samples


def test_create_data_with_sys_msg_default(data_engine):
    # Mock the generate method on the data_engine's llm_client instance
    from deepfabric.schemas import ChatMessage, ChatTranscript  # noqa: PLC0415

    data_engine.llm_client.generate_async = AsyncMock(
        return_value=ChatTranscript(
            messages=[
                ChatMessage(role="user", content="example"),
                ChatMessage(role="assistant", content="response"),
            ]
        )
    )

    topic_tree = MagicMock()
    topic_tree.tree_paths = ["path1"]
    topic_tree.get_all_paths.return_value = [["path1"]]

    # Generate data with default sys_msg (True)
    dataset = data_engine.create_data(num_steps=1, batch_size=1, topic_model=topic_tree)

    # Verify system message is included
    assert len(dataset.samples) == 1
    assert len(dataset.samples[0]["messages"]) == 3  # noqa: PLR2004
    assert dataset.samples[0]["messages"][0]["role"] == "system"
    assert dataset.samples[0]["messages"][0]["content"] == data_engine.config.dataset_system_prompt


def test_create_data_without_sys_msg(data_engine):
    # Mock the generate method on the data_engine's llm_client instance
    from deepfabric.schemas import ChatMessage, ChatTranscript  # noqa: PLC0415

    data_engine.llm_client.generate_async = AsyncMock(
        return_value=ChatTranscript(
            messages=[
                ChatMessage(role="user", content="example"),
                ChatMessage(role="assistant", content="response"),
            ]
        )
    )

    topic_tree = MagicMock()
    topic_tree.tree_paths = ["path1"]
    topic_tree.get_all_paths.return_value = [["path1"]]

    # Generate data with sys_msg=False
    dataset = data_engine.create_data(
        num_steps=1, batch_size=1, topic_model=topic_tree, sys_msg=False
    )

    # Verify system message is not included
    assert len(dataset.samples) == 1
    assert len(dataset.samples[0]["messages"]) == 2  # noqa: PLR2004
    assert dataset.samples[0]["messages"][0]["role"] == "user"


def test_create_data_sys_msg_override():
    # Create engine with sys_msg=False
    with patch("deepfabric.generator.LLMClient"):
        engine = DataSetGenerator(
            instructions="Test instructions",
            generation_system_prompt="Test system prompt",
            dataset_system_prompt="Test dataset system prompt",
            provider="openai",
            model_name="test-model",
            prompt_template=None,
            example_data=None,
            temperature=0.7,
            max_retries=3,
            default_batch_size=5,
            default_num_examples=3,
            request_timeout=30,
            sys_msg=False,  # Default to False
        )

    # Mock the generate method on the engine's llm_client instance
    from deepfabric.schemas import ChatMessage, ChatTranscript  # noqa: PLC0415

    engine.llm_client.generate_async = AsyncMock(
        return_value=ChatTranscript(
            messages=[
                ChatMessage(role="user", content="example"),
                ChatMessage(role="assistant", content="response"),
            ]
        )
    )

    topic_tree = MagicMock()
    topic_tree.tree_paths = ["path1"]
    topic_tree.get_all_paths.return_value = [["path1"]]

    # Override sys_msg=False with True in create_data
    dataset = engine.create_data(num_steps=1, batch_size=1, topic_model=topic_tree, sys_msg=True)

    # Verify system message is included despite engine default
    assert len(dataset.samples) == 1  # type: ignore
    assert len(dataset.samples[0]["messages"]) == 3  # type: ignore # noqa: PLR2004
    assert dataset.samples[0]["messages"][0]["role"] == "system"  # type: ignore


def test_build_prompt(data_engine):
    prompt = data_engine.build_prompt("Test prompt", 3, ["subtopic1", "subtopic2"])
    assert "{{generation_system_prompt}}" not in prompt
    assert "{{instructions}}" not in prompt
    assert "{{examples}}" not in prompt
    assert "{{subtopics}}" not in prompt


def test_build_system_prompt(data_engine):
    system_prompt = data_engine.build_system_prompt()
    assert system_prompt == data_engine.config.dataset_system_prompt


def test_build_custom_instructions_text(data_engine):
    instructions_text = data_engine.build_custom_instructions_text()
    assert "<instructions>" in instructions_text
    assert data_engine.config.instructions in instructions_text


def test_build_examples_text_no_examples(data_engine):
    examples_text = data_engine.build_examples_text(3)
    assert examples_text == ""


def test_build_subtopics_text(data_engine):
    subtopics_text = data_engine.build_subtopics_text(["subtopic1", "subtopic2"])
    assert "subtopic1 -> subtopic2" in subtopics_text


@patch.object(Dataset, "save")
def test_save_dataset(mock_save, data_engine):
    data_engine.save_dataset("test_path.jsonl")
    mock_save.assert_called_once_with("test_path.jsonl")

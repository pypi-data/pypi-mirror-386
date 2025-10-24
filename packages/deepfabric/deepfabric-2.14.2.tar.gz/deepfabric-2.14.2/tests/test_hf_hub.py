"""Tests for the HF Hub uploader module."""

from unittest.mock import Mock, patch

import pytest

from huggingface_hub.errors import HfHubHTTPError, RepositoryNotFoundError
from requests import Request, Response

from deepfabric.hf_hub import HFUploader


@pytest.fixture
def mock_dataset_card():
    """Create a mock dataset card."""
    card = Mock()
    card.data.tags = []
    return card


@pytest.fixture
def uploader():
    """Create an HFUploader instance."""
    return HFUploader("dummy_token")


def test_update_dataset_card(uploader, mock_dataset_card):
    """Test updating dataset card with tags."""
    with patch("deepfabric.hf_hub.DatasetCard") as mock_card_class:
        mock_card_class.load.return_value = mock_dataset_card

        # Test with default tags only
        uploader.update_dataset_card("test/repo")
        assert "deepfabric" in mock_dataset_card.data.tags
        assert "synthetic" in mock_dataset_card.data.tags
        mock_dataset_card.push_to_hub.assert_called_once_with("test/repo")

        # Reset mock
        mock_dataset_card.data.tags = []
        mock_dataset_card.push_to_hub.reset_mock()

        # Test with custom tags
        custom_tags = ["custom1", "custom2"]
        uploader.update_dataset_card("test/repo", tags=custom_tags)
        assert all(
            tag in mock_dataset_card.data.tags for tag in ["deepfabric", "synthetic"] + custom_tags
        )
        mock_dataset_card.push_to_hub.assert_called_once_with("test/repo")


def test_push_to_hub_success(uploader):
    """Test successful dataset push to hub."""
    with (
        patch("deepfabric.hf_hub.login") as mock_login,
        patch("deepfabric.hf_hub.load_dataset") as mock_load_dataset,
        patch.object(uploader, "update_dataset_card") as mock_update_card,
    ):
        mock_dataset = Mock()
        mock_load_dataset.return_value = mock_dataset

        result = uploader.push_to_hub("test/repo", "test.jsonl", tags=["test"])

        mock_login.assert_called_once_with(token="dummy_token")  # noqa: S106
        mock_load_dataset.assert_called_once_with("json", data_files={"train": "test.jsonl"})
        mock_dataset.push_to_hub.assert_called_once_with(
            "test/repo",
            token="dummy_token",  # noqa: S106
        )
        mock_update_card.assert_called_once()

        assert result["status"] == "success"
        assert "test/repo" in result["message"]


def test_push_to_hub_file_not_found(uploader):
    """Test push to hub with non-existent file."""
    with (
        patch("deepfabric.hf_hub.login") as _mock_login,
        patch("deepfabric.hf_hub.load_dataset") as mock_load_dataset,  # noqa: F841
    ):
        mock_load_dataset.side_effect = FileNotFoundError("File not found")

        result = uploader.push_to_hub("test/repo", "nonexistent.jsonl")
        assert result["status"] == "error"
        assert "not found" in result["message"]


@patch("deepfabric.hf_hub.login")
def test_push_to_hub_repository_not_found(mock_login, uploader):
    """Test push to hub with non-existent repository."""
    mock_login.side_effect = RepositoryNotFoundError("Repository not found")

    result = uploader.push_to_hub("nonexistent/repo", "test.jsonl")
    assert result["status"] == "error"
    assert "Repository" in result["message"]


@patch("deepfabric.hf_hub.login")
def test_push_to_hub_http_error(mock_login, uploader):
    """Test push to hub with HTTP error."""
    # Create a mock response object with all required attributes
    mock_response = Mock(spec=Response)
    mock_response.headers = {"x-request-id": "test-id"}
    mock_response.request = Mock(spec=Request)
    mock_response.status_code = 400
    mock_response.text = "Error message"

    # Create HfHubHTTPError with mock response
    mock_login.side_effect = HfHubHTTPError("HTTP Error", response=mock_response)

    result = uploader.push_to_hub("test/repo", "test.jsonl")
    assert result["status"] == "error"
    assert "HTTP Error" in result["message"]

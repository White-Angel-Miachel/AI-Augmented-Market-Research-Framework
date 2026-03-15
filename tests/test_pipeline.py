"""
Smoke tests for AI-Augmented Market Research Framework.
These tests do NOT require actual API keys or external services.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Report Parser Tests ────────────────────────────────────────────────────────

def test_report_parser_imports():
    """Test that ReportParser can be imported."""
    from src.report_parser import ReportParser
    assert ReportParser is not None


def test_report_parser_handles_missing_file():
    """Test that parser raises an exception on missing files."""
    from src.report_parser import ReportParser
    import pytest
    parser = ReportParser()
    with pytest.raises(Exception):
        parser.parse("non_existent_file.pdf")


def test_report_parser_txt_file(tmp_path):
    """Test that parser can read a plain text file."""
    from src.report_parser import ReportParser
    txt_file = tmp_path / "test_report.txt"
    txt_file.write_text("This is a test market report with investment data.")
    parser = ReportParser()
    content = parser.parse(str(txt_file))
    assert "test market report" in content
    assert len(content) > 0


# ── Pipeline Initialization Tests ─────────────────────────────────────────────

def test_pipeline_import():
    """Test that pipeline can be imported without error."""
    from src.pipeline import MarketResearchPipeline
    assert MarketResearchPipeline is not None


def test_pipeline_init_gemini():
    """Test pipeline initializes correctly with mocked Gemini client."""
    from src.pipeline import MarketResearchPipeline
    with patch("src.pipeline.genai") as mock_genai:
        mock_genai.Client.return_value = MagicMock()
        pipeline = MarketResearchPipeline(
            model_name="gemini-2.5-flash",
            use_api=True,
            api_key="fake-gemini-key"
        )
        assert pipeline.model_name == "gemini-2.5-flash"
        assert pipeline.provider == "gemini"


def test_pipeline_init_nvidia():
    """Test pipeline initializes correctly for an NVIDIA NIM model."""
    from src.pipeline import MarketResearchPipeline
    with patch("src.pipeline.OpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()
        pipeline = MarketResearchPipeline(
            model_name="minimaxai/minimax-m2.5",
            use_api=True,
            openai_api_key="fake-nvidia-key"
        )
        assert pipeline.model_name == "minimaxai/minimax-m2.5"
        assert pipeline.provider == "openai"


def test_pipeline_raises_without_api_key():
    """Test that pipeline raises ValueError if no API key is provided."""
    from src.pipeline import MarketResearchPipeline
    import pytest
    # Clear env vars to ensure no accidental key is picked up
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
            MarketResearchPipeline(
                model_name="minimaxai/minimax-m2.5",
                use_api=True
            )


def test_pipeline_bearer_prefix_stripped():
    """Test that 'Bearer ' prefix in API key is stripped automatically."""
    from src.pipeline import MarketResearchPipeline
    with patch("src.pipeline.OpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()
        pipeline = MarketResearchPipeline(
            model_name="minimaxai/minimax-m2.5",
            use_api=True,
            openai_api_key="Bearer fake-key-123"
        )
        assert not pipeline.openai_api_key.startswith("Bearer ")
        assert pipeline.openai_api_key == "fake-key-123"


# ── Pitch Generator Tests ──────────────────────────────────────────────────────

def test_pitch_generator_import():
    """Test that PitchBriefGenerator can be imported."""
    from src.pitch_generator import PitchBriefGenerator
    assert PitchBriefGenerator is not None


# ── Flask App Tests ────────────────────────────────────────────────────────────

def test_flask_app_import():
    """Test that Flask app can be imported."""
    import app as flask_app
    assert flask_app.app is not None


def test_flask_index_route():
    """Test that the index route returns 200."""
    import app as flask_app
    client = flask_app.app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_flask_results_endpoint():
    """Test that /results returns a JSON list."""
    import app as flask_app
    client = flask_app.app.test_client()
    response = client.get("/results")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

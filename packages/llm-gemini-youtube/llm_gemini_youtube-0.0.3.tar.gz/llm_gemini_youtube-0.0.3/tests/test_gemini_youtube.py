import subprocess

import pytest
from llm.plugins import load_plugins, pm

from llm_gemini_youtube import is_youtube_uri


def test_plugin_is_installed():
    load_plugins()

    names = [mod.__name__ for mod in pm.get_plugins()]
    assert "llm_gemini_youtube" in names


class TestIsYouTubeUri:
    @pytest.mark.parametrize(
        "uri",
        [
            "https://www.youtube.com/watch?v=9hE5-98ZeCg",
            "https://youtu.be/9hE5-98ZeCg",
            "https://www.youtube.com/shorts/46ycw2pQJCA",
        ],
    )
    def test_youtube_uri(self, uri):
        assert is_youtube_uri(uri)

    def test_not_youtube_uri(self):
        assert not is_youtube_uri("https://example.com")


class TestSupportedModels:
    @pytest.mark.parametrize(
        "expected_model",
        [
            "gemini-2.0-flash-yt",
            "gemini-1.5-pro-yt",
            "gemini-2.5-pro-yt",
            "gemini-2.5-flash-yt",
        ],
    )
    def test_contains_llm_models_output(self, expected_model):
        result = subprocess.run(
            ["llm", "models", "-q", "-yt"],
            check=True,
            capture_output=True,
            text=True,
        )

        assert expected_model in result.stdout

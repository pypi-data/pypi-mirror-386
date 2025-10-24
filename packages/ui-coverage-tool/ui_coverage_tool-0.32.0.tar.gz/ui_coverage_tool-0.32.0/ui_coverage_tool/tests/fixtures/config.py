from pathlib import Path

import pytest
from pydantic import HttpUrl

from ui_coverage_tool.config import Settings, AppConfig
from ui_coverage_tool.src.tools.types import AppKey, AppName


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        apps=[
            AppConfig(
                url=HttpUrl("https://example.com/login"),
                key=AppKey("test-service"),
                name=AppName("Test Service")
            )
        ],
        results_dir=results_dir
    )


@pytest.fixture
def coverage_history_settings(tmp_path: Path, settings: Settings) -> Settings:
    settings.results_dir = tmp_path / "results"
    settings.history_file = tmp_path / "history.json"
    settings.history_retention_limit = 3
    return settings


@pytest.fixture
def reports_settings(tmp_path: Path, coverage_history_settings: Settings) -> Settings:
    coverage_history_settings.json_report_file = tmp_path / "report.json"
    coverage_history_settings.html_report_file = tmp_path / "report.html"
    return coverage_history_settings

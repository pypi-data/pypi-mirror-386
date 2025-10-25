import json
import os
from pathlib import Path

import pytest

from axe_playwright_python.base import AxeResults


@pytest.fixture
def test_results_json():
    result_path = os.path.join(os.path.dirname(__file__), "test_result.json")
    with open(result_path) as f:
        results = json.load(f)
    return results


def test_report(test_results_json):
    results = AxeResults(test_results_json)
    report = results.generate_report()
    report_path = os.path.join(os.path.dirname(__file__), "test_report.txt")
    with open(report_path) as f:
        assert report == f.read()


def test_report_for_id(test_results_json):
    results = AxeResults(test_results_json)
    report = results.generate_report(violation_id="color-contrast")
    report_path = os.path.join(os.path.dirname(__file__), "test_report_color.txt")
    with open(report_path) as f:
        assert report == f.read()


def test_save_results(test_results_json):
    results = AxeResults(test_results_json)
    results.save_to_file()
    # Assert that file was created and looks like JSON
    assert Path("results.json").is_file()
    with open("results.json") as f:
        assert f.readline() == "{\n"
    os.remove("results.json")


def test_save_results_with_path(test_results_json):
    results = AxeResults(test_results_json)
    results.save_to_file("results2.json")
    assert Path("results2.json").is_file()
    os.remove("results2.json")


def test_save_results_with_pathlib(test_results_json):
    results = AxeResults(test_results_json)
    results.save_to_file(Path("results3.json"))
    assert Path("results3.json").is_file()
    os.remove("results3.json")


def test_save_results_violations_only(test_results_json):
    file_path = Path("results_violations.json")
    results = AxeResults(test_results_json)
    results.save_to_file(file_path, violations_only=True)
    assert file_path.is_file()
    results_json = open(file_path).read()
    assert "incomplete" not in results_json
    assert "passes" not in results_json
    assert "inapplicable" not in results_json
    os.remove(file_path)


def test_violations_count(test_results_json):
    results = AxeResults(test_results_json)
    assert results.violations_count == 2

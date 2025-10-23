"""Tests the validators."""

import pandas as pd
import polars as pl

from morai.experience import validators
from morai.utils import helpers

test_validators_path = (
    helpers.ROOT_PATH / "tests" / "files" / "experience" / "validators"
)
lzdf = pl.scan_csv(test_validators_path / "shapes.csv")


def test_get_checks() -> None:
    """Tests the get checks function."""
    check_dict = validators.get_checks(
        checks_path=test_validators_path / "test_checks.yaml"
    )
    assert isinstance(check_dict, dict), "Check dict should be a dictionary"
    assert len(check_dict) == 2, "Check dict should have 2 checks"


def test_run_checks() -> None:
    """Tests the run checks function."""
    check_dict = validators.get_checks(
        checks_path=test_validators_path / "test_checks.yaml"
    )
    check_output = validators.run_checks(lzdf=lzdf, check_dict=check_dict)
    assert isinstance(check_output, pd.DataFrame), "Check output should be a DataFrame"
    assert len(check_output) == 2, "Check output should have 2 checks"
    assert (
        check_output.loc[check_output["checks"] == "logic_circle", "percent"].iloc[0]
        == 0
    ), "Check output should have 0 percent as all circles have 0 sides"
    assert (
        check_output.loc[check_output["checks"] == "limit_id", "result"].iloc[0] == 1
    ), "Check should show 1 failure the triangle since it has id of 3"


def test_single_check() -> None:
    """Tests the single check function."""
    check_dict = validators.get_checks(
        checks_path=test_validators_path / "test_checks.yaml"
    )
    single_check = validators.view_single_check(
        lzdf=lzdf, check_dict=check_dict, check_name="limit_id"
    )
    assert single_check.shape == (1, 3)


def test_replace_newlines_in_dict() -> None:
    """Tests the replace newlines in dict function."""
    data = {
        "a": "new\nline",
        "b": {"b1": "new\nline", "b2": ["line1", {"b21": "new\nline"}]},
    }
    expected = {
        "a": "new line",
        "b": {"b1": "new line", "b2": ["line1", {"b21": "new line"}]},
    }
    result = validators._replace_newlines_in_dict(data, old="\n", new=" ")
    assert result == expected

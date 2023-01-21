import os
from typing import Any, Dict, List

import pytest
from pytest_mock import MockerFixture

from lib import config

# This needs to be accessed to be tested
# pylint: disable=protected-access


# Make sure we don't actually read the config file. The
# mocks can still be overriden in each test
@pytest.fixture(autouse=True)
def mock_open(mocker: MockerFixture) -> None:
    mocker.patch("builtins.open")
    mocker.patch("json.load")


def test_config_exits_on_error_in_config_file(mocker: MockerFixture) -> None:
    mock_sys_exit = mocker.patch("sys.exit")
    mocker.patch.object(config.Config, "_parse_config", side_effect=TypeError())

    config.Config()
    mock_sys_exit.assert_called_once()


def test_read_config_reads_the_config_file_correctly(mocker: MockerFixture) -> None:
    mock_open = mocker.patch("builtins.open")
    mocker.patch("json.load", return_value={"test": "data"})

    test_config = config.Config()
    config_content = test_config._read_config()

    assert config_content == {"test": "data"}
    mock_open.assert_called_with(
        os.path.dirname(os.path.dirname(__file__)) + "/" + config.CONFIG_FILE_NAME
    )


def test_read_config_returns_empty_config_when_file_is_not_found(mocker: MockerFixture) -> None:
    mocker.patch("builtins.open", side_effect=FileNotFoundError())

    test_config = config.Config()
    config_content = test_config._read_config()

    assert config_content == {}


@pytest.mark.parametrize(
    "config_content",
    [
        {"notification_urls": None},
        {"notification_level": "invalid"},
        {"retrieval_interval": "invalid"},
        {"accounts": "invalid"},
    ],
)
def test_parse_config_raises_exception_with_invalid_entries(config_content: Dict[str, Any]) -> None:
    test_config = config.Config()

    with pytest.raises(TypeError):
        test_config._parse_config(config_content)


def test_parse_config_sets_the_correct_config_values() -> None:
    test_config = config.Config()
    test_config._parse_config(
        {"notification_urls": "test_url", "notification_level": 30, "retrieval_interval": 20}
    )

    assert test_config.notification_urls == "test_url"
    assert test_config.notification_level == 30
    assert test_config.retrieval_interval == 20


def test_parse_config_does_not_set_values_when_a_config_value_is_empty(
    mocker: MockerFixture,
) -> None:
    mock_parse_accounts = mocker.patch.object(config.Config, "_parse_accounts")
    test_config = config.Config()
    expected_config = config.Config()

    test_config._parse_config({})

    assert test_config.notification_urls == expected_config.notification_urls
    assert test_config.notification_level == expected_config.notification_level
    assert test_config.retrieval_interval == test_config.retrieval_interval
    mock_parse_accounts.assert_not_called()


def test_parse_config_sets_retrieval_interval_to_a_minimum() -> None:
    test_config = config.Config()
    test_config._parse_config({"retrieval_interval": -1})

    assert test_config.retrieval_interval == 1


def test_parse_config_parses_accounts_when_available(mocker: MockerFixture) -> None:
    mock_parse_accounts = mocker.patch.object(config.Config, "_parse_accounts")
    test_config = config.Config()
    test_config._parse_config({"accounts": []})

    mock_parse_accounts.assert_called_once()


@pytest.mark.parametrize("account_content", [[""], [1], [True]])
def test_parse_accounts_raises_exception_with_invalid_entries(account_content: List[Any]) -> None:
    test_config = config.Config()

    with pytest.raises(TypeError):
        test_config._parse_accounts(account_content)


def test_parse_accounts_parses_every_account(mocker: MockerFixture) -> None:
    mock_parse_account = mocker.patch.object(config.Config, "_parse_account")
    test_config = config.Config()
    test_config._parse_accounts([{}, {}])

    assert mock_parse_account.call_count == 2


@pytest.mark.parametrize(
    "account_content",
    [
        {},
        {"username": ""},  # No password
        {"password": ""},  # No username
        {"username": 1, "password": "valid"},  # Invalid username type
        {"username": "valid", "password": 1},  # Invalid password type
    ],
)
def test_parse_account_raises_exception_with_invalid_entries(account_content: List[Any]) -> None:
    test_config = config.Config()

    with pytest.raises(TypeError):
        test_config._parse_account(account_content)


def test_parse_account_adds_an_account() -> None:
    test_config = config.Config()
    test_config._parse_account({"username": "user", "password": "pass"})

    assert len(test_config.accounts) == 1
    assert test_config.accounts[0] == ["user", "pass"]

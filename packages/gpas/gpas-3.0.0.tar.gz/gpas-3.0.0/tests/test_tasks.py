import logging
from unittest.mock import MagicMock, patch

import httpx
import pytest

from gpas import tasks
from gpas.errors import UnsupportedClientError


@patch("httpx.Client.get")
@patch("gpas.__version__", "1.0.0")
def test_check_new_version_available(
    mock_get: MagicMock, capsys: pytest.CaptureFixture
) -> None:
    """Test to check that a new version is available if it exists.

    Args:
        mock_get (MagicMock): Mocked `httpx.Client.get` method.
        caplog (pytest.LogCaptureFixture): Pytest fixture to capture log output.
    """
    mock_get.return_value = httpx.Response(
        status_code=200, json={"info": {"version": "1.1.0"}}
    )
    tasks.check_for_newer_version()
    contents = capsys.readouterr()
    assert "A new version of the GPAS CLI" in contents.out


@patch("httpx.Client.get")
@patch("gpas.__version__", "1.0.0")
def test_check_no_new_version_available(
    mock_get: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that no new version is available if request is latest.

    Args:
        mock_get (MagicMock): Mocked `httpx.Client.get` method.
        caplog (pytest.LogCaptureFixture): Pytest fixture to capture log output.
    """
    caplog.set_level(logging.INFO, logger="gpas")
    mock_get.return_value = httpx.Response(
        status_code=200, json={"info": {"version": "1.0.0"}}
    )
    tasks.check_for_newer_version()
    assert not caplog.text


@patch("httpx.Client.get")
@patch("gpas.__version__", "1.0.1")
def test_check_version_compatibility(
    mock_get: MagicMock, caplog: pytest.LogCaptureFixture, test_host: str
) -> None:
    """Test to check whether two minor versions are compatible.

    Args:
        mock_get (MagicMock): Mocked `httpx.Client.get` method.
        caplog (pytest.LogCaptureFixture): Pytest fixture to capture log output.
    """
    mock_get.return_value = httpx.Response(status_code=200, json={"version": "1.0.0"})
    tasks.check_version_compatibility(host=test_host)


@patch("httpx.Client.get")
@patch("gpas.__version__", "1.0.0")
def test_fail_check_version_compatibility(
    mock_get: MagicMock, caplog: pytest.LogCaptureFixture, test_host: str
) -> None:
    """Test failure of version compatibility check.

    Args:
        mock_get (MagicMock): Mocked `httpx.Client.get` method.
        caplog (pytest.LogCaptureFixture): Pytest fixture to capture log output.
    """
    caplog.set_level(logging.INFO, logger="gpas")
    mock_get.return_value = httpx.Response(status_code=200, json={"version": "1.0.1"})
    with pytest.raises(UnsupportedClientError):
        tasks.check_version_compatibility(host=test_host)
        assert "is no longer supported" in caplog.text


@patch("httpx.Client.get")
@patch("gpas.client.env.get_access_token")
def test_get_balance(
    mock_token: MagicMock, mock_get: MagicMock, capsys: pytest.CaptureFixture
) -> None:
    """Test successfully getting the balance for a given account.

    Args:
        mock_token (MagicMock): Mocked `gpas.client.env.get_access_token` method.
        mock_get (MagicMock): Mocked `httpx.Client.get` method.
        caplog (pytest.LogCaptureFixture): Pytest fixture to capture log output.
    """
    mock_token.return_value = "fake_token"
    mock_get.return_value = httpx.Response(status_code=200, text="1000")
    tasks.fetch_credit_balance(host="fake_host")
    assert "Your remaining account balance is 1000 credits" in capsys.readouterr().out


@patch("httpx.Client.get")
@patch("gpas.client.env.get_access_token")
def test_get_balance_failure(
    mock_token: MagicMock, mock_client_get: MagicMock, capsys: pytest.CaptureFixture
) -> None:
    """Test failure to get the account balance.

    Args:
        mock_token (MagicMock): Mocked `gpas.client.env.get_access_token` method.
        mock_client_get (MagicMock): Mocked `httpx.Client.get` method.
        caplog (pytest.LogCaptureFixture): Pytest fixture to capture log output.
    """
    mock_token.return_value = "fake_token"
    mock_client_get.return_value = httpx.Response(status_code=402)
    tasks.fetch_credit_balance(host="fake_host")
    assert (
        "Your account doesn't have enough credits to fulfil the number of Samples in your Batch"
        in capsys.readouterr().err
    )

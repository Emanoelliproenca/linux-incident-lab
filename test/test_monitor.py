
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from monitor.monitor import check_service


@patch("monitor.monitor.urllib.request.urlopen")
def test_service_available(mock_urlopen):
    response = MagicMock()
    response.status = 200
    mock_urlopen.return_value.__enter__.return_value = response

    assert check_service() is True
    assert mock_urlopen.call_count == 1


@patch("monitor.monitor.time.sleep")
@patch("monitor.monitor.urllib.request.urlopen")
def test_service_unavailable(mock_urlopen, mock_sleep):
    mock_urlopen.side_effect = URLError("Connection refused")

    assert check_service() is False
    assert mock_urlopen.call_count == 3
    assert mock_sleep.call_count == 2



@patch("monitor.monitor.time.sleep")
@patch("monitor.monitor.urllib.request.urlopen")
def test_service_recovers_on_retry(mock_urlopen, mock_sleep):
    response = MagicMock()
    response.__enter__.return_value.status = 200

    mock_urlopen.side_effect = [
        URLError("Temporary failure"),
        response,
    ]

    assert check_service() is True
    assert mock_urlopen.call_count == 2
    assert mock_sleep.call_count == 1

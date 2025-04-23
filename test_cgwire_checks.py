import json
from unittest import TestCase
from unittest.mock import patch, call

import requests

from cgwire_checks import CheckURL


def connection_error(yes, timeout=10):
    raise requests.exceptions.ConnectionError()


class TestCheckURL(TestCase):
    def setUp(self):
        self.t = CheckURL("http://127.0.0.1")
        self.msg_ok = "✅ 01 Check Kitsu /"
        self.msg_ko = "🔥 01 Check Kitsu /"

    def test_init(self):
        assert self.t.base_url == "http://127.0.0.1"
        assert self.t.status == 0
        assert self.t.request is None

        t = CheckURL("http://127.0.0.1:8080")
        assert t.base_url == "http://127.0.0.1:8080"

    def test_check_url_root(self):
        with patch("requests.get") as mock_request:
            mock_request.return_value.status_code = 200
            assert (self.t.check_url("/", self.msg_ok, self.msg_ko)) == self.msg_ok
            assert self.t.status == 0
            mock_request.assert_called_once_with("http://127.0.0.1/", timeout=5)

    def test_check_url_with_502(self):
        with patch("requests.get") as mock_request:
            mock_request.return_value.status_code = 502
            mock_request.return_value.text = "<html>502 Bad Gateway</html>"
            assert (
                self.t.check_url("/api/ko", self.msg_ok, self.msg_ko)
            ) == self.msg_ko + "\n<html>502 Bad Gateway</html>"
            assert self.t.status == 1
            mock_request.assert_called_once_with("http://127.0.0.1/api/ko", timeout=5)

    def test_check_url_with_502_and_json(self):
        def json_patch():
            raise requests.exceptions.JSONDecodeError("JSONDecodeError", "", 0)

        with patch(
            "requests.get",
            **{
                "return_value.status_code": 502,
                "return_value.text": "<html>502 Bad Gateway</html>",
                "return_value.json.side_effect": json_patch,
            },
        ):
            self.t.check_url("/", self.msg_ok, self.msg_ko)
            assert (
                self.t.check_if_error(self.msg_ok, self.msg_ko)
            ) == self.msg_ko + "\n<html>502 Bad Gateway</html>"
            assert (
                self.t.check_login(self.msg_ok, self.msg_ko)
            ) == self.msg_ko + "\n<html>502 Bad Gateway</html>"
            assert (
                self.t.check_bad_login(self.msg_ok, self.msg_ko)
            ) == self.msg_ko + "\n<html>502 Bad Gateway</html>"
            assert (
                self.t.check_zou_version(self.msg_ok, self.msg_ko)
            ) == self.msg_ko + "\n<html>502 Bad Gateway</html>"

    def test_check_url_with_db_error(self):
        msg_db_ko = "{'error': True, 'login': False, 'message': \"Database doesn't seem reachable.\"}"
        with patch("requests.get") as mock_request:
            mock_request.return_value.status_code = 500
            mock_request.return_value.text = msg_db_ko
            assert (
                self.t.check_url("/api/db_ko", self.msg_ok, self.msg_ko)
            ) == self.msg_ko + "\n" + msg_db_ko
            assert self.t.status == 1
            mock_request.assert_called_once_with(
                "http://127.0.0.1/api/db_ko", timeout=5
            )

    def test_check_url_with_http_error(self):
        with patch("requests.get", **{"side_effect": connection_error}) as mock_request:
            assert (self.t.check_url("/", self.msg_ok, self.msg_ko)) == self.msg_ko
            assert self.t.status == 1
            mock_request.assert_called_once_with("http://127.0.0.1/", timeout=5)

        with patch("requests.get") as mock_request:
            mock_request.return_value.status_code = 200
            self.t.check_url("/", self.msg_ok, self.msg_ko)
            assert self.t.status == 1

    def test_check_if_last_request_is_a_kitsu(self):
        self.msg_ok = "✅ 01b Check if it's really a Kitsu"
        self.msg_ko = "🔥 01b Check if it's really a Kitsu"
        with patch(
            "requests.get",
            **{
                "return_value.status_code": 200,
                "return_value.text": """<html>
                <title>Kitsu - Collaboration Platform For Animation Studios</title>
                </html>
                """,
            },
        ):
            self.t.check_url("/", self.msg_ok, self.msg_ko)
            assert (
                self.t.check_if_last_request_is_a_kitsu(
                    self.msg_ok,
                    self.msg_ko,
                )
            ) == self.msg_ok

    def test_check_if_last_request_is_a_kitsu_ko(self):
        self.msg_ok = "✅ 01b Check if it's really a Kitsu"
        self.msg_ko = "🔥 01b Check if it's really a Kitsu"
        with patch(
            "requests.get",
            **{
                "return_value.status_code": 200,
                "return_value.text": """<html>
                <title>Another web page</title>
                </html>
                """,
            },
        ):
            self.t.check_url("/", self.msg_ok, self.msg_ko)
            assert (
                self.t.check_if_last_request_is_a_kitsu(
                    self.msg_ok,
                    self.msg_ko,
                )
            ) == self.msg_ko

    def test_check_if_last_request_is_a_zou(self):
        self.msg_ok = "✅ 02b Check if it's really a Zou"
        self.msg_ko = "🔥 02b Check if it's really a Zou"
        msg_api_ok = '{"api": "Zou", "version": "X.XX.XX"}'

        def json_patch():
            return json.loads(msg_api_ok)

        with patch(
            "requests.get",
            **{
                "return_value.status_code": 200,
                "return_value.text": msg_api_ok,
                "return_value.json.side_effect": json_patch,
            },
        ):
            self.t.check_url("/api", self.msg_ok, self.msg_ko)
            assert (
                self.t.check_if_last_request_is_a_zou(
                    self.msg_ok,
                    self.msg_ko,
                )
            ) == self.msg_ok

    def test_check_if_last_request_is_a_zou_ko(self):
        self.msg_ok = "✅ 02b Check if it's really a Zou"
        self.msg_ko = "🔥 02b Check if it's really a Zou"
        msg_api_ko = '{"api": "NotMine", "version": "X.XX.XX"}'

        def json_patch():
            return json.loads(msg_api_ko)

        with patch(
            "requests.get",
            **{
                "return_value.status_code": 200,
                "return_value.text": msg_api_ko,
                "return_value.json.side_effect": json_patch,
            },
        ):
            self.t.check_url("/api", self.msg_ok, self.msg_ko)
            assert (
                self.t.check_if_last_request_is_a_zou(
                    self.msg_ok,
                    self.msg_ko,
                )
            ) == self.msg_ko

    def test_check_url_with_login_ok(self):
        self.msg_ok = "✅ 01 Check Kitsu auth /api/auth/login"
        self.msg_ko = "🔥 01 Check Kitsu auth /api/auth/login"
        msg_login_ok = '{"login": true}'

        def json_patch():
            return json.loads(msg_login_ok)

        with patch(
            "requests.post",
            **{
                "return_value.status_code": 200,
                "return_value.text": msg_login_ok,
                "return_value.json.side_effect": json_patch,
            },
        ) as mock_request:
            assert (
                self.t.check_url(
                    "/api/auth/login",
                    self.msg_ok,
                    self.msg_ko,
                    {"email": "toto@kitsu", "password": "pass"},
                )
            ) == self.msg_ok
            assert self.t.status == 0
            mock_request.assert_called_once_with(
                "http://127.0.0.1/api/auth/login",
                json={"email": "toto@kitsu", "password": "pass"},
                timeout=5,
            )

            # Check error status
            self.msg_ok = "✅ 02 Check Kitsu auth /api/auth/login (check error status)"
            self.msg_ko = "🔥 02 Check Kitsu auth /api/auth/login (check error status)"
            assert (
                self.t.check_if_error(
                    self.msg_ok,
                    self.msg_ko,
                )
                == self.msg_ok
            )

            # Check login status
            self.msg_ok = "✅ 02 Check Kitsu auth /api/auth/login (check login status)"
            self.msg_ko = "🔥 02 Check Kitsu auth /api/auth/login (check login status)"
            assert (
                self.t.check_login(
                    self.msg_ok,
                    self.msg_ko,
                )
                == self.msg_ok
            )

            self.msg_ok = "✅ 02 Check Kitsu auth /api/auth/login (check login status)"
            self.msg_ko = "🔥 02 Check Kitsu auth /api/auth/login (check login status)"
            assert (
                self.t.check_bad_login(
                    self.msg_ok,
                    self.msg_ko,
                )
                == self.msg_ko
            )

    def test_check_url_with_login_ko(self):
        self.msg_ok = "✅ 01 Check Kitsu auth /api/auth/login"
        self.msg_ko = "🔥 01 Check Kitsu auth /api/auth/login"
        msg_login_ko = '{"error": true}'

        def json_patch():
            data = json.loads(msg_login_ko)
            print(data)
            return data

        with patch(
            "requests.post",
            **{
                "return_value.status_code": 400,
                "return_value.text": msg_login_ko,
                "return_value.json.side_effect": json_patch,
            },
        ) as mock_request:
            assert (
                self.t.check_url(
                    "/api/auth/login",
                    self.msg_ok,
                    self.msg_ko,
                    {"email": "toto@kitsu", "password": "not_the_pass"},
                )
            ) == self.msg_ko + "\n" + msg_login_ko
            assert self.t.status == 1
            mock_request.assert_called_once_with(
                "http://127.0.0.1/api/auth/login",
                json={"email": "toto@kitsu", "password": "not_the_pass"},
                timeout=5,
            )

            # Same but with the wrong login expected
            assert (
                self.t.check_url(
                    "/api/auth/login",
                    self.msg_ok,
                    self.msg_ko,
                    {"email": "toto@kitsu", "password": "not_the_pass"},
                    400,
                )
            ) == self.msg_ok

            # Check error status
            self.msg_ok = "✅ 02 Check Kitsu auth /api/auth/login (check error status)"
            self.msg_ko = "🔥 02 Check Kitsu auth /api/auth/login (check error status)"
            assert (
                self.t.check_if_error(
                    self.msg_ok,
                    self.msg_ko,
                )
                == self.msg_ko + "\n" + msg_login_ko
            )

            # Check login status
            self.msg_ok = "✅ 02 Check Kitsu auth /api/auth/login (check login status)"
            self.msg_ko = "🔥 02 Check Kitsu auth /api/auth/login (check login status)"
            assert (
                self.t.check_login(
                    self.msg_ok,
                    self.msg_ko,
                )
                == self.msg_ko + "\n" + msg_login_ko
            )

            self.msg_ok = "✅ 02 Check Kitsu auth /api/auth/login (check login status)"
            self.msg_ko = "🔥 02 Check Kitsu auth /api/auth/login (check login status)"
            assert (
                self.t.check_bad_login(
                    self.msg_ok,
                    self.msg_ko,
                )
                == self.msg_ok
            )

    def test_check_if_last_request_without_request(self):
        # Kitsu
        self.msg_ok = "✅ 01b Check if it's really a Kitsu"
        self.msg_ko = "🔥 01b Check if it's really a Kitsu"
        assert (
            self.t.check_if_last_request_is_a_kitsu(
                self.msg_ok,
                self.msg_ko,
            )
        ) == self.msg_ko

        # Zou
        self.msg_ok = "✅ 02b Check if it's really a Zou"
        self.msg_ko = "🔥 02b Check if it's really a Zou"

        assert (
            self.t.check_if_last_request_is_a_zou(
                self.msg_ok,
                self.msg_ko,
            )
        ) == self.msg_ko

        # check_if_error
        self.msg_ok = "✅ 02 Check Kitsu auth /api/auth/login (check error status)"
        self.msg_ko = "🔥 02 Check Kitsu auth /api/auth/login (check error status)"
        assert (
            self.t.check_if_error(
                self.msg_ok,
                self.msg_ko,
            )
            == self.msg_ko
        )

        # check_login
        self.msg_ok = "✅ 02 Check Kitsu auth /api/auth/login (check login status)"
        self.msg_ko = "🔥 02 Check Kitsu auth /api/auth/login (check login status)"
        assert (
            self.t.check_login(
                self.msg_ok,
                self.msg_ko,
            )
            == self.msg_ko
        )

        # check_bad_login
        self.msg_ok = "✅ 02 Check Kitsu auth /api/auth/login (check login status)"
        self.msg_ko = "🔥 02 Check Kitsu auth /api/auth/login (check login status)"
        assert (
            self.t.check_bad_login(
                self.msg_ok,
                self.msg_ko,
            )
            == self.msg_ko
        )

        # check_kitsu_version
        self.msg_ok = "✅ 06b Kitsu version 0.17.30 == "
        self.msg_ko = "🔥 06b Kitsu version 0.17.30 != "
        assert (
            self.t.check_kitsu_version(
                self.msg_ok,
                self.msg_ko,
            )
            == self.msg_ko
        )

        # check_kitsu_version
        self.msg_ok = "✅ 07b Zou version 0.17.38 == "
        self.msg_ko = "🔥 07b Zou version 0.17.38 != "
        assert (
            self.t.check_zou_version(
                self.msg_ok,
                self.msg_ko,
            )
            == self.msg_ko
        )

    def test_check_if_i_can_get_kitsu_version(self):
        with patch(
            "requests.get",
            **{
                "return_value.status_code": 200,
                "return_value.text": "0.17.30\n",
            },
        ):
            self.t.check_url("/.version.txt", self.msg_ok, self.msg_ko)
        self.t.kitsu_version = "0.17.30"
        self.msg_ok = "✅ 06a Kitsu version 0.17.30 == "
        self.msg_ko = "🔥 06a Kitsu version 0.17.30 != "
        assert (
            self.t.check_kitsu_version(
                self.msg_ok,
                self.msg_ko,
            )
        ) == self.msg_ok + "0.17.30"

    def test_check_if_i_can_get_bad_kitsu_version(self):
        with patch(
            "requests.get",
            **{
                "return_value.status_code": 200,
                "return_value.text": "0.17.30\n",
            },
        ):
            self.t.check_url("/.version.txt", self.msg_ok, self.msg_ko)
        self.t.kitsu_version = "0.12.13"
        self.msg_ok = "✅ 06a Kitsu version 0.12.13 == "
        self.msg_ko = "🔥 06a Kitsu version 0.12.13 != "
        assert (
            self.t.check_kitsu_version(
                self.msg_ok,
                self.msg_ko,
            )
        ) == self.msg_ko + "\n" + "0.17.30" + "\n"

    def test_check_if_i_can_get_zou_version(self):
        msg_api_ok = '{"api": "Zou", "version": "0.17.30"}'

        def json_patch():
            return json.loads(msg_api_ok)

        with patch(
            "requests.get",
            **{
                "return_value.status_code": 200,
                "return_value.text": msg_api_ok,
                "return_value.json.side_effect": json_patch,
            },
        ):
            self.t.check_url("/.version.txt", self.msg_ok, self.msg_ko)
        self.t.zou_version = "0.17.30"
        self.msg_ok = "✅ 06a Kitsu version 0.17.30 == "
        self.msg_ko = "🔥 06a Kitsu version 0.17.30 != "
        assert (
            self.t.check_zou_version(
                self.msg_ok,
                self.msg_ko,
            )
        ) == self.msg_ok + "0.17.30"

    def test_check_if_i_can_get_bad_zou_version(self):
        msg_api_ok = '{"api": "Zou", "version": "0.17.41"}'

        def json_patch():
            return json.loads(msg_api_ok)

        with patch(
            "requests.get",
            **{
                "return_value.status_code": 200,
                "return_value.text": msg_api_ok,
                "return_value.json.side_effect": json_patch,
            },
        ):
            self.t.check_url("/.version.txt", self.msg_ok, self.msg_ko)
        self.t.zou_version = "0.17.30"
        self.msg_ok = "✅ 06a Kitsu version 0.17.30 == "
        self.msg_ko = "🔥 06a Kitsu version 0.17.30 != "
        assert (
            self.t.check_zou_version(
                self.msg_ok,
                self.msg_ko,
            )
        ) == self.msg_ko + "\n0.17.41"

    def test_wait_success_first_try(self):
        """Test wait() method when connection succeeds on first try."""
        with patch("requests.get") as mock_request:
            mock_request.return_value.status_code = 200
            with patch("time.sleep") as mock_sleep:  # Mock sleep to speed up test
                result = self.t.wait("/api")
                assert result is True
                mock_request.assert_called_once_with("http://127.0.0.1/api", timeout=5)
                mock_sleep.assert_not_called()  # Sleep should not be called on first success

    def test_wait_success_after_retry(self):
        """Test wait() method when connection succeeds after a retry."""
        # Create a mock that fails once then succeeds
        mock_responses = [
            requests.exceptions.ConnectionError("Connection refused"),
            requests.exceptions.ReadTimeout(
                "Server did not respond within the specified timeout"
            ),
            type("MockResponse", (), {"status_code": 200})(),
        ]

        with patch("requests.get", side_effect=mock_responses) as mock_request:
            with patch("time.sleep") as mock_sleep:
                with patch("builtins.print") as mock_print:
                    self.t.retry = 5
                    result = self.t.wait("/api")
                    assert result is True
                    assert mock_request.call_count == 3
                    mock_sleep.assert_has_calls(
                        [call(1), call(1)]
                    )  # Sleep should be called twice
                    # Check that dots were printed
                    mock_print.assert_any_call(".", end="", flush=True)
                    mock_print.assert_any_call(".", end="", flush=True)
                    mock_print.assert_any_call("")  # Empty line after success

    def test_wait_always_fail(self):
        """Test wait() method when connection never succeeds."""
        # Create a mock that fails once then succeeds
        mock_responses = [
            requests.exceptions.ConnectionError("Connection refused"),
            requests.exceptions.ConnectionError("Connection refused"),
            requests.exceptions.ReadTimeout(
                "Server did not respond within the specified timeout"
            ),
            requests.exceptions.ReadTimeout(
                "Server did not respond within the specified timeout"
            ),
            requests.exceptions.ReadTimeout(
                "Server did not respond within the specified timeout"
            ),
        ]

        with patch("requests.get", side_effect=mock_responses) as mock_request:
            with patch("time.sleep") as mock_sleep:
                with patch("builtins.print") as mock_print:
                    self.t.retry = 3
                    self.t.sleep = 2
                    result = self.t.wait("/api")
                    assert result is None
                    assert mock_request.call_count == 3
                    mock_sleep.assert_has_calls(
                        [call(2), call(2), call(2)]
                    )  # Sleep should be called three times for 2 seconds
                    # Check that dots were printed
                    mock_print.assert_any_call(".", end="", flush=True)
                    mock_print.assert_any_call(".", end="", flush=True)
                    mock_print.assert_any_call(".", end="", flush=True)

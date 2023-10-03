#!/usr/bin/env python
import os
import sys

import requests


class CheckURL:
    def __init__(self, base_url):
        self.base_url = base_url
        self.status = 0
        self.request = None
        self.kitsu_version = None
        self.zou_version = None

    def check_url(self, url, message_ok, message_ko, data=None, error_code=200):
        try:
            if data:
                self.request = requests.post(f"{self.base_url}{url}", json=data)
            else:
                self.request = requests.get(f"{self.base_url}{url}")

            if self.request.status_code == error_code:
                return message_ok
            else:
                self.status = 1
                return message_ko + "\n" + self.request.text
        except requests.exceptions.ConnectionError:
            self.status = 1
            return message_ko

    def check_if_last_request_is_a_kitsu(self, message_ok, message_ko):
        if self.request and "Kitsu" in self.request.text:
            return message_ok
        else:
            return message_ko

    def check_if_last_request_is_a_zou(self, message_ok, message_ko):
        api = ""
        if self.request:
            api = self.request.json().get("api", "")
        if api == "Zou":
            return message_ok
        else:
            return message_ko

    def check_if_error(self, message_ok, message_ko):
        if self.request is None:
            return message_ko
        error = self.request.json().get("error", False)
        if error:
            return message_ko + "\n" + self.request.text
        else:
            return message_ok

    def check_login(self, message_ok, message_ko):
        if self.request is None:
            return message_ko
        if self.request.json().get("login", False):
            return message_ok
        else:
            return message_ko + "\n" + self.request.text

    def check_bad_login(self, message_ok, message_ko):
        if self.request is None:
            return message_ko
        if self.request.json().get("login", False):
            return message_ko
        else:
            return message_ok

    def check_kitsu_version(self, message_ok, message_ko):
        if self.request is None:
            return message_ko
        if self.request.text.rstrip() == self.kitsu_version:
            return message_ok + self.kitsu_version
        else:
            return message_ko + "\n" + self.request.text

    def check_zou_version(self, message_ok, message_ko):
        if self.request is None:
            return message_ko
        if self.request.json().get("version") == self.zou_version:
            return message_ok + self.zou_version
        else:
            return message_ko + "\n" + self.request.json().get("version")


if __name__ == "__main__":  # pragma: nocover
    print(80 * "#")
    t = CheckURL(os.getenv("KITSU_URL", "http://127.0.0.1"))
    t.kitsu_version = os.getenv("KITSU_VERSION", None)
    t.zou_version = os.getenv("ZOU_VERSION", None)
    # Check Kitsu
    print(
        t.check_url(
            "/",
            "✅ 01a Check Kitsu /",
            "🔥 01a Check Kitsu /",
        )
    )
    print(
        t.check_if_last_request_is_a_kitsu(
            "✅ 01b  Check if it's realy a Kitsu",
            "🔥 01b  Check if it's realy a Kitsu",
        )
    )

    # Check Kitsu API (Zou)
    print(
        t.check_url(
            "/api",
            "✅ 02a Check Kitsu API /api",
            "🔥 02a Check Kitsu API /api",
        )
    )
    print(
        t.check_if_last_request_is_a_zou(
            "✅ 02b  Check if it's realy a Kitsu API",
            "🔥 02b  Check if it's realy a Kitsu API",
        )
    )

    # Check good login
    print(
        t.check_url(
            "/api/auth/login",
            "✅ 03a Check login /api/auth/login",
            "🔥 03a Check login /api/auth/login",
            {"email": "admin@example.com", "password": "mysecretpassword"},
        )
    )
    print(
        t.check_if_error(
            "✅ 03b  Check login /api/auth/login (check error status)",
            "🔥 03b  Check login /api/auth/login (check error status)",
        )
    )
    print(
        t.check_login(
            "✅ 03c  Check login /api/auth/login (check login status)",
            "🔥 03c  Check login /api/auth/login (check login status)",
        )
    )

    # Check bad pass
    print(
        t.check_url(
            "/api/auth/login",
            "✅ 04a Check login /api/auth/login",
            "🔥 04a Check login /api/auth/login",
            {"email": "admin@example.com", "password": "badpass"},
            400,
        )
    )
    print(
        t.check_bad_login(
            "✅ 04b  Check login /api/auth/login (check login status)",
            "🔥 04b  Check login /api/auth/login (check login status)",
        )
    )

    # Check bad account
    print(
        t.check_url(
            "/api/auth/login",
            "✅ 05a Check login /api/auth/login",
            "🔥 05a Check login /api/auth/login",
            {"email": "not-a-user@example.com", "password": "badpass"},
            400,
        )
    )
    print(
        t.check_bad_login(
            "✅ 05b  Check login /api/auth/login (check login status)",
            "🔥 05b  Check login /api/auth/login (check login status)",
        )
    )

    # Check Kistu version
    print(
        t.check_url(
            "/.version.txt",
            "✅ 06a Kitsu version",
            "🔥 06a Kitsu version",
        )
    )
    if t.kitsu_version:
        print(
            t.check_kitsu_version(
                f"✅ 06b Kitsu version {t.kitsu_version} == ",
                f"🔥 06b Kitsu {t.kitsu_version} != ",
            )
        )

    # Check Zou version
    print(
        t.check_url(
            "/api",
            "✅ 07a Zou version",
            "🔥 07a Zou version",
        )
    )
    if t.zou_version:
        print(
            t.check_zou_version(
                f"✅ 07b Zou version {t.zou_version} == ",
                f"🔥 07b Zou {t.zou_version} != ",
            )
        )

    # Show status and exit with error code
    print(f"Error code: {t.status}")
    sys.exit(t.status)

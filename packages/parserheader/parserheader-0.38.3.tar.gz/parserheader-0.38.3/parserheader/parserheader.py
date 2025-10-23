#!/usr/bin/env python3

import re
import sys
from pprint import pprint

try:
    import click
except ImportError:
    click = None

try:
    from pause import pause
except ImportError:
    def pause(*args, **kwargs):
        input("Press Enter to continue...")

try:
    from pydebugger.debug import debug
except ImportError:
    def debug(*args, **kwargs):
        for k, v in kwargs.items():
            print(f"{k} = {v} ({type(v)})")


class ParserHeader:
    """Parser for HTTP headers with case-insensitive key handling and convenient access."""

    _default_headers = {}

    def __init__(self, headers=None, **kwargs):
        self._headers = self.parse_headers(headers, **kwargs)
        for key, value in self._headers.items():
            normalized_key = self._normalize_key(key)
            if normalized_key.lower() != 'user-agent':
                setattr(self, normalized_key, value)
                setattr(self, normalized_key.lower(), value)

    def __str__(self):
        return str(self._headers)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._headers})"

    def __getitem__(self, key):
        key_lower = key.lower()
        for k in self._headers:
            if k.lower() == key_lower:
                return self._headers[k]
        raise KeyError(key)

    def __setitem__(self, key, value):
        key_lower = key.lower()
        for k in list(self._headers.keys()):
            if k.lower() == key_lower:
                del self._headers[k]
                self._headers[self._normalize_key(key)] = value
                return
        self._headers[self._normalize_key(key)] = value

    def __delitem__(self, key):
        key_lower = key.lower()
        for k in list(self._headers.keys()):
            if k.lower() == key_lower:
                del self._headers[k]
                return
        raise KeyError(key)

    def __len__(self):
        return len(self._headers)

    def __contains__(self, key):
        key_lower = key.lower()
        return any(k.lower() == key_lower for k in self._headers)

    def __add__(self, other):
        if isinstance(other, dict):
            new_headers = self._headers.copy()
            for k, v in other.items():
                new_headers[self._normalize_key(k)] = v
            return ParserHeader(new_headers)
        elif isinstance(other, ParserHeader):
            return self + other._headers
        else:
            raise TypeError("Can only add dict or ParserHeader")

    def __iadd__(self, other):
        if isinstance(other, dict):
            for k, v in other.items():
                self[k] = v
        elif isinstance(other, ParserHeader):
            self += other._headers
        else:
            raise TypeError("Can only add dict or ParserHeader")
        return self

    def __call__(self, **kwargs):
        for k, v in kwargs.items():
            self[k] = v
        return self._headers

    @staticmethod
    def _normalize_key(key):
        """Convert key like 'user_agent' or 'user-agent' to 'User-Agent'."""
        parts = re.split(r"[-_]", str(key))
        return "-".join(part.title() for part in parts)

    @classmethod
    def parse_headers(cls, headers_input=None, show_empty=False, **kwargs):
        """Parse headers from string, dict, or use defaults."""
        if headers_input is None:
            headers_input = cls._default_headers

        if isinstance(headers_input, dict):
            result = {cls._normalize_key(k): v for k, v in headers_input.items()}
        elif isinstance(headers_input, (str, bytes)):
            if isinstance(headers_input, bytes):
                headers_input = headers_input.decode('utf-8')
            result = {}
            lines = [line.strip() for line in re.split(r"[\r\n]+", headers_input) if line.strip()]
            for line in lines:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                key = cls._normalize_key(key.strip())
                value = value.strip()
                if value in ("''", '""'):
                    value = ""
                if value or show_empty:
                    result[key] = value
        else:
            raise TypeError("headers_input must be str, bytes, or dict")

        # Apply kwargs
        for k, v in kwargs.items():
            result[cls._normalize_key(k)] = v

        return result

    def set_cookies(self, cookies_input, dont_format=False, **kwargs):
        """Parse or format cookies from string or dict."""
        if isinstance(cookies_input, str):
            cookie_dict = {}
            for part in cookies_input.split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    cookie_dict[k.strip()] = v.strip()
            cookie_str = cookies_input
        elif isinstance(cookies_input, dict):
            cookie_dict = cookies_input
            cookie_str = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
        else:
            raise TypeError("cookies_input must be str or dict")

        # Apply kwargs
        for k, v in kwargs.items():
            key = k if dont_format else k.replace("_", "-")
            cookie_dict[key] = v

        return cookie_dict, cookie_str

    def get_user_agent(self):
        return self.get("User-Agent", "")

    def set_user_agent(self, ua):
        self["User-Agent"] = ua

    user_agent = property(get_user_agent, set_user_agent)

    # Aliases for backward compatibility
    UserAgent = useragent = User_Agent = user_agent

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return self._headers.keys()

    def values(self):
        return self._headers.values()

    def items(self):
        return self._headers.items()


# Aliases
parserheader = ParserHeader
Parserheader = ParserHeader
parserHeader = ParserHeader
Parser = ParserHeader


# ========================
# CLI / Demo Section
# ========================
if __name__ == "__main__":
    # Try to get input from clipboard or argv
    data = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "c":
            try:
                import clipboard
                data = clipboard.paste()
            except ImportError:
                print("clipboard module not installed", file=sys.stderr)
                sys.exit(1)
        else:
            data = sys.argv[1]

    # Fallback example
    if data is None:
        data = """ec-ch-ua: "Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
sec-fetch-site: same-origin
sec-fetch-mode: navigate
sec-fetch-user: ?1
sec-fetch-dest: document
referer: https://dsvplay.com/d/if3q2cyva4yz
accept-language: en-US,en;q=0.9
cookie: lang=1
priority: u=0, i
accept-encoding: gzip, deflate, br"""

    try:
        from jsoncolor import jprint
    except ImportError:
        def jprint(obj):
            pprint(obj)

    parser = ParserHeader(data)
    jprint(parser())

    # Optional: print user-agent
    if click:
        click.secho(f"User-Agent: {parser.user_agent}", fg="yellow")


# FUCK ERROR:
"""╭────────────────────────────────────────────────────────────────────────────────────────────────────────────────── Traceback (most recent call last) ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ C:\PROJECTS\parserheader\parserheader\parserheader.py:239 in <module>                                                                                                                                                                                                 │
│                                                                                                                                                                                                                                                                       │
│   236 │   │   def jprint(obj):                                                                                                                                                                                                                                        │
│   237 │   │   │   pprint(obj)                                                                                                                                                                                                                                         │
│   238 │                                                                                                                                                                                                                                                               │
│ ❱ 239 │   parser = ParserHeader(data)                                                                                                                                                                                                                                 │
│   240 │   jprint(parser())                                                                                                                                                                                                                                            │
│   241 │                                                                                                                                                                                                                                                               │
│   242 │   # Optional: print user-agent                                                                                                                                                                                                                                │
│                                                                                                                                                                                                                                                                       │
│ C:\PROJECTS\parserheader\parserheader\parserheader.py:33 in __init__                                                                                                                                                                                                  │
│                                                                                                                                                                                                                                                                       │
│    30 │                                                                                                                                                                                                                                                               │
│    31 │   def __init__(self, headers=None, **kwargs):                                                                                                                                                                                                                 │
│    32 │   │   # Initialize with provided headers or empty dict                                                                                                                                                                                                        │
│ ❱  33 │   │   self._headers = dict(headers) if headers else dict(self._default_headers)                                                                                                                                                                               │
│    34 │   │   self._headers = self.parse_headers(self._headers, **kwargs)                                                                                                                                                                                             │
│    35 │   │                                                                                                                                                                                                                                                           │
│    36 │   │   # Create attributes for each header (case-insensitive)                                                                                                                                                                                                  │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
ValueError: dictionary update sequence element #0 has length 1; 2 is required"""
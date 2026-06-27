"""util.validators: pure-function tests."""

from __future__ import annotations

import pytest

from pihole_mcp.util.validators import (
    cap_duration,
    is_fqdn,
    is_http_url,
    is_safe_config_path,
    normalize_mac,
)


@pytest.mark.parametrize(
    "domain,expected",
    [
        ("example.com", True),
        ("sub.example.co.uk", True),
        ("a.b.c.d.e", True),
        ("example.com.", True),
        ("no-dot", True),
        ("*.example.com", False),
        ("a" * 64 + ".com", False),
        ("a" * 254, False),
        ("", False),
        ("http://example.com", False),
        ("white space.com", False),
    ],
)
def test_is_fqdn(domain, expected):
    assert is_fqdn(domain) is expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("http://example.com", True),
        ("https://example.com/path?x=1", True),
        ("ftp://example.com", False),
        ("file:///etc/passwd", False),
        ("javascript:alert(1)", False),
        ("not a url", False),
        ("", False),
    ],
)
def test_is_http_url(url, expected):
    assert is_http_url(url) is expected


def test_normalize_mac_colon():
    assert normalize_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"


def test_normalize_mac_dash():
    assert normalize_mac("aa-bb-cc-dd-ee-ff") == "aa:bb:cc:dd:ee:ff"


def test_normalize_mac_bare():
    assert normalize_mac("AABBCCDDEEFF") == "aa:bb:cc:dd:ee:ff"


@pytest.mark.parametrize("bad", ["", "AA:BB", "GG:HH:II:JJ:KK:LL", "aabbccddeefff"])
def test_normalize_mac_invalid(bad):
    with pytest.raises(ValueError):
        normalize_mac(bad)


def test_cap_duration_caps_at_max():
    assert cap_duration(100000, 86400) == 86400


def test_cap_duration_passes_through():
    assert cap_duration(60, 86400) == 60


def test_cap_duration_rejects_negative():
    with pytest.raises(ValueError):
        cap_duration(-1, 86400)


@pytest.mark.parametrize(
    "path,expected",
    [
        ("dns.upstreams", True),
        ("misc.foo", True),
        ("webserver.api.app_pwhash", False),
        ("database.queries", False),
        ("dns.port", False),
        ("files.gravity", False),
        ("debug.x", False),
        ("", False),
    ],
)
def test_is_safe_config_path(path, expected):
    assert is_safe_config_path(path) is expected

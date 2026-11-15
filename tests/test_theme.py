"""Theme palettes and the CSS the interface injects on top of Streamlit."""

from __future__ import annotations

import re

import pytest

from app import theme


def test_palettes_are_symmetric() -> None:
    assert set(theme.PALETTE) == set(theme.LANGS)
    keys = set(theme.PALETTE["light"])
    for name in theme.LANGS:
        assert set(theme.PALETTE[name]) == keys


@pytest.mark.parametrize("name", theme.LANGS)
def test_every_placeholder_is_substituted(name: str) -> None:
    css = theme.css(name, force=True)
    assert "$" not in css
    assert css.startswith("<style>")
    assert css.endswith("</style>")


@pytest.mark.parametrize("name", theme.LANGS)
def test_every_variable_used_is_defined(name: str) -> None:
    """An undefined ``var()`` silently drops the declaration, so check them all."""
    css = theme.css(name, force=True)
    used = set(re.findall(r"var\((--kib-[a-z-]+)\)", css))
    defined = set(re.findall(r"(--kib-[a-z-]+):", css))
    assert used
    assert used <= defined


@pytest.mark.parametrize("name", theme.LANGS)
def test_scheme_matches_the_palette(name: str) -> None:
    css = theme.css(name, force=True)
    assert f"color-scheme: {theme.PALETTE[name]['scheme']}" in css
    assert f"--kib-app: {theme.PALETTE[name]['app']}" in css


def test_widget_rules_appear_only_when_forced() -> None:
    native = theme.css("dark")
    forced = theme.css("dark", force=True)
    assert 'data-testid="stFileUploaderDropzone"' not in native
    assert 'data-testid="stFileUploaderDropzone"' in forced
    assert ".kib-table" in native
    assert "stAppDeployButton" in native


def test_badges_stay_readable_in_both_palettes() -> None:
    for name in theme.LANGS:
        css = theme.css(name)
        assert "color: #ffffff !important" in css
        for level in ("p1", "p2", "p3", "p4"):
            assert f".kib-badge.{level}" in css


def test_active_theme_follows_the_system_choice() -> None:
    assert theme.active_theme("system", "dark") == "dark"
    assert theme.active_theme("system", "light") == "light"
    assert theme.active_theme("dark", "light") == "dark"
    assert theme.active_theme("light", "dark") == "light"


def test_unknown_theme_falls_back_to_light() -> None:
    assert theme.active_theme("purple", "dark") == "light"
    assert theme.palette("purple") == theme.PALETTE["light"]
    assert theme.palette("dark") == theme.PALETTE["dark"]


@pytest.mark.parametrize(
    ("reported", "expected"),
    [
        ({"type": "dark"}, "dark"),
        ({"type": "light"}, "light"),
        ({}, "light"),
        ({"type": "contrast"}, "light"),
    ],
)
def test_system_theme_reads_the_streamlit_context(
    monkeypatch: pytest.MonkeyPatch, reported: dict[str, str], expected: str
) -> None:
    monkeypatch.setattr(theme.st, "context", type("Ctx", (), {"theme": reported})())
    assert theme.system_theme() == expected


def test_system_theme_survives_a_broken_context(monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom:
        @property
        def theme(self) -> None:
            raise RuntimeError("no context outside a run")

    monkeypatch.setattr(theme.st, "context", Boom())
    assert theme.system_theme() == "light"

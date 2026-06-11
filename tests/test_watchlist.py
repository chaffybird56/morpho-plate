from pathlib import Path

import pytest

from morphoplate.watchlist import Watchlist, normalize_plate


def test_normalize_plate_strips_separators():
    assert normalize_plate("ab c-123") == "ABC123"


def test_watchlist_from_file(tmp_path: Path):
    path = tmp_path / "plates.txt"
    path.write_text("# demo\nABC123\nxy-z789\n", encoding="utf-8")

    wl = Watchlist.from_file(path)
    assert wl.contains("abc 123")
    assert wl.contains("XYZ789")
    assert not wl.contains("NOPE")


def test_watchlist_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        Watchlist.from_file(tmp_path / "missing.txt")

import time
import pytest
from roblox_panel.storage import Storage


@pytest.fixture
def store(tmp_path):
    db_file = tmp_path / "test_panel.db"
    return Storage(db_path=str(db_file))


def test_api_key_persistence(store):
    assert store.get_api_key() is None
    store.set_api_key("rbx-secret-key-12345")
    assert store.get_api_key() == "rbx-secret-key-12345"


def test_add_and_list_universes(store):
    store.add_universe(12345678, name="Obby Legends")
    store.add_universe(87654321, name="Tycoon City", alias="tycoon")

    universes = store.get_universes()
    assert len(universes) == 2

    u1 = next(u for u in universes if u["id"] == 12345678)
    assert u1["name"] == "Obby Legends"
    assert u1["alias"] is None

    u2 = next(u for u in universes if u["id"] == 87654321)
    assert u2["alias"] == "tycoon"


def test_add_universe_duplicate_updates_metadata(store):
    store.add_universe(123, name="Old Name", alias="old")
    store.add_universe(123, name="New Name", alias="new")

    universes = store.get_universes()
    assert len(universes) == 1
    assert universes[0]["name"] == "New Name"
    assert universes[0]["alias"] == "new"


def test_remove_universe(store):
    store.add_universe(111, "Test Game")
    assert len(store.get_universes()) == 1

    store.remove_universe(111)
    assert len(store.get_universes()) == 0


def test_active_universe_toggle(store):
    store.add_universe(100, "Game A")
    store.add_universe(200, "Game B")

    # default should pick the first or None if unset
    store.set_active_universe(200)
    assert store.get_active_universe_id() == 200

    store.set_active_universe(100)
    assert store.get_active_universe_id() == 100


def test_metrics_cache_save_and_fetch(store):
    sample_payload = {
        "playing": 428,
        "visits": 1520300,
        "favorites": 8900,
        "servers": [{"id": "job-1", "players": 18}, {"id": "job-2", "players": 22}],
    }

    store.cache_metrics(555, sample_payload)
    cached = store.get_cached_metrics(555)

    assert cached is not None
    assert cached["playing"] == 428
    assert len(cached["servers"]) == 2
    # print(f"cached at: {cached.get('_cached_at')}")


def test_metrics_cache_missing(store):
    assert store.get_cached_metrics(9999999) is None

from ghoshell_common.contracts.storage import MemoryStorage


def test_memory_storage_baseline():
    storage = MemoryStorage("a")
    assert not storage.exists("foo")
    storage.put("foo", "bar".encode())
    assert storage.exists("foo")
    assert storage.get("foo") == "bar".encode()

    sub = storage.sub_storage("bar")
    assert not sub.exists("foo")

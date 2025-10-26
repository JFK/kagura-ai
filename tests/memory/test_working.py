"""Tests for WorkingMemory."""


from kagura.core.memory.working import WorkingMemory


def test_working_memory_basic():
    """Test basic set/get operations."""
    memory = WorkingMemory()

    memory.set("key1", "value1")
    assert memory.get("key1") == "value1"


def test_working_memory_default():
    """Test get with default value."""
    memory = WorkingMemory()

    assert memory.get("nonexistent", "default") == "default"
    assert memory.get("nonexistent") is None


def test_working_memory_has():
    """Test has() method."""
    memory = WorkingMemory()

    memory.set("key1", "value1")
    assert memory.has("key1") is True
    assert memory.has("nonexistent") is False


def test_working_memory_delete():
    """Test delete operation."""
    memory = WorkingMemory()

    memory.set("key1", "value1")
    assert memory.has("key1") is True

    memory.delete("key1")
    assert memory.has("key1") is False


def test_working_memory_clear():
    """Test clear all data."""
    memory = WorkingMemory()

    memory.set("key1", "value1")
    memory.set("key2", "value2")
    assert len(memory) == 2

    memory.clear()
    assert len(memory) == 0


def test_working_memory_keys():
    """Test keys() method."""
    memory = WorkingMemory()

    memory.set("key1", "value1")
    memory.set("key2", "value2")

    keys = memory.keys()
    assert "key1" in keys
    assert "key2" in keys
    assert len(keys) == 2


def test_working_memory_complex_values():
    """Test storing complex data types."""
    memory = WorkingMemory()

    # Store dict
    memory.set("dict", {"a": 1, "b": 2})
    assert memory.get("dict") == {"a": 1, "b": 2}

    # Store list
    memory.set("list", [1, 2, 3])
    assert memory.get("list") == [1, 2, 3]

    # Store object
    class TestObj:
        pass

    obj = TestObj()
    memory.set("obj", obj)
    assert memory.get("obj") is obj


def test_working_memory_to_dict():
    """Test export to dictionary."""
    memory = WorkingMemory()

    memory.set("key1", "value1")
    memory.set("key2", "value2")

    export = memory.to_dict()
    assert "data" in export
    assert "access_log" in export
    assert export["data"]["key1"] == "value1"
    assert export["data"]["key2"] == "value2"


def test_working_memory_len():
    """Test __len__ method."""
    memory = WorkingMemory()

    assert len(memory) == 0

    memory.set("key1", "value1")
    assert len(memory) == 1

    memory.set("key2", "value2")
    assert len(memory) == 2


def test_working_memory_repr():
    """Test string representation."""
    memory = WorkingMemory()
    memory.set("key1", "value1")

    repr_str = repr(memory)
    assert "WorkingMemory" in repr_str
    assert "items=1" in repr_str


def test_working_memory_access_log():
    """Test access logging."""
    memory = WorkingMemory()

    memory.set("key1", "value1")
    export1 = memory.to_dict()
    timestamp1 = export1["access_log"]["key1"]

    # Access the key
    memory.get("key1")
    export2 = memory.to_dict()
    timestamp2 = export2["access_log"]["key1"]

    # Timestamp should be updated
    assert timestamp2 >= timestamp1

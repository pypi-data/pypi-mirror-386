"""Smoke tests for BearBase MVP functionality."""

from pathlib import Path

import pytest

from bear_dereth.datastore import BearBase, Columns
from bear_dereth.query import query


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database file path."""
    return tmp_path / "test.json"


@pytest.fixture
def memory_db() -> BearBase:
    """Create an in-memory database for testing."""
    return BearBase(storage="memory")


def test_create_table_and_insert(memory_db: BearBase):
    """Test creating a table and inserting records."""
    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="email", type="str", nullable=True),
        ],
    )

    users = memory_db.table("users")
    users.insert(id=1, name="Bear")
    users.insert(id=2, name="Shannon", email="shannon@example.com")

    assert len(users) == 2


def test_insert_dict_style(memory_db: BearBase):
    """Test inserting with dict syntax."""
    memory_db.create_table(
        "posts",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="title", type="str"),
        ],
    )

    posts = memory_db.table("posts")
    posts.insert({"id": 1, "title": "First Post"})

    assert len(posts) == 1


def test_all_records(memory_db: BearBase):
    """Test retrieving all records."""
    memory_db.create_table(
        "items",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    items = memory_db.table("items")
    items.insert(id=1, name="Item 1")
    items.insert(id=2, name="Item 2")
    items.insert(id=3, name="Item 3")

    all_items = items.all()
    assert len(all_items) == 3


def test_get_by_primary_key(memory_db: BearBase):
    """Test getting a record by primary key."""
    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    users = memory_db.table("users")
    users.insert(id=1, name="Bear")
    users.insert(id=2, name="Shannon")

    bear = users.get(id=1).first()
    assert bear is not None
    assert bear["name"] == "Bear"


def test_search_with_query(memory_db: BearBase):
    """Test searching with QueryMapping."""
    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="age", type="int"),
        ],
    )

    users = memory_db.table("users")
    users.insert(id=1, name="Bear", age=30)
    users.insert(id=2, name="Shannon", age=25)
    users.insert(id=3, name="Claude", age=35)

    q = query("mapping")()
    results = users.search(q.age > 28).all()

    assert len(results) == 2
    names = {r["name"] for r in results}
    assert names == {"Bear", "Claude"}


def test_validation_unknown_field(memory_db: BearBase):
    """Test that unknown fields are rejected."""
    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    users = memory_db.table("users")

    with pytest.raises(ValueError, match="Unknown fields"):
        users.insert(id=1, name="Bear", invalid_field="oops")


def test_validation_missing_required_field(memory_db: BearBase):
    """Test that missing required fields are rejected."""
    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    users = memory_db.table("users")

    with pytest.raises(ValueError, match="Missing required fields"):
        users.insert(id=1)


def test_insert_without_schema_fails(memory_db: BearBase):
    """Test that inserting without creating table fails."""
    with pytest.raises(ValueError, match="does not exist"):
        memory_db.table("users")


def test_persistence_json(temp_db_path: Path):
    """Test that data persists across database instances."""
    db1: BearBase = BearBase(str(temp_db_path), storage="json")
    db1.create_table(
        name="users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    db1.insert(id=1, name="Bear")
    db1.close()

    db2 = BearBase(str(temp_db_path), storage="json")
    users2 = db2.table("users")
    all_users = users2.all()

    assert len(all_users) == 1
    assert all_users[0]["name"] == "Bear"
    db2.close()

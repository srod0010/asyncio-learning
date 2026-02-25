"""
Dependency Injection (DI) in Python — one file demo

DI = pass dependencies in (instead of hardcoding them inside your class).

This gives you:
- Flexibility: swap implementations (MySQL vs Postgres) without changing core logic
- Testability: inject a fake/mock dependency for fast, isolated tests
- Cleaner design: your service depends on an interface/contract, not a concrete class

This script shows:
1) WITHOUT DI (tight coupling): UserService creates MySQLDatabase itself
2) WITH DI (loose coupling): UserService receives a Database implementation
3) Testing becomes easy: inject FakeDatabase
"""

from __future__ import annotations


# ---------------------------------------------------------------------
# 1) WITHOUT DI (tight coupling)
# ---------------------------------------------------------------------
class MySQLDatabase:
    def save(self, data: dict) -> None:
        print(f"Saving {data} to MySQL")


class UserServiceTightCoupling:
    def __init__(self) -> None:
        # ❌ Hard-coded dependency:
        # This service is now "stuck" with MySQLDatabase unless we edit this class.
        self.db = MySQLDatabase()

    def create_user(self, name: str) -> None:
        self.db.save({"name": name})


# ---------------------------------------------------------------------
# 2) WITH DI (loose coupling)
#    Define an interface/contract for what we need from a DB.
# ---------------------------------------------------------------------
class Database:
    """
    "Interface" / contract:
    Any database we inject must implement save(data).
    (In real projects you might use abc.ABC or typing.Protocol.)
    """
    def save(self, data: dict) -> None:
        raise NotImplementedError


class MySQLDatabaseDI(Database):
    def save(self, data: dict) -> None:
        print(f"Saving {data} to MySQL")


class PostgresDatabaseDI(Database):
    def save(self, data: dict) -> None:
        print(f"Saving {data} to PostgreSQL")


class UserService:
    def __init__(self, db: Database) -> None:
        # ✅ Dependency is injected from the outside.
        # The service only cares that "db" supports .save(...)
        self.db = db

    def create_user(self, name: str) -> None:
        # Core logic stays the same no matter which DB implementation we inject.
        self.db.save({"name": name})


# ---------------------------------------------------------------------
# 3) TESTING WITH DI (mock/fake dependency)
# ---------------------------------------------------------------------
class FakeDatabase(Database):
    """
    A fake DB for tests:
    - No real database
    - Just stores what was "saved" in memory
    """
    def __init__(self) -> None:
        self.storage: list[dict] = []

    def save(self, data: dict) -> None:
        self.storage.append(data)


# ---------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("\n--- WITHOUT DI (tight coupling) ---")
    tight = UserServiceTightCoupling()
    tight.create_user("Alice")
    # If you want Postgres here, you must edit UserServiceTightCoupling's code.

    print("\n--- WITH DI (loose coupling): swap implementations easily ---")
    mysql_service = UserService(MySQLDatabaseDI())
    mysql_service.create_user("Alice")

    pg_service = UserService(PostgresDatabaseDI())
    pg_service.create_user("Bob")
    # Notice: UserService didn't change at all. Only what we injected changed.

    print("\n--- Testing with DI (inject fake DB) ---")
    fake_db = FakeDatabase()
    test_service = UserService(fake_db)

    test_service.create_user("Charlie")

    # We can assert against in-memory storage instead of a real DB:
    print("Fake DB storage:", fake_db.storage)  # [{'name': 'Charlie'}]
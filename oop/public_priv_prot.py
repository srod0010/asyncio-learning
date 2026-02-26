"""
===========================================================
Access Levels in Python (Public, Protected, Private)
===========================================================

SUMMARY
-------
Python does NOT enforce strict access modifiers like Java or C++.
Everything is technically accessible.

Instead, Python uses CONVENTIONS:

1) Public (default)
   - No underscore prefix.
   - Accessible from anywhere.

2) Protected (single underscore: _attribute)
   - Meant for internal use.
   - Still accessible from outside.
   - Convention: "Please don't touch this."

3) Private (double underscore: __attribute)
   - Triggers name mangling.
   - Python renames it internally to:
       _ClassName__attribute
   - Harder (but still possible) to access externally.

IMPORTANT:
These are conventions, not strict enforcement.
Python trusts developers to respect the intent.
"""


class Person:
    """
    Example class demonstrating public, protected,
    and private attributes.
    """

    def __init__(self, name: str, age: int, salary: float):
        # ---------------------------
        # PUBLIC attribute
        # ---------------------------
        # No underscore
        # Accessible from anywhere
        self.name = name

        # ---------------------------
        # PROTECTED attribute
        # ---------------------------
        # Single underscore
        # Convention: internal use only
        self._age = age

        # ---------------------------
        # PRIVATE attribute
        # ---------------------------
        # Double underscore
        # Triggers name mangling:
        # Internally becomes _Person__salary
        self.__salary = salary

    # Public method
    def greet(self):
        """
        Public method.
        Can be called from anywhere.
        """
        return f"Hi, I'm {self.name}."

    # Protected method (by convention)
    def _internal_calculation(self):
        """
        Meant for internal use.
        Still callable from outside (but discouraged).
        """
        return self._age * 2

    # Private method (name mangled)
    def __salary_with_bonus(self):
        """
        Private method.
        Internally renamed to _Person__salary_with_bonus.
        """
        return self.__salary * 1.10

    # Public accessor for private data (recommended approach)
    def get_salary_with_bonus(self):
        """
        Proper way to access private logic.
        """
        return self.__salary_with_bonus()


# ===========================================================
# Demonstration
# ===========================================================

if __name__ == "__main__":

    p = Person("Alice", 30, 100000)

    print("----- PUBLIC ACCESS -----")
    print(p.name)          # ✅ Works
    print(p.greet())       # ✅ Works

    print("\n----- PROTECTED ACCESS -----")
    print(p._age)          # ⚠️ Works, but discouraged
    print(p._internal_calculation())  # ⚠️ Works, but discouraged

    print("\n----- PRIVATE ACCESS -----")
    # print(p.__salary)    # ❌ AttributeError
    # print(p.__salary_with_bonus())  # ❌ AttributeError

    print("\nTrying name mangled access:")
    print(p._Person__salary)  # ⚠️ Works (not recommended)
    print(p._Person__salary_with_bonus())  # ⚠️ Works

    print("\nRecommended way:")
    print(p.get_salary_with_bonus())  # ✅ Proper usage
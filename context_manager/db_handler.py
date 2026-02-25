# A context manager defines setup and teardown logic
# for a `with` block using __enter__ and __exit__.

class DBHandler:
    def __enter__(self):
        # This method runs when the `with` block starts.
        # It is typically used for setup logic.
        print("Stopping database...")
        
        # The return value of __enter__ is assigned
        # to the variable after `as` (if used).
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # This method runs when the `with` block ends.
        # It runs EVEN IF an exception occurs inside the block.
        print("Starting database...")

        # exc_type  -> The exception class (if an exception occurred)
        # exc_val   -> The exception instance
        # exc_tb    -> The traceback object

        # If you return True here, the exception is suppressed.
        # Returning False (or None) allows the exception to propagate.
        return False


def backup():
    # This function represents the operation
    # that requires the database to be stopped.
    print("Backing up database...")


# Usage example
if __name__ == "__main__":
    # When entering this block:
    # 1. __enter__ runs (Stopping database...)
    # 2. backup() runs
    # 3. __exit__ runs (Starting database...)
    with DBHandler():
        backup()
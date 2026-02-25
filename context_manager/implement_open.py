class MyFile:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        print(f"Opening {self.filename} in {self.mode} mode...")
        self.file = open(self.filename, self.mode)
        return self.file  # returned object is assigned to "as f"

    def __exit__(self, exc_type, exc_value, traceback):
        if self.file:
            print(f"Closing {self.filename}...")
            self.file.close()

        # Optional: handle exceptions here
        if exc_type:
            print(f"Exception occurred: {exc_type.__name__} - {exc_value}")

        # Returning False re-raises the exception (same behavior as open())
        return False


if __name__ == "__main__":
    # Example 1: Write to a file
    with MyFile("example.txt", "w") as f:
        f.write("Hello, context manager!\n")

    print("File written successfully.\n")

    # Example 2: Read from the file
    with MyFile("example.txt", "r") as f:
        content = f.read()
        print("File contents:")
        print(content)

    # Example 3: Trigger an exception (to test __exit__)
    try:
        with MyFile("example.txt", "r") as f:
            raise ValueError("Testing exception handling")
    except ValueError:
        print("Exception was re-raised as expected.")
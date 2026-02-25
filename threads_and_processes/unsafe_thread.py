import threading

def example():
    print("Trying to join self...")

    # threading.current_thread() returns the thread object that is running *right now*.
    current = threading.current_thread()

    
    """
    join() means: "block (pause) THIS thread until `current` finishes".
    But `current` *is* this thread, so it is waiting for itself to finish...
    ...which can never happen because it's blocked.

    Example below: DONT UNCOMMENT.
    Note: If you do run current.join() below you’ll have to stop it manually (Ctrl+C in terminal, or stop the run button in your IDE).
    """
    # current.join()

    # You will never reach this line.
    print("This will never print")

if __name__ == "__main__":
    example()
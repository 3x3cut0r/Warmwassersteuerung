import os


def append_log(msg: str, path: str, max_size: int = 1024 * 1024) -> None:
    """Append a message to a log file and trim it if it grows too large.

    Args:
        msg (str): Message to be written.
        path (str): Target file path.
        max_size (int, optional): Maximum allowed file size in bytes.
            Defaults to 1 MiB.
    """
    try:
        # Append the message
        with open(path, "a", encoding="utf-8") as file:
            file.write(msg)

        # Check file size
        size = os.stat(path).st_size
        if size > max_size:
            # Keep only the last half of max_size bytes
            with open(path, "r+", encoding="utf-8", errors="ignore") as file:
                file.seek(size - max_size // 2)
                data = file.read()
                file.seek(0)
                file.write(data)
                file.truncate()
    except OSError:
        # Ignore file system errors to avoid blocking main program
        pass

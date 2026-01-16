class Sink:
    """Base Sink interface for pluggable delivery targets.

    Implementations should provide `open(spider)`, `send(item)` and `close()`.
    """

    def open(self, spider) -> None:
        return None

    def send(self, item) -> None:
        return None

    def close(self) -> None:
        return None

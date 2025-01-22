from ..core.callable_layer import CallableLayer


class Multiply(CallableLayer[int | float, int | float]):
    """A layer that multiplies the input by a constant factor."""

    def __init__(self, multiplier: int | float, name: str | None = None) -> None:
        super().__init__(name=name)
        self.multiplier = multiplier

    async def call(self, x: int | float) -> int | float:
        """Multiplies the input by a constant factor."""
        return x * self.multiplier

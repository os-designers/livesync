# import asyncio

import livesync as ls
from livesync import layers

if __name__ == "__main__":
    # Example: Linear chain
    #
    # ●  (f3): Multiplies merged values (8 * 16 = 128)
    # │
    # ○  (u): Merges outputs from x1 and x2 when both are available
    # │
    # ○──●  (wait for all streams)
    # │  │
    # │  ●  (f2): Multiplies input by 4 (4 * 4 = 16)
    # │  │
    # │  ◇  (x2): Generates constant value 4 every 1 second
    # │
    # ●  (f1): Multiplies input by 4 (2 * 4 = 8)
    # │
    # ◇  (x1): Generates constant value 2 every 1 second
    #
    x1 = ls.PeriodicConstantInput(2, interval=1.0)
    f1 = layers.Multiply(multiplier=4)

    x2 = ls.PeriodicConstantInput(4, interval=1.0)
    f2 = layers.Multiply(multiplier=4)

    h1 = f1(x1)
    h2 = f2(x2)
    u = layers.Merge([h1, h2], how="inner")

    async def async_mul(inputs: dict[str, int]) -> int:
        return inputs[h1.name] * inputs[h2.name]

    f3 = layers.Lambda(function=async_mul)
    y = f3(u)

    # Option 1: Run synchronously
    sync = ls.Sync(inputs=[x1, x2], outputs=[y])
    with sync.compile() as runner:
        runner.run(continuous=False, callback=ls.LoggingCallback())

    # Option 2: Run asynchronously
    # async def main():
    #     sync = ls.Sync(inputs=[constant_input_1, constant_input_2], outputs=[y])
    #     with sync.compile() as runner:
    #         run = await runner.async_run(continuous=False, callback=ls.LoggingCallback(log_level="info"))
    #         await run.wait()

    # asyncio.run(main())

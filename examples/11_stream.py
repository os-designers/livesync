import asyncio

import livesync as ls

if __name__ == "__main__":
    # Example: Basic stream
    #
    # ●  (y): Stream that depends on x
    # │
    # ◇  (x): Stream that generates values
    #

    x = ls.Stream(dtype=float)
    y = ls.Stream(dtype=float, dependencies=[x])

    async def main():
        async def producer():
            print("producer started")
            async for value in x:
                print(f"x: {value}")
            print("producer finished")

        async def consumer():
            print("consumer started")
            async for value in y:
                print(f"y: {value}")
            print("consumer finished")

        producer_task = asyncio.create_task(producer())
        consumer_task = asyncio.create_task(consumer())

        # Push values to x
        await x.push(1)
        await x.push(2)
        await x.push(3)

        await asyncio.sleep(1)

        producer_task.cancel()
        consumer_task.cancel()

    asyncio.run(main())

import asyncio
import logging

import cv2

import livesync as ls

_settings = {"alpha": 1.0, "beta": 0.0}


async def on_call(ctx: ls.RemoteLayerServicer, x: ls.VideoFrame) -> ls.VideoFrame | None:
    """Adjusts frame brightness

    - alpha > 1.0: increases brightness (e.g. 1.5 = 50% brighter)
    - alpha < 1.0: decreases brightness (e.g. 0.7 = 30% darker)
    - alpha = 1.0: original brightness
    """
    global _settings
    if not ctx.initialized:
        raise RuntimeError("Server not initialized")

    try:
        frame = x
        adjusted_frame = cv2.convertScaleAbs(frame.data, alpha=_settings["alpha"], beta=_settings["beta"])  # type: ignore
        frame = ls.VideoFrame(
            data=adjusted_frame,
            width=frame.width,
            height=frame.height,
            buffer_type=frame.buffer_type,
            pts=frame.pts,  # type: ignore
        )
        return frame
    except Exception as e:
        print(f"Error converting frame to gray: {e}")
        return None


async def on_init(ctx: ls.RemoteLayerServicer, alpha: float | None = None, beta: float | None = None):
    global _settings
    if alpha is not None:
        _settings["alpha"] = alpha
        print(f"Alpha set to {alpha}")
    if beta is not None:
        _settings["beta"] = beta
        print(f"Beta set to {beta}")


async def serve():
    server = ls.RemoteLayerServer(on_call=on_call, on_init=on_init, port=50051, max_workers=10)
    await server.async_run()
    await server.wait()


if __name__ == "__main__":
    # Example: Configurable Remote Layer for Frame Processing (Part 1 of 2) - Server
    #
    # This example demonstrates how to create a configurable remote processing server that can be used
    # in conjunction with RemoteLayer client (see example 10). The server receives video frames,
    # adjusts their brightness based on configurable alpha and beta parameters, and sends them back
    # to the client.
    #
    # Parameters:
    #   - alpha: Contrast control (1.0 = original, >1 = higher contrast, <1 = lower contrast)
    #   - beta: Brightness control (0 = original, >0 = brighter, <0 = darker)
    #
    # This is the SERVER component. For the CLIENT component, see example 10_configurable_remote_client.py
    #
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())

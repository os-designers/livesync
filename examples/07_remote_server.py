import asyncio
import logging

import cv2

import livesync as ls


async def on_call(ctx: ls.RemoteLayerServicer, x: ls.VideoFrame) -> ls.VideoFrame | None:
    try:
        frame = x

        # Convert to grayscale based on input buffer type
        if frame.buffer_type == "rgba":
            gray_frame = cv2.cvtColor(frame.data, cv2.COLOR_RGBA2GRAY)
        elif frame.buffer_type == "bgra":
            gray_frame = cv2.cvtColor(frame.data, cv2.COLOR_BGRA2GRAY)
        elif frame.buffer_type == "rgb24":
            gray_frame = cv2.cvtColor(frame.data, cv2.COLOR_RGB2GRAY)
        else:
            raise ValueError(f"Unsupported buffer type: {frame.buffer_type}")

        # Convert back to original format
        if frame.buffer_type == "rgba":
            final_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGBA)
        elif frame.buffer_type == "bgra":
            final_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGRA)
        elif frame.buffer_type == "rgb24":
            final_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
        else:
            raise ValueError(f"Unsupported buffer type: {frame.buffer_type}")

        frame = ls.VideoFrame(
            data=final_frame,
            width=frame.width,
            height=frame.height,
            buffer_type=frame.buffer_type,
            pts=frame.pts,
        )
        return frame
    except Exception as e:
        print(f"Error converting frame to gray: {e}")
        return None


async def serve():
    server = ls.RemoteLayerServer(on_call=on_call, port=50051, max_workers=10)
    await server.async_run()
    await server.wait()


if __name__ == "__main__":
    # Example: Remote Layer for Frame Processing (Part 1 of 2) - Server
    #
    # This example demonstrates how to create a remote processing server that can be used
    # in conjunction with RemoteLayer client (see example 08). The server receives video frames,
    # converts them to grayscale, and sends them back to the client.
    #
    # This is the SERVER component. For the CLIENT component, see example 08_remote_client.py
    #

    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(serve())

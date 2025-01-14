import sys
import asyncio

import qasync  # type: ignore
from PyQt6.QtWidgets import QApplication

from .core.flow import init_graph, on_node_replace_requested
from .gui.main_window import MainWindow


async def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create the main video frame window
    window = MainWindow()
    window.show()

    # Setup and start RTC graph
    graph = await init_graph(window)

    # Update the window
    window.update_graph(graph)

    # Connect toggle button signal to node replacement function
    window.node_replace_requested.connect(lambda: asyncio.create_task(on_node_replace_requested(graph, window)))

    await graph.start()

    async def cleanup():
        await graph.stop()
        loop = asyncio.get_running_loop()
        loop.stop()
        app.quit()

    app.aboutToQuit.connect(lambda: asyncio.create_task(cleanup()))  # type: ignore

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        qasync.run(main())  # type: ignore
    except (KeyboardInterrupt, SystemExit):
        print("Application exited.")

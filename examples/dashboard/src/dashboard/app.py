import sys
import asyncio

import qasync  # type: ignore
from PyQt6.QtWidgets import QApplication

from .ui import MainWindow, StreamSettings
from .workflow import workflow_manager


class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()

        # Connect signals
        self.window.settings_changed.connect(  # type: ignore
            lambda settings: asyncio.create_task(self._handle_settings_changed(settings))  # type: ignore
        )

    async def _handle_settings_changed(self, settings: StreamSettings):
        # Cancel current run if exists
        workflow_manager.cleanup()

        # Start new run with updated settings
        await workflow_manager.start_workflow(
            window=self.window,
            webcam_device_id=settings.webcam_device_id,
            quality=settings.quality,
            target_fps=settings.target_fps,
        )

    async def run(self):
        # Setup event loop
        loop = qasync.QEventLoop(self.app)
        asyncio.set_event_loop(loop)

        # Show main window
        self.window.show()

        # Initial workflow run with default settings
        await workflow_manager.start_workflow(window=self.window)

        # Setup cleanup
        async def cleanup():
            workflow_manager.cleanup()
            loop = asyncio.get_running_loop()
            loop.stop()
            self.app.quit()

        self.app.aboutToQuit.connect(lambda: asyncio.create_task(cleanup()))  # type: ignore

        # Wait indefinitely
        await asyncio.Event().wait()


async def app():
    application = Application()
    await application.run()

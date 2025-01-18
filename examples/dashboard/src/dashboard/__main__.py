import qasync  # type: ignore

from .app import app

if __name__ == "__main__":
    try:
        qasync.run(app())  # type: ignore
    except (KeyboardInterrupt, SystemExit):
        print("Application exited.")

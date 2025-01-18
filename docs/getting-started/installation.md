# Installation

LiveSync is a **graph-based video processing framework** designed for real-time applications. This guide will walk you through setting it up on your system.

## Requirements

- **Python 3.10 or higher**
- **pip** (latest version recommended)
- **FFmpeg** (for video processing)
- **OpenCV** (automatically installed with LiveSync)

## Installing LiveSync

### Option 1: Using `rye` (Recommended)

```bash
rye add livesync-io
```

### Option 2: Using `pip`

```bash
pip install livesync-io
```

## Verifying Installation

After installation, verify that LiveSync is installed correctly:

```bash
python -c "import livesync; print(livesync.__version__)"
```

If the installation was successful, you should see the LiveSync version number.

---

**Next Steps**  
Now that LiveSync is installed, check out the [Quick Start Guide](quickstart.md) to create your first processing pipeline.

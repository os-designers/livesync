# Installation

LiveSync is a real-time media processing framework that helps you build efficient video and audio pipelines. This guide will walk you through the setup process.

## Requirements

- **Python 3.10 or higher**
- **FFmpeg** (required for media processing)
- **OpenCV** (automatically installed with LiveSync)

### Installing FFmpeg

FFmpeg is required for media processing. Here's how to install it:

**Windows**:

```bash
choco install ffmpeg
```

**macOS**:

```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian)**:

```bash
sudo apt update
sudo apt install ffmpeg
```

Verify FFmpeg installation:

```bash
ffmpeg -version
```

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

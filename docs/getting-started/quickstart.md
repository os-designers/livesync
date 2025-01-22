# Quick Start

Let's start with a simple example that demonstrates the core concepts of LiveSync.

## Installation

```bash
pip install livesync
```

## Basic Example

Here's a minimal example that shows how LiveSync processes data streams:

```python
import livesync as ls
from livesync import layers

# Create two input streams that generate numbers
x1 = ls.PeriodicConstantInput(2, interval=1.0)    # Generates '2' every second
x2 = ls.PeriodicConstantInput(4, interval=1.0)    # Generates '4' every second

# Create processing layers
f1 = layers.Multiply(multiplier=4)                # Multiplies input by 4
f2 = layers.Multiply(multiplier=4)                # Multiplies input by 4

# Build processing chain
h1 = f1(x1)                                       # 2 * 4 = 8
h2 = f2(x2)                                       # 4 * 4 = 16

# Merge streams and process
u = layers.Merge([h1, h2], how="inner")          # Waits for both inputs
y = layers.Lambda(
    function=lambda inputs: inputs[h1.name] * inputs[h2.name]
)(u)                                             # 8 * 16 = 128

# Run the pipeline
sync = ls.Sync(inputs=[x1, x2], outputs=[y])
with sync.compile() as runner:
    runner.run(
        continuous=False,                         # Run once and stop
        callback=ls.LoggingCallback()
    )
```

This pipeline:

```
  ●  Final output: 128
  │
  ●  Multiply merged values
  │
  ○  Merge (waits for both inputs)
  │
  ○──●
  │  │
  │  ●  Multiply by 4 (16)
  │  │
  │  ◇  Input: 4
  │
  ●  Multiply by 4 (8)
  │
  ◇  Input: 2
```

## Understanding the Flow

1. **Input Streams**: Two periodic inputs generate constant values
2. **Processing Layers**: Each input is multiplied by 4
3. **Merge Operation**: Streams are combined using "inner" mode (waits for both inputs)
4. **Final Processing**: Merged values are multiplied together
5. **Execution**: Pipeline runs once and logs the result

## Next Steps

- Try more complex examples in [Basic Examples](./basic.md)
- Learn about media processing in [Advanced Examples](./advanced.md)
- Explore core concepts in the [User Guide](../user-guide/core-concepts.md)

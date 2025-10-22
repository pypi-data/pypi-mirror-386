# pixtreme-draw

GPU-accelerated drawing primitives for pixtreme

## Overview

`pixtreme-draw` provides high-performance drawing operations for rendering shapes, text, and masks directly on GPU memory.

## Features

- **Shape Drawing**: Circles, rectangles with anti-aliasing
- **Text Rendering**: GPU-accelerated text with custom fonts
- **Mask Generation**: Rounded masks for compositing
- **Zero-Copy**: Direct GPU memory operations via CuPy

## Installation

```bash
pip install pixtreme-draw
```

Requires `pixtreme-core`, `pixtreme-filter`, and CUDA Toolkit 12.x.

## Quick Start

```python
import pixtreme_draw as pd
import pixtreme_core as px

# Read image
img = px.imread("input.jpg")

# Draw circle
img = pd.circle(img, center=(256, 256), radius=100, color=(0, 255, 0), thickness=2)

# Draw rectangle
img = pd.rectangle(img, pt1=(100, 100), pt2=(300, 300), color=(255, 0, 0), thickness=3)

# Add text label
img = pd.add_label(img, text="Hello World", position=(50, 50), color=(255, 255, 255))

# Save result
px.imwrite("output.jpg", img)
```

## API

### Shape Drawing

```python
# Circle
pd.circle(image, center, radius, color, thickness=-1)

# Rectangle
pd.rectangle(image, pt1, pt2, color, thickness=-1)
```

### Text Rendering

```python
# Simple text
pd.put_text(image, text, position, font_scale=1.0, color=(255, 255, 255), thickness=1)

# Text with background label
pd.add_label(image, text, position, color=(255, 255, 255), bg_color=(0, 0, 0))
```

### Mask Generation

```python
# Rounded mask for compositing
mask = pd.create_rounded_mask(size=(512, 512), radius=50)
```

## License

MIT License - see LICENSE file for details.

## Links

- Repository: https://github.com/sync-dev-org/pixtreme

"""pixtreme-core: High-Performance GPU Image Processing Core Library

Core functionality for image I/O, color space conversions, and geometric transforms.
"""

__version__ = "0.6.3"

# I/O operations
from .io import (
    destroy_all_windows,
    imdecode,
    imencode,
    imread,
    imshow,
    imwrite,
    waitkey,
)

# Utils
from .utils.device import Device
from .utils.dlpack import to_cupy, to_numpy, to_tensor
from .utils.dtypes import (
    to_dtype,
    to_float16,
    to_float32,
    to_float64,
    to_uint16,
    to_uint8,
)

# Color operations
from .color import (
    apply_lut,
    bgr_to_grayscale,
    bgr_to_hsv,
    bgr_to_rgb,
    bgr_to_ycbcr,
    hsv_to_bgr,
    hsv_to_rgb,
    ndi_uyvy422_to_ycbcr444,
    read_lut,
    rgb_to_bgr,
    rgb_to_grayscale,
    rgb_to_hsv,
    rgb_to_ycbcr,
    uyvy422_to_ycbcr444,
    ycbcr_full_to_legal,
    ycbcr_legal_to_full,
    ycbcr_to_bgr,
    ycbcr_to_grayscale,
    ycbcr_to_rgb,
    yuv420p_to_ycbcr444,
    yuv422p10le_to_ycbcr444,
)

# Transform operations
from .transform import (
    INTER_AREA,
    INTER_AUTO,
    INTER_B_SPLINE,
    INTER_CATMULL_ROM,
    INTER_CUBIC,
    INTER_LANCZOS2,
    INTER_LANCZOS3,
    INTER_LANCZOS4,
    INTER_LINEAR,
    INTER_MITCHELL,
    INTER_NEAREST,
    affine_transform,
    affine_transform as affine,
    erode,
    get_inverse_matrix,
    merge_tiles,
    resize,
    tile_image,
)

__all__ = [
    "__version__",
    # I/O
    "destroy_all_windows",
    "imdecode",
    "imencode",
    "imread",
    "imshow",
    "imwrite",
    "waitkey",
    # Utils - Device
    "Device",
    # Utils - DLPack
    "to_cupy",
    "to_numpy",
    "to_tensor",
    # Utils - dtypes
    "to_dtype",
    "to_float16",
    "to_float32",
    "to_float64",
    "to_uint16",
    "to_uint8",
    # Color - LUT
    "apply_lut",
    "read_lut",
    # Color - BGR/RGB
    "bgr_to_rgb",
    "rgb_to_bgr",
    # Color - Grayscale
    "bgr_to_grayscale",
    "rgb_to_grayscale",
    # Color - HSV
    "bgr_to_hsv",
    "hsv_to_bgr",
    "hsv_to_rgb",
    "rgb_to_hsv",
    # Color - YCbCr
    "bgr_to_ycbcr",
    "rgb_to_ycbcr",
    "ycbcr_full_to_legal",
    "ycbcr_legal_to_full",
    "ycbcr_to_bgr",
    "ycbcr_to_grayscale",
    "ycbcr_to_rgb",
    # Color - Video formats
    "uyvy422_to_ycbcr444",
    "ndi_uyvy422_to_ycbcr444",
    "yuv420p_to_ycbcr444",
    "yuv422p10le_to_ycbcr444",
    # Transform - Interpolation constants
    "INTER_AREA",
    "INTER_AUTO",
    "INTER_B_SPLINE",
    "INTER_CATMULL_ROM",
    "INTER_CUBIC",
    "INTER_LANCZOS2",
    "INTER_LANCZOS3",
    "INTER_LANCZOS4",
    "INTER_LINEAR",
    "INTER_MITCHELL",
    "INTER_NEAREST",
    # Transform - Operations
    "affine",
    "affine_transform",
    "erode",
    "get_inverse_matrix",
    "merge_tiles",
    "resize",
    "tile_image",
]

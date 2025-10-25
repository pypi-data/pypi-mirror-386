from yta_programming.decorators.requires_dependency import requires_dependency
from typing import Union

import numpy as np


@requires_dependency('PIL', 'yta_numpy', 'pillow')
def numpy_to_file(
    frame: np.ndarray,
    output_filename: str
) -> str:
    """
    *Optional `pillow` (imported as `PIL`) library is required*

    Save the provided numpy frame array as a file.
    """
    from PIL import Image
    # TODO: Force 'IMAGE' output (?)
    # Example: np.zeros((480, 640, 3), dtype=np.uint8)
    Image.fromarray(frame).save(output_filename)

    return output_filename

@requires_dependency('PIL', 'yta_numpy', 'pillow')
def read_image_as_numpy(
    path: str,
    do_read_as_rgba: bool = True,
    size: Union[tuple[int, int], None] = None
) -> np.ndarray:
    """
    *Optional dependency `pillow` (imported as `PIL`) required*

    Read an image from a file and transform it into a
    numpy array. It will force the 'size' if provided,
    or leave the original one if it is None.
    """
    from PIL import Image

    mode = (
        'RGBA'
        if do_read_as_rgba else
        'RGB'
    )

    with Image.open(path) as img:
        img = img.convert(mode)
        np_img = np.array(img, dtype = np.uint8)

    return (
        scale_numpy_pillow(
            input = np_img,
            size = size
        ) if size is not None else
        np_img
    )

"""
TODO: Code migrated from other project, check if this
is set in the 'yta_numpy_resizer' library or not, and
remove if duplicated.
"""
@requires_dependency('cv2', 'yta_numpy', 'opencv-python')
def scale_numpy(
    input: np.ndarray,
    size: tuple[int, int]
) -> np.ndarray:
    """
    *Optional dependency `opencv-python` (imported as `cv2`) required*

    Resize the 'input' numpy array to the provided 'size'
    if needed, using a rescaling method with 'opencv-python'
    (cv2).

    The 'size' provided must be (width, height).
    """
    import cv2

    return cv2.resize(input, size, interpolation = cv2.INTER_LINEAR)

@requires_dependency('PIL', 'yta_numpy', 'pillow')
def scale_numpy_pillow(
    input: np.ndarray,
    size: tuple[int, int]
) -> np.ndarray:
    """
    *Optional dependency `pillow` (imported as `PIL`) required*

    Resize the 'input' numpy array to the provided 'size'
    if needed, using a rescaling method with 'pillow'
    (PIL).

    The 'size' provided must be (width, height).
    """
    from PIL import Image

    return np.array(Image.fromarray(input).resize(size, Image.BILINEAR))


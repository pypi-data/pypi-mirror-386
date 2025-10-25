from PIL import Image
from yta_programming.decorators.requires_dependency import requires_dependency

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
    # TODO: Force 'IMAGE' output (?)
    # Example: np.zeros((480, 640, 3), dtype=np.uint8)
    Image.fromarray(frame).save(output_filename)

    return output_filename


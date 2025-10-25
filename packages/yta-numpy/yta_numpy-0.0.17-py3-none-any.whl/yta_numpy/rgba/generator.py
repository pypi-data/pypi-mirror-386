
from typing import Union

import numpy as np
import random


class _RGBAColorFrameGenerator:
    """
    *For internal use only*

    Class to wrap functionality related to
    generating RGBA color frames.
    """

    @staticmethod
    def _get_numpy_array(
        color: Union[tuple[int, int, int], None],
        size: tuple[int, int] = (1920, 1080),
        dtype: np.dtype = np.uint8,
        alpha: Union[int, None] = None
    ) -> np.ndarray:
        """
        *For internal use only*

        Get the numpy array with the provided
        color and all the attributes set.

        The size must be provided as (w, h), but
        the numpy array will be like (h, w). Be careful
        if you need to invert the size for your result 
        and pass it already inverted.

        The 'alpha' must be an int in `[0, 255]`
        range:
        - `0` is transparent
        - `255` is opaque

        Providing 'alpha' as None will 
        result in a numpy with only 3 dimensions.
        """
        dimensions = (
            4
            if alpha is not None else
            3
        )

        color = (
            # Handmade random color to avoid importing
            # 'yta_colors' library just to this
            (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
            if color is None else
            color
        )

        fill_value = (
            color + (alpha,)
            if alpha is not None else
            color
        )

        return np.full(
            shape = (size[1], size[0], dimensions),
            fill_value = fill_value,
            dtype = dtype
        )
    
    @staticmethod
    def white(
        size: tuple[int, int] = (1920, 1080),
        dtype: np.dtype = np.uint8,
        alpha: Union[int, None] = None
    ) -> np.ndarray:
        """
        Get a numpy array that represents a full
        blue frame of the given 'size' and with
        the given 'dtype'.
        
        The 'alpha' must be an int in `[0, 255]`
        range:
        - `0` is transparent
        - `255` is opaque

        Providing 'alpha' as None will 
        result in a numpy with only 3 dimensions.
        """
        return _RGBAColorFrameGenerator._get_numpy_array(
            color = (255, 255, 255),
            size = size,
            dtype = dtype,
            alpha = alpha
        )
    
    @staticmethod
    def black(
        size: tuple[int, int] = (1920, 1080),
        dtype: np.dtype = np.uint8,
        alpha: Union[int, None] = None
    ) -> np.ndarray:
        """
        Get a numpy array that represents a full
        blue frame of the given 'size' and with
        the given 'dtype'.

        The 'alpha' must be an int in `[0, 255]`
        range:
        - `0` is transparent
        - `255` is opaque

        Providing 'alpha' as None will 
        result in a numpy with only 3 dimensions.
        """
        return _RGBAColorFrameGenerator._get_numpy_array(
            color = (0, 0, 0),
            size = size,
            dtype = dtype,
            alpha = alpha
        )
    
    @staticmethod
    def red(
        size: tuple[int, int] = (1920, 1080),
        dtype: np.dtype = np.uint8,
        alpha: Union[int, None] = None
    ) -> np.ndarray:
        """
        Get a numpy array that represents a full
        blue frame of the given 'size' and with
        the given 'dtype'.
        
       The 'alpha' must be an int in `[0, 255]`
        range:
        - `0` is transparent
        - `255` is opaque

        Providing 'alpha' as None will 
        result in a numpy with only 3 dimensions.
        """
        return _RGBAColorFrameGenerator._get_numpy_array(
            color = (255, 0, 0),
            size = size,
            dtype = dtype,
            alpha = alpha
        )
    
    @staticmethod
    def green(
        size: tuple[int, int] = (1920, 1080),
        dtype: np.dtype = np.uint8,
        alpha: Union[int, None] = None
    ) -> np.ndarray:
        """
        Get a numpy array that represents a full
        blue frame of the given 'size' and with
        the given 'dtype'.
        
       The 'alpha' must be an int in `[0, 255]`
        range:
        - `0` is transparent
        - `255` is opaque

        Providing 'alpha' as None will 
        result in a numpy with only 3 dimensions.
        """
        return _RGBAColorFrameGenerator._get_numpy_array(
            color = (0, 255, 0),
            size = size,
            dtype = dtype,
            alpha = alpha
        )
    
    @staticmethod
    def blue(
        size: tuple[int, int] = (1920, 1080),
        dtype: np.dtype = np.uint8,
        alpha: Union[int, None] = None
    ) -> np.ndarray:
        """
        Get a numpy array that represents a full
        blue frame of the given 'size' and with
        the given 'dtype'.
        
        The 'alpha' must be an int in `[0, 255]`
        range:
        - `0` is transparent
        - `255` is opaque

        Providing 'alpha' as None will 
        result in a numpy with only 3 dimensions.
        """
        return _RGBAColorFrameGenerator._get_numpy_array(
            color = (0, 0, 255),
            size = size,
            dtype = dtype,
            alpha = alpha
        )

class RGBAFrameGenerator:
    """
    Class to wrap functionality related to
    generating RGBA frames.
    """

    color: _RGBAColorFrameGenerator = _RGBAColorFrameGenerator
    """
    Shortcut to rgba color generation.
    """
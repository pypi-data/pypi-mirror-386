from typing import Union

import numpy as np
import random


class RGBAFrameUtils:
    """
    Class to wrap utils related to RGBA frame
    numpy arrays, which are frames with values
    between 0 and 255 and an optional alpha
    layer.

    Useful to be used with images or video 
    frames.
    """

    @staticmethod
    def random_rgba_frame(
        size: tuple[int, int] = (2, 2),
        alpha: Union[int, bool, None] = True
    ):
        """
        Create a random RGB or RGBA frame of the given
        'size', including alpha channel or not according
        to our condition (see explanation below).

        This method has been created to be used in tests.

        The possible alpha values:
        - `True` => A random alpha value between 0 and 255
        - `[0, 255]` => The value provided between 0 and 255
        - `None | False` => No alpha value, no alpha layer

        Remember that 0 means transparent and 255 opaque.
        """
        alpha_value = (
            random.randint(0, 256)
            if alpha is True else
            alpha
        )

        rgb = np.random.randint(0, 256, size + (3,), dtype = np.uint8)

        return (
            # RGBA
            np.concatenate(
                [
                    rgb,
                    np.full(size + (1,), alpha_value, dtype = np.uint8)
                ],
                axis = 2
            )
            if (
                alpha is not None and
                alpha is not False
            ) else
            # RGB
            rgb
        )
    
    @staticmethod
    def numpy_frame_has_alpha_layer_and_transparent_pixels(
        frame: 'np.ndarray'
    ) -> bool:
        """
        Check if the provided numpy array has alpha
        pixels or not and if it also has some
        pixels that are not full opaque (we consider
        a transparent pixel a pixel that has a value
        different than 255).
        """
        return (
            RGBAFrameUtils.numpy_frame_has_alpha_layer(frame) and
            RGBAFrameUtils._numpy_frame_has_transparent_pixels(frame)
        )

    @staticmethod
    def _numpy_frame_has_transparent_pixels(
        frame: 'np.ndarray'
    ) -> bool:
        """
        *For internal use only*

        Check if the provided numpy array has alpha
        pixels or not. If the provided numpy array
        doesn't include an alpha layer the result
        will be False.

        This method could generate exceptions if
        used with numpy arrays without the right
        shape.

        The code:
        - `np.any(frame[..., 3]  255)`
        """
        return np.any(frame[..., 3] < 255)
    
    @staticmethod
    def numpy_frame_has_alpha_layer(
        frame: np.ndarray
    ) -> bool:
        """
        Check if the provided numpy array has alpha
        channel or not. Having an alpha layer doesn't
        mean that the frame includes some transparent
        pixels.

        The code:
        - `frame.ndim == 3 and frame.shape[2] == 4`
        """
        return (
            frame.ndim == 3 and
            frame.shape[2] == 4
        )
    
    @staticmethod
    def invert_numpy_frame(
        frame: 'np.ndarray',
        do_invert_alpha: bool = False
    ) -> np.ndarray:
        """
        Invert the provided 'frame' numpy array,
        inverting the alpha channel if existing
        and 'do_invert_alpha' is True.
        """
        output = frame.copy()

        if (
            do_invert_alpha and
            RGBAFrameUtils.numpy_frame_has_alpha_layer(frame)
        ):
            output = 255 - output
        else:
            output[..., :3] = 255 - output[..., :3]

        return output
    
    @staticmethod
    def invert_alpha_channel_of_numpy_array(
        frame: 'np.ndarray'
    ) -> np.ndarray:
        """
        Invert the alpha channel of the given
        'frame' numpy array if existing.
        """
        output = frame.copy()

        if RGBAFrameUtils.numpy_frame_has_alpha_layer(frame):
            output[..., 3] = 255 - output[..., 3]

        return output
    
    @staticmethod
    def remove_alpha_channel_from_frame(
        frame: 'np.ndarray'
    ) -> 'np.ndarray':
        """
        Remove the alpha channel from the given
        numpy 'array', if existing.
        """
        return (
            frame[:, :, :3]
            if RGBAFrameUtils.numpy_frame_has_alpha_layer(frame) else
            frame
        )
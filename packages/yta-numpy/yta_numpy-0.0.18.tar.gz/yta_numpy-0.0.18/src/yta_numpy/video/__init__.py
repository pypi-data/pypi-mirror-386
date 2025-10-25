"""
Module to handle numpy arrays related to
video files.
"""
import numpy as np


# TODO: Move to RGBA better because it is
# valid also for images (video frame is 
# an image) and it will be found easier
class VideoFrame:
    """
    Class to wrap a video frame.
    """

    @property
    def size(
        self
    ) -> tuple[int, int]:
        """
        The size of the frames expressed always as
        (width, height).
        """
        return (
            self._frame.shape[:2][::-1]
            if self._is_height_first else
            self._frame.shape[:2]
        )
    
    @property
    def has_alpha(
        self
    ) -> bool:
        """
        Flag to indicate if the video frame has an
        alpha layer (3rd channel) or not.
        """
        return (
            len(self._frame.shape) == 3 and
            self._frame.shape[2] == 3
        )
    
    @property
    def has_transparent_pixels(
        self
    ) -> bool:
        """
        Flag to indicate if the video frame has 
        some transparent pixels (any pixel that
        is not full opaque is considered as
        transparent).
        """
        return (
            self.has_alpha and
            np.any(self._frame[..., 3] < 255)
        )
        

    def __init__(
        self,
        frame: np.ndarray,
        is_height_first: bool = False
    ):
        """
        Set the 'is_height_first' parameter as True if
        the height is the first value (height, width, ...)
        or as False if width is the first value
        (width, height, ...). Some libraries use the
        height as the first value.
        """
        # TODO: Validate 'array' somehow, but being able
        # to avoid that validation for a better speed
        self._frame: np.ndarray = frame
        """
        The frame array that includes all the pixels
        of the video frame.
        """
        self._is_height_first: bool = is_height_first
        """
        Flag to indicate if the first property is the
        height or if it is the width.
        """
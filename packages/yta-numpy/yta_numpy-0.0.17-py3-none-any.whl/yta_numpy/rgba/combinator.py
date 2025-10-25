import numpy as np


class _AlphaBlending:
    """
    *For internal use only*

    Class to wrap functionality related to
    alpha blending, to be used by the 
    RGBAFrameCombinator class.
    """

    @staticmethod
    def blend(
        bottom: np.ndarray,
        top: np.ndarray,
    ):
        """
        Composición alpha de `top` sobre `bottom`.
        Ambos deben ser RGBA uint8 del mismo tamaño.
        """
        # Normalizamos a [0,1]
        top_rgb = top[..., :3].astype(np.float32) / 255.0
        bottom_rgb = bottom[..., :3].astype(np.float32) / 255.0
        top_a = top[..., 3].astype(np.float32) / 255.0
        bottom_a = bottom[..., 3].astype(np.float32) / 255.0

        # Fórmulas Porter–Duff "over"
        out_a = top_a + bottom_a * (1 - top_a)
        # Evitar división por 0
        out_rgb = np.where(
            out_a[..., None] > 0,
            (top_rgb * top_a[..., None] + bottom_rgb * bottom_a[..., None] * (1 - top_a[..., None])) / out_a[..., None],
            0
        )

        # Convertimos a uint8
        out = np.zeros_like(top)
        out[..., :3] = np.clip(out_rgb * 255, 0, 255).astype(np.uint8)
        out[..., 3] = np.clip(out_a * 255, 0, 255).astype(np.uint8)
        return out

    @staticmethod
    def alpha(
        bottom: np.ndarray,
        top: np.ndarray,
        alpha = 0.5
    ):
        return (alpha * top + (1 - alpha) * bottom).astype(np.uint8)

    @staticmethod
    def add(
        bottom: np.ndarray,
        top: np.ndarray
    ):
        """
        Lighten the combined image, as if you
        were superimposing two light projectors.
        """
        return np.clip(bottom.astype(np.int16) + top.astype(np.int16), 0, 255).astype(np.uint8)

    @staticmethod
    def multiply(
        bottom: np.ndarray,
        top: np.ndarray
    ):
        """
        It darkens, like projecting two
        transparencies together.
        """
        return ((bottom.astype(np.float32) * top.astype(np.float32)) / 255).astype(np.uint8)

    @staticmethod
    def screen(
        bottom: np.ndarray,
        top: np.ndarray
    ):
        """
        It does the opposite of Multiply, it
        clarifies the image.
        """
        return (255 - ((255 - bottom.astype(np.float32)) * (255 - top.astype(np.float32)) / 255)).astype(np.uint8)

    @staticmethod
    def overlay(
        bottom: np.ndarray,
        top: np.ndarray
    ):
        """
        Mix between Multiply and Screen
        depending on the brightness of each
        pixel.
        """
        b = bottom.astype(np.float32) / 255
        t = top.astype(np.float32) / 255
        mask = b < 0.5
        result = np.zeros_like(b)
        result[mask] = 2 * b[mask] * t[mask]
        result[~mask] = 1 - 2 * (1 - b[~mask]) * (1 - t[~mask])

        return (result * 255).astype(np.uint8)

    @staticmethod
    def difference(
        bottom: np.ndarray,
        top: np.ndarray
    ):
        """
        Highlight the differences between the
        two frames.
        """
        return np.abs(bottom.astype(np.int16) - top.astype(np.int16)).astype(np.uint8)

    # TODO: This one needs a mask, thats why
    # it is commented
    # @staticmethod
    # def mask(
    #     bottom,
    #     top,
    #     mask
    # ):
    #     """
    #     En lugar de un alpha fijo, puedes pasar una máscara (por ejemplo, un degradado o un canal alfa real)

    #     mask: array float32 entre 0 y 1, mismo tamaño que frame.
    #     """
    #     return (mask * top + (1 - mask) * bottom).astype(np.uint8)

class RGBAFrameCombinator:
    """
    Class to wrap functionality related to
    combine RGBA frames.
    """

    alpha_blending: _AlphaBlending = _AlphaBlending
    """
    Shortcut to the alpha blending code.
    """
    
    
    
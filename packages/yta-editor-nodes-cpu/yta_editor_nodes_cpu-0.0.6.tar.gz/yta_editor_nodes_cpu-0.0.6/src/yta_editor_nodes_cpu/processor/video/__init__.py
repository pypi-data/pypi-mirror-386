from yta_editor_nodes_cpu.processor import _NodeProcessorCPU
from yta_programming.decorators.requires_dependency import requires_dependency
from abc import abstractmethod

import numpy as np


class _VideoNodeProcessorCPU(_NodeProcessorCPU):
    """
    *Abstract class*

    *Singleton class*

    *For internal use only*

    Class to represent a node processor that uses CPU
    to transform the input but it is meant to video
    processing, so it implements a 'time' parameter to
    manipulate the frames according to that time
    moment.

    This class must be implemented by any processor
    that uses CPU to modify an input.
    """
    
    @abstractmethod
    def process(
        self,
        # TODO: What about the type (?)
        input: np.ndarray,
        t: float,
        **kwargs
    # TODO: What about the output type (?)
    ) -> np.ndarray:
        """
        Process the provided `input` and transform it by
        using the code that is defined here according to
        the `t` time moment provided.
        """
        # TODO: Specific attributes can be received as
        # **kwargs to modify the specific process
        pass

# Specific implementations here below:
class WavingFramesVideoNodeProcessorCPU(_VideoNodeProcessorCPU):
    """
    Just an example of a specific class that is a node
    processor that uses CPU.

    TODO: Untested and needing 'opencv-python' as 'cv2'
    """

    def __init__(
        self,
        amplitude: float = 0.05,
        frequency: float = 10.0,
        speed: float = 2.0
    ):
        """
        time: tiempo actual (float)
        amplitude: desplazamiento vertical máximo (en píxeles o en [0,1] si normalizado)
        frequency: frecuencia de la onda (ciclos por ancho)
        speed: velocidad de movimiento (en radianes / segundo)
        """
        self._amplitude: float = amplitude
        self._frequency: float = frequency
        self._speed: float = speed

    @requires_dependency('cv2', 'yta_editor_nodes_cpu', 'opencv-python')
    def process(
        self,
        # TODO: What about the type (?)
        input: np.ndarray,
        t: float
    # TODO: What about the output type (?)
    ) -> np.ndarray:
        """
        Process the provided 'input' and transform it by
        using the code that is defined here.
        """
        import numpy as np
        import cv2  # opcional, solo para redimensionar/interpolar

        h, w, _ = input.shape

        # UV coordinates [0, 1]
        x = np.linspace(0, 1, w, dtype = np.float32)
        y = np.linspace(0, 1, h, dtype = np.float32)
        xv, yv = np.meshgrid(x, y)

        wave = np.sin(xv * self._frequency + t * self._speed) * self._amplitude

        # UV coordinates displacement
        yv_new = yv + wave

        # Imitate wrap/clamp of OpenGL (comment if REPEAT)
        yv_new = np.clip(yv_new, 0.0, 1.0)

        # UV coordinates to pixels
        map_x = (xv * (w - 1)).astype(np.float32)
        map_y = (yv_new * (h - 1)).astype(np.float32)

        return cv2.remap(
            input,
            map_x,
            map_y,
            interpolation = cv2.INTER_LINEAR,
            borderMode = cv2.BORDER_REFLECT
        )
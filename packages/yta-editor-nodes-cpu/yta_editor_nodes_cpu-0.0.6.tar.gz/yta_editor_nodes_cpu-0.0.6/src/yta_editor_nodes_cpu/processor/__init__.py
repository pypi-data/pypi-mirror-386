"""
The nodes that modify inputs by using static parameters
and not 't' time moments, with CPU.
"""
from yta_programming.singleton import SingletonABCMeta
from yta_editor_utils import NumpyTextureUtils
from abc import abstractmethod

import numpy as np


class _NodeProcessorCPU(metaclass = SingletonABCMeta):
    """
    *Singleton class*

    *For internal use only*

    Class to represent a node processor that uses CPU
    to transform the input.

    This class must be implemented by any processor
    that uses CPU to modify an input.
    """
    
    # TODO: Just code and the same attributes that the
    # GPU version also has
    @abstractmethod
    def process(
        self,
        # TODO: What about the type (?)
        input: np.ndarray,
        **kwargs
    # TODO: What about the output type (?)
    ) -> np.ndarray:
        """
        Process the provided 'input' and transform it by
        using the code that is defined here.
        """
        # TODO: Specific attributes can be received as
        # **kwargs to modify the specific process
        pass

# Specific implementations below
class SelectionMaskProcessorCPU(_NodeProcessorCPU):
    """
    Class to use a mask selection (from which we will
    determine if the pixel must be applied or not) to
    apply the `processed_input` on the `original_input`.
    """

    def process(
        self,
        # TODO: What about the type (?)
        original_input: np.ndarray,
        processed_input: np.ndarray,
        selection_mask_input: np.ndarray
    ):
        """
        Apply the `selection_mask` provided to the also
        given `original` and `processed` nuumpy arrays to
        obtain the processed one but affected only as the
        selection mask says.

        The input are processed as float32, with float 
        precission, to be able to calculate properly,
        and then returned to uint8 [0, 255] values (the
        ones our OpenGL is able to handle with the 'f1'
        dtype and the sampler2d uniforms).
        """
        # We force to have float precission for the calculations
        original_input = NumpyTextureUtils.numpy_to_float32(original_input)
        processed_input = NumpyTextureUtils.numpy_to_float32(processed_input)
        selection_mask_input = NumpyTextureUtils.numpy_to_float32(selection_mask_input)

        # We need a 3D or 4D mask
        selection_mask_input = (
            np.expand_dims(selection_mask_input, axis = -1)
            if selection_mask_input.ndim == 2 else
            selection_mask_input
        )

        selection_mask_input = (
            np.repeat(
                a = selection_mask_input,
                repeats = original_input.shape[-1],
                axis = -1
            )
            if (
                selection_mask_input.shape[-1] == 1 and
                original_input.shape[-1] in (3, 4)
            ) else
            selection_mask_input
        )

        # Mix with the selection mask
        final = original_input * (1.0 - selection_mask_input) + processed_input * selection_mask_input

        return NumpyTextureUtils.numpy_to_uint8(final)
"""
A selection mask is a numpy array or a texture that
indicates where we should apply the changes from
the processed input in the original input, and also
how much we have todo.

A selection mask that is fulfilled with all ones will
make the output be the processed input, but one with
all zeros will keep the original input as not modified.

(!) If a moderngl texture is detected as the input this
will trigger the detector to raise an Exception if the
library is not installed and it cannot be processed.

TODO: I think this module is very similar to the 
`yta-numpy` library we have.
"""
# TODO: Should we move this module from here to
# another different one
from yta_validation import PythonValidator
from yta_validation.parameter import ParameterValidator
from yta_programming.decorators.requires_dependency import requires_dependency
from typing import Union


"""
Here we handle the dtypes as strings that
are accepted by opengl ('f4' for 'float32', 'u1'
for 'uint8') where f means float and 4 means
4 * 8 = 32
"""
class _TextureSelectionMaskGenerator:
    """
    *For internal use only*

    Class to be used as a shortcut within the general
    selection mask generator, to simplify the way we
    create selection masks as moderngl textures.
    """

    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_full_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get a full mask (all values are 1.0) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_full_mask_for_input(
                input = input,
                dtype = dtype
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )

    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_full_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get a full mask (all values are 1.0) of the
        provided `width` and `height` given, and the
        `dtype` provided, ready to be used in an
        OpenGL shader.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_full_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_half_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get a half mask (all values are 0.5) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_half_mask_for_input(
                input = input,
                dtype = dtype
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_half_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get a half mask (all values are 0.5) of the
        provided `width` and `height` given, and the
        `dtype` provided, ready to be used in an
        OpenGL shader.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_half_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_empty_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get an empty mask (all values are 0.0) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_empty_mask_for_input(
                input = input,
                dtype = dtype
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_empty_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get an empty mask (all values are 0.0) of the
        provided `width` and `height` given, and the
        `dtype` provided, ready to be used in an
        OpenGL shader.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_empty_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_random_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get a random mask (all values are random values
        in the range [0.0, 1.0]) that fits the
        dimensions and properties of the `input` provided,
        returning it with the given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_random_mask_for_input(
                input = input,
                dtype = dtype
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )

    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_random_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get a random mask (all values are random values
        in the range [0.0, 1.0]) of the provided `width`
        and `height` given, and the `dtype` provided,
        ready to be used in an OpenGL shader.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_random_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_custom_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
        value: float = 0.75,
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get a custom mask (all values are the provided
        `value`, that must be a value in the [0.0, 1.0]
        range) that fits the dimensions and properties
        of the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_custom_mask_for_input(
                input = input,
                dtype = dtype,
                value = value
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_custom_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        value: float = 0.75,
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        Get a custom mask (all values are the provided
        `value`, that must be a value in the [0.0, 1.0]
        range) of the provided `width` and `height` and
        the `dtype` provided.
        """
        return _NumpySelectionMaskGenerator._numpy_mask_to_texture(
            mask = _NumpySelectionMaskGenerator.get_custom_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype,
                value = value
            ),
            dtype = dtype,
            opengl_context = opengl_context
        )

class _NumpySelectionMaskGenerator:
    """
    *For internal use only*

    Class to be used as a shortcut within the general
    selection mask generator, to simplify the way we
    create seletion masks as numpy arrays.
    """

    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_full_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
    ) -> 'np.ndarray':
        """
        Get a full mask (all values are 1.0) that fits
        the dimensions and properties of the `input`
        provided, returning it with the given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        width, height, number_of_channels = _get_width_height_and_number_of_channels_from_input(input)

        return _NumpySelectionMaskGenerator.get_full_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_full_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1'
    ) -> 'np.ndarray':
        """
        Get a full mask (all values are 1.0) of the
        provided `width` and `height`, also with the
        `number_of_channels` given, and the `dtype`
        provided.

        These are the values according to the `dtype`
        provided:
        - `f1 (np.uint8)` -> `255`
        - `u1 (np.uint8)` -> `255`
        - `f4 (np.float32)` -> `1.0`
        """
        import numpy as np

        dtype = _get_numpy_dtype_from_moderngl_dtype(dtype)

        fill_value = (
            255
            if dtype == np.uint8 else
            1.0
        )

        return np.full(
            shape = (height, width, number_of_channels),
            fill_value = fill_value, 
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_half_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
    ) -> 'np.ndarray':
        """
        Get a half mask (all values are 0.5) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.

        These are the values according to the `dtype`
        provided:
        - `f1 (np.uint8)` -> `127`
        - `u1 (np.uint8)` -> `127`
        - `f4 (np.float32)` -> `0.5`
        """
        width, height, number_of_channels = _get_width_height_and_number_of_channels_from_input(input)

        return _NumpySelectionMaskGenerator.get_half_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_half_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1'
    ) -> 'np.ndarray':
        """
        Get a half mask (all values are 0.5) of the
        provided `width` and `height`, also with the
        `number_of_channels` given, and the `dtype`
        provided.
        """
        return _NumpySelectionMaskGenerator.get_custom_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype,
            value = 0.5
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_empty_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
    ) -> 'np.ndarray':
        """
        Get an empty mask (all values are 0.0) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        width, height, number_of_channels = _get_width_height_and_number_of_channels_from_input(input)

        return _NumpySelectionMaskGenerator.get_empty_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_empty_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1'
    ) -> 'np.ndarray':
        """
        Get an empty mask (all values are 0.0) of the
        provided `width` and `height`, also with the
        `number_of_channels` given, and the `dtype`
        provided.

        These are the values according to the `dtype`
        provided:
        - `f1 (np.uint8)` -> `0`
        - `u1 (np.uint8)` -> `0`
        - `f4 (np.float32)` -> `0.0`
        """
        import numpy as np

        return np.zeros(
            shape = (height, width, number_of_channels),
            dtype = _get_numpy_dtype_from_moderngl_dtype(dtype)
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_random_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
    ) -> 'np.ndarray':
        """
        Get a random mask (all values are random
        values in the range [0.0, 1.0]) that fits
        the dimensions and properties of the `input`
        provided, returning it with the given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        width, height, number_of_channels = _get_width_height_and_number_of_channels_from_input(input)

        return _NumpySelectionMaskGenerator.get_random_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype
        )

    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_random_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1'
    ) -> 'np.ndarray':
        """
        Get a full mask (all values are random values
        in the range [0.0, 1.0]) of the provided `width`
        and `height`, also with the `number_of_channels`
        given, and the `dtype` provided.

        These are the value ranges according to the
        `dtype` provided:
        - `f1 (np.uint8)` -> `[0, 255]`
        - `u1 (np.uint8)` -> `[0, 255]`
        - `f4 (np.float32)` -> `[0.0, 1.0]`
        """
        import numpy as np

        dtype = _get_numpy_dtype_from_moderngl_dtype(dtype)

        array = np.random.rand(height, width, number_of_channels)

        return (
            array * 255
            if dtype == np.uint8 else
            array
        ).astype(dtype)

    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_custom_mask_for_input(
        input: Union['moderngl.Texture', 'np.ndarray'],
        dtype: str = 'f1',
        value: float = 0.75
    ) -> 'np.ndarray':
        """
        Get a custom mask (all values are the provided
        `value`, that must be a value in the [0.0, 1.0]
        range) that fits the dimensions and properties
        of the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        width, height, number_of_channels = _get_width_height_and_number_of_channels_from_input(input)

        return _NumpySelectionMaskGenerator.get_custom_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype,
            value = value
        )

    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    def get_custom_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1',
        value: float = 0.75
    ) -> 'np.ndarray':
        """
        Get a custom mask (all values are the provided
        `value`, that must be a value in the [0.0, 1.0]
        range) of the provided `width` and `height`, also
        with the `number_of_channels` given, and the
        `dtype` provided.

        These are the values according to the `dtype`
        provided:
        - `f1 (np.uint8)` -> `value * 255`
        - `u1 (np.uint8)` -> `value * 255`
        - `f4 (np.float32)` -> `value`
        """
        import numpy as np

        ParameterValidator.validate_mandatory_number_between('value', value, 0.0, 1.0)

        dtype = _get_numpy_dtype_from_moderngl_dtype(dtype)
        
        value = (
            value * 255
            if dtype == np.uint8 else
            value
        )

        return np.full(
            shape = (height, width, number_of_channels),
            fill_value = value,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('numpy', 'yta_editor_utils', 'numpy')
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def _numpy_mask_to_texture(
        mask: 'np.ndarray',
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *For internal use only*

        Transform the provided numpy array `mask` into a
        moderngl Texture mask using the context provided
        as `opengl_context` or creating a new one.
        """
        import moderngl
        # TODO: This code is useful to force a mask array
        # with only one channel:
        # opengl_context = OpenGLContext().context
        # mask = mask[..., 0]  # quedarse con un canal
        # h, w = mask.shape[:2]

        # mask_tex = opengl_context.texture((w, h), 1, data = mask.astype('f4').tobytes())

        opengl_context: moderngl.Context = (
            moderngl.create_context(standalone = True)
            if opengl_context is None else
            opengl_context
        )

        h, w = mask.shape[:2]
        number_of_components = (
            mask.shape[2]
            if mask.ndim == 3 else
            1
        )

        # TODO: This code is repeated and I should have
        # it only in one place
        def prepare_mask(
            mask: 'np.ndarray',
            dtype: str = 'f1'
        ):
            import numpy as np

            mask = np.flipud(mask)

            if (
                dtype not in [None, 'u1', 'f1', 'f4'] or
                mask.dtype not in [np.uint8, np.float32]
            ):
                raise Exception('The only accepted "dtype" are "u1", "f1" and "f4" for moderngl, and "np.uint8" and "np.float32".')
            
            return (
                np.clip(mask * 255.0, 0, 255).astype(np.uint8)
                if (
                    dtype in ['u1', 'f1'] and
                    mask.dtype == np.float32
                ) else
                (mask.astype(np.float32) / 255.0)
                if (
                    dtype == 'f4' and 
                    mask.dtype == np.uint8
                ) else
                # f1 and np.uint8 is like this
                mask
            )

        mask_tex = opengl_context.texture(
            (w, h),
            components = number_of_components,
            # We need to make some clippings and
            # transformations as in 'yta_video_opengl'
            data = prepare_mask(mask, dtype).tobytes(),
            dtype = dtype
        )
        
        mask_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        # TODO: This below was suggested but it is working
        # without it
        # Make R be all the channels
        #mask_tex.swizzle = 'RRRR'
        #opengl_context.unpack_alignment = 1

        return mask_tex

class SelectionMaskGenerator:
    """
    *Class to be used as a static class*
    
    Class to simplify the way we generate selection
    masks, to be used when handling selection mask
    for CPU or GPU processing.
    """

    texture: _TextureSelectionMaskGenerator = _TextureSelectionMaskGenerator
    """
    Shortcut to the generation of the moderngl textures
    selection masks.
    """
    numpy: _NumpySelectionMaskGenerator = _NumpySelectionMaskGenerator
    """
    Shortcut to the generation of numpy arrays as 
    selection masks.
    """
    
def _get_width_height_and_number_of_channels_from_input(
    input: Union['moderngl.Texture', 'np.ndarray']
) -> tuple[int, int, int]:
    """
    *For internal use only*

    Get the width, the height and the number of
    channels we need to use when creating the
    selection mask to fit the provided `input`.

    They will come as a tuple:
    - `(width, height, number_of_channels)`
    """
    if PythonValidator.is_numpy_array(input):
        return _get_width_height_and_number_of_channels_from_numpy_array(input)
    elif PythonValidator.is_instance_of(input, 'Texture'):
        return _get_width_height_and_number_of_channels_from_moderngl_texture(input)
    else:
        raise Exception('The "input" provided is not a numpy array nor a moderngl Texture.')

@requires_dependency('numpy', 'yta_editor_utils', 'numpy')
def _get_width_height_and_number_of_channels_from_numpy_array(
    input: 'np.ndarray'
) -> tuple[int, int, int]:
    """
    *For internal use only*

    *The "numpy" library is required"

    Get the width, the height and the number of
    channels we need to use when creating the
    selection mask to fit the provided `input`.

    They will come as a tuple:
    - `(width, height, number_of_channels)`
    """
    h, w = input.shape[:2]
    number_of_channels = (
        input.shape[2]
        if input.ndim == 3 else
        1
    )

    return w, h, number_of_channels

@requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
def _get_width_height_and_number_of_channels_from_moderngl_texture(
    input: 'moderngl.Texture'
) -> tuple[int, int, int]:
    """
    *For internal use only*

    *The "moderngl" library is required"

    Get the width, the height and the number of
    channels we need to use when creating the
    selection mask to fit the provided `input`.

    They will come as a tuple:
    - `(width, height, number_of_channels)`
    """
    w, h = input.size
    number_of_channels = input.components

    return w, h, number_of_channels

@requires_dependency('numpy', 'yta_editor_utils', 'numpy')
def _get_numpy_dtype_from_moderngl_dtype(
    dtype: str
) -> 'np.ndarray':
    """
    *For internal use only*

    *The "numpy" library is required"

    Transform the moderngl dtype string into the
    numpy dtype.
    """
    import numpy as np

    if dtype not in ['u1', 'f1', 'f4']:
        # TODO: Maybe omit 'f4' as we don't use it
        raise Exception(f'Unexpected dtype "{dtype}". The accepted values are "u1", "f1" and "f4".')

    return (
        np.uint8
        if dtype in ['u1', 'f1'] else
        np.float32
    )
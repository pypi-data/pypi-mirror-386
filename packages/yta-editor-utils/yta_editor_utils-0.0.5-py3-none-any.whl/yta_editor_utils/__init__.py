"""
This is the utils module related to the main
editor.
"""
from yta_validation import PythonValidator
from yta_programming.decorators.requires_dependency import requires_dependency
from typing import Union


@requires_dependency('numpy', 'yta_editor_utils', 'numpy')
@requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
def frame_to_texture(
    frame: Union['VideoFrame', 'np.ndarray'],
    context: 'moderngl.Context',
    numpy_format: str = 'rgb24'
):
    """
    *Optional dependency `numpy` (imported as `numpy`) required*

    *Optional dependency `moderngl` (imported as `moderngl`) required*
    
    Transform the given 'frame' to an opengl
    texture. The frame can be a VideoFrame
    instance (from pyav library) or a numpy
    array.

    (!) This method is useful to transform a
    frame into a texture quick and for a single
    use, but we have the GPUTextureHandler class
    to handle it in an specific contexto to 
    optimize the performance and avoid creating
    textures but rewriting on them.
    """
    import numpy as np
    import moderngl

    # To numpy RGB inverted for opengl
    frame: np.ndarray = (
        np.flipud(frame.to_ndarray(format = numpy_format))
        if PythonValidator.is_instance_of(frame, 'VideoFrame') else
        np.flipud(frame)
    )

    # Sometimes we have 'float32' values but we need to
    # force 'uint8' to be able to work with
    if frame.dtype != np.uint8:
        frame = np.clip(frame, 0, 255).astype(np.uint8)

    return context.texture(
        size = (frame.shape[1], frame.shape[0]),
        components = frame.shape[2],
        data = frame.tobytes()
    )

# TODO: I should make different methods to
# obtain a VideoFrame or a numpy array frame
@requires_dependency('numpy', 'yta_editor_utils', 'numpy')
@requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
def texture_to_frame(
    texture: 'moderngl.Texture',
    do_include_alpha: bool = True
) -> 'np.ndarray':
    """
    *Optional dependency `numpy` (imported as `numpy`) required*

    *Optional dependency `moderngl` (imported as `moderngl`) required*

    Transform an opengl texture into numpy array.

    The `do_include_alpha` will include the
    alpha channel if True.
    """
    import numpy as np
    import moderngl

    data = texture.read(alignment = 1)
    # Read 4 channels always (RGBA8)
    frame = np.frombuffer(data, dtype = np.uint8).reshape((texture.size[1], texture.size[0], 4))
    # TODO: Do this with a utils
    frame = (
        frame
        if do_include_alpha else
        # Discard alpha channel if not needed
        frame[:, :, :3]
    )
    # Opengl gives it with the 'y' inverted
    frame = np.flipud(frame)
    # TODO: This can be returned as a numpy frame

    # This is if we need an 'av' VideoFrame (to
    # export through the demuxer, for example)
    # TODO: I avoid this by now because we don't
    # want to import the pyav library, so this
    # below has to be done with the numpy array
    # received...
    # frame = av.VideoFrame.from_ndarray(frame, format = 'rgba')
    # # TODO: Make this customizable
    # frame = frame.reformat(format = 'yuv420p')

    return frame

# TODO: The code of this one is similar to the
# 'texture_to_frame', so we should keep only one
# (maybe this one)
@requires_dependency('numpy', 'yta_editor_utils', 'numpy')
@requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
def texture_to_numpy(
    texture: 'moderngl.Texture',
    do_include_alpha: bool = True
) -> 'np.ndarray':
    """
    *Optional dependency `numpy` (imported as `numpy`) required*

    *Optional dependency `moderngl` (imported as `moderngl`) required*

    Transform the provided OpenGL `texture` into a numpy
    array to be able to validate the values that are
    contained in the texture.

    The alpha layer will be removed if the parameter
    `do_include_alpha` is set as False.
    """
    import numpy as np
    import moderngl

    data = texture.read()

    # OpenGL uses only f4 and u1 for the textures so
    # we don't need a mapping
    dtype = (
        np.float32
        if texture.dtype == 'f4' else
        np.uint8
    )

    frame = np.frombuffer(
        buffer = data,
        dtype = dtype
    ).reshape(
        texture.height,
        texture.width,
        texture.components
    )

    # Discard alpha channel if not needed
    frame = (
        frame
        if do_include_alpha else
        frame[:, :, :3]
    )

    # Opengl gives it with the 'y' inverted
    frame = np.flipud(frame)

    return frame

# TODO: I think I have this methods in other library
# maybe yta-image-utils (?)
@requires_dependency('cv2', 'yta_editor_utils', 'opencv-python')
def scale_numpy(
    input: 'np.ndarray',
    size: tuple[int, int]
) -> 'np.ndarray':
    """
    *Optional dependency `opencv-python` required*

    Resize the 'input' numpy array to the provided 'size'
    if needed, using a rescaling method with 'opencv-python'
    (cv2).

    The 'size' provided must be (width, height).
    """
    import cv2

    return cv2.resize(input, size, interpolation = cv2.INTER_LINEAR)

@requires_dependency('PIL', 'yta_editor_utils', 'pillow')
@requires_dependency('numpy', 'yta_editor_utils', 'numpy')
def scale_numpy_pillow(
    input: 'np.ndarray',
    size: tuple[int, int]
) -> 'np.ndarray':
    """
    *Optional dependency `pillow` (imported as `PIL`) required*

    *Optional dependency `numpy` (imported as `numpy`) required*

    Resize the 'input' numpy array to the provided 'size'
    if needed, using a rescaling method with 'pillow'
    (PIL).

    The 'size' provided must be (width, height).
    """
    from PIL import Image
    import numpy as np

    return np.array(Image.fromarray(input).resize(size, Image.BILINEAR))

@requires_dependency('PIL', 'yta_editor_utils', 'pillow')
@requires_dependency('numpy', 'yta_editor_utils', 'numpy')
def read_image_as_numpy(
    path: str,
    do_read_as_rgba: bool = True,
    size: Union[tuple[int, int], None] = None
) -> 'np.ndarray':
    """
    *Optional dependency `pillow` (imported as `PIL`) required*

    *Optional dependency `numpy` (imported as `numpy`) required*

    Read an image from a file and transform it into a
    numpy array. It will force the 'size' if provided,
    or leave the original one if it is None.
    """
    from PIL import Image
    import numpy as np

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

@requires_dependency('PIL', 'yta_editor_utils', 'pillow')
def numpy_to_file(
    input: 'np.ndarray',
    output_filename: str
) -> str:
    """
    *Optional dependency `pillow` (imported as `PIL`) required*

    Export the provided 'array' numpy array as a file
    with the given 'output_filename' name.
    """
    from PIL import Image

    Image.fromarray(input).save(output_filename)

    return output_filename

@requires_dependency('PIL', 'yta_editor_utils', 'pillow')
def texture_to_file(
    texture: 'moderngl.Texture',
    output_filename: str
) -> str:
    """
    *Optional dependency `pillow` (imported as `PIL`) required*

    Export the provided OpenGL texture 'texture' as a
    file with the given 'output_filename' name.
    """
    return numpy_to_file(
        input = texture_to_frame(texture),
        output_filename = output_filename
    )
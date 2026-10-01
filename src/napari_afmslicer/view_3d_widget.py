"""View images in three dimensions."""

from typing import TYPE_CHECKING

import napari.types
from afmslicer.slicer import slice_3d
from magicgui import magic_factory
from napari import current_viewer  # pylint: disable=no-name-in-module
from napari.layers import Image

if TYPE_CHECKING:
    import napari


@magic_factory(
    image={"label": "Image"},
    binary={
        "label": "Produce binary array.",
    },
)
def view_3d(
    image: Image,
    binary: bool = False,
) -> napari.types.LayerDataTuple:
    """
    View image in three dimensions.

    Parameters
    ----------
    image : Image
        Image to be viewed in three dimensions, typically post-filtering.
    binary : bool
        Whether to convert data points to binary, normally you won't want this.

    Returns
    -------
    napari.types.LayerDataTuple:
        Modified image in three-dimensions.
    """
    three_dimensions = slice_3d(array=image.data, scaling=image.metadata["px2nm"], binary=binary)
    viewer = current_viewer()
    viewer.dims.ndisplay = 3
    return (
        three_dimensions,
        {"name": f"{image.name}_3D"},
        "image",
    )

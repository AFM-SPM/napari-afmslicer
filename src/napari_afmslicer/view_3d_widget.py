"""View images in three dimensions."""

from typing import TYPE_CHECKING

import napari.types
from magicgui import magic_factory
from napari import current_viewer  # pylint: disable=no-name-in-module
from napari.layers import Image
from napari_topostats.utils import afm2stack

if TYPE_CHECKING:
    import napari


@magic_factory(
    by_slices={"label": "Whether to stack by slices."},
    numslices={"label": "Number of slices.", "min": 20, "max": 2000, "step": 1},
    resolution={"label": "Resolution.", "min": 1.0, "max": 100.0, "step": 0.1},
)
def view_3d(
    image: Image,
    by_slices: bool = True,
    numslices: int = 255,
    resolution: float = 1.0,
) -> napari.types.LayerDataTuple:
    """
    View image in three dimensions.

    Parameters
    ----------
    image : Image
        Image to be viewed in three dimensions.
    by_slices : bool
        Whether to stack by slices (default ``True``). If ``False`` then ``resolution`` is used.
    numslices : int
        Number of slices to create.
    resolution : float
        The resolution/distance between each slice, by default 1.0.

    Returns
    -------
    napari.types.LayerDataTuple:
        Modified image in three-dimensions.
    """
    three_dimensions = afm2stack(image=image.data, by_slices=by_slices, numslices=numslices, resolution=resolution)
    viewer = current_viewer()
    viewer.dims.ndisplay = 3
    return (
        three_dimensions,
        {"name": f"{image.name}_3D"},
        "image",
    )

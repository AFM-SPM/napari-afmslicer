"""Utilities for slicing images."""

import copy

from napari.layers import Image
from napari.utils import notifications


def update_metadata(image: Image, source_image: Image) -> None:
    """Update metadata of `image` with metadata from `source_image`.

    Parameters
    ----------
    image : Image
        An image to be updated.
    source_image : Image
        The source image from which metadata is copied.

    Raises
    ------
    KeyError
        If `source_image.metadata` (a dictionary) is missing either `px2nm` or `image_path` in its keys a `KeyError`
        will be raised.
    ValueError
        If `source_image` is `None` a `ValueError` is raised.
    """

    if source_image is None:
        raise ValueError("Select the original image layer.")
    if "px2nm" not in source_image.metadata:
        raise KeyError(f"The selected source layer {source_image.name!r} is missing 'px2nm' from metadata.")
    if "image_path" not in source_image.metadata:
        raise KeyError(f"The selected source layer {source_image.name!r} is missing 'image_path' from metadata.")
    # image.metadata = dict(image.metadata)
    # image.metadata["px2nm"] = source_image.metadata["px2nm"]
    # image.metadata["image_path"] = source_image.metadata["image_path"]
    image.metadata = copy.deepcopy(source_image.metadata)
    image.name = image.name.replace(" ", "_")
    image.name = image.name.replace("[", "").replace("]", "")
    notifications.show_info(f"Metadata for {image.name} updated from {source_image.name}")

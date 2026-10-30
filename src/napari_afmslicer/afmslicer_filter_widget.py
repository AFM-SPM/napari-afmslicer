"""Widgets for running AFMSlicer filtering."""

from pkgutil import get_data
from typing import TYPE_CHECKING

import afmslicer
import napari.types
import yaml
from afmslicer.filter import SlicingFilter
from magicgui import magic_factory
from napari.layers import Image
from topostats import __version__ as topostats_version
from topostats.classes import TopoStats

from napari_afmslicer import utils

if TYPE_CHECKING:
    import napari


@magic_factory(
    image={"label": "Image"},
    source_image={"label": "Original image (uncropped)"},
    row_alignment_quantile={
        "label": "Row alignment quantile",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
    gaussian_size={
        "label": "Gaussian size",
        "min": 0.5,
        "max": 4.0,
        "step": 0.001,
    },
    gaussian_mode={
        "label": "Gaussian mode",
        "choices": {"reflect", "constant", "nearest", "mirror", "wrap"},
    },
    remove_scars={"label": "Remove scars"},
    removal_iterations={
        "label": "Removal iterations",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    threshold_low={
        "label": "Low threshold\n(low values make scar removal more sensitive)",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
    threshold_high={
        "label": "High threshold\n(low values make scar removal more sensitive)",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
    max_scar_width={
        "label": "Maximum scar width",
        "min": 2,
        "max": 16,
        "step": 1,
    },
    min_scar_length={
        "label": "Minimum scar length",
        "min": 5,
        "max": 200,
        "step": 1,
    },
    call_button="Filter",
)
def afmslicer_filter_widget(  # pylint: disable=too-many-positional-arguments,too-many-arguments
    image: Image,
    source_image: Image,
    row_alignment_quantile: float = 0.5,
    gaussian_size: float = 2.0,
    gaussian_mode: str = "nearest",
    remove_scars: bool = True,
    removal_iterations: int = 2,
    threshold_low: float = 0.250,
    threshold_high: float = 0.666,
    max_scar_width: int = 4,
    min_scar_length: int = 16,
) -> napari.types.LayerDataTuple:
    """
    AFMSlicer filter widget for running ``AFMSlicer.filter.SlicingFilter()``.

    Parameters
    ----------
    image : Image
        Image to be filtered.
    source_image : Image
        Original source image, typically the uncropped image.
    row_alignment_quantile : float
        Quantile to use for median flattening, typically ``0.5`` but other values can be used.
    gaussian_size : float
        Size of Gaussian dilation to use.
    gaussian_mode : str
        Method of Gaussian dilation.
    remove_scars : bool
        Whether to remove scars or not. Default is ``True``.
    removal_iterations : int
        Number of scar iterations to run.
    threshold_low : float
        Low threshold for scar removal. Lower values make scar removal more sensitive.
    threshold_high : float
        High threshold for scar removal. Lower values make scar removal more sensitive.
    max_scar_width : int
        Maximum width of scars in pixels.
    min_scar_length : int
        Maximum length of scars in pixels.

    Returns
    -------
    napari.types.LayerDataTuple
        Modified image.
    """
    # Load configuration and update with parameters from Napari
    config = get_data(package=afmslicer.__package__, resource="default_config.yaml")
    config = yaml.full_load(config)
    config["filter"]["row_alignment_quantile"] = row_alignment_quantile
    config["filter"]["gaussian_size"] = gaussian_size
    config["filter"]["gaussian_mode"] = gaussian_mode
    config["filter"]["remove_scars"]["run"] = remove_scars
    config["filter"]["remove_scars"]["removal_iterations"] = removal_iterations
    config["filter"]["remove_scars"]["threshold_low"] = threshold_low
    config["filter"]["remove_scars"]["threshold_high"] = threshold_high
    config["filter"]["remove_scars"]["max_scar_width"] = max_scar_width
    config["filter"]["remove_scars"]["min_scar_length"] = min_scar_length
    # napari-crops are plain numpy arrays and don't inherit px2nm so we need to use source_image if we have such a
    # cropped layer
    if "px2nm" not in image.metadata:
        utils.update_metadata(image=image, source_image=source_image)
    # Make topostats_object
    topostats_object = TopoStats(
        image_original=image.data,
        filename="",
        # napari-AFMReader returns very basic info in img_layer.metadata
        pixel_to_nm_scaling=image.metadata["px2nm"],
        img_path=image.metadata["image_path"],
        basename="",
        topostats_version=topostats_version,
        config=config,
    )
    # Instantiate afmslicer.SlicingFilter and filter image
    slicing_filter = SlicingFilter(
        topostats_object=topostats_object,
        row_alignment_quantile=row_alignment_quantile,
        gaussian_size=gaussian_size,
        gaussian_mode=gaussian_mode,
        remove_scars=config["filter"]["remove_scars"],
    )
    slicing_filter.filter_image()
    # image.metadata["img_name"] = image.name
    return (
        topostats_object.image,
        {"name": f"{image.name}_filtered", "metadata": image.metadata},  # "config": config},
        "image",
    )

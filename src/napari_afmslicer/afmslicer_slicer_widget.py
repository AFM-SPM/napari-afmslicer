"""Widgets for running AFMSlicer slicing."""

from pathlib import Path
from pkgutil import get_data
from typing import TYPE_CHECKING

import afmslicer
import yaml
from afmslicer import statistics
from afmslicer.classes import AFMSlicer
from magicgui import magic_factory
from napari.layers import Image
from topostats.io import write_yaml

if TYPE_CHECKING:
    pass


@magic_factory(
    image={"label": "Image"},
    slices={"label": "Slices", "widget_type": "Slider", "min": 2, "max": 255, "step": 1},
    segment_method={
        "label": "Segmentation method",
        "choices": ["label", "watershed"],
    },
    area={"label": "Area"},
    minimum_size={"label": "Minimum Size", "min": "20000", "max": 20000000, "step": 100},
    centroid={"label": "Centroid"},
    feret_maximum={"label": "Feret Maximum"},
    plotting_format={"label": "Save image format", "choices": ["png", "svg"]},
    plotting_gif_duration={"label": "Gif duration", "widget_type": "Slider", "min": 10, "max": 1000, "step": 1},
    output_dir={"label": "Output directory", "widget_type": "LineEdit", "value": "output"},
    call_button="Slice Image and Summarise",
)
def afmslicer_slicing_widget(  # pylint: disable=too-many-positional-arguments
    image: Image,
    slices: int = 50,
    segment_method: str = "label",
    area: bool = True,
    minimum_size: int = 20000,
    centroid: bool = False,
    feret_maximum: bool = False,
    plotting_format: str = "png",
    plotting_gif_duration: int = 100,
    output_dir: str | Path = Path("output"),
) -> None:
    """
    Wrapper for updating configuration and slicing the image.

    Parameters
    ----------
    image : Image
        Napari Image to be sliced.
    slices : int
        Number of slices to create through the image between the min and max height.
    segment_method : str
        Method for segmenting images.
    area : bool
        Whether to calculate the area of pores on each slice, pretty much always needed.
    minimum_size : int
        Minimum size in nanometres squared of objects to retain, <= ``minimum_size`` are masked & excluded.
    centroid : bool
        Whether to calculate the centroid of pores on each slice and include in output.
    feret_maximum : bool
        Whether to calculate the maximum feret distance of pores on each slice and include in output.
    plotting_format : str
        Format to save images, default ``png``, other options are those supported by Matplotlib.
    plotting_gif_duration : int
        Microseconds pause between images in ``gif`` file.
    output_dir : str | Path
        Path to output directory where images and ``.csv`` files are saved.
    """
    # Load configuration and update with parameters from Napari
    config = get_data(package=afmslicer.__package__, resource="default_config.yaml")
    config = yaml.full_load(config)
    config["slicing"]["slices"] = slices
    config["slicing"]["segment_method"] = segment_method
    config["slicing"]["area"] = area
    config["slicing"]["minimum_size"] = minimum_size
    config["slicing"]["centroid"] = centroid
    config["slicing"]["feret_maximum"] = feret_maximum
    config["plotting"]["format"] = plotting_format
    config["plotting"]["gif_duration"] = plotting_gif_duration
    config["output_dir"] = Path(output_dir)
    clean_image_name = image.name.replace("_filtered", "")
    # Make AFMSlicer
    afmslicer_object = AFMSlicer(
        image=image.data,
        pixel_to_nm_scaling=image.metadata["px2nm"],
        img_path=image.metadata["image_path"],
        filename=clean_image_name,
        slices=slices,
        config=config,
    )
    afmslicer_object.slice_image()
    # Extract statistics and write to disk along with configuration file
    # Need to add in image name and reset the index (normally added by `pd.concat()` when running at the command line
    # but here we only ever have a single image so have to manually add it.)
    afmslicer_object.statistics["image"] = clean_image_name
    afmslicer_object.statistics = afmslicer_object.statistics.reset_index().set_index(["image", "layer", "pore"])
    afmslicer_object.statistics = statistics.classify_pore_size(
        df=afmslicer_object.statistics,
        area_thresholds=config["slicing"]["area_thresholds"],
        area_colors=config["slicing"]["area_colors"],
        area_val="area",
    )
    afmslicer_object.statistics.to_csv(Path(config["output_dir"]) / f"{clean_image_name}_statistics.csv", index=False)
    color_count_df = statistics.summarise_pores(df=afmslicer_object.statistics)
    color_count_df.to_csv(Path(config["output_dir"]) / f"{clean_image_name}_color_count.csv")
    write_yaml(config, output_dir=config["output_dir"])

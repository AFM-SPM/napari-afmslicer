"""Tests of the afmslicer_slicer_widget module."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from napari.layers import Image

# pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments


def copy_px2nm(image: Image, source_image: Image) -> None:
    """Test side effect for copying scaling metadata."""
    image.metadata["px2nm"] = source_image.metadata["px2nm"]


@pytest.mark.parametrize(
    (
        "slices",
        "segment_method",
        "area",
        "minimum_size",
        "centroid",
        "feret_maximum",
        "plotting_format",
        "plotting_gif_duration",
        "metadata_present",
    ),
    [
        (20, "label", True, 20000, False, False, "png", 100, True),
        (75, "watershed", False, 50000, True, True, "svg", 250, False),
    ],
)
def test_slicing_widget_runs_pipeline(
    slicing_function: Any,
    slicing_mocks: dict[str, MagicMock],
    sample1_image: Image,
    sample2_image: Image,
    tmp_path: Path,
    slices: int,
    segment_method: str,
    area: bool,
    minimum_size: int,
    centroid: bool,
    feret_maximum: bool,
    plotting_format: str,
    plotting_gif_duration: int,
    metadata_present: bool,
) -> None:
    """Test the `slicing_widget.py` using mocks."""
    image: Image = sample1_image
    source_image: Image = sample2_image
    output_dir: Path = tmp_path / "results"
    output_dir.mkdir()

    if not metadata_present:
        image.metadata.pop("px2nm", None)
        slicing_mocks["update_metadata"].side_effect = copy_px2nm
    slicing_function(
        image=image,
        source_image=source_image,
        slices=slices,
        segment_method=segment_method,
        area=area,
        minimum_size=minimum_size,
        centroid=centroid,
        feret_maximum=feret_maximum,
        plotting_format=plotting_format,
        plotting_gif_duration=plotting_gif_duration,
        output_dir=output_dir,
    )
    slicing_mocks["AFMSlicer"].assert_called_once()
    slicer_kwargs: dict[str, Any] = slicing_mocks["AFMSlicer"].call_args.kwargs
    config: dict[str, Any] = slicer_kwargs["config"]

    assert slicer_kwargs["image"] is image.data
    assert slicer_kwargs["pixel_to_nm_scaling"] == image.metadata["px2nm"]
    assert slicer_kwargs["img_path"] == image.metadata["image_path"]
    assert slicer_kwargs["filename"] == image.name
    assert slicer_kwargs["slices"] == slices

    assert config["slicing"]["slices"] == slices
    assert config["slicing"]["segment_method"] == segment_method
    assert config["slicing"]["area"] is area
    assert config["slicing"]["minimum_size"] == minimum_size
    assert config["slicing"]["centroid"] is centroid
    assert config["slicing"]["feret_maximum"] is feret_maximum
    assert config["plotting"]["format"] == plotting_format
    assert config["plotting"]["gif_duration"] == plotting_gif_duration
    assert config["output_dir"] == output_dir

    if metadata_present:
        slicing_mocks["update_metadata"].assert_not_called()
    else:
        slicing_mocks["update_metadata"].assert_called_once_with(
            image=image,
            source_image=source_image,
        )
    slicing_mocks["AFMSlicer"].return_value.slice_image.assert_called_once_with()
    slicing_mocks["classify_pore_size"].assert_called_once()
    slicing_mocks["summarise_pores"].assert_called_once()
    slicing_mocks["write_yaml"].assert_called_once_with(
        config,
        output_dir=output_dir,
    )
    slicing_mocks["show_info"].assert_called_once_with(f"🔪 Slicing complete results are in  : {output_dir} 🔪")
    assert (output_dir / f"{image.name}_statistics.csv").is_file()
    assert (output_dir / f"{image.name}_color_count.csv").is_file()

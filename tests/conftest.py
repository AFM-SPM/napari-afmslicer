"""Fixtures for tests."""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

import numpy as np
import numpy.typing as npt
import pandas as pd
import pytest
from AFMReader.spm import load_spm
from napari.layers import Image
from napari.types import LayerDataTuple

from napari_afmslicer import afmslicer_filter_widget, afmslicer_slicer_widget

BASE_DIR = Path().cwd()
RESOURCES = BASE_DIR / "tests" / "resources"
SPM_DIR = RESOURCES / "spm"


@pytest.fixture
def sample1_image() -> Image:
    """Load sample1.spm and wrap its data as a napari Image layer."""
    sample_path = SPM_DIR / "sample1.spm"

    data: npt.NDArray
    px2nm: float
    data, px2nm = load_spm(file_path=str(sample_path), channel="Height")
    layer: Image = Image(
        data=np.asarray(data),
        name=sample_path.name,
        metadata={
            "px2nm": px2nm,
            "image_path": str(sample_path),
        },
    )
    return layer


@pytest.fixture
def sample2_image() -> Image:
    """Load sample2.spm and wrap its data as a napari Image layer."""
    sample_path = SPM_DIR / "sample2.spm"

    data: npt.NDArray
    px2nm: float
    data, px2nm = load_spm(file_path=str(sample_path), channel="Height")
    layer = Image(
        data=np.asarray(data),
        name=sample_path.name,
        metadata={
            "px2nm": px2nm,
            "image_path": str(sample_path),
        },
    )
    return layer


@pytest.fixture
def filter_function() -> Callable[..., LayerDataTuple]:
    """Return the Python function wrapped by the magic_factory."""
    function: object = afmslicer_filter_widget.afmslicer_filter_widget.keywords["function"]
    return cast(Callable[..., LayerDataTuple], function)


@pytest.fixture
def widget_mocks() -> Iterator[tuple[MagicMock, MagicMock, MagicMock]]:
    """Mock configuration loading and the TopoStats/filtering pipeline."""
    config_yaml: bytes = b"""
filter:
  row_alignment_quantile: 0.5
  gaussian_size: 2.0
  gaussian_mode: nearest
  remove_scars:
    run: true
    removal_iterations: 2
    threshold_low: 0.25
    threshold_high: 0.666
    max_scar_width: 4
    min_scar_length: 16
"""

    with (
        patch.object(afmslicer_filter_widget, "get_data", return_value=config_yaml),
        patch.object(afmslicer_filter_widget, "TopoStats") as topostats_cls,
        patch.object(afmslicer_filter_widget, "SlicingFilter") as slicing_filter_cls,
    ):
        topostats = topostats_cls.return_value
        topostats.image = np.zeros((4, 4))
        yield topostats_cls, topostats, slicing_filter_cls


# @pytest.fixture
# def slicing_function() -> Callable[..., None]:
#     """Return the Python function wrapped by the magic_factory."""
#     function: object = afmslicer_slicer_widget.keywords["function"]
#     return cast(Callable[..., None], function)


@pytest.fixture
def slicing_function() -> Callable[..., None]:
    """Return the Python function wrapped by the magic_factory."""
    function: object = afmslicer_slicer_widget.afmslicer_slicing_widget.keywords["function"]
    return cast(Callable[..., None], function)


@pytest.fixture
def slicing_mocks() -> Iterator[dict[str, MagicMock]]:
    """Mock AFMSlicer, statistics, configuration, and notification calls."""
    config_yaml: bytes = b"""
slicing:
  area_thresholds: [10, 100]
  pore_colors: ["blue", "red"]
plotting: {}
output_dir: old_output
"""

    initial_statistics: pd.DataFrame = pd.DataFrame(
        {"area": [25.0]},
        index=pd.MultiIndex.from_tuples(
            [(0, 1)],
            names=["layer", "pore"],
        ),
    )
    summary: pd.DataFrame = pd.DataFrame({"count": [1]})

    def return_dataframe(df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:  # pylint: disable=unused-argument
        return df

    with (
        patch.object(afmslicer_slicer_widget, "get_data", return_value=config_yaml),
        patch.object(afmslicer_slicer_widget, "AFMSlicer") as afmslicer_class,
        patch.object(
            afmslicer_slicer_widget.statistics,
            "classify_pore_size",
            side_effect=return_dataframe,
        ) as classify_pores,
        patch.object(
            afmslicer_slicer_widget.statistics,
            "summarise_pores",
            return_value=summary,
        ) as summarise_pores,
        patch.object(afmslicer_slicer_widget, "write_yaml") as write_yaml,
        patch.object(afmslicer_slicer_widget.notifications, "show_info") as show_info,
        patch.object(afmslicer_slicer_widget.utils, "update_metadata") as update_metadata,
    ):
        afmslicer_class.return_value.statistics = initial_statistics

        yield {
            "AFMSlicer": afmslicer_class,
            "classify_pore_size": classify_pores,
            "summarise_pores": summarise_pores,
            "write_yaml": write_yaml,
            "show_info": show_info,
            "update_metadata": update_metadata,
        }

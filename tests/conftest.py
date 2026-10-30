"""Fixtures for tests."""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import numpy as np
import numpy.typing as npt
import pytest
from AFMReader.spm import load_spm
from napari.layers import Image
from napari.types import LayerDataTuple

from napari_afmslicer import afmslicer_filter_widget

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

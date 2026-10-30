"""Tests of the afmslicer_filter_widget module."""

from collections.abc import Callable
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from napari.layers import Image
from napari.types import LayerDataTuple

from napari_afmslicer import afmslicer_filter_widget


@pytest.mark.parametrize(
    ("parameter", "value", "config_path"),
    [
        pytest.param(
            "row_alignment_quantile",
            0.75,
            (
                "filter",
                "row_alignment_quantile",
            ),
            id="row alignment quantile",
        ),
        pytest.param(
            "gaussian_size",
            1.25,
            (
                "filter",
                "gaussian_size",
            ),
            id="gaussian size",
        ),
        pytest.param(
            "gaussian_mode",
            "reflect",
            (
                "filter",
                "gaussian_mode",
            ),
            id="gaussian mode",
        ),
        pytest.param("remove_scars", False, ("filter", "remove_scars", "run"), id="remove scars"),
        pytest.param(
            "removal_iterations", 5, ("filter", "remove_scars", "removal_iterations"), id="removal iterations"
        ),
        pytest.param("threshold_low", 0.1, ("filter", "remove_scars", "threshold_low"), id="threshold low"),
        pytest.param("threshold_high", 0.8, ("filter", "remove_scars", "threshold_high"), id="threshold high"),
        pytest.param("max_scar_width", 8, ("filter", "remove_scars", "max_scar_width"), id="max scar width"),
        pytest.param("min_scar_length", 32, ("filter", "remove_scars", "min_scar_length"), id="min scar width"),
    ],
)
def test_filter_parameters_are_passed_to_filter(
    sample1_image: Image,
    filter_function: Callable[..., LayerDataTuple],
    widget_mocks: tuple[MagicMock, MagicMock, MagicMock],
    parameter: str,
    value: object,
    config_path: tuple[str, ...],
) -> None:
    """Test parameters are correctly passed to `afmslicer_filter_widget()`."""
    topostats_cls, _, _ = widget_mocks

    filter_function(
        image=sample1_image,
        source_image=sample1_image,
        **{parameter: value},
    )

    config: object = topostats_cls.call_args.kwargs["config"]
    assert isinstance(config, dict)
    # Pull out the relevant part of the dictionary
    for key in config_path[:-1]:
        nested_config = config[key]
        assert isinstance(nested_config, dict)
        config = nested_config
    assert config[config_path[-1]] == value


def test_construct_topostats(
    sample1_image: Image,
    filter_function: Callable[..., LayerDataTuple],
    widget_mocks: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    """Test that `TopoStats` object is correctly instantiated."""
    topostats_cls, _, _ = widget_mocks
    filter_function(
        image=sample1_image,
        source_image=sample1_image,
    )
    kwargs = topostats_cls.call_args.kwargs
    np.testing.assert_array_equal(kwargs["image_original"], sample1_image.data)
    assert kwargs["pixel_to_nm_scaling"] == sample1_image.metadata["px2nm"]
    assert kwargs["img_path"] == sample1_image.metadata["image_path"]


def test_filter_returns_layer_data_tuple(
    sample1_image: Image,
    filter_function: Callable[..., LayerDataTuple],
    widget_mocks: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    """Test `afmslicer_filter_widget()` filters the image and returns a valid layer."""
    _, topostats, slicing_filter_cls = widget_mocks
    filtered_data = np.ones((4, 4))
    topostats.image = filtered_data
    result = filter_function(
        image=sample1_image,
        source_image=sample1_image,
    )
    slicing_filter_cls.return_value.filter_image.assert_called_once_with()
    assert result[0] is filtered_data
    assert result[1]["name"] == f"{sample1_image.name}_filtered"
    assert result[1]["metadata"] == sample1_image.metadata
    assert result[2] == "image"


def test_restore_metadata(
    sample1_image: Image,
    filter_function: Callable[..., LayerDataTuple],
) -> None:
    """Test `px2nm` and other metadata are updated from `source_image` if missing."""
    cropped_image = Image(
        data=sample1_image.data[1:, 1:],
        name=f"{sample1_image.name}_crop",
        metadata={},
    )
    real_update_metadata = afmslicer_filter_widget.utils.update_metadata
    with patch.object(
        afmslicer_filter_widget.utils,
        "update_metadata",
        wraps=real_update_metadata,
    ) as update_metadata:
        filter_function(
            image=cropped_image,
            source_image=sample1_image,
        )
        update_metadata.assert_called_once_with(
            image=cropped_image,
            source_image=sample1_image,
        )
    assert cropped_image.metadata["px2nm"] == sample1_image.metadata["px2nm"]
    assert cropped_image.metadata["image_path"] == sample1_image.metadata["image_path"]


def test_no_restore_metadata(
    sample1_image: Image,
    filter_function: Callable[..., LayerDataTuple],
) -> None:
    """Test metadata is not restored when crop already has `px2nm`."""
    with patch.object(afmslicer_filter_widget.utils, "update_metadata") as update_metadata:
        filter_function(
            image=sample1_image,
            source_image=sample1_image,
        )
        update_metadata.assert_not_called()

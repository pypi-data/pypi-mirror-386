"""Tests for analysis utils."""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import h5py
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from playNano.analysis.utils import common, frames, particles
from playNano.analysis.utils.common import (
    NumpyEncoder,
    load_analysis_from_hdf5,
    safe_json_dumps,
)

matplotlib.use("Agg")  # Use a non-interactive backend suitable for testing

# --- Common Utils ---


def create_hdf5_file(structure, dataset_name="analysis_record"):
    """Make a hdf5 file for testing."""
    temp_file = NamedTemporaryFile(delete=False, suffix=".h5")
    with h5py.File(temp_file.name, "w") as h5file:
        group = h5file.create_group(dataset_name)

        def recurse_write(g, obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    recurse_write(g.create_group(k), v)
            elif isinstance(obj, list):
                if len(obj) == 0:
                    g.create_group("empty")
                else:
                    for i, item in enumerate(obj):
                        recurse_write(g.create_group(f"item_{i}"), item)
            elif isinstance(obj, np.ndarray):
                g.create_dataset("values", data=obj)
            elif isinstance(obj, (int, float, str)):
                g.attrs["value"] = obj
            else:
                g.attrs["value"] = str(obj)

        recurse_write(group, structure)
    return temp_file.name


def test_load_valid_structure():
    """Test loading a nested structure with arrays, lists, dicts and strings."""
    data = {
        "a": np.array([1.0, 2.0]),
        "b": [1.0, 2.0],
        "c": {"d": 3.0},
        "e": [],
        "f": "text",
    }
    file_path = create_hdf5_file(data)
    result = load_analysis_from_hdf5(file_path)
    assert result["a"].tolist() == [1, 2]
    assert result["b"] == [1, 2]
    assert result["c"]["d"] == 3
    assert result["e"] == []
    assert result["f"] == "text"


def test_missing_dataset():
    """Test that a KeyError is raised when the specified dataset is missing."""
    file_path = create_hdf5_file({}, dataset_name="other_record")
    with pytest.raises(KeyError, match="Dataset 'analysis_record' not found"):
        load_analysis_from_hdf5(file_path, dataset_name="analysis_record")


def test_scalar_float_conversion():
    """Test that scalar NumPy float is converted to int if it's integer-valued."""
    data = {"x": np.array(5.0)}
    file_path = create_hdf5_file(data)
    result = load_analysis_from_hdf5(file_path)
    assert result["x"] == 5


def test_scalar_array_conversion():
    """Test that scalar array with a single float value is converted to int."""
    file_path = create_hdf5_file({"scalar": np.array(5.0)})
    result = load_analysis_from_hdf5(file_path)
    assert result["scalar"] == 5


def test_full_array_conversion():
    """Test that a full NumPy float array with int values is converted to int array."""
    file_path = create_hdf5_file({"array": np.array([1.0, 2.0, 3.0])})
    result = load_analysis_from_hdf5(file_path)
    assert isinstance(result["array"], np.ndarray)
    assert result["array"].tolist() == [1, 2, 3]


def test_string_array_conversion():
    """Test that a NumPy byte string array is converted to a list of Python strings."""
    file_path = create_hdf5_file({"strings": np.array([b"foo", b"bar"])})
    result = load_analysis_from_hdf5(file_path)
    assert result["strings"].tolist() == ["foo", "bar"]


def test_empty_list_handling():
    """Test that an empty list is correctly reconstructed from the HDF5 group."""
    file_path = create_hdf5_file({"empty_list": []})
    result = load_analysis_from_hdf5(file_path)
    assert result["empty_list"] == []


def test_value_attribute_handling():
    """Test that primitive values stored in attributes are loaded and converted."""
    file_path = create_hdf5_file({"value": 42.0})
    result = load_analysis_from_hdf5(file_path)
    assert result["value"] == 42


def test_list_structure_handling():
    """Test that a list-like group with item_* keys reconstructs as a Python list."""
    file_path = create_hdf5_file({"mylist": [1.0, 2.0, 3.0]})
    result = load_analysis_from_hdf5(file_path)
    assert result["mylist"] == [1, 2, 3]


def test_dict_structure_handling():
    """Test that a dict-like group is reconstructed as a Python dictionary."""
    file_path = create_hdf5_file({"mydict": {"a": 1.0, "b": 2.0}})
    result = load_analysis_from_hdf5(file_path)
    assert result["mydict"] == {"a": 1, "b": 2}


def test_numpy_encoder_serializes_ndarray():
    """Test that numpy encoder serializes a numpy array."""
    data = {"arr": np.array([1, 2, 3])}
    json_str = json.dumps(data, cls=common.NumpyEncoder)
    assert json_str == '{"arr": [1, 2, 3]}'


def test_numpy_encoder_raises_for_unserializable():
    """Test that numpy encoder raises error for unserializable."""

    class Dummy:
        pass

    data = {"obj": Dummy()}
    with pytest.raises(TypeError):
        json.dumps(data, cls=common.NumpyEncoder)


def test_numpy_encoder_callable_serialization():
    """Test that callables are serialized to a string with their function name."""

    def dummy_function():
        pass

    data = {"func": dummy_function}
    encoded = json.dumps(data, cls=common.NumpyEncoder)

    assert '"<function dummy_function>"' in encoded


# Sample nested record
sample_record = {
    "metadata": {"experiment": "test", "version": 1.0},
    "results": {"values": [1, 2, 3], "array": np.array([4.5, 5.5])},
}


def test_export_to_hdf5_creates_file():
    """Test export_to_hdf5 creates an HDF5 file on disk."""
    with TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "test.h5"
        common.export_to_hdf5(sample_record, out_path)
        assert out_path.exists()


def test_export_to_hdf5_structure_and_values():
    """Test export_to_hdf5 writes correct structure and values."""
    with TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "test.h5"
        common.export_to_hdf5(sample_record, out_path)
        with h5py.File(out_path, "r") as f:
            root = f["analysis_record"]
            assert "metadata" in root
            assert "results" in root

            # Check scalar attributes

            assert root["metadata"]["experiment"].attrs["value"] == "test"
            assert root["metadata"]["version"].attrs["value"] == 1.0

            # Check array values
            values_ds = root["results"]["values"]
            values_ds = values_ds[
                "values"
            ]  # Access the actual dataset inside the group

            values = [
                json.loads(v) if isinstance(v, (str, bytes)) else v
                for v in values_ds[:]
            ]
            assert values == sample_record["results"]["values"]


def test_safe_json_dumps_serializable():
    """Test that safe_json_dumps serializes a simple object."""
    obj = {"value": np.float32(3.14), "array": np.array([1, 2, 3])}
    result = safe_json_dumps(obj)
    parsed = json.loads(result)  # Should succeed without error
    assert parsed["value"] == pytest.approx(3.14)
    assert parsed["array"] == [1, 2, 3]


def test_safe_json_dumps_fallback(monkeypatch):
    """Test that safe_json_dumps falls back to str() for unserializable objects."""

    # Force the encoder to fail and test fallback to str()
    def failing_default(self, obj):
        raise TypeError("mock failure")

    monkeypatch.setattr(NumpyEncoder, "default", failing_default)
    obj = {"value": 123}
    result = safe_json_dumps(obj)
    assert isinstance(result, str)
    assert "value" in result


def test_safe_json_dumps_non_serializable():
    """Test that safe_json_dumps falls back to str() for non-serializable objects."""
    obj = {"callback": lambda x: x}
    result = safe_json_dumps(obj)
    # Falls back to str()
    assert isinstance(result, str)
    assert "function" in result or "lambda" in result


def test_safe_json_dumps_fallback_on_array():
    """Test that safe_json_dumps falls back to str() for numpy arrays."""
    obj = {"array": np.array([1, 2, 3])}
    result = safe_json_dumps(obj)
    # Not valid JSON; fallback used
    assert isinstance(result, str)
    assert "array" in result


# --- Frame Utils ---

# Mock input data
tracking_outputs = {
    "tracks": [
        {
            "id": 1,
            "frames": [0, 1],
            "point_indices": [0, 0],
            "centroids": [(5, 5), (6, 6)],
            "labels": [10, 11],
        }
    ],
    "n_tracks": 1,
}

detection_outputs = {
    "features_per_frame": [
        [
            {
                "label": 10,
                "frame_timestamp": 0.0,
                "centroid": (5.0, 5.0),
                "area": 100,
                "mean": 1.0,
                "min": 0.5,
                "max": 1.5,
            }
        ],
        [
            {
                "label": 11,
                "frame_timestamp": 1.0,
                "centroid": (6.0, 6.0),
                "area": 110,
                "mean": 1.1,
                "min": 0.6,
                "max": 1.6,
            }
        ],
    ],
    "labeled_masks": [],
    "summary": {},
}


def test_flatten_particle_features_autodetect_track_id():
    """Autodetects track ID when 'tracks' key is present."""
    grouping = {"tracks": [{"id": 1, "frames": [0], "point_indices": [0]}]}
    detection = {"features_per_frame": [[{"centroid": (1, 1)}]]}
    df = particles.flatten_particle_features(grouping, detection)
    assert "track_id" in df.columns
    assert df.loc[0, "track_id"] == 1


def test_flatten_particle_features_autodetect_cluster_id():
    """Autodetects cluster ID when 'clusters' key is present."""
    grouping = {"clusters": [{"id": 7, "frames": [0], "point_indices": [0]}]}
    detection = {"features_per_frame": [[{"centroid": (1, 1)}]]}
    df = particles.flatten_particle_features(grouping, detection)
    assert "cluster_id" in df.columns
    assert df.loc[0, "cluster_id"] == 7


def test_flatten_particle_features_raises_on_unknown_key():
    """Raises ValueError if object key is not auto-detectable."""
    grouping = {"nonsense": [{"id": 1, "frames": [0], "point_indices": [0]}]}
    detection = {"features_per_frame": [[]]}
    with pytest.raises(ValueError, match="Unable to autodetect object_key"):
        particles.flatten_particle_features(grouping, detection)


def test_flatten_particle_features_raises_on_missing_keys():
    """Raises KeyError if 'frames' or 'point_indices' keys are missing."""
    grouping = {"tracks": [{"id": 1, "frames": [0]}]}  # Missing point_indices
    detection = {"features_per_frame": [[]]}
    with pytest.raises(KeyError, match="point_indices"):
        particles.flatten_particle_features(grouping, detection)


def test_flatten_particle_features_skips_out_of_bounds_frame():
    """Skips features if frame index is out of bounds."""
    grouping = {"tracks": [{"id": 1, "frames": [10], "point_indices": [0]}]}
    detection = {"features_per_frame": [[]]}  # Only 1 frame
    df = particles.flatten_particle_features(grouping, detection)
    assert df.empty


def test_flatten_particle_features_skips_out_of_bounds_point():
    """Skips features if point index is out of bounds."""
    grouping = {"tracks": [{"id": 1, "frames": [0], "point_indices": [99]}]}
    detection = {"features_per_frame": [[{"centroid": (1, 1)}]]}
    df = particles.flatten_particle_features(grouping, detection)
    assert df.empty


def test_flatten_tracks_returns_dataframe():
    """Test flatten_tracks returns a DataFrame with expected columns."""
    df = particles.flatten_particle_features(
        tracking_outputs,
        detection_outputs,
        object_key="tracks",
        object_id_field="track_id",
    )
    expected_cols = {
        "track_id",  # if using object_id_field="track_id"
        "frame",
        "timestamp",
        "label",  # still included from `feat.get("label", idx)`
        "centroid_x",
        "centroid_y",
        "area",
        "mean",
        "min",
        "max",
    }
    assert isinstance(df, pd.DataFrame)
    assert expected_cols.issubset(df.columns)


def test_plot_tracks_3d_returns_axes():
    """Test plot_tracks_3d returns a matplotlib Axes object."""
    df = particles.flatten_particle_features(
        tracking_outputs,
        detection_outputs,
        object_key="tracks",
        object_id_field="track_id",
    )
    ax = particles.plot_particle_labels_3d(df)
    assert hasattr(ax, "plot")


def test_plot_tracks_3d_saves_file():
    """Test plot_tracks_3d saves a file if save_to is provided."""
    df = particles.flatten_particle_features(
        tracking_outputs,
        detection_outputs,
        object_key="tracks",
        object_id_field="track_id",
    )
    with TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "plot.png"
        particles.plot_particle_labels_3d(df, save_to=out_path)
        assert out_path.exists()


def test_export_particle_csv_creates_file():
    """Test export_particle_csv writes a CSV file to disk."""
    df = particles.flatten_particle_features(
        tracking_outputs,
        detection_outputs,
        object_key="tracks",
        object_id_field="track_id",
    )
    with TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "tracks.csv"
        particles.export_particle_csv(df, out_path)
        assert out_path.exists()
        loaded = pd.read_csv(out_path)
        assert not loaded.empty


# --- Frame Utils ---

# Mock input data
mock_features_per_frame = [
    [{"area": 10, "mean": 1.0}, {"area": 20, "mean": 2.0}],
    [{"area": 15, "mean": 1.5}],
    [],
]


def test_frame_summary_to_dataframe_structure():
    """Test frame_summary_to_dataframe returns expected DataFrame structure."""
    df = frames.frame_summary_to_dataframe(mock_features_per_frame)
    expected_cols = {
        "frame_index",
        "n_features",
        "total_area",
        "mean_area",
        "mean_intensity",
    }
    assert isinstance(df, pd.DataFrame)
    assert expected_cols.issubset(df.columns)
    assert len(df) == 3


def test_plot_frame_histogram_returns_axes():
    """Test plot_frame_histogram returns a matplotlib Axes object."""
    df = frames.frame_summary_to_dataframe(mock_features_per_frame)
    ax = frames.plot_frame_histogram(df, column="n_features")
    assert isinstance(ax, plt.Axes)


def test_plot_frame_histogram_saves_file():
    """Test plot_frame_histogram saves a file if save_to is provided."""
    df = frames.frame_summary_to_dataframe(mock_features_per_frame)
    with TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "hist.png"
        frames.plot_frame_histogram(df, column="n_features", save_to=out_path)
        assert out_path.exists()

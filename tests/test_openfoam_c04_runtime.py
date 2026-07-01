from __future__ import annotations

import pytest

from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.runtime import (
    _skew_face_geometry_by_processor,
    _skew_faces_by_processor,
)


def _write_poly_mesh(root, skew_faces: str) -> None:
    poly_mesh = root / "constant" / "polyMesh"
    sets = poly_mesh / "sets"
    sets.mkdir(parents=True)
    (sets / "skewFaces").write_text(skew_faces, encoding="utf-8")
    (poly_mesh / "points").write_text(
        "\n".join(
            [
                "5",
                "(",
                "(0 0 0)",
                "(1 0 0)",
                "(0 1 0)",
                "(0 0 1)",
                "(1 1 1)",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (poly_mesh / "faces").write_text(
        "\n".join(
            [
                "3",
                "(",
                "3(0 1 2)",
                "3(0 1 3)",
                "4(1 2 3 4)",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_openfoam_c04_skew_face_parser_handles_multiline_inline_and_empty_sets(tmp_path) -> None:
    case_dir = tmp_path / "case"
    _write_poly_mesh(case_dir / "processor0", "2\n(\n0\n1\n)\n")
    _write_poly_mesh(case_dir / "processor1", "3(0 1 2)\n")
    _write_poly_mesh(case_dir / "processor2", "0()\n")

    counts = _skew_faces_by_processor(tmp_path)
    geometry = _skew_face_geometry_by_processor(tmp_path)

    assert counts == {"processor0": 2, "processor1": 3, "processor2": 0}
    assert geometry["processor0"]["face_count"] == 2
    assert geometry["processor0"]["located_face_count"] == 2
    assert geometry["processor0"]["bbox_min"] == [0.0, 0.0, 0.0]
    assert geometry["processor0"]["bbox_max"] == [1.0, 1.0, 1.0]
    assert geometry["processor0"]["centroid_mean"] == [pytest.approx(1 / 3), pytest.approx(1 / 6), pytest.approx(1 / 6)]
    assert geometry["processor1"]["face_count"] == 3
    assert geometry["processor1"]["located_face_count"] == 3
    assert len(geometry["processor1"]["sample_centroids"]) == 3
    assert "processor2" not in geometry

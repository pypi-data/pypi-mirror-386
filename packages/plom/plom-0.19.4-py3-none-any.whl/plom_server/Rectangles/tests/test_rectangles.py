# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2025 Colin B. Macdonald

import tempfile
from importlib import resources
from pathlib import Path

import numpy
import numpy as np
import cv2 as cv
from django.test import TestCase
from PIL import Image

from plom.scan import QRextract
import plom_server.Scan.tests as _Scan_tests
from plom_server.Scan.services import ScanService

from ..services.rectangle import (
    extract_rect_region_from_image,
    get_largest_rectangle_contour_from_image,
    get_reference_rectangle_from_QR_data,
    _get_affine_transf_matrix_ref_to_QR_target,
)


class RectangleServiceTests(TestCase):
    """Tests for the Rectangle extraction and related tests.

    Testing RectangleExtractor directly requires a lot of boiler plate setup so
    here we mostly check the underlying functions used in its implementation.
    """

    def test_rectangle_floats(self) -> None:
        img_path = resources.files(_Scan_tests) / "id_page_img.png"
        img = Image.open(img_path)  # type: ignore[arg-type]
        img_size = (img.width, img.height)
        img_bytes = img_path.read_bytes()
        r = get_largest_rectangle_contour_from_image(
            img_bytes, img_size, (0, 0, 100, 100)
        )
        assert r is not None
        for k, v in r.items():
            self.assertIsInstance(k, str)
            self.assertIsInstance(v, float)
            self.assertNotIsInstance(v, numpy.float64)  # Issue #3870
        self.assertEqual(set(r.keys()), set(("top_f", "bottom_f", "left_f", "right_f")))

    def test_rectangle_find(self) -> None:
        img_path = resources.files(_Scan_tests) / "id_page_img.png"
        img = Image.open(img_path)  # type: ignore[arg-type]
        img_size = (img.width, img.height)
        img_bytes = img_path.read_bytes()
        ref_rect = (0, 0, img_size[0], img_size[1])

        # given the whole image, we find *some* rectangle
        r = get_largest_rectangle_contour_from_image(img_bytes, img_size, ref_rect)
        assert r is not None
        self.assertEqual(set(r.keys()), set(("top_f", "bottom_f", "left_f", "right_f")))

        # coor sys increases as we go down so bottom bigger than top
        self.assertGreater(r["bottom_f"], r["top_f"])

        # Find rectangle in the lower right
        region = {"left_f": 0.7, "top_f": 0.7, "right_f": 1.0, "bottom_f": 1.0}
        r = get_largest_rectangle_contour_from_image(
            img_bytes, img_size, ref_rect, region=region
        )
        assert r is not None
        ratio = (r["right_f"] - r["left_f"]) / (r["bottom_f"] - r["top_f"])
        # not a square b/c we're in [0,1]^2 coord system but should match
        # the ratio of height to width of the over all image (about 1.3)
        target_ratio = img.height / img.width
        self.assertAlmostEqual(ratio, target_ratio, delta=0.1)

        # search the top middle to find the boxed text
        region = {"left_f": 0.2, "top_f": 0, "right_f": 0.8, "bottom_f": 0.2}
        r = get_largest_rectangle_contour_from_image(
            img_bytes, img_size, ref_rect, region=region
        )
        assert r is not None
        self.assertAlmostEqual(r["left_f"], 0.4, delta=0.1)
        self.assertAlmostEqual(r["right_f"], 0.6, delta=0.1)
        self.assertAlmostEqual(r["top_f"], 0.02, delta=0.01)
        self.assertAlmostEqual(r["bottom_f"], 0.05, delta=0.02)

        # no box in the bottom middle
        region = {"left_f": 0.2, "top_f": 0.9, "right_f": 0.8, "bottom_f": 1.0}
        r = get_largest_rectangle_contour_from_image(
            img_bytes, img_size, ref_rect, region=region
        )
        self.assertIsNone(r)

    def test_rectangle_find_QR_coord_system(self) -> None:
        img_path = resources.files(_Scan_tests) / "id_page_img.png"
        img = Image.open(img_path)  # type: ignore[arg-type]
        img_size = (img.width, img.height)
        img_bytes = img_path.read_bytes()

        codes = QRextract(img_path)
        parsed_codes = ScanService.parse_qr_code([codes])
        rd = get_reference_rectangle_from_QR_data(parsed_codes)
        ref_rect = (rd["left"], rd["top"], rd["right"], rd["bottom"])

        # find the lower-right box around the QR code
        region = {"left_f": 0.9, "top_f": 0.9, "right_f": 1.1, "bottom_f": 1.1}
        r = get_largest_rectangle_contour_from_image(
            img_bytes, img_size, ref_rect, region=region
        )
        assert r is not None
        self.assertAlmostEqual(r["left_f"], 0.93, delta=0.05)
        self.assertAlmostEqual(r["right_f"], 1.07, delta=0.05)
        self.assertAlmostEqual(r["top_f"], 0.94, delta=0.05)
        self.assertAlmostEqual(r["bottom_f"], 1.04, delta=0.05)

    def test_rect_affine_matrix_minimal_correction(self) -> None:
        """Close to identity for affine transformation matrix."""
        img_path = resources.files(_Scan_tests) / "id_page_img.png"
        codes = QRextract(img_path)
        parsed_codes = ScanService.parse_qr_code([codes])
        rd = get_reference_rectangle_from_QR_data(parsed_codes)
        ref_rect = (rd["left"], rd["top"], rd["right"], rd["bottom"])
        matrix = _get_affine_transf_matrix_ref_to_QR_target(ref_rect, parsed_codes)
        assert matrix is not None
        expected_rot = np.array([[1.0, 0.0], [0.0, 1.0]])
        expected_shift = np.array([[0.0], [0.0]])
        rot = matrix[:, 0:-1]
        shift = matrix[:, 2:]
        self.assertLess(np.linalg.norm(rot - expected_rot, "fro"), 0.001)
        # at most one pixel of error in shifts
        self.assertLess(np.linalg.norm(shift - expected_shift, "fro"), 1.0)

    def test_rect_precisely_affine_matrix_no_correction(self) -> None:
        img_path = resources.files(_Scan_tests) / "id_page_img.png"
        codes = QRextract(img_path)
        # hack our own integer values in, so we get a precise transform
        codes["NE"]["x"] = 1500
        codes["NE"]["y"] = 100
        codes["SE"]["x"] = 1500
        codes["SE"]["y"] = 2000
        codes["SW"]["x"] = 100
        codes["SW"]["y"] = 2000
        parsed_codes = ScanService.parse_qr_code([codes])
        rd = get_reference_rectangle_from_QR_data(parsed_codes)
        ref_rect = (rd["left"], rd["top"], rd["right"], rd["bottom"])
        matrix = _get_affine_transf_matrix_ref_to_QR_target(ref_rect, parsed_codes)
        expected_matrix = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        self.assertLess(np.linalg.norm(matrix - expected_matrix, "fro"), 0.000001)

        # Now try the other corner
        codes["NW"] = codes.pop("NE")
        codes["NW"]["x"] = 100
        codes["SE"]["x"] = 1500
        codes["SE"]["y"] = 2000
        codes["SW"]["x"] = 100
        codes["SW"]["y"] = 2000
        parsed_codes = ScanService.parse_qr_code([codes])
        rd = get_reference_rectangle_from_QR_data(parsed_codes)
        ref_rect = (rd["left"], rd["top"], rd["right"], rd["bottom"])
        matrix = _get_affine_transf_matrix_ref_to_QR_target(ref_rect, parsed_codes)
        expected_matrix = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        self.assertLess(np.linalg.norm(matrix - expected_matrix, "fro"), 0.000001)

    def test_rect_fail_with_less_than_three_corners(self) -> None:
        img_path = resources.files(_Scan_tests) / "id_page_img.png"
        codes = QRextract(img_path)
        # hack these a bit for testing: without a top point, we'll get None
        codes.pop("NE")
        codes.pop("NW")
        parsed_codes = ScanService.parse_qr_code([codes])
        rd = get_reference_rectangle_from_QR_data(parsed_codes)
        ref_rect = (rd["left"], rd["top"], rd["right"], rd["bottom"])
        matrix = _get_affine_transf_matrix_ref_to_QR_target(ref_rect, parsed_codes)
        self.assertIsNone(matrix)

        codes = QRextract(img_path)
        codes.pop("SE")
        parsed_codes = ScanService.parse_qr_code([codes])
        rd = get_reference_rectangle_from_QR_data(parsed_codes)
        ref_rect = (rd["left"], rd["top"], rd["right"], rd["bottom"])
        matrix = _get_affine_transf_matrix_ref_to_QR_target(ref_rect, parsed_codes)
        self.assertIsNone(matrix)

    def test_rect_affine_matrix_5degree_rot(self) -> None:
        """Rotation of image, and affine transformation."""
        img_path = resources.files(_Scan_tests) / "id_page_img.png"
        img = Image.open(img_path)  # type: ignore[arg-type]
        codes = QRextract(img_path)
        parsed_codes = ScanService.parse_qr_code([codes])
        rd = get_reference_rectangle_from_QR_data(parsed_codes)
        ref_rect = (rd["left"], rd["top"], rd["right"], rd["bottom"])

        with tempfile.TemporaryDirectory() as tmpdir:
            # Debug the test by saving images locally:
            # tmpdir = Path("/home/cbm/src/plom/plom.git")
            img_rot_path = Path(tmpdir) / "rot_5_deg_img.png"
            img_rot = img.rotate(5, expand=True)
            img_rot.save(img_rot_path)

            codes = QRextract(img_rot_path)
            parsed_codes = ScanService.parse_qr_code([codes])

            matrix = _get_affine_transf_matrix_ref_to_QR_target(ref_rect, parsed_codes)
            expected_matrix = np.array(
                [[0.996, 0.0870, 0.338], [-0.0870, 0.996, 134.263]]
            )
            err = np.linalg.norm(matrix - expected_matrix, "fro")
            relative_err = err / np.linalg.norm(expected_matrix, "fro")
            self.assertLess(relative_err, 0.05)

    def test_rect_ID_box_corrected_and_extracted_from_3degree_rotation(self) -> None:
        """Artificially rotate the image, then try to recover the ID box based on its known location in the source image."""
        img_path = resources.files(_Scan_tests) / "id_page_img.png"
        # mypy stumbling over Traversable
        img = Image.open(img_path)  # type: ignore[arg-type]
        img = img.convert("RGB")  # type: ignore[assignment]

        img_bytes = img_path.read_bytes()
        codes = QRextract(img_path)
        parsed_codes = ScanService.parse_qr_code([codes])
        rd = get_reference_rectangle_from_QR_data(parsed_codes)
        ref_rect = (rd["left"], rd["top"], rd["right"], rd["bottom"])

        # find id box in the source image
        idbox_src_loc = get_largest_rectangle_contour_from_image(
            img_bytes,
            img.size,
            ref_rect,
            region={"left_f": 0.0, "top_f": 0.25, "right_f": 1.0, "bottom_f": 0.65},
        )
        assert idbox_src_loc is not None

        with tempfile.TemporaryDirectory() as tmpdir:
            # Debug the test by saving images locally:
            # tmpdir = Path("/home/cbm/src/plom/plom.git")
            img_rot_path = Path(tmpdir) / "rotated_img.png"
            img_rot = img.rotate(3, expand=True)
            img_rot.save(img_rot_path)
            codes = QRextract(img_rot_path)
            parsed_codes = ScanService.parse_qr_code([codes])

            output_bytes = extract_rect_region_from_image(
                img_rot_path,
                parsed_codes,
                idbox_src_loc["left_f"],
                idbox_src_loc["top_f"],
                idbox_src_loc["right_f"],
                idbox_src_loc["bottom_f"],
                ref_rect,
            )
            assert output_bytes is not None
            output_path = Path(tmpdir) / "output_img.png"
            with output_path.open("wb") as f:
                f.write(output_bytes)
            output_img = Image.open(output_path)
            output_opencv = cv.cvtColor(np.array(output_img), cv.COLOR_RGB2BGR)
            t = round(0.44 * output_img.height)
            b = round(0.6 * output_img.height)
            l = round(0.32 * output_img.width)
            r = round(0.96 * output_img.width)
            # print(((t, b), (l, r)))
            white_subimage = output_opencv[t:b, l:r]
            self.assertAlmostEqual(np.mean(white_subimage.astype(float)), 255, delta=5)

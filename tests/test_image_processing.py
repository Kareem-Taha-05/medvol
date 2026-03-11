"""
Tests for medvol.utils.image_processing.

Pure numpy — no Qt or VTK involved, so these run on any platform including CI.
"""

import numpy as np
import pytest

from medvol.utils.image_processing import adjust_brightness_contrast


class TestAdjustBrightnessContrast:

    # ── Fixtures ───────────────────────────────────────────────────────────────

    @pytest.fixture
    def grey_image(self) -> np.ndarray:
        """128×128 mid-grey image (all pixels = 128)."""
        return np.full((128, 128), 128, dtype=np.uint8)

    @pytest.fixture
    def gradient_image(self) -> np.ndarray:
        """128×128 linear gradient from 0 to 255."""
        return np.tile(np.linspace(0, 255, 128, dtype=np.uint8), (128, 1))

    # ── Identity (no change) ───────────────────────────────────────────────────

    def test_zero_params_returns_same_values(self, gradient_image):
        result = adjust_brightness_contrast(gradient_image, brightness=0, contrast=0)
        np.testing.assert_array_equal(result, gradient_image)

    def test_output_dtype_is_uint8(self, gradient_image):
        result = adjust_brightness_contrast(gradient_image, brightness=50, contrast=50)
        assert result.dtype == np.uint8

    def test_output_shape_preserved(self, gradient_image):
        result = adjust_brightness_contrast(gradient_image, brightness=10, contrast=10)
        assert result.shape == gradient_image.shape

    # ── Brightness ─────────────────────────────────────────────────────────────

    def test_positive_brightness_increases_values(self, grey_image):
        result = adjust_brightness_contrast(grey_image, brightness=50, contrast=0)
        assert result.mean() > grey_image.mean()

    def test_negative_brightness_decreases_values(self, grey_image):
        result = adjust_brightness_contrast(grey_image, brightness=-50, contrast=0)
        assert result.mean() < grey_image.mean()

    def test_max_brightness_clips_to_255(self, grey_image):
        result = adjust_brightness_contrast(grey_image, brightness=255, contrast=0)
        assert result.max() == 255

    def test_min_brightness_clips_to_0(self, grey_image):
        result = adjust_brightness_contrast(grey_image, brightness=-255, contrast=0)
        assert result.max() == 0   # all clipped to 0

    # ── Contrast ───────────────────────────────────────────────────────────────

    def test_positive_contrast_increases_spread(self, gradient_image):
        baseline_std = gradient_image.astype(float).std()
        result = adjust_brightness_contrast(gradient_image, brightness=0, contrast=100)
        # Higher contrast → values cluster at 0 and 255, so std may stay similar
        # but min should drop and max should rise (or clip)
        assert result.min() <= gradient_image.min()
        assert result.max() >= gradient_image.max()

    def test_max_negative_contrast_flattens_image(self, gradient_image):
        """Contrast = -255 → factor = 0 → all pixels map to 0.5 → 127 or 128."""
        result = adjust_brightness_contrast(gradient_image, brightness=0, contrast=-255)
        # All values should collapse to approximately 127-128
        assert result.std() < 2.0

    def test_no_singularity_at_extreme_contrast(self, gradient_image):
        """Should not raise at contrast = 255 (old formula had divide-by-zero risk)."""
        result = adjust_brightness_contrast(gradient_image, brightness=0, contrast=255)
        assert result.dtype == np.uint8
        assert not np.any(np.isnan(result.astype(float)))

    # ── Output bounds ──────────────────────────────────────────────────────────

    def test_output_always_in_0_255(self):
        rng = np.random.default_rng(42)
        image = rng.integers(0, 256, (256, 256), dtype=np.uint8)
        for br in (-255, -100, 0, 100, 255):
            for co in (-255, -100, 0, 100, 255):
                result = adjust_brightness_contrast(image, brightness=br, contrast=co)
                assert result.min() >= 0
                assert result.max() <= 255

    # ── Brightness/contrast interaction ────────────────────────────────────────

    def test_brightness_and_contrast_combined(self, grey_image):
        """Midpoint grey + positive brightness + positive contrast → bright."""
        result = adjust_brightness_contrast(grey_image, brightness=60, contrast=80)
        assert result.mean() > 200   # should be in the bright range
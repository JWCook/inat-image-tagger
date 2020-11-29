import pytest

from naturtag.atlas import get_atlas_dimensions


# Test various combinations of inputs and limits
@pytest.mark.parametrize(
    'n_images, x, y, limit_kwarg, expected_dimensions',
    [
        (14, 75, 75, {}, (154, 539)),
        (15, 75, 75, {}, (308, 308)),
        (16, 75, 75, {}, (308, 308)),
        (17, 75, 75, {}, (231, 462)),
        (200, 75, 75, {}, (770, 1540)),
        (2000, 75, 75, {'max_size': 1024}, (1001, 1001)),
        (2000, 75, 75, {'max_bins': 4}, (1540, 1925)),
        (2000, 75, 75, {'max_per_bin': 425}, (462, 5467)),
        (2000, 128, 209, {'max_size': 1024}, (910, 844)),
        (2000, 128, 209, {'max_bins': 4}, (2600, 5275)),
        (2000, 128, 209, {'max_per_bin': 425}, (780, 14981)),
    ],
)
def test_get_atlas_dimensions(n_images, x, y, limit_kwarg, expected_dimensions):
    assert get_atlas_dimensions(n_images, x, y, **limit_kwarg) == expected_dimensions

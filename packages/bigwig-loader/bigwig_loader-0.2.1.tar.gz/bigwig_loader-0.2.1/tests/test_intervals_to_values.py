import cupy as cp
import pytest

from bigwig_loader.intervals_to_values import intervals_to_values


def test_throw_exception_when_queried_intervals_are_of_different_lengths() -> None:
    """All query_ends - query_starts should have the same
    length. Otherwise, ValueError should be raised.
    """
    track_starts = cp.asarray([1, 2, 3], dtype=cp.int32)
    track_ends = cp.asarray([2, 3, 4], dtype=cp.int32)
    track_values = cp.asarray([1.0, 1.0, 1.0], dtype=cp.dtype("f4"))
    query_starts = cp.asarray([2, 2], dtype=cp.int32)
    query_ends = cp.asarray([4, 5], dtype=cp.int32)
    reserved = cp.zeros((2, 2), dtype=cp.float32)

    with pytest.raises(ValueError):
        intervals_to_values(
            track_starts, track_ends, track_values, query_starts, query_ends, reserved
        )


@pytest.mark.parametrize("default_value", [0.0, cp.nan])
def test_get_values_from_intervals(default_value) -> None:
    """Probably most frequent situation."""
    track_starts = cp.asarray([1, 3, 10, 12, 16], dtype=cp.int32)
    track_ends = cp.asarray([3, 10, 12, 16, 20], dtype=cp.int32)
    track_values = cp.asarray([20.0, 15.0, 30.0, 40.0, 50.0], dtype=cp.dtype("f4"))
    query_starts = cp.asarray([2], dtype=cp.int32)
    query_ends = cp.asarray([17], dtype=cp.int32)
    reserved = cp.zeros((1, 15), dtype=cp.float32)
    values = intervals_to_values(
        track_starts,
        track_ends,
        track_values,
        query_starts,
        query_ends,
        default_value=default_value,
        out=reserved,
    )
    expected = cp.asarray(
        [[20, 15, 15, 15, 15, 15, 15, 15, 30, 30, 40, 40, 40, 40, 50]]
    )
    assert cp.allclose(expected, values, equal_nan=True)


@pytest.mark.parametrize("default_value", [0.0, cp.nan])
def test_get_values_from_intervals_edge_case_1(default_value) -> None:
    """Query start is somewhere in a "gap"."""
    track_starts = cp.asarray([1, 10, 12, 16], dtype=cp.int32)
    track_ends = cp.asarray([3, 12, 16, 20], dtype=cp.int32)
    track_values = cp.asarray([20.0, 30.0, 40.0, 50.0], dtype=cp.dtype("f4"))
    query_starts = cp.asarray([6], dtype=cp.int32)
    query_ends = cp.asarray([18], dtype=cp.int32)
    reserved = cp.zeros((1, 12), dtype=cp.dtype("<f4"))
    values = intervals_to_values(
        track_starts,
        track_ends,
        track_values,
        query_starts,
        query_ends,
        default_value=default_value,
        out=reserved,
    )
    x = default_value
    expected = cp.asarray([[x, x, x, x, 30, 30, 40, 40, 40, 40, 50, 50]])

    print(expected)
    print(values)

    assert (
        cp.allclose(values, expected, equal_nan=True)
        and expected.shape[-1] == query_ends[0] - query_starts[0]
    )


@pytest.mark.parametrize("default_value", [0.0, cp.nan])
def test_get_values_from_intervals_edge_case_2(default_value) -> None:
    """Query start is exactly at start index after "gap"."""
    track_starts = cp.asarray([1, 10, 12, 16], dtype=cp.int32)
    track_ends = cp.asarray([3, 12, 16, 20], dtype=cp.int32)
    track_values = cp.asarray([20.0, 30.0, 40.0, 50.0], dtype=cp.dtype("f4"))
    query_starts = cp.asarray([10], dtype=cp.int32)
    query_ends = cp.asarray([18], dtype=cp.int32)
    reserved = cp.zeros((1, 8), dtype=cp.dtype("<f4"))
    values = intervals_to_values(
        track_starts,
        track_ends,
        track_values,
        query_starts,
        query_ends,
        default_value=default_value,
        out=reserved,
    )
    expected = cp.asarray([[30, 30, 40, 40, 40, 40, 50, 50]])
    assert (
        cp.allclose(values, expected, equal_nan=True)
        and expected.shape[-1] == query_ends[0] - query_starts[0]
    )


@pytest.mark.parametrize("default_value", [0.0, cp.nan])
def test_get_values_from_intervals_edge_case_3(default_value) -> None:
    """Query end is somewhere in a "gap"."""
    track_starts = cp.asarray([5, 10, 12, 18], dtype=cp.int32)
    track_ends = cp.asarray([10, 12, 14, 20], dtype=cp.int32)
    track_values = cp.asarray([20.0, 30.0, 40.0, 50.0], dtype=cp.dtype("f4"))
    query_starts = cp.asarray([9], dtype=cp.int32)
    query_ends = cp.asarray([16], dtype=cp.int32)
    reserved = cp.zeros((1, 7), dtype=cp.dtype("<f4"))
    values = intervals_to_values(
        track_starts,
        track_ends,
        track_values,
        query_starts,
        query_ends,
        default_value=default_value,
        out=reserved,
    )
    x = default_value
    expected = cp.asarray([[20, 30, 30, 40, 40, x, x]])
    assert (
        cp.allclose(values, expected, equal_nan=True)
        and expected.shape[-1] == query_ends[0] - query_starts[0]
    )


@pytest.mark.parametrize("default_value", [0.0, cp.nan])
def test_get_values_from_intervals_edge_case_4(default_value) -> None:
    """Query end is exactly at end index before "gap"."""
    track_starts = cp.asarray([5, 10, 12, 18], dtype=cp.int32)
    track_ends = cp.asarray([10, 12, 14, 20], dtype=cp.int32)
    track_values = cp.asarray([20.0, 30.0, 40.0, 50.0], dtype=cp.dtype("f4"))
    query_starts = cp.asarray([9], dtype=cp.int32)
    query_ends = cp.asarray([14], dtype=cp.int32)
    reserved = cp.zeros((1, 5), dtype=cp.dtype("<f4"))
    values = intervals_to_values(
        track_starts,
        track_ends,
        track_values,
        query_starts,
        query_ends,
        default_value=default_value,
        out=reserved,
    )
    expected = cp.asarray([[20, 30, 30, 40, 40]])

    print(expected)
    print(values)

    assert (values == expected).all() and expected.shape[-1] == query_ends[
        0
    ] - query_starts[0]


@pytest.mark.parametrize("default_value", [0.0, cp.nan])
def test_get_values_from_intervals_edge_case_5(default_value) -> None:
    """Query end is exactly at end index before "gap"."""
    track_starts = cp.asarray([5, 10, 12, 18], dtype=cp.uint32)
    track_ends = cp.asarray([10, 12, 14, 20], dtype=cp.uint32)
    track_values = cp.asarray([20.0, 30.0, 40.0, 50.0], dtype=cp.dtype("f4"))
    query_starts = cp.asarray([9], dtype=cp.uint32)
    query_ends = cp.asarray([20], dtype=cp.uint32)
    reserved = cp.zeros((1, 11), dtype=cp.dtype("<f4"))
    values = intervals_to_values(
        track_starts,
        track_ends,
        track_values,
        query_starts,
        query_ends,
        default_value=default_value,
        out=reserved,
    )
    x = default_value
    expected = cp.asarray([[20, 30, 30, 40, 40, x, x, x, x, 50, 50]])

    print(expected)
    print(values)

    assert (
        cp.allclose(expected, values, equal_nan=True)
        and expected.shape[-1] == query_ends[0] - query_starts[0]
    )


@pytest.mark.parametrize("default_value", [0.0, cp.nan])
def test_get_values_from_intervals_batch_of_2(default_value) -> None:
    """Query end is exactly at end index before "gap"."""
    track_starts = cp.asarray([5, 10, 12, 18], dtype=cp.int32)
    track_ends = cp.asarray([10, 12, 14, 20], dtype=cp.int32)
    track_values = cp.asarray([20.0, 30.0, 40.0, 50.0], dtype=cp.dtype("f4"))
    query_starts = cp.asarray([7, 9], dtype=cp.int32)
    query_ends = cp.asarray([18, 20], dtype=cp.int32)
    reserved = cp.zeros([2, 11], dtype=cp.dtype("<f4"))
    values = intervals_to_values(
        track_starts,
        track_ends,
        track_values,
        query_starts,
        query_ends,
        default_value=default_value,
        out=reserved,
    )

    x = default_value

    expected = cp.asarray(
        [
            [20.0, 20.0, 20.0, 30.0, 30.0, 40.0, 40.0, x, x, x, x],
            [20.0, 30.0, 30.0, 40.0, 40.0, x, x, x, x, 50.0, 50.0],
        ]
    )
    print(expected)
    print(values)
    assert cp.allclose(expected, values, equal_nan=True)


@pytest.mark.parametrize("default_value", [0.0, cp.nan])
def test_get_values_from_intervals_batch_multiple_tracks(default_value) -> None:
    """Query end is exactly at end index before "gap"."""
    track_starts = cp.asarray(
        [5, 10, 12, 18, 8, 9, 10, 18, 25, 10, 100, 1000], dtype=cp.int32
    )
    track_ends = cp.asarray(
        [10, 12, 14, 20, 9, 10, 14, 22, 55, 20, 200, 2000], dtype=cp.int32
    )
    track_values = cp.asarray(
        [20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 130.0],
        dtype=cp.dtype("f4"),
    )
    query_starts = cp.asarray([7, 9, 20, 99], dtype=cp.int32)
    query_ends = cp.asarray([18, 20, 31, 110], dtype=cp.int32)
    reserved = cp.zeros([3, 4, 11], dtype=cp.dtype("<f4"))
    values = intervals_to_values(
        track_starts,
        track_ends,
        track_values,
        query_starts,
        query_ends,
        default_value=default_value,
        out=reserved,
        sizes=cp.asarray([4, 5, 3], dtype=cp.int32),
    )
    x = default_value
    expected = cp.asarray(
        [
            [
                [20.0, 20.0, 20.0, 30.0, 30.0, 40.0, 40.0, x, x, x, x],
                [20.0, 30.0, 30.0, 40.0, 40.0, x, x, x, x, 50.0, 50.0],
                [x, x, x, x, x, x, x, x, x, x, x],
                [x, x, x, x, x, x, x, x, x, x, x],
            ],
            [
                [x, 60.0, 70.0, 80.0, 80.0, 80.0, 80.0, x, x, x, x],
                [70.0, 80.0, 80.0, 80.0, 80.0, x, x, x, x, 90.0, 90.0],
                [90.0, 90.0, x, x, x, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0],
                [x, x, x, x, x, x, x, x, x, x, x],
            ],
            [
                [x, x, x, 110.0, 110.0, 110.0, 110.0, 110.0, 110.0, 110.0, 110.0],
                [
                    x,
                    110.0,
                    110.0,
                    110.0,
                    110.0,
                    110.0,
                    110.0,
                    110.0,
                    110.0,
                    110.0,
                    110.0,
                ],
                [x, x, x, x, x, x, x, x, x, x, x],
                [
                    x,
                    120.0,
                    120.0,
                    120.0,
                    120.0,
                    120.0,
                    120.0,
                    120.0,
                    120.0,
                    120.0,
                    120.0,
                ],
            ],
        ]
    )
    print(expected)
    print(values)
    assert cp.allclose(expected, values, equal_nan=True)

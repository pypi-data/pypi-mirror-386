"""Define tests for :class:`.SimulationsResults`."""

import logging
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from simultipac.simulation_results.simulation_results import SimulationResults
from simultipac.simulation_results.simulations_results import (
    DuplicateIndexError,
    NonExistingIDError,
    SimulationsResults,
)


def test_add(mocker: MagicMock) -> None:
    """Test :meth:`.SimulationsResults._add`."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_results = 5

    results = (
        SimulationResults(id=i, e_acc=i, time=time, population=pop)
        for i in range(n_results)
    )
    mock_add = mocker.patch.object(SimulationsResults, "_add")
    SimulationsResults(results)
    assert mock_add.call_count == n_results


def test_add_double_id_error() -> None:
    """Test :meth:`.SimulationsResults._add`."""
    time = np.linspace(0, 10, 11)
    population = time
    n_results = 5

    results = (
        SimulationResults(
            id=i if i > 0 else 1, e_acc=i, time=time, population=population
        )
        for i in range(n_results)
    )
    with pytest.raises(DuplicateIndexError):
        SimulationsResults(results)


def test_len() -> None:
    """Test :meth:`.SimulationsResults._add`."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_results = 5

    results = (
        SimulationResults(id=i, e_acc=i, time=time, population=pop)
        for i in range(n_results)
    )

    assert len(SimulationsResults(results)) == n_results


def test_e_acc_sorting() -> None:
    """Check that results are sorted by increasing ``e_acc``."""
    time = np.linspace(0, 10, 11)
    pop = time
    unsorted_results = (
        r3 := SimulationResults(id=3, e_acc=3, time=time, population=pop),
        r1 := SimulationResults(id=1, e_acc=1, time=time, population=pop),
        r0 := SimulationResults(id=0, e_acc=0, time=time, population=pop),
        r4 := SimulationResults(id=4, e_acc=4, time=time, population=pop),
        r2 := SimulationResults(id=2, e_acc=2, time=time, population=pop),
    )
    simulations_results = SimulationsResults(unsorted_results)

    expected = [r0, r1, r2, r3, r4]
    assert simulations_results.to_list == expected


def test_get_by_id() -> None:
    """Test :meth:`.SimulationsResults._get_by_id`."""
    time = np.linspace(0, 10, 11)
    pop = time
    unsorted_results = (
        r3 := SimulationResults(id=3, e_acc=3, time=time, population=pop),
        SimulationResults(id=1, e_acc=1, time=time, population=pop),
        SimulationResults(id=0, e_acc=0, time=time, population=pop),
        SimulationResults(id=4, e_acc=4, time=time, population=pop),
        SimulationResults(id=2, e_acc=2, time=time, population=pop),
    )
    simulations_results = SimulationsResults(unsorted_results)
    assert simulations_results.get_by_id(3) is r3


def test_get_by_id_missing() -> None:
    """Test :meth:`.SimulationsResults._get_by_id`."""
    time = np.linspace(0, 10, 11)
    pop = time
    results = (
        SimulationResults(id=i, e_acc=i, time=time, population=pop)
        for i in range(5)
    )
    simulations_results = SimulationsResults(results)
    with pytest.raises(NonExistingIDError):
        simulations_results.get_by_id(6)


def test_to_pandas() -> None:
    """Test :meth:`.SimulationsResults._to_pandas`."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_points = 5
    results = (
        SimulationResults(id=i, e_acc=i**2, time=time, population=pop)
        for i in range(n_points)
    )
    returned = SimulationsResults(results)._to_pandas("id", "e_acc")
    expected = pd.DataFrame(
        {
            "id": [i for i in range(n_points)],
            "e_acc": [i**2 for i in range(n_points)],
        }
    )
    pd.testing.assert_frame_equal(expected, returned)


def test_to_pandas_with_exp_growth_params() -> None:
    """Test :meth:`.SimulationsResults._to_pandas` with ``alpha``."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_points = 5
    results = [
        SimulationResults(id=i, e_acc=i**2, time=time, population=pop)
        for i in range(n_points)
    ]
    for r in results:
        r.alpha = r.e_acc

    returned = SimulationsResults(results)._to_pandas("id", "alpha")
    expected = pd.DataFrame(
        {
            "id": [i for i in range(n_points)],
            "alpha": [i**2 for i in range(n_points)],
        }
    )
    pd.testing.assert_frame_equal(expected, returned)


def test_to_pandas_with_array_raises_error() -> None:
    """Test :meth:`.SimulationsResults._to_pandas` with ``population``."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_points = 5
    results = (
        SimulationResults(id=i, e_acc=i**2, time=time, population=pop)
        for i in range(n_points)
    )
    simulations_results = SimulationsResults(results)
    with pytest.raises(ValueError):
        simulations_results._to_pandas("id", "population")  # type: ignore


def test_to_pandas_with_generator_error() -> None:
    """Test :meth:`.SimulationsResults._to_pandas` with a generator."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_points = 5
    results = [
        SimulationResults(id=i, e_acc=i**2, time=time, population=pop)
        for i in range(n_points)
    ]
    simulations_results = SimulationsResults(results)

    # A generator can be called only once, so iterating over it for "id" and
    # then for "e_acc" will raise an error
    sub_results = (r for r in results if r.id != 3)
    with pytest.raises(ValueError):
        simulations_results._to_pandas("id", "e_acc", results=sub_results)  # type: ignore


def test_parameter_values() -> None:
    """Check that we can get the different parameters values."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_points = 10
    results = (
        SimulationResults(
            id=i,
            e_acc=i**2,
            time=time,
            population=pop,
            parameters={"dummy": i % 3, "not dummy": i % 4, "hello": 0},
        )
        for i in range(n_points)
    )
    simulations_results = SimulationsResults(results)

    expected = {"dummy": {0, 1, 2}, "not dummy": {0, 1, 2, 3}}
    got = simulations_results.parameter_values("dummy", "not dummy")
    assert got == expected


def test_parameter_values_no_arg() -> None:
    """Check that we can get all the parameters values when no arg."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_points = 10
    results = (
        SimulationResults(
            id=i,
            e_acc=i**2,
            time=time,
            population=pop,
            parameters={"dummy": i % 3, "not dummy": i % 4, "hello": 0},
        )
        for i in range(n_points)
    )
    simulations_results = SimulationsResults(results)

    expected = {"dummy": {0, 1, 2}, "not dummy": {0, 1, 2, 3}, "hello": {0}}
    assert simulations_results.parameter_values() == expected


def test_parameter_values_missing() -> None:
    """Check that a missing parameter value raises an error."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_points = 10
    results = (
        SimulationResults(
            id=i,
            e_acc=i**2,
            time=time,
            population=pop,
            parameters={"dummy": i % 3} if i != 5 else {},
        )
        for i in range(n_points)
    )
    simulations_results = SimulationsResults(results)

    with pytest.raises(ValueError):
        simulations_results.parameter_values("dummy", allow_missing=False)


def test_with_parameter_value() -> None:
    """Check that we can get simulation results from parameters values."""
    time = np.linspace(0, 10, 11)
    pop = time
    n_points = 10
    results = [
        SimulationResults(
            id=i,
            e_acc=i**2,
            time=time,
            population=pop,
            parameters={"dummy": i % 3, "not_dummy": i % 2},
        )
        for i in range(n_points)
    ]
    simulations_results = SimulationsResults(results)

    expected = (results[0], results[6])
    got = simulations_results.with_parameter_value(
        {"dummy": 0, "not_dummy": 0}
    )
    assert tuple(got) == expected


def test_format_for_save_0d() -> None:
    """Check on 0D data."""
    time = np.linspace(0, 10, 11)
    populations = (time, time**2)
    results = (
        SimulationResults(
            id=i,
            e_acc=i**2,
            time=time,
            population=populations[i],
        )
        for i in range(2)
    )
    returned = SimulationsResults(results)._format_for_save("id", "e_acc")
    expected = pd.DataFrame({"id": [0, 1], "e_acc": [0, 1]})
    pd.testing.assert_frame_equal(expected, returned)


def test_format_for_save_1d() -> None:
    """Check on 1D data."""
    time = np.linspace(0, 10, 11)
    populations = [time, time**2]
    results = (
        SimulationResults(
            id=i,
            e_acc=i**2,
            time=time,
            population=populations[i],
        )
        for i in range(2)
    )
    returned = SimulationsResults(results)._format_for_save(
        "time", "population"
    )
    data = np.column_stack([time, populations[0], time, populations[1]])
    expected = pd.DataFrame(
        data, columns=["time", "population", "time", "population"]
    )
    pd.testing.assert_frame_equal(expected, returned)


def test_format_for_save_1d_merge() -> None:
    """Check on 1D data."""
    time = np.linspace(0, 10, 11)
    populations = [time, time**2, time / 2, time * 3]
    results = (
        SimulationResults(
            id=i,
            e_acc=i**2,
            time=time,
            population=populations[i],
        )
        for i in range(4)
    )
    returned = SimulationsResults(results)._format_for_save(
        "time", "population", merge_on="time"
    )

    data = np.column_stack([time] + populations)
    expected = pd.DataFrame(
        data,
        columns=[
            "time",
            "population_0",
            "population_1",
            "population_2",
            "population_3",
        ],
    )
    pd.testing.assert_frame_equal(expected, returned)

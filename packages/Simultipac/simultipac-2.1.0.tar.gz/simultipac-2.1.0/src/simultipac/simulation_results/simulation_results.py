"""Define a base object to store a multipactor simulation results."""

import logging
from abc import ABC
from pathlib import Path
from typing import Any, Callable, Literal

import numpy as np
import pandas as pd

from simultipac.plotter.default import DefaultPlotter
from simultipac.plotter.plotter import Plotter
from simultipac.types import DATA_0D_t, DATA_1D_t
from simultipac.util.exponential_growth import ExpGrowthParameters, fit_alpha


class ShapeMismatchError(Exception):
    """Raise error when ``population`` and ``time`` have different shapes."""


class MissingDataError(Exception):
    """Error raised when trying to access non-existing data."""


class SimulationResults(ABC):
    """Store a single simulation results."""

    def __init__(
        self,
        id: int,
        e_acc: float,
        time: np.ndarray,
        population: np.ndarray,
        p_rms: float | None = None,
        plotter: Plotter | None = None,
        trim_trailing: bool = False,
        period: float | None = None,
        parameters: dict[str, float | bool | str] | None = None,
        **kwargs,
    ) -> None:
        """Instantiate, post-process.

        Parameters
        ----------
        id :
            Unique simulation identifier.
        e_acc :
            Accelerating field in :unit:`V/m`.
        time :
            Time in :unit:`ns`.
        population :
            Evolution of population with time. Same shape as ``time``.
        p_rms :
            RMS power in :unit:`W`.
        plotter :
            An object allowing to plot data.
        trim_trailing :
            To remove the last simulation points, when the population is 0.
            Used with SPARK3D (``CSV`` import) for consistency with CST.
        period :
            RF period in :unit:`ns`. Mandatory for exponential growth fits.
        parameters :
            Additional information on the simulation. Typically, value of
            magnetic field, number of PIC cells, simulation flags...

        """
        self.id = id
        self.e_acc = e_acc
        self.p_rms = p_rms
        self.time = time
        self.population = population
        if plotter is None:
            plotter = DefaultPlotter()
        self._plotter = plotter
        self._check_consistent_shapes()
        if trim_trailing:
            self._trim_trailing()
        self._exp_growth_parameters: ExpGrowthParameters | dict[str, float] = (
            {}
        )
        self._period: float | None = period
        self._modelled_population: np.ndarray | None = None
        self._color: Any = None
        self._alpha: float | None = None

        self.parameters: dict[str, Any] = (
            {} if parameters is None else parameters
        )

    def __str__(self) -> str:
        """Print info on current simulation."""
        info = [f"Sim. #{self.id}", f"E_acc = {self.e_acc:.2e} V/m"]
        if len(self._exp_growth_parameters) == 0:
            return ", ".join(info)
        info.append(r"$\alpha = $" + f"{self.alpha:.3f} ns^-1")
        return ", ".join(info)

    def __repr__(self) -> str:
        """Print minimal info on current simulation."""
        return f"SimulationResults(id={self.id}, e_acc={self.e_acc:.2e})"

    def _check_consistent_shapes(self) -> None:
        """Raise an error if ``time`` and ``population`` have diff shapes."""
        if self.time.shape == self.population.shape:
            return
        raise ShapeMismatchError(
            f"{self.time.shape = } but {self.population.shape = }"
        )

    def _trim_trailing(self) -> None:
        """Remove data for which population is null."""
        idx_to_remove = np.argwhere(self.population == 0.0)
        if idx_to_remove.size == 0:
            return
        last_idx = idx_to_remove[0][0]
        self.population = self.population[:last_idx]
        self.time = self.time[:last_idx]

    @property
    def alpha(self) -> float:
        """Return the exponential growth factor in :unit:`ns^{-1}`."""
        if self._alpha is not None:
            return self._alpha

        alpha = self._exp_growth_parameters.get("alpha", None)
        if alpha is not None:
            self.alpha = alpha
            return alpha

        logging.warning(
            "Exponential growth factor not calculated yet. Returnin NaN."
        )
        return np.nan

    @alpha.setter
    def alpha(self, value: float) -> None:
        """Set the value of exp growth factor."""
        self._alpha = value

    @alpha.deleter
    def alpha(self) -> None:
        """Delete the value."""
        self._alpha = None

    def fit_alpha(
        self,
        fitting_periods: int,
        running_mean: bool = False,
        log_fit: bool = True,
        minimum_final_number_of_electrons: int = 0,
        bounds: tuple[list[float], list[float]] = (
            [1e-10, -10.0],
            [np.inf, 10.0],
        ),
        initial_values: list[float] = [0.0, 0.0],
        minimum_number_of_points: int = 5,
        **kwargs,
    ) -> None:
        """Fit exp growth factor.

        Parameters
        ----------
        fitting_periods :
            Number of periods over which the exp growth is searched. Longer is
            better, but you do not want to start the fit before the exp growth
            starts.
        running_mean :
            To tell if you want to average the number of particles over one
            period. It is recommended with CST, but does not bring anything for
            SPARK3D. The default is False.
        log_fit :
            To perform the fit on :func:`exp_growth_log` rather than
            :func:`exp_growth`. The default is True, as it generally shows
            better convergence.
        minimum_final_number_of_electrons :
            Under this final number of electrons, we do no bother finding the
            exp growth factor and set all fit parameters to ``NaN``.
        bounds :
            Upper bound and lower bound for the two variables: initial number
            of electrons, exp growth factor.
        initial_values: list[float], optional
            Initial values for the two variables: initial number of electrons,
            exp growth factor.
        minimum_number_of_points :
            Minimum number of fitting points; under this limit, a warning is
            issued. For CST, should be at least 10 or 20. With SPARK3D, there
            are two points per RF period so a value of 2 or 4 should be enough.

        """
        assert self._period is not None, "RF period is needed."
        fitting_range = self._period * fitting_periods

        self._exp_growth_parameters = fit_alpha(
            self.time,
            self.population,
            fitting_range=fitting_range,
            period=self._period,
            running_mean=running_mean,
            log_fit=log_fit,
            minimum_final_number_of_electrons=minimum_final_number_of_electrons,
            bounds=bounds,
            initial_values=initial_values,
            minimum_number_of_points=minimum_number_of_points,
            **kwargs,
        )

    @property
    def modelled_population(self) -> np.ndarray:
        """Define evolution of population, as modelled."""
        if self._modelled_population is not None:
            return self._modelled_population
        if self._exp_growth_parameters is None:
            raise ValueError(
                "Cannot model population evolution if fit not performed."
            )
        model = self._exp_growth_parameters["model"]
        assert isinstance(model, Callable)
        self._modelled_population = model(
            self.time, **self._exp_growth_parameters
        )
        assert isinstance(self._modelled_population, np.ndarray)
        return self._modelled_population

    def plot(
        self,
        x: DATA_0D_t | DATA_1D_t,
        y: DATA_0D_t | DATA_1D_t,
        plotter: Plotter | None = None,
        label: str | Literal["auto"] | None = None,
        grid: bool = True,
        axes: Any | None = None,
        **kwargs,
    ) -> Any:
        """Plot ``y`` vs ``x`` using ``plotter.plot()`` method.

        Parameters
        ----------
        x, y :
            Name of properties to plot.
        plotter :
            Object to use for plot. If not provided, we use :attr:`._plotter`.
        label :
            If provided, overrides the legend. Useful when several simulations
            are shown on the same plot. Use the magic keyword ``"auto"`` to
            legend with a short description of current object.
        grid :
            If grid should be plotted. Default is True.
        axes :
            Axes to re-use, if provided. The default is None (plot on new
            axis).
        kwargs :
            Other keyword arguments passed to the :meth:`.Plotter.plot` method.

        Returns
        -------
        Any
            Objects created by the :meth:`.Plotter.plot`.

        """
        if plotter is None:
            plotter = self._plotter
        data = self.to_pandas(x, y)

        if label == "auto":
            label = str(self)

        axes, color = plotter.plot(
            data,
            x=x,
            y=y,
            grid=grid,
            axes=axes,
            label=label,
            color=self._color,
            **kwargs,
        )
        if self._color is None:
            self._color = color
        return axes

    def hist(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    def to_pandas(self, *args: DATA_0D_t | DATA_1D_t) -> pd.DataFrame:
        """Concatenate all attribute arrays which name is in ``args`` to a df.

        Parameters
        ----------
        args :
            Name of arguments as saved in current objects. Example:
            ``"population"``, ``"time"``...

        Returns
        -------
        pandas.DataFrame
            Concatenates all desired data.

        Raises
        ------
        MissingDataError:
            If a string in ``args`` does not correspond to any attribute in
            ``self`` (or if corresponding value is ``None``).
        ValueError:
            If all the ``args`` are a single value (float/int/bool).

        """
        data: dict[str, float | np.ndarray] = {
            arg: value
            for arg in args
            if (value := getattr(self, arg, None)) is not None
        }
        if len(data) == len(args):
            try:
                return pd.DataFrame(data)
            except ValueError as e:
                raise ValueError(
                    "Floats/ints/bools are not gettable with this method if "
                    f"no array is asked at the same time.\n{e}"
                )

        missing = [arg for arg in args if getattr(self, arg, None) is None]
        raise MissingDataError(f"{missing} not found in {self}")

    def show(self) -> None:
        """Show the plots that were produced.

        Useful for the bash interface.

        """
        return self._plotter.show()


class SimulationResultsFactory(ABC):
    """Easily create :class:`.SimulationResults`."""

    def __init__(
        self,
        plotter: Plotter | None = None,
        freq_ghz: float | None = None,
        stl_path: str | Path | None = None,
        stl_alpha: float | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Instantiate object.

        Parameters
        ----------
        plotter :
            Object to create the plots.
        freq_ghz :
            RF frequency in :unit:`GHz`. Used to compute RF period, which is
            mandatory for exp growth fitting.
        stl_path :
            Path to the ``STL`` file holding the 3D structure of the system.
            The default is None.
        stl_alpha :
            Transparency setting for the mesh.

        """
        if plotter is None:
            plotter = DefaultPlotter()
        self._plotter = plotter
        self._freq_ghz = freq_ghz
        self._period = 1.0 / freq_ghz if freq_ghz is not None else None
        self._stl_path = stl_path
        self._stl_alpha = stl_alpha

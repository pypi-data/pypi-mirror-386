"""Define :class:`ParticleMonitor`.

This dictionary-based  object holds :class:`Particle` objects. Keys of the
dictionary are the particle id of the :class:`Particle`.

.. todo::
    Raise error when folder is not found.

"""

import logging
import os
import re
from collections.abc import Callable, Collection, Generator
from pathlib import Path
from typing import Any, Literal, Self

import numpy as np
import pandas as pd
import vedo
from numpy._typing import NDArray

from simultipac.particle_monitor.particle import Particle, PartMonLine
from simultipac.plotter.default import DefaultPlotter
from simultipac.plotter.plotter import Plotter
from simultipac.types import PARTICLE_0D_t


def _load_particle_monitor_file(
    filepath: Path, delimiter: str | None = None
) -> tuple[PartMonLine, ...]:
    """Load a single Particle Monitor file.

    A Particle Monitor file holds the ID, position, momentum of every particle
    alive at a specific time.

    .. todo::
        Type hints could be cleaner.

    """
    n_header = 6

    with open(filepath, encoding="utf-8") as file:
        particles_info = tuple(
            tuple(line.split(delimiter))
            for i, line in enumerate(file)
            if i > n_header
        )

    return particles_info  # type: ignore


FILTER_KEY = Literal["seed", "emitted", "collision", "no collision"]
FILTER_FUNC = Callable[[Particle], bool]


class ParticleMonitor(dict):
    """Holds all :class:`Particle` objects as values, particle id as keys.

    Attributes
    ----------
    max_time :
        Time at which the simulation ended.

    """

    FILTERS: dict[str, FILTER_FUNC] = {
        "_default": lambda _: True,
        "seed": lambda p: p.source_id == 0,
        "emitted": lambda p: p.source_id == 1,
        "collision": lambda p: not p.alive_at_end,
        "no collision": lambda p: p.alive_at_end,
    }

    def __init__(
        self,
        dict_of_parts: dict[int, Particle],
        max_time: float,
        stl_path: str | Path | None = None,
        stl_alpha: float | None = None,
        plotter: Plotter | None = None,
        **kwargs,
    ) -> None:
        """Create the object, ordered list of filepaths beeing provided.

        Also handle mesh related operations: collision/emission angles
        calculation.

        Parameters
        ----------
        dict_of_parts :
            Dictionary which values are :class:`.Particle` instances and keys
            are the associated unique ID.
        max_time :
            Simulation end time. Used to determine which particles were alive
            at the end of the simulation.
        stl_path :
            Path to the structure mesh. In particular, used to compute the
            collision and emission angles.
        stl_alpha :
            Mesh transparency setting.
        plotter :
            Object to create the plots.

        """
        if plotter is None:
            plotter = DefaultPlotter()
        self._plotter = plotter
        self._stl_path = stl_path
        self._mesh: vedo.Mesh
        self._kwargs = kwargs
        super().__init__(dict_of_parts)

        self.max_time = max_time
        for particle in self.values():
            particle.determine_if_alive_at_end(self.max_time)

        if stl_path is not None:
            self._mesh = self._load_mesh(
                stl_path, stl_alpha=stl_alpha, **kwargs
            )
            self.compute_collision_angles(self._mesh)
        return

    def __repr__(self) -> str:
        """Return how the object was initialized."""
        return (
            f"ParticleMonitor(dict_of_parts={len(self)} particles, "
            f"stl_path={self._stl_path}, plotter={self._plotter}, kwargs="
            f"{self._kwargs})"
        )

    @classmethod
    def from_folder(
        cls,
        folder: str | Path,
        delimiter: str | None = None,
        stl_path: str | Path | None = None,
        stl_alpha: float | None = None,
        plotter: Plotter | None = None,
        load_first_n_particles: int | None = None,
        particle_monitor_ignore: Collection[str] = (".swp",),
        **kwargs,
    ) -> Self:
        """Load all the particle monitor files and create object.

        Parameters
        ----------
        folder :
            Where all the CST particle monitor files are stored.
        delimiter :
            Delimiter between columns.
        stl_path :
            Path to the mesh file, saved as ``STL``.
        stl_alpha :
            Transparency for the 3D mesh.
        plotter :
            Object realizing the plots.
        load_first_n_particles :
            To only load the first particles that are found in the ``folder``.
        particle_monitor_ignore :
            File extensions to skip when exploring the particle monitor folder.

        Returns
        -------
        particle_monitor : ParticleMonitor
            Instantiated object.

        """
        if stl_path is None:
            raise ValueError
        if isinstance(folder, str):
            folder = Path(folder)
        dict_of_parts: dict[int, Particle] = {}

        filepaths, max_time = _sorted_particle_monitor_files(
            folder, particle_monitor_ignore=particle_monitor_ignore
        )

        for filepath in filepaths:
            particles_info = _load_particle_monitor_file(
                filepath, delimiter=delimiter
            )

            for part_mon_line in particles_info:
                particle_id = int(part_mon_line[10])

                if (
                    load_first_n_particles is not None
                    and particle_id > load_first_n_particles
                ):
                    continue

                if particle_id in dict_of_parts:
                    dict_of_parts[particle_id].add_a_file(part_mon_line)
                    continue

                dict_of_parts[particle_id] = Particle(part_mon_line)

        for particle in dict_of_parts.values():
            particle.finalize()
            particle.extrapolate_pos_and_mom_one_time_step_further()

        return cls(
            dict_of_parts,
            stl_path=stl_path,
            stl_alpha=stl_alpha,
            plotter=plotter,
            max_time=max_time,
            **kwargs,
        )

    @property
    def seed_electrons(self) -> dict[int, Particle]:
        """Return only seed electrons."""
        return _filter_source_id(self, 0)

    @property
    def emitted_electrons(self) -> dict[int, Particle]:
        """Return only emitted electrons."""
        return _filter_source_id(self, 1)

    def __str__(self) -> str:
        """Resume information on the simulation."""
        n_total_particles = len(self.keys())
        n_seed_electrons = len(self.seed_electrons.keys())
        n_emitted_electrons = len(self.emitted_electrons.keys())
        n_collisions = len(_filter_out_alive_at_end(self).keys())
        n_alive_at_end = len(_filter_out_dead_at_end(self).keys())
        out = f"This simulation involved {n_total_particles} electrons."
        out += f"\n\t{n_seed_electrons} where seed electrons."
        out += f"\n\t{n_emitted_electrons} where emitted electrons."
        out += f"\n\t{n_alive_at_end} where still alive at end of simulation."
        out += f"\n\tThere was {n_collisions} collisions."
        return out

    def emission_energies(
        self, source_id: int | None = None
    ) -> NDArray[np.float64]:
        """Get emission energies of all or only a subset of particles."""
        subset = self
        if source_id is not None:
            subset = _filter_source_id(subset, source_id)
        out = [part.emission_energy for part in subset.values()]
        return np.array(out)

    def collision_energies(
        self,
        source_id: int | None = None,
        extrapolation: bool = True,
        remove_alive_at_end: bool = True,
    ) -> NDArray[np.float64]:
        """Get all collision energies in :unit:`eV`.

        Parameters
        ----------
        source_id : int | None, optional
            If set, we only take particles which source_id is ``source_id``.
            The default is None.
        extrapolation : bool, optional
            If True, we extrapolate over the last time steps to refine the
            collision energy. Otherwise, we simply take the last known energy
            of the particle. The default is True.
        remove_alive_at_end : bool, optional
            To remove particles alive at the end of the simulation (did not
            impact a wall). The default is True.

        """
        subset = self
        if source_id is not None:
            subset = _filter_source_id(subset, source_id)
        if remove_alive_at_end:
            subset = _filter_out_alive_at_end(subset)

        out = [
            part.collision_energy(extrapolation) for part in subset.values()
        ]
        return np.array(out)

    def emission_angles(
        self,
        source_id: int | None = None,
        extrapolation: bool = True,
    ) -> NDArray[np.float64]:
        """Get all emission angles in :unit:`deg`.

        Parameters
        ----------
        source_id : int | None, optional
            If set, we only take particles which source_id is ``source_id``.
            The default is None.
        extrapolation : bool, optional
            If True, we extrapolate over the last time steps to refine the
            collision energy. Otherwise, we simply take the last known energy
            of the particle. The default is True.
        remove_alive_at_end : bool, optional
            To remove particles alive at the end of the simulation (did not
            impact a wall). The default is True.

        Returns
        -------
        out : NDArray[np.float64]
            Emission angles in degrees.

        """
        raise NotImplementedError
        subset = self
        if source_id is not None:
            subset = _filter_source_id(subset, source_id)
        out = [part.emission_angle for part in subset.values()]
        return np.array(out)

    def collision_angles(
        self,
        source_id: int | None = None,
        remove_alive_at_end: bool = True,
    ) -> NDArray[np.float64]:
        """Get all collision angles in :unit:`deg`.

        Parameters
        ----------
        source_id :
            If set, we only take particles which source_id is ``source_id``.
            The default is None.
        remove_alive_at_end :
            To remove particles alive at the end of the simulation (did not
            impact a wall). The default is True.

        """
        subset = self
        if source_id is not None:
            subset = _filter_source_id(subset, source_id)
        if remove_alive_at_end:
            subset = _filter_out_alive_at_end(subset)

        out = [part.collision_angle for part in subset.values()]
        return np.array(out)

    def last_known_position(
        self,
        source_id: int | None = None,
        remove_alive_at_end: bool = True,
    ) -> NDArray[np.float64]:
        """Get the last recorded position of every particle.

        Parameters
        ----------
        source_id : int | None, optional
            If set, we only take particles which source_id is ``source_id``.
            The default is None.
        to_numpy : bool, optional
            If True, output list is transformed to an array. The default is
            True.
        remove_alive_at_end : bool, optional
            To remove particles alive at the end of the simulation (did not
            impact a wall). The default is True.

        Returns
        -------
        out : NDArray[np.float64]
            Last known position in :unit:`mm` of every particle.

        """
        subset = self
        if source_id is not None:
            subset = _filter_source_id(subset, source_id)
        if remove_alive_at_end:
            subset = _filter_out_alive_at_end(subset)

        out = [part.position.last for part in subset.values()]
        return np.array(out)

    def last_known_direction(
        self,
        source_id: int | None = None,
        normalize: bool = True,
        remove_alive_at_end: bool = True,
    ) -> NDArray[np.float64]:
        """
        Get the last recorded direction of every particle.

        .. todo::
            Why did I choose to compute position difference rather than just
            taking the momentum array when not normalizing???

        Parameters
        ----------
        source_id : int | None, optional
            If set, we only take particles which source_id is ``source_id``.
            The default is None.
        normalize : bool, optional
            To normalize the direction vector. The default is True.
        remove_alive_at_end : bool, optional
            To remove particles alive at the end of the simulation (did not
            impact a wall). The default is True.

        Returns
        -------
        out : NDArray[np.float64]
            Last known moment vector of every particle.

        """
        subset = self
        if source_id is not None:
            subset = _filter_source_id(subset, source_id)
        if remove_alive_at_end:
            subset = _filter_out_alive_at_end(subset)

        out = [part.momentum.last for part in subset.values()]

        if normalize:
            out = [mom / np.linalg.norm(mom) for mom in out]

        return np.array(out)

    def compute_collision_angles(self, mesh: vedo.Mesh, **kwargs) -> None:
        """Find all collisions."""
        mesh.compute_normals(points=False, cells=True)
        for particle in self.values():
            particle.find_collision(mesh, **kwargs)
            particle.compute_collision_angle(mesh)

    def hist(
        self,
        x: PARTICLE_0D_t,
        bins: int = 200,
        hist_range: tuple[float, float] | None = None,
        plotter: Plotter | None = None,
        filter: FILTER_KEY | FILTER_FUNC | None = None,
        title: str | None = None,
        **kwargs,
    ) -> Any:
        """Create a histogram.

        Parameters
        ----------
        x :
            Name of the data to plot.
        bins :
            Number of histogram bins.
        hist_range :
            Lower and upper value for the histogram.
        plotter :
            Object creating the plots.
        filter :
            To plot only some of the particles.
        title :
            Figure title. If not provided, we take a default according to the
            value of ``filter``.

        """
        if plotter is None:
            plotter = self._plotter
        data = self.to_pandas(x, filter=filter)

        if title is None:
            if isinstance(filter, str):
                title = filter
            elif filter is None:
                title = None
            else:
                title = "Personnalized filter"

        return self._plotter.hist(
            data, x, bins=bins, hist_range=hist_range, title=title, **kwargs
        )

    def plot_mesh(
        self, plotter: Plotter | None = None, *args, **kwargs
    ) -> Any:
        """Plot the stored mesh."""
        if plotter is None:
            plotter = self._plotter
        return plotter.plot_mesh(self._mesh, *args, **kwargs)

    def plot_trajectories(
        self,
        emission_color: str | None = None,
        collision_color: str | None = None,
        lw: int = 7,
        r: int = 8,
        plotter: Plotter | None = None,
        filter: FILTER_KEY | FILTER_FUNC | None = None,
        **kwargs,
    ) -> Any:
        """Plot trajectories in 3D.

        Parameters
        ----------
        emission_color :
            If provided, the first known position is colored with this color.
        collision_color :
            If provided, the last known position is colored with this color.
        collision_point :
            If provided and ``collision_color`` is not ``None``, we plot this
            point instead of the last of ``points``. This is useful when the
            extrapolated time is large, and actuel collision point may differ
            significantly from last position points.
        lw :
            Trajectory line width.
        r :
            Size of the emission/collision points.
        plotter :
            An object allowing to plot data.
        filter :
            To select the particles to be plotted.

        """
        if plotter is None:
            plotter = self._plotter
        particles = self.filter_particles(filter)

        veplotter = None
        for p in particles:
            veplotter = p.plot_trajectory(
                plotter=plotter,
                emission_color=emission_color,
                collision_color=collision_color,
                lw=lw,
                r=r,
                **kwargs,
            )
        return veplotter

    @property
    def to_list(self) -> list[Particle]:
        """Return stored :class:`.Particle` as a list."""
        return list(self.values())

    def to_pandas(
        self,
        *args: PARTICLE_0D_t,
        filter: FILTER_KEY | FILTER_FUNC | None = None,
    ) -> pd.DataFrame:
        particles = self.filter_particles(filter)

        data: dict[str, list[float]] = {}

        for arg in args:
            concat: list[float] = []
            for result in particles:
                value = getattr(result, arg, None)
                if not isinstance(value, (float, int)):
                    logging.debug(
                        f"The {arg} attribute of {result} is not a float but a"
                        f" {type(value)}, so it was not added to the "
                        "dataframe."
                    )
                    continue
                concat.append(value)
            data[arg] = concat

        lengths = {key: len(value) for key, value in data.items()}
        if len(set(lengths.values())) > 1:
            raise ValueError(
                "All the lists in data must have the same length. Maybe "
                f"{particles = } is a Generator? Or maybe one of the keys was "
                "not found in one or more of the Particles?\n"
                f"{lengths = }"
            )

        try:
            return pd.DataFrame(data)
        except ValueError as e:
            raise ValueError(
                f"Could not get a data, creating malformed dataframe.\n{e}"
            )

    def filter_particles(
        self, filter: FILTER_KEY | FILTER_FUNC | None
    ) -> list[Particle]:
        """Return a list of particles that match the given criterion."""
        if isinstance(filter, str):
            filter = self.FILTERS.get(filter)
            if filter is None:
                logging.error(
                    f"Unknown filter: {filter}. Returning all particles."
                )
        if filter is None:
            filter = self.FILTERS["_default"]

        return [p for p in self.values() if filter(p)]

    def _load_mesh(
        self, stl_path: Path | str, stl_alpha: float | None = None, **kwargs
    ) -> vedo.Mesh:
        """Load the ``STL`` file with :meth:`self._plotter.load_mesh`."""
        if isinstance(stl_path, str):
            stl_path = Path(stl_path)
        assert stl_path.is_file, f"{stl_path = } does not exist."
        return self._plotter.load_mesh(stl_path, stl_alpha=stl_alpha, **kwargs)


def _absolute_file_paths(
    directory: Path, particle_monitor_ignore: Collection[str] = (".swp",)
) -> Generator[Path, Path, None]:
    """Get all filepaths in absolute from dir, remove unwanted files.

    Parameters
    ----------
    directory :
        Folder to explore.
    particle_monitor_ignore :
        Extensions to skip.

    """
    for dirpath, _, filenames in os.walk(directory):
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                f = Path(f)
                if f.suffix in particle_monitor_ignore:
                    continue
                yield Path(dirpath, f)


def _get_float_from_filename(filename: Path) -> float:
    """Extract the float value from the filename.

    Parameters
    ----------
    filename :
        Filename, looking like
        :file:`position  monitor 1_0.117175810039043.txt`

    """
    match = re.search(
        r"_(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)(?=\.txt$)", filename.name
    )
    if match:
        return float(match.group(1))
    raise ValueError(
        f"Cannot extract float from {filename = }. Expected format: "
        "`position  monitor 1_0.117175810039043.txt`."
    )


def _sorted_particle_monitor_files(
    directory: Path, particle_monitor_ignore: Collection[str] = (".swp",)
) -> tuple[list[Path], float]:
    """Recursively get and sort all particle monitor files.

    Typical structure is::

        directory
        ├──'position  monitor 1_0.117175810039043.txt'
        ├──'position  monitor 1_0.156234413385391.txt'
        ├──'position  monitor 1_0.19529302418232.txt'
        ├──'position  monitor 1_0.232905015349388.txt'
        ├──'position  monitor 1_0.271963626146317.txt'
        ├──...
        └──'position  monitor 1_7.81172066926956E-02.txt'

    Parameters
    ----------
    directory :
        Folder to explore.
    particle_monitor_ignore :
        Extensions to skip.

    Returns
    -------
    files : list[Path]
        The sorted filepaths.
    max_time : float
        Highest time among provided files.

    """
    files = list(
        _absolute_file_paths(
            directory, particle_monitor_ignore=particle_monitor_ignore
        )
    )
    sorted_files = sorted(files, key=_get_float_from_filename)
    max_time = (
        _get_float_from_filename(sorted_files[-1]) if sorted_files else 0.0
    )
    return sorted_files, max_time


def _filter_source_id(
    input_dict: dict[int, Particle],
    wanted_id: int,
) -> dict[int, Particle]:
    """Filter Particles against the sourceID field."""
    return {
        pid: part
        for pid, part in input_dict.items()
        if part.source_id == wanted_id
    }


def _filter_out_dead_at_end(
    input_dict: dict[int, Particle],
) -> dict[int, Particle]:
    """Filter out Particles that collisioned during simulation."""
    particles_alive_at_end = {
        pid: part for pid, part in input_dict.items() if part.alive_at_end
    }
    return particles_alive_at_end


def _filter_out_alive_at_end(
    input_dict: dict[int, Particle],
) -> dict[int, Particle]:
    """Filter out Particles that were alive at the end of simulation."""
    particles_that_collisioned_during_simulation = {
        pid: part for pid, part in input_dict.items() if not part.alive_at_end
    }
    return particles_that_collisioned_during_simulation


def _filter_out_part_with_one_time_step(
    input_dict: dict[int, Particle],
) -> dict[int, Particle]:
    """Remove particle with only one known position.

    This is useful when the time resolution is low.

    """
    return {
        pid: part for pid, part in input_dict.items() if len(part.time) > 1
    }

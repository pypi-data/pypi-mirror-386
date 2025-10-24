# -*- coding: utf-8 -*-

import copy
import importlib
import logging
import time
from pathlib import Path
from typing import Literal, TypeVar

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from baderkit.core.methods import Method
from baderkit.core.methods.shared_numba import get_edges, get_min_avg_surface_dists
from baderkit.core.toolkit import Format, Grid, Structure

# This allows for Self typing and is compatible with python 3.10
Self = TypeVar("Self", bound="Bader")


class Bader:
    """
    Class for running Bader analysis on a regular grid. For information on each
    method, see our [docs](https://sweav02.github.io/baderkit/)

    Parameters
    ----------
    charge_grid : Grid
        A Grid object with the charge density that will be integrated.
    reference_grid : Grid | None
        A Grid object whose values will be used to construct the basins. If
        None, defaults to the charge_grid.
    method : str | Method, optional
        The algorithm to use for generating bader basins.
    vacuum_tol: float | bool, optional
        If a float is provided, this is the value below which a point will
        be considered part of the vacuum. If a bool is provided, no vacuum
        will be used on False, and the default tolerance will be used on True.
    normalize_vacuum: bool, optional
        Whether or not the reference data needs to be converted to real space
        units for vacuum tolerance comparison. This should be True for charge
        densities and False for the ELF. If None, the setting will be guessed
        from the reference grid's data type.
    basin_tol: float, optional
        The value below which a basin will not be considered significant. This
        is used only used to avoid writing out data that is likely not valuable.

    """

    def __init__(
        self,
        charge_grid: Grid,
        reference_grid: Grid | None = None,
        method: str | Method = Method.weight,
        vacuum_tol: float | bool = 1.0e-3,
        normalize_vacuum: bool | None = None,
        basin_tol: float = 1.0e-3,
    ):

        # ensure th method is valid
        valid_methods = [m.value for m in Method]
        if isinstance(method, Method):
            self._method = method
        elif method in valid_methods:
            self._method = Method(method)
        else:
            raise ValueError(
                f"Invalid method '{method}'. Available options are: {valid_methods}"
            )

        self._charge_grid = charge_grid

        # if no reference is provided, use the base charge grid
        if reference_grid is None:
            reference_grid = charge_grid.copy()
        self._reference_grid = reference_grid

        # guess whether the reference should be scaled for vacuum tolerance comparison
        if normalize_vacuum is None:
            if reference_grid.data_type == "elf":
                normalize_vacuum = False
            else:
                normalize_vacuum = True

        # if vacuum tolerance is True, set it to the same default as above
        if vacuum_tol is True:
            self._vacuum_tol = 1.0e-3
        else:
            self._vacuum_tol = vacuum_tol
        self._normalize_vacuum = normalize_vacuum
        self._basin_tol = basin_tol

        # set hidden class variables. This allows us to cache properties and
        # still be able to recalculate them if needed, though that should only
        # be done by advanced users
        self._reset_properties()

        # whether or not to use overdetermined gradients in neargrid methods.
        self._use_overdetermined = False

    ###########################################################################
    # Set Properties
    ###########################################################################
    def _reset_properties(
        self,
        include_properties: list[str] = None,
        exclude_properties: list[str] = [],
    ):
        # if include properties is not provided, we wnat to reset everything
        if include_properties is None:
            include_properties = [
                # assigned by run_bader
                "basin_labels",
                "basin_maxima_frac",
                "basin_maxima_charge_values",
                "basin_maxima_ref_values",
                "basin_maxima_vox",
                "basin_charges",
                "basin_volumes",
                "vacuum_charge",
                "vacuum_volume",
                "significant_basins",
                "vacuum_mask",
                "num_vacuum",
                # Assigned by calling the property
                "basin_min_surface_distances",
                "basin_avg_surface_distances",
                "basin_edges",
                "atom_edges",
                "structure",
                # Assigned by run_atom_assignment
                "basin_atoms",
                "basin_atom_dists",
                "atom_labels",
                "atom_charges",
                "atom_volumes",
                "atom_min_surface_distances",
                "atom_avg_surface_distances" "total_electron_number",
            ]
        # get our final list of properties
        reset_properties = [
            i for i in include_properties if i not in exclude_properties
        ]
        # set corresponding hidden variable to None
        for prop in reset_properties:
            setattr(self, f"_{prop}", None)

    @property
    def charge_grid(self) -> Grid:
        """

        Returns
        -------
        Grid
            A Grid object with the charge density that will be integrated.

        """
        return self._charge_grid

    @charge_grid.setter
    def charge_grid(self, value: Grid):
        self._charge_grid = value
        self._reset_properties()

    @property
    def reference_grid(self) -> Grid:
        """

        Returns
        -------
        Grid
            A grid object whose values will be used to construct the basins.

        """
        return self._reference_grid

    @reference_grid.setter
    def reference_grid(self, value: Grid):
        self._reference_grid = value
        self._reset_properties()

    @property
    def method(self) -> str:
        """

        Returns
        -------
        str
            The algorithm to use for generating bader basins. If None, defaults
            to neargrid.

        """
        return self._method

    @method.setter
    def method(self, value: str | Method):
        # Support both Method instances and their string values
        valid_values = [m.value for m in Method]
        if isinstance(value, Method):
            self._method = value
        elif value in valid_values:
            self._method = Method(value)
        else:
            raise ValueError(
                f"Invalid method '{value}'. Available options are: {valid_values}"
            )
        self._reset_properties(exclude_properties=["vacuum_mask", "num_vacuum"])

    @property
    def vacuum_tol(self) -> float | bool:
        """

        Returns
        -------
        float
            The value below which a point will be considered part of the vacuum.
            The default is 0.001.

        """
        return self._vacuum_tol

    @vacuum_tol.setter
    def vacuum_tol(self, value: float | bool):
        self._vacuum_tol = value
        self._reset_properties()
        # TODO: only reset everything if the vacuum actually changes

    @property
    def normalize_vacuum(self) -> bool:
        """

        Returns
        -------
        bool
            Whether or not the reference data needs to be converted to real space
            units for vacuum tolerance comparison. This should be set to True if
            the data follows VASP's CHGCAR standards, but False if the data should
            be compared as is (e.g. in ELFCARs)

        """
        return self._normalize_vacuum

    @normalize_vacuum.setter
    def normalize_vacuum(self, value: bool) -> bool:
        self._normalize_vacuum = value
        self._reset_properties()
        # TODO: only reset everything if the vacuum actually changes

    @property
    def basin_tol(self) -> float:
        """

        Returns
        -------
        float
            The value below which a basin will not be considered significant. This
            is used to avoid writing out data that is likely not valuable.
            The default is 0.001.

        """
        return self._basin_tol

    @basin_tol.setter
    def basin_tol(self, value: float):
        self._basin_tol = value
        self._reset_properties(include_properties=["significant_basins"])

    ###########################################################################
    # Calculated Properties
    ###########################################################################

    @property
    def basin_labels(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            A 3D array of the same shape as the reference grid with entries
            representing the basin the voxel belongs to. Note that for some
            methods (e.g. weight) the voxels have weights for each basin.
            These will be stored in the basin_weights property.

        """
        if self._basin_labels is None:
            self.run_bader()
        return self._basin_labels

    @property
    def basin_maxima_frac(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The fractional coordinates of each attractor.

        """
        if self._basin_maxima_frac is None:
            self.run_bader()
        return self._basin_maxima_frac

    @property
    def basin_maxima_charge_values(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The charge data value at each maximum. If the maximum is
            off grid, this value will be interpolated.

        """
        if self._basin_maxima_charge_values is None:
            self._basin_maxima_charge_values = self.charge_grid.values_at(
                self.basin_maxima_frac
            )
        return self._basin_maxima_charge_values

    @property
    def basin_maxima_ref_values(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The reference data value at each maximum. If the maximum is
            off grid, this value will be interpolated.

        """
        if self._basin_maxima_ref_values is None:
            # we get these values during each bader method anyways, so
            # we run this here.
            self.run_bader()
        return self._basin_maxima_ref_values

    @property
    def basin_maxima_vox(self) -> NDArray[int]:
        """

        Returns
        -------
        NDArray[int]
            The voxel coordinates of each attractor. There may be more of these
            than the fractional coordinates, as some maxima sit exactly between
            several voxels.

        """
        if self._basin_maxima_vox is None:
            self.run_bader()
        return self._basin_maxima_vox

    @property
    def basin_charges(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The charges assigned to each attractor.

        """
        if self._basin_charges is None:
            self.run_bader()
        return self._basin_charges

    @property
    def basin_volumes(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The volume assigned to each attractor.

        """
        if self._basin_volumes is None:
            self.run_bader()
        return self._basin_volumes

    @property
    def basin_min_surface_distances(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The distance from each basin maxima to the nearest point on
            the basins surface

        """
        if self._basin_min_surface_distances is None:
            self._get_basin_surface_distances()
        return self._basin_min_surface_distances

    @property
    def basin_avg_surface_distances(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The avg distance from each basin maxima to the edges of its basin

        """
        if self._basin_avg_surface_distances is None:
            self._get_basin_surface_distances()
        return self._basin_avg_surface_distances

    @property
    def basin_atoms(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The atom index of each basin is assigned to.

        """
        if self._basin_atoms is None:
            self.run_atom_assignment()
        return self._basin_atoms

    @property
    def basin_atom_dists(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The distance from each attractor to the nearest atom

        """
        if self._basin_atom_dists is None:
            self.run_atom_assignment()
        return self._basin_atom_dists

    @property
    def significant_basins(self) -> NDArray[bool]:
        """

        Returns
        -------
        NDArray[bool]
            A 1D mask with an entry for each basin that is True where basins
            are significant.

        """
        if self._significant_basins is None:
            self._significant_basins = self.basin_charges > self.basin_tol
        return self._significant_basins

    @property
    def atom_labels(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            A 3D array of the same shape as the reference grid with entries
            representing the atoms the voxel belongs to.

            Note that for some methods (e.g. weight) some voxels have fractional
            assignments for each basin and this will not represent exactly how
            charges are assigned.

        """
        if self._atom_labels is None:
            self.run_atom_assignment()
        return self._atom_labels

    @property
    def atom_charges(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The charge assigned to each atom

        """
        if self._atom_charges is None:
            self.run_atom_assignment()
        return self._atom_charges

    @property
    def atom_volumes(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The volume assigned to each atom

        """
        if self._atom_volumes is None:
            self.run_atom_assignment()
        return self._atom_volumes

    @property
    def atom_min_surface_distances(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The distance from each atom to the nearest point on the atoms surface.

        """
        if self._atom_min_surface_distances is None:
            self._get_atom_surface_distances()
        return self._atom_min_surface_distances

    @property
    def atom_avg_surface_distances(self) -> NDArray[float]:
        """

        Returns
        -------
        NDArray[float]
            The avg distance from each atom to the edges of its basin

        """
        if self._atom_avg_surface_distances is None:
            self._get_basin_surface_distances()
        return self._atom_avg_surface_distances

    @property
    def structure(self) -> Structure:
        """

        Returns
        -------
        Structure
            The pymatgen structure basins are assigned to.

        """
        if self._structure is None:
            self._structure = self.reference_grid.structure.copy()
            self._structure.relabel_sites(ignore_uniq=True)
        return self._structure

    @property
    def basin_edges(self) -> NDArray[np.bool_]:
        """

        Returns
        -------
        NDArray[np.bool_]
            A mask with the same shape as the input grids that is True at points
            on basin edges.

        """
        if self._basin_edges is None:
            self._basin_edges = get_edges(
                labeled_array=self.basin_labels,
                vacuum_mask=np.zeros(self.basin_labels.shape, dtype=np.bool_),
                neighbor_transforms=self.reference_grid.point_neighbor_transforms[0],
            )
        return self._basin_edges

    @property
    def atom_edges(self) -> NDArray[np.bool_]:
        """

        Returns
        -------
        NDArray[np.bool_]
            A mask with the same shape as the input grids that is True at points
            on atom edges.

        """
        if self._atom_edges is None:
            self._atom_edges = get_edges(
                labeled_array=self.atom_labels,
                vacuum_mask=np.zeros(self.atom_labels.shape, dtype=np.bool_),
                neighbor_transforms=self.reference_grid.point_neighbor_transforms[0],
            )
        return self._atom_edges

    @property
    def vacuum_charge(self) -> float:
        """

        Returns
        -------
        float
            The charge assigned to the vacuum.

        """
        if self._vacuum_charge is None:
            self.run_bader()
        return self._vacuum_charge

    @property
    def vacuum_volume(self) -> float:
        """

        Returns
        -------
        float
            The total volume assigned to the vacuum.

        """
        if self._vacuum_volume is None:
            self.run_bader()
        return self._vacuum_volume

    @property
    def vacuum_mask(self) -> NDArray[bool]:
        """

        Returns
        -------
        NDArray[bool]
            A mask representing the voxels that belong to the vacuum.

        """
        if self._vacuum_mask is None:
            # if vacuum tolerance is set to False, ignore vacuum
            if self.vacuum_tol is False:
                self._vacuum_mask = np.zeros_like(
                    self.reference_grid.total, dtype=np.bool_
                )
            else:
                if self.normalize_vacuum:
                    self._vacuum_mask = self.reference_grid.total < (
                        self.vacuum_tol * self.structure.volume
                    )
                else:
                    self._vacuum_mask = self.reference_grid.total < self.vacuum_tol
        return self._vacuum_mask

    @property
    def num_vacuum(self) -> int:
        """

        Returns
        -------
        int
            The number of vacuum points in the array

        """
        if self._num_vacuum is None:
            self._num_vacuum = np.count_nonzero(self.vacuum_mask)
        return self._num_vacuum

    @property
    def total_electron_number(self) -> float:
        """

        Returns
        -------
        float
            The total number of electrons in the system calculated from the
            atom charges and vacuum charge. If this does not match the true
            total electron number within reasonable floating point error,
            there is a major problem.

        """

        return self.atom_charges.sum() + self.vacuum_charge

    @staticmethod
    def all_methods() -> list[str]:
        """

        Returns
        -------
        list[str]
            A list of the available methods.

        """

        return [i.value for i in Method]

    @property
    def results_summary(self) -> dict:
        """

        Returns
        -------
        results_dict : dict
            A dictionary summary of all results

        """
        results_dict = {
            "method": self.method,
            "basin_maxima_frac": self.basin_maxima_frac,
            "basin_maxima_vox": self.basin_maxima_vox,
            "basin_charges": self.basin_charges,
            "basin_volumes": self.basin_volumes,
            "basin_min_surface_distances": self.basin_min_surface_distances,
            "basin_avg_surface_distances": self.basin_avg_surface_distances,
            "basin_atoms": self.basin_atoms,
            "basin_atom_dists": self.basin_atom_dists,
            "atom_charges": self.atom_charges,
            "atom_volumes": self.atom_volumes,
            "atom_min_surface_distances": self.atom_min_surface_distances,
            "atom_avg_surface_distances": self.atom_avg_surface_distances,
            "structure": self.structure,
            "vacuum_charge": self.vacuum_charge,
            "vacuum_volume": self.vacuum_volume,
            "significant_basins": self.significant_basins,
            "total_electron_num": self.total_electron_number,
        }
        return results_dict

    def run_bader(self) -> None:
        """
        Runs the entire Bader process and saves results to class variables.

        Returns
        -------
        None

        """
        t0 = time.time()
        logging.info(f"Beginning Bader Algorithm Using '{self.method.name}' Method")
        # Normalize the method name to a module and class name
        module_name = self.method.replace(
            "-", "_"
        )  # 'pseudo-neargrid' -> 'pseudo_neargrid'
        class_name = (
            "".join(part.capitalize() for part in module_name.split("_")) + "Method"
        )

        # import method
        mod = importlib.import_module(f"baderkit.core.methods.{module_name}")
        Method = getattr(mod, class_name)

        # Instantiate and run the selected method
        method = Method(
            charge_grid=self.charge_grid,
            reference_grid=self.reference_grid,
            vacuum_mask=self.vacuum_mask,
            num_vacuum=self.num_vacuum,
        )
        if self._use_overdetermined:
            method._use_overdetermined = True
        results = method.run()

        for key, value in results.items():
            setattr(self, f"_{key}", value)
        t1 = time.time()
        logging.info("Bader Algorithm Complete")
        logging.info(f"Time: {round(t1-t0,2)}")

    def assign_basins_to_structure(self, structure: Structure):

        # Get basin and atom frac coords
        basins = self.basin_maxima_frac  # (N_basins, 3)
        atoms = structure.frac_coords  # (N_atoms, 3)

        # get lattice matrix and number of atoms/basins
        L = structure.lattice.matrix  # (3, 3)
        N_basins = len(basins)

        # Vectorized deltas, minimum‑image wrapping
        diffs = atoms[None, :, :] - basins[:, None, :]
        diffs += np.where(diffs <= -0.5, 1, 0)
        diffs -= np.where(diffs >= 0.5, 1, 0)

        # Cartesian diffs & distances
        cart = np.einsum("bij,jk->bik", diffs, L)
        dists = np.linalg.norm(cart, axis=2)

        # Basin→atom assignment & distances
        basin_atoms = np.argmin(dists, axis=1)  # (N_basins,)
        basin_atom_dists = dists[np.arange(N_basins), basin_atoms]  # (N_basins,)

        # Atom labels per grid point
        # NOTE: append -1 so that vacuum gets assigned to -1 in the atom_labels
        # array
        basin_atoms = np.insert(basin_atoms, len(basin_atoms), -1)
        atom_labels = basin_atoms[self.basin_labels]

        return basin_atoms, basin_atom_dists, atom_labels

    def run_atom_assignment(self):
        """
        Assigns bader basins to this Bader objects structure.

        Returns
        -------
        None.

        """
        # ensure bader has run (otherwise our time will include the bader time)
        self.basin_maxima_frac

        # Default structure
        structure = self.structure

        t0 = time.time()
        logging.info("Assigning Atom Properties")
        # get basin assignments for this bader objects structure
        basin_atoms, basin_atom_dists, atom_labels = self.assign_basins_to_structure(
            structure
        )

        # Sum up charges/volumes per atom in one shot. slice with -1 is necessary
        # to prevent no negative value error
        atom_charges = np.bincount(
            basin_atoms[:-1], weights=self.basin_charges, minlength=len(structure)
        )
        atom_volumes = np.bincount(
            basin_atoms[:-1], weights=self.basin_volumes, minlength=len(structure)
        )

        # Store everything
        self._basin_atoms = basin_atoms[:-1]
        self._basin_atom_dists = basin_atom_dists
        self._atom_labels = atom_labels
        self._atom_charges = atom_charges
        self._atom_volumes = atom_volumes
        logging.info("Atom Assignment Finished")
        t1 = time.time()
        logging.info(f"Time: {round(t1-t0, 2)}")

    def _get_atom_surface_distances(self):
        """
        Calculates the distance from each atom to the nearest surface. This is
        automatically called during the atom assignment and generally should
        not be called manually.

        Returns
        -------
        None.

        """
        self._atom_min_surface_distances, self._atom_avg_surface_distances = (
            get_min_avg_surface_dists(
                labels=self.atom_labels,
                frac_coords=self.structure.frac_coords,
                edge_mask=self.atom_edges,
                matrix=self.reference_grid.matrix,
                max_value=np.max(self.structure.lattice.abc) * 2,
            )
        )

    def _get_basin_surface_distances(self):
        """
        Calculates the distance from each basin maxima to the nearest surface.
        This is automatically called during the atom assignment and generally
        should not be called manually.

        Returns
        -------
        None.

        """
        # get the minimum distances
        self._basin_min_surface_distances, self._basin_avg_surface_distances = (
            get_min_avg_surface_dists(
                labels=self.basin_labels,
                frac_coords=self.basin_maxima_frac,
                edge_mask=self.basin_edges,
                matrix=self.reference_grid.matrix,
                max_value=np.max(self.structure.lattice.abc) * 2,
            )
        )

    @classmethod
    def from_vasp(
        cls,
        charge_filename: Path | str = "CHGCAR",
        reference_filename: Path | None | str = None,
        total_only: bool = True,
        **kwargs,
    ) -> Self:
        """
        Creates a Bader class object from VASP files.

        Parameters
        ----------
        charge_filename : Path | str, optional
            The path to the CHGCAR like file that will be used for summing charge.
            The default is "CHGCAR".
        reference_filename : Path | None | str, optional
            The path to CHGCAR like file that will be used for partitioning.
            If None, the charge file will be used for partitioning.
        total_only: bool
            If true, only the first set of data in the file will be read. This
            increases speed and reduced memory usage as the other data is typically
            not used.
            Defaults to True.
        **kwargs : dict
            Keyword arguments to pass to the Bader class.

        Returns
        -------
        Self
            A Bader class object.

        """
        charge_grid = Grid.from_vasp(charge_filename, total_only=total_only)
        if reference_filename is None:
            reference_grid = None
        else:
            reference_grid = Grid.from_vasp(reference_filename, total_only=total_only)

        return cls(charge_grid=charge_grid, reference_grid=reference_grid, **kwargs)

    @classmethod
    def from_cube(
        cls,
        charge_filename: Path | str,
        reference_filename: Path | None | str = None,
        **kwargs,
    ) -> Self:
        """
        Creates a Bader class object from .cube files.

        Parameters
        ----------
        charge_filename : Path | str, optional
            The path to the .cube file that will be used for summing charge.
        reference_filename : Path | None | str, optional
            The path to .cube file that will be used for partitioning.
            If None, the charge file will be used for partitioning.
        **kwargs : dict
            Keyword arguments to pass to the Bader class.

        Returns
        -------
        Self
            A Bader class object.

        """
        charge_grid = Grid.from_cube(charge_filename)
        if reference_filename is None:
            reference_grid = None
        else:
            reference_grid = Grid.from_cube(reference_filename)
        return cls(charge_grid=charge_grid, reference_grid=reference_grid, **kwargs)

    @classmethod
    def from_dynamic(
        cls,
        charge_filename: Path | str,
        reference_filename: Path | None | str = None,
        format: Literal["vasp", "cube", None] = None,
        total_only: bool = True,
        **kwargs,
    ) -> Self:
        """
        Creates a Bader class object from VASP or .cube files. If no format is
        provided the method will automatically try and determine the file type
        from the name

        Parameters
        ----------
        charge_filename : Path | str
            The path to the file containing the charge density that will be
            integrated.
        reference_filename : Path | None | str, optional
            The path to the file that will be used for partitioning.
            If None, the charge file will be used for partitioning.
        format : Literal["vasp", "cube", None], optional
            The format of the grids to read in. If None, the formats will be
            guessed from the file names.
        total_only: bool
            If true, only the first set of data in the file will be read. This
            increases speed and reduced memory usage as the other data is typically
            not used. This is only used if the file format is determined to be
            VASP, as cube files are assumed to contain only one set of data.
            Defaults to True.
        **kwargs : dict
            Keyword arguments to pass to the Bader class.

        Returns
        -------
        Self
            A Bader class object.

        """

        charge_grid = Grid.from_dynamic(
            charge_filename, format=format, total_only=total_only
        )
        if reference_filename is None:
            reference_grid = None
        else:
            reference_grid = Grid.from_dynamic(
                reference_filename, format=format, total_only=total_only
            )
        return cls(charge_grid=charge_grid, reference_grid=reference_grid, **kwargs)

    def copy(self) -> Self:
        """

        Returns
        -------
        Self
            A deep copy of this Bader object.

        """
        return copy.deepcopy(self)

    def write_basin_volumes(
        self,
        basin_indices: NDArray,
        directory: str | Path = None,
        write_reference: bool = False,
        output_format: str | Format = None,
        **writer_kwargs,
    ):
        """
        Writes bader basins to vasp-like files. Points belonging to the basin
        will have values from the charge or reference grid, and all other points
        will be 0.

        Parameters
        ----------
        basin_indices : NDArray
            The list of basin indices to write
        directory : str | Path
            The directory to write the files in. If None, the active directory
            is used.
        write_reference : bool, optional
            Whether or not to write the reference data rather than the charge data.
            Default is False.
        output_format : str | Format, optional
            The format to write with. If None, writes to source format stored in
            the Grid objects metadata.
            Defaults to None.

        Returns
        -------
        None.

        """
        # get the data to use
        if write_reference:
            data_array = self.reference_grid.total
            data_type = self.reference_grid.data_type
        else:
            data_array = self.charge_grid.total
            data_type = self.charge_grid.data_type

        if directory is None:
            directory = Path(".")
        for basin in basin_indices:
            # get a mask everywhere but the requested basin
            mask = self.basin_labels != basin
            # copy data to avoid overwriting. Set data off of basin to 0
            data_array_copy = data_array.copy()
            data_array_copy[mask] = 0.0
            grid = Grid(
                structure=self.structure,
                data={"total": data_array_copy},
                data_type=data_type,
            )
            file_path = directory / f"{grid.data_type.prefix}_b{basin}"
            # write file
            grid.write(filename=file_path, output_format=output_format, **writer_kwargs)

    def write_all_basin_volumes(
        self,
        directory: str | Path = None,
        write_reference: bool = False,
        output_format: str | Format = None,
        **writer_kwargs,
    ):
        """
        Writes all bader basins to vasp-like files. Points belonging to the basin
        will have values from the charge or reference grid, and all other points
        will be 0.

        Parameters
        ----------
        directory : str | Path
            The directory to write the files in. If None, the active directory
            is used.
        write_reference : bool, optional
            Whether or not to write the reference data rather than the charge data.
            Default is False.
        output_format : str | Format, optional
            The format to write with. If None, writes to source format stored in
            the Grid objects metadata.
            Defaults to None.

        Returns
        -------
        None.

        """
        basin_indices = np.where(self.significant_basins)[0]
        self.write_basin_volumes(
            basin_indices=basin_indices,
            directory=directory,
            write_reference=write_reference,
            output_format=output_format,
            **writer_kwargs,
        )

    def write_basin_volumes_sum(
        self,
        basin_indices: NDArray,
        directory: str | Path = None,
        write_reference: bool = False,
        output_format: str | Format = None,
        **writer_kwargs,
    ):
        """
        Writes the union of the provided bader basins to vasp-like files.
        Points belonging to the basins will have values from the charge or
        reference grid, and all other points will be 0.

        Parameters
        ----------
        basin_indices : NDArray
            The list of basin indices to sum and write
        directory : str | Path
            The directory to write the files in. If None, the active directory
            is used.
        write_reference : bool, optional
            Whether or not to write the reference data rather than the charge data.
            Default is False.
        output_format : str | Format, optional
            The format to write with. If None, writes to source format stored in
            the Grid objects metadata.
            Defaults to None.

        Returns
        -------
        None.

        """
        # get the data to use
        if write_reference:
            data_array = self.reference_grid.total
            data_type = self.reference_grid.data_type
        else:
            data_array = self.charge_grid.total
            data_type = self.charge_grid.data_type

        if directory is None:
            directory = Path(".")
        # create a mask including each of the requested basins
        mask = np.isin(self.basin_labels, basin_indices)
        # copy data to avoid overwriting. Set data off of basin to 0
        data_array_copy = data_array.copy()
        data_array_copy[~mask] = 0.0
        grid = Grid(
            structure=self.structure,
            data={"total": data_array_copy},
            data_type=data_type,
        )
        file_path = directory / f"{grid.data_type.prefix}_bsum"
        # write file
        grid.write(filename=file_path, output_format=output_format, **writer_kwargs)

    def write_atom_volumes(
        self,
        atom_indices: NDArray,
        directory: str | Path = None,
        write_reference: bool = False,
        output_format: str | Format = None,
        **writer_kwargs,
    ):
        """
        Writes atomic basins to vasp-like files. Points belonging to the atom
        will have values from the charge or reference grid, and all other points
        will be 0.

        Parameters
        ----------
        atom_indices : NDArray
            The list of atom indices to write
        directory : str | Path
            The directory to write the files in. If None, the active directory
            is used.
        write_reference : bool, optional
            Whether or not to write the reference data rather than the charge data.
            Default is False.
        output_format : str | Format, optional
            The format to write with. If None, writes to source format stored in
            the Grid objects metadata.
            Defaults to None.

        Returns
        -------
        None.

        """
        # get the data to use
        if write_reference:
            data_array = self.reference_grid.total
            data_type = self.reference_grid.data_type
        else:
            data_array = self.charge_grid.total
            data_type = self.charge_grid.data_type

        if directory is None:
            directory = Path(".")
        for atom_index in atom_indices:
            # get a mask everywhere but the requested basin
            mask = self.atom_labels != atom_index
            # copy data to avoid overwriting. Set data off of basin to 0
            data_array_copy = data_array.copy()
            data_array_copy[mask] = 0.0
            grid = Grid(
                structure=self.structure,
                data={"total": data_array_copy},
                data_type=data_type,
            )
            file_path = directory / f"{grid.data_type.prefix}_a{atom_index}"
            # write file
            grid.write(filename=file_path, output_format=output_format, **writer_kwargs)

    def write_all_atom_volumes(
        self,
        directory: str | Path = None,
        write_reference: bool = False,
        output_format: str | Format = None,
        **writer_kwargs,
    ):
        """
        Writes all atomic basins to vasp-like files. Points belonging to the atom
        will have values from the charge or reference grid, and all other points
        will be 0.

        Parameters
        ----------
        directory : str | Path
            The directory to write the files in. If None, the active directory
            is used.
        directory : str | Path
            The directory to write the files in. If None, the active directory
            is used.
        write_reference : bool, optional
            Whether or not to write the reference data rather than the charge data.
            Default is False.
        output_format : str | Format, optional
            The format to write with. If None, writes to source format stored in
            the Grid objects metadata.
            Defaults to None.

        Returns
        -------
        None.

        """
        atom_indices = np.array(range(len(self.structure)))
        self.write_atom_volumes(
            atom_indices=atom_indices,
            directory=directory,
            write_reference=write_reference,
            output_format=output_format,
            **writer_kwargs,
        )

    def write_atom_volumes_sum(
        self,
        atom_indices: NDArray,
        directory: str | Path = None,
        write_reference: bool = False,
        output_format: str | Format = None,
        **writer_kwargs,
    ):
        """
        Writes the union of the provided atom basins to vasp-like files.
        Points belonging to the atoms will have values from the charge or
        reference grid, and all other points will be 0.

        Parameters
        ----------
        atom_indices : NDArray
            The list of atom indices to sum and write
        directory : str | Path
            The directory to write the files in. If None, the active directory
            is used.
        write_reference : bool, optional
            Whether or not to write the reference data rather than the charge data.
            Default is False.
        output_format : str | Format, optional
            The format to write with. If None, writes to source format stored in
            the Grid objects metadata.
            Defaults to None.

        Returns
        -------
        None.

        """
        # get the data to use
        if write_reference:
            data_array = self.reference_grid.total
            data_type = self.reference_grid.data_type
        else:
            data_array = self.charge_grid.total
            data_type = self.charge_grid.data_type

        if directory is None:
            directory = Path(".")
        mask = np.isin(self.atom_labels, atom_indices)
        data_array_copy = data_array.copy()
        data_array_copy[~mask] = 0.0
        grid = Grid(
            structure=self.structure,
            data={"total": data_array_copy},
            data_type=data_type,
        )
        file_path = directory / f"{grid.data_type.prefix}_asum"
        # write file
        grid.write(filename=file_path, output_format=output_format, **writer_kwargs)

    def get_atom_results_dataframe(self) -> pd.DataFrame:
        """
        Collects a summary of results for the atoms in a pandas DataFrame.

        Returns
        -------
        atoms_df : pd.DataFrame
            A table summarizing the atomic basins.

        """
        # Get atom results summary
        atom_frac_coords = self.structure.frac_coords
        atoms_df = pd.DataFrame(
            {
                "label": self.structure.labels,
                "x": atom_frac_coords[:, 0],
                "y": atom_frac_coords[:, 1],
                "z": atom_frac_coords[:, 2],
                "charge": self.atom_charges,
                "volume": self.atom_volumes,
                "surface_dist": self.atom_min_surface_distances,
            }
        )
        return atoms_df

    def get_basin_results_dataframe(self):
        """
        Collects a summary of results for the basins in a pandas DataFrame.

        Returns
        -------
        basin_df : pd.DataFrame
            A table summarizing the basins.

        """
        subset = self.significant_basins
        basin_frac_coords = self.basin_maxima_frac[subset]
        basin_df = pd.DataFrame(
            {
                "atoms": np.array(self.structure.labels)[self.basin_atoms[subset]],
                "x": basin_frac_coords[:, 0],
                "y": basin_frac_coords[:, 1],
                "z": basin_frac_coords[:, 2],
                "charge": self.basin_charges[subset],
                "volume": self.basin_volumes[subset],
                "surface_dist": self.basin_min_surface_distances[subset],
                "atom_dist": self.basin_atom_dists[subset],
            }
        )
        return basin_df

    def write_results_summary(
        self,
        directory: Path | str | None = None,
    ):
        """
        Writes a summary of atom and basin results to .tsv files.

        Parameters
        ----------
        directory : str | Path
            The directory to write the files in. If None, the active directory
            is used.

        Returns
        -------
        None.

        """
        if directory is None:
            directory = Path(".")

        # Get atom results summary
        atoms_df = self.get_atom_results_dataframe()
        formatted_atoms_df = atoms_df.copy()
        numeric_cols = formatted_atoms_df.select_dtypes(include="number").columns
        formatted_atoms_df[numeric_cols] = formatted_atoms_df[numeric_cols].map(
            lambda x: f"{x:.5f}"
        )

        # Get basin results summary
        basin_df = self.get_basin_results_dataframe()
        formatted_basin_df = basin_df.copy()
        numeric_cols = formatted_basin_df.select_dtypes(include="number").columns
        formatted_basin_df[numeric_cols] = formatted_basin_df[numeric_cols].map(
            lambda x: f"{x:.5f}"
        )

        # Determine max width per column including header
        atom_col_widths = {
            col: max(len(col), formatted_atoms_df[col].map(len).max())
            for col in atoms_df.columns
        }
        basin_col_widths = {
            col: max(len(col), formatted_basin_df[col].map(len).max())
            for col in basin_df.columns
        }

        # Write to file with aligned columns using tab as separator
        for df, col_widths, name in zip(
            [formatted_atoms_df, formatted_basin_df],
            [atom_col_widths, basin_col_widths],
            ["bader_atom_summary.tsv", "bader_basin_summary.tsv"],
        ):
            # Note what we're writing in log
            if "atom" in name:
                logging.info(f"Writing Atom Summary to {name}")
            else:
                logging.info(f"Writing Basin Summary to {name}")

            # write output summaries
            with open(directory / name, "w") as f:
                # Write header
                header = "\t".join(f"{col:<{col_widths[col]}}" for col in df.columns)
                f.write(header + "\n")

                # Write rows
                for _, row in df.iterrows():
                    line = "\t".join(
                        f"{val:<{col_widths[col]}}" for col, val in row.items()
                    )
                    f.write(line + "\n")
                # write vacuum summary to atom file
                if name == "bader_atom_summary.tsv":
                    f.write("\n")
                    f.write(f"Vacuum Charge:\t\t{self.vacuum_charge:.5f}\n")
                    f.write(f"Vacuum Volume:\t\t{self.vacuum_volume:.5f}\n")
                    f.write(f"Total Electrons:\t{self.total_electron_number:.5f}\n")

# -*- coding: utf-8 -*-
"""
This file contains a series of tests for the core functionality of baderkit.
"""
from pathlib import Path

import pytest

from baderkit.core import Bader, Grid
from baderkit.core.methods import Method

TEST_FOLDER = Path(__file__).parent / "test_files"
TEST_CHGCAR = TEST_FOLDER / "CHGCAR"
TEST_CHGCAR_CUBE = TEST_FOLDER / "CHGCAR.cube"
TEST_CHGCAR_HDF5 = TEST_FOLDER / "CHGCAR.hdf5"


def test_instance_bader_from_grid():
    # try reading the grid with vasp method
    grid = Grid.from_vasp(TEST_CHGCAR, total_only=False)
    assert grid.diff is not None
    # try reading the grid with dynamic method
    grid = Grid.from_dynamic(TEST_CHGCAR, total_only=False)
    assert grid.diff is not None
    # try to make bader object
    bader = Bader(charge_grid=grid, reference_grid=grid)
    assert bader.reference_grid.diff is not None


def test_read_bader_from_file():
    # test default read ins
    # vasp
    bader = Bader.from_dynamic(TEST_CHGCAR, total_only=False)
    assert bader.charge_grid.diff is not None
    # cube
    bader = Bader.from_dynamic(TEST_CHGCAR_CUBE)
    assert bader.charge_grid.total is not None
    # hdf5
    bader = Bader.from_dynamic(TEST_CHGCAR_HDF5)
    assert bader.charge_grid.diff is not None
    # test reading in reference file
    bader = Bader.from_dynamic(
        charge_filename=TEST_CHGCAR, reference_filename=TEST_CHGCAR
    )
    assert bader.reference_grid.total is not None


def test_writing_bader(tmp_path):
    # read in bader
    bader = Bader.from_dynamic(TEST_CHGCAR, method="ongrid")
    # get results
    results = bader.results_summary
    # Try writing results
    bader.write_results_summary(directory=tmp_path)
    bader.write_atom_volumes([0], directory=tmp_path)
    bader.write_atom_volumes_sum([0], directory=tmp_path)
    bader.write_basin_volumes([0], directory=tmp_path)
    bader.write_basin_volumes_sum([0], directory=tmp_path)
    assert Path(tmp_path / "bader_atom_summary.tsv").exists()
    assert Path(tmp_path / "bader_basin_summary.tsv").exists()
    assert Path(tmp_path / "CHGCAR_a0").exists()
    assert Path(tmp_path / "CHGCAR_b0").exists()
    assert Path(tmp_path / "CHGCAR_asum").exists()
    assert Path(tmp_path / "CHGCAR_bsum").exists()


@pytest.mark.parametrize(
    "method",
    [i.value for i in Method],
)
def test_running_bader_methods(tmp_path, method):
    bader = Bader.from_dynamic(TEST_CHGCAR, method=method)
    with open(TEST_FOLDER / method / "bader_atom_summary.tsv", "r") as file:
        expected_atom_results = file.read()
    with open(TEST_FOLDER / method / "bader_basin_summary.tsv", "r") as file:
        expected_basin_results = file.read()
    # write results to temp file then compare outputs
    bader.write_results_summary(directory=tmp_path)
    # read in results and compare
    with open(tmp_path / "bader_atom_summary.tsv", "r") as file:
        atom_results = file.read()
    with open(tmp_path / "bader_basin_summary.tsv", "r") as file:
        basin_results = file.read()
    assert atom_results == expected_atom_results
    assert basin_results == expected_basin_results

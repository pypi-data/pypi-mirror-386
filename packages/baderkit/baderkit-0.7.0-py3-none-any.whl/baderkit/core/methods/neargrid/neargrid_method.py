# -*- coding: utf-8 -*-

import logging

import numpy as np

from baderkit.core.methods.base import MethodBase
from baderkit.core.methods.shared_numba import get_edges

from .neargrid_numba import (
    get_gradient_pointers_overdetermined,
    get_gradient_pointers_simple,
    refine_fast_neargrid,
)


class NeargridMethod(MethodBase):

    _use_overdetermined = False

    def _run_bader(self, labels):
        """
        Assigns voxels to basins and calculates charge using the near-grid
        method:
            W. Tang, E. Sanville, and G. Henkelman
            A grid-based Bader analysis algorithm without lattice bias
            J. Phys.: Condens. Matter 21, 084204 (2009)

        Returns
        -------
        None.

        """
        reference_grid = self.reference_grid
        reference_data = reference_grid.total
        shape = reference_grid.shape
        # get neigbhor transforms
        neighbor_transforms, neighbor_dists = reference_grid.point_neighbor_transforms
        logging.info("Calculating Gradients")
        if not self._use_overdetermined:
            # calculate gradients and pointers to best neighbors
            labels, gradients = get_gradient_pointers_simple(
                data=reference_data,
                labels=labels,
                dir2lat=self.dir2lat,
                neighbor_dists=neighbor_dists,
                neighbor_transforms=neighbor_transforms,
                vacuum_mask=self.vacuum_mask,
                maxima_mask=self.maxima_mask,
            )
        else:
            # NOTE: This is an alternatvie method using an overdetermined system
            # of all 26 neighbors to calculate the gradient. I didn't see any
            # improvement for NaCl or H2O, but both were cubic systems.
            # get cartesian transforms and normalize
            cart_transforms = reference_grid.grid_to_cart(neighbor_transforms)
            norm_cart_transforms = (
                cart_transforms.T / np.linalg.norm(cart_transforms, axis=1)
            ).T
            # get the pseudo inverse
            inv_norm_cart_trans = np.linalg.pinv(norm_cart_transforms[:13])
            # calculate gradients and pointers to best neighbors
            labels, gradients, self._maxima_mask = get_gradient_pointers_overdetermined(
                data=reference_data,
                labels=labels,
                car2lat=self.car2lat,
                inv_norm_cart_trans=inv_norm_cart_trans,
                neighbor_dists=neighbor_dists,
                neighbor_transforms=neighbor_transforms,
                vacuum_mask=self.vacuum_mask,
                maxima_mask=self.maxima_mask,
            )
        # Find roots
        # NOTE: Vacuum points are indicated by a value of -1 and we want to
        # ignore these
        logging.info("Finding Roots")
        labels = self.get_roots(labels)
        # We now have our roots. Relabel so that they go from 0 to the length of our
        # roots
        unique_roots, labels = np.unique(labels, return_inverse=True)
        # shift back to vacuum at -1
        if -1 in unique_roots:
            labels -= 1
        # reconstruct a 3D array with our labels
        labels = labels.reshape(shape)
        # get frac coords

        logging.info("Starting Edge Refinement")
        # reduce maxima/basins
        # labels, self._maxima_frac = self.reduce_label_maxima(labels)
        # shift to vacuum at 0
        labels += 1

        # Now we refine the edges with the neargrid method
        # Get our edges, not including edges on the vacuum.
        refinement_mask = get_edges(
            labeled_array=labels,
            neighbor_transforms=neighbor_transforms,
            vacuum_mask=self.vacuum_mask,
        )
        # remove maxima from refinement
        refinement_mask[self.maxima_mask] = False
        # note these labels should not be reassigned again in future cycles
        labels[refinement_mask] = -labels[refinement_mask]
        labels = refine_fast_neargrid(
            data=reference_data,
            labels=labels,
            refinement_mask=refinement_mask,
            maxima_mask=self.maxima_mask,
            gradients=gradients,
            neighbor_dists=neighbor_dists,
            neighbor_transforms=neighbor_transforms,
        )

        # switch negative labels back to positive and subtract by 1 to get to
        # correct indices
        labels = np.abs(labels) - 1
        # get all results
        results = {
            "basin_labels": labels,
        }
        # assign charges/volumes, etc.
        logging.info("Assigning Charges and Volumes")
        results.update(self.get_basin_charges_and_volumes(labels))
        return results

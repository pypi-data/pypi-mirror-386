#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 04/02/2025
Last modified on 04/02/2025

Author: Alexis Sauvageon
Email: alexis.sauvageon@gmail.com

Description: This module defines the Volume class, a subclass of Elem that represents a 3D mesh
stored in vtkUnstructuredGrid. The class is designed to generate and manipulate 3D meshes such 
as hex meshes or tetrahedral meshes. It works by interpolating between two given surfaces (s0 
and s1) and building an unstructured grid based on these interpolated points. The class supports 
advanced mesh generation techniques, including element size progression and grading for adaptive meshing.
"""

import numpy as np
import vtk as vtk
from pybmesh.geom.mesh import Elem
from pybmesh.io.vtk2numpy import mesh_to_numpy_connectivity, numpy_to_vtk_connectivity
from pybmesh.utils.vtkquery import nbPt, nbEl
from pybmesh.utils.miscutils import sort_points
from scipy.optimize import fsolve
from vtk.util.numpy_support import vtk_to_numpy


class Volume(Elem):
    """
    Volume Class
    ------------
    A 3D mesh representation stored in vtkUnstructuredGrid. This class is designed to create
    and manipulate 3D meshes, such as hex meshes or tetrahedral meshes, by interpolating between
    two given surfaces (s0 and s1) to generate the corresponding 3D mesh grid.
    """

    def __init__(self, s0=None, s1=None, n=None, size=None, grading=1, progression = 'linear', pid=0, profile=None, lexsort = [2, 1, 0]):
        """
        Initialize a Volume object using two surfaces (s0 and s1) and generate the corresponding 3D mesh.

        Parameters:
            s0, s1 (Mesh): The two surfaces to interpolate between, must be homeomorphic (same topology).
            n (int, optional): The number of interpolation layers between s0 and s1. Default is None.
            size (float, optional): Size of the elements along the mesh. Overrides `n` if provided.
            grading (float, optional): The grading factor for mesh element size progression.
            progression (str, optional): Defines the progression type, either 'linear' or 'geometric'.
            pid (int, optional): Part ID for the element, identifying its unique properties or material.
            profile (array_like of shape (L, 3), optional):
                A 3D polyline. The relative distances along this polyline are
                used as the interpolation parameters t in [0,1].
                If provided, overrides n/size/grading/progression.

        Raises:
            ValueError: If s0 and s1 are not homeomorphic.
        """
        super().__init__(pid=pid)
        self._profile = profile
        self._lexsort = lexsort
        if (s0,s1) != (None, None):
            # Check if s0 and s1 are homeomorphic
            if not self._check_homeomorphism(s0, s1):
                raise ValueError("The surfaces s0 and s1 are not homeomorphic.")
            
            # Build unstructured grid
            self._build_ugrid(s0, s1, n, size, grading, progression)

    def _check_homeomorphism(self, s0, s1):
        """
        Check if the two surfaces are homeomorphic (i.e., have the same topology).

        Parameters:
            s0, s1 (Mesh): The surfaces to check.

        Returns:
            bool: True if surfaces are homeomorphic, otherwise False.
        """
        return ((nbEl(s0) == nbEl(s1)) and (nbPt(s0) == nbPt(s1)))


    def _update_cell_connectivity(self, cells, sorted_indices):
        """
        Update cell connectivity based on sorted point indices.

        Parameters:
            cells (list): List of cells with original point indices.
            sorted_indices (list): List of sorted point indices.

        Returns:
            list: Updated list of cells with re-mapped point indices.
        """
        index_map = {original_idx: sorted_idx for sorted_idx, original_idx in enumerate(sorted_indices)}
        
        updated_cells = []
        for cell in cells:
            updated_cells.append([index_map[idx] for idx in cell])
        
        return updated_cells

    def _interpolate_points(self, pts0, pts1, n, grading=1.0, progression='linear', t=None):
        """
        Interpolate layers between pts0 and pts1.
    
        Two modes:
          1) Parameter-driven (new): pass explicit t in [0,1], shape (L,)
          2) Legacy: build t from n/grading/progression
    
        Returns
        -------
        ndarray, shape (L, M, 3)  where L = len(t) or n+1
        """
        # --- validation ---
        pts0 = np.asarray(pts0, dtype=float)
        pts1 = np.asarray(pts1, dtype=float)
        if pts0.shape[-1] != 3 or pts1.shape[-1] != 3:
            raise ValueError("pts0 and pts1 must have last dimension 3 (x,y,z).")
    
        pts0 = np.atleast_2d(pts0)
        pts1 = np.atleast_2d(pts1)
    
        # --- build or validate t ---
        if t is not None:
            t = np.asarray(t, dtype=float).ravel()
            if t.size < 2:
                raise ValueError("t must have at least two values (start and end).")
            if (t.min() < -1e-12) or (t.max() > 1 + 1e-12):
                raise ValueError("t must lie within [0,1].")
            # clamp extremes and ensure strictly [0,1]
            t[0], t[-1] = 0.0, 1.0
        else:
            if n is None:
                raise ValueError("Either provide t or provide n (and optional grading/progression).")
            if n < 1:
                raise ValueError("n must be >= 1")
            if grading <= 0:
                raise ValueError("grading must be > 0")
    
            eps = 1e-12
            if abs(grading - 1.0) < eps or n == 1:
                t = np.linspace(0.0, 1.0, n + 1)
            elif progression == 'geometric':
                q = grading ** (1.0 / (n - 1))
                if abs(q - 1.0) < 1e-12:
                    t = np.linspace(0.0, 1.0, n + 1)
                else:
                    i = np.arange(n + 1, dtype=float)
                    denom = (q ** n) - 1.0
                    t = (q ** i - 1.0) / denom
            elif progression == 'linear':
                r = (grading - 1.0) / (n - 1)
                k = np.arange(n + 1, dtype=float)
                num = k * (2.0 + (k - 1.0) * r)
                den = n * (2.0 + (n - 1.0) * r)
                t = num / den
            else:
                raise ValueError("progression must be 'linear' or 'geometric'")
            t[0], t[-1] = 0.0, 1.0
    
        # --- interpolate layers (L, M, 3) ---
        interp = (1.0 - t)[:, None, None] * pts0[None, ...] + t[:, None, None] * pts1[None, ...]
        if interp.ndim != 3 or interp.shape[-1] != 3:
            interp = np.reshape(interp, (t.size, -1, 3))
        return interp


    def _t_from_profile(self, profile_pts, *, ensure_endpoints=True):
        """
        Convert a 3D polyline to normalized parameters t in [0,1] based on
        cumulative arc-length.
    
        Parameters
        ----------
        profile_pts : array_like, shape (L, 3)
        ensure_endpoints : bool
            If True, guarantees t starts at 0 and ends at 1 (adds endpoints if missing).
    
        Returns
        -------
        t : ndarray, shape (L' ,)
            Monotone non-decreasing values in [0,1]. Duplicate (within eps) values are removed.
        """
        arr = np.asarray(profile_pts, dtype=float)
        if arr.ndim != 2 or arr.shape[1] != 3:
            raise ValueError("profile must have shape (L, 3).")
        if arr.shape[0] < 2:
            raise ValueError("profile must contain at least 2 points (start & end).")
    
        seg = np.linalg.norm(np.diff(arr, axis=0), axis=1)
        total = float(seg.sum())
        if not np.isfinite(total) or total <= 0.0:
            raise ValueError("profile polyline must have positive total length.")
    
        cum = np.concatenate(([0.0], np.cumsum(seg)))
        t = cum / total
    
        # Optionally force exact endpoints
        if ensure_endpoints:
            if t[0] > 1e-15:
                t = np.concatenate(([0.0], t))
            if t[-1] < 1.0 - 1e-15:
                t = np.concatenate((t, [1.0]))
    
        # Remove numerically duplicate parameters
        eps = 1e-12
        keep = np.ones_like(t, dtype=bool)
        keep[1:] = np.diff(t) > eps
        t = t[keep]
        t[0], t[-1] = 0.0, 1.0
        return t

    def reverse_orientation(self, *, inplace=True):
        """
        Flip orientation of *all* cells by applying an odd permutation per VTK type.
    
        Notes
        -----
        - Works for VTK TETRA, HEXAHEDRON, WEDGE (prism), PYRAMID.
        - Also flips TRI/QUAD (useful if surface cells are present).
        - Handedness is inverted for every cell unconditionally.
        """
    
        # --- grab arrays ---
        pts, cells, ctypes = mesh_to_numpy_connectivity(self)
        if ctypes is None or len(ctypes) != len(cells):
            ctypes = [None] * len(cells)
    
        pts = np.asarray(pts, dtype=float)
    
        # Odd permutations that invert orientation (consistent with VTK node orderings)
        PERM = {
            vtk.VTK_TETRA:       np.array([0, 2, 1, 3], dtype=int),              # swap 1<->2
            vtk.VTK_HEXAHEDRON:  np.array([0, 3, 2, 1, 4, 7, 6, 5], dtype=int),  # reverse each quad ring
            vtk.VTK_WEDGE:       np.array([0, 2, 1, 3, 5, 4], dtype=int),        # swap last two of each tri
            vtk.VTK_PYRAMID:     np.array([0, 3, 2, 1, 4], dtype=int),           # reverse base quad
            # 2D (surfaces)
            'TRI':               np.array([0, 2, 1], dtype=int),
            'QUAD':              np.array([0, 3, 2, 1], dtype=int),
        }
    
        def _guess_key(cell):
            n = len(cell)
            if n == 3:  return 'TRI'
            if n == 4:  return 'QUAD'
            if n == 5:  return vtk.VTK_PYRAMID
            if n == 6:  return vtk.VTK_WEDGE
            if n == 8:  return vtk.VTK_HEXAHEDRON
            return None
    
        new_cells = []
        for cell, ct in zip(cells, ctypes):
            perm_key = ct if ct in PERM else _guess_key(cell)
            perm = PERM.get(perm_key, None)
    
            c_arr = np.asarray(cell, dtype=int)
            if perm is None or len(perm) != len(c_arr):
                # Unknown: last-resort odd swap if possible
                if len(c_arr) >= 3:
                    c_arr = c_arr.copy()
                    c_arr[1], c_arr[2] = c_arr[2], c_arr[1]
                new_cells.append(c_arr)
            else:
                new_cells.append(c_arr[perm])
    
        ugrid = numpy_to_vtk_connectivity(pts, [c.tolist() for c in new_cells], ctypes)
        if inplace:
            self._set_vtk_unstructured_grid(ugrid)
            self._generate_pid_field()
            return self
        else:
            out = self.copy()
            out._set_vtk_unstructured_grid(ugrid)
            out._generate_pid_field()
            return out
    
    def correct_orientation(self, *, quality_threshold=1000.0, inplace=True):
        """
        Flip only the cells whose vtkMeshQuality 'Quality' value exceeds the threshold.
    
        Parameters
        ----------
        quality_threshold : float, default=1000.0
            Cells with Quality > threshold are flipped once using an odd permutation
            consistent with VTK node ordering for that cell type.
        inplace : bool, default=True
            If True, modify this mesh; otherwise return a corrected copy.
        """
        # --- get connectivity ---
        pts, cells, ctypes = mesh_to_numpy_connectivity(self)
        if ctypes is None or len(ctypes) != len(cells):
            ctypes = [None] * len(cells)
        pts = np.asarray(pts, dtype=float)
    
        # Odd permutations that invert handedness (VTK-consistent)
        PERM = {
            vtk.VTK_TETRA:       np.array([0, 2, 1, 3], dtype=int),
            vtk.VTK_HEXAHEDRON:  np.array([0, 3, 2, 1, 4, 7, 6, 5], dtype=int),
            vtk.VTK_WEDGE:       np.array([0, 2, 1, 3, 5, 4], dtype=int),
            vtk.VTK_PYRAMID:     np.array([0, 3, 2, 1, 4], dtype=int),
            'TRI':               np.array([0, 2, 1], dtype=int),
            'QUAD':              np.array([0, 3, 2, 1], dtype=int),
        }
    
        def _guess_key(cell):
            n = len(cell)
            if n == 3:  return 'TRI'
            if n == 4:  return 'QUAD'
            if n == 5:  return vtk.VTK_PYRAMID
            if n == 6:  return vtk.VTK_WEDGE
            if n == 8:  return vtk.VTK_HEXAHEDRON
            return None
    
        # build current mesh
        ugrid = numpy_to_vtk_connectivity(pts, [np.asarray(c, int).tolist() for c in cells], ctypes)
    
        # --- run vtkMeshQuality with the measures matching your UI screenshot ---
        mq = vtk.vtkMeshQuality()
        mq.SetInputData(ugrid)
        mq.SetTriangleQualityMeasureToRadiusRatio()
        mq.SetQuadQualityMeasureToEdgeRatio()
        mq.SetTetQualityMeasureToRadiusRatio()
        mq.SetPyramidQualityMeasureToShape()
        mq.SetWedgeQualityMeasureToEdgeRatio()
        mq.SetHexQualityMeasureToMaxAspectFrobenius()
        mq.Update()
    
        q_arr = mq.GetOutput().GetCellData().GetArray("Quality")
        qual = vtk_to_numpy(q_arr) if q_arr is not None else None
    
        # nothing to do?
        if qual is None or not np.isfinite(qual).any():
            if inplace:
                return self
            out = self.copy()
            return out
    
        # flip only the "bad" ones
        new_cells = []
        for i, (cell, ct) in enumerate(zip(cells, ctypes)):
            c_arr = np.asarray(cell, dtype=int)
            if np.isfinite(qual[i]) and qual[i] > quality_threshold:
                key = ct if ct in PERM else _guess_key(c_arr)
                perm = PERM.get(key, None)
                if perm is not None and len(perm) == len(c_arr):
                    new_cells.append(c_arr[perm])
                    continue
            new_cells.append(c_arr)
    
        # write back
        ugrid_final = numpy_to_vtk_connectivity(pts, [c.tolist() for c in new_cells], ctypes)
        if inplace:
            self._set_vtk_unstructured_grid(ugrid_final)
            self._generate_pid_field()
            return self
        else:
            out = self.copy()
            out._set_vtk_unstructured_grid(ugrid_final)
            out._generate_pid_field()
            return out





    # def reverse_orientation(self, *, ensure_positive=False, inplace=True):
    #     """
    #     Fix cell orientations by reordering node indices.
    
    #     Parameters
    #     ----------
    #     ensure_positive : bool
    #         If True (default), only reorders cells whose signed volume is negative.
    #         If False, flips *all* cells unconditionally.
    #     inplace : bool
    #         If True (default) modify this mesh. If False, return a copy.
    
    #     Notes
    #     -----
    #     - Works for VTK TETRA, HEXAHEDRON, WEDGE (prism), PYRAMID.
    #     - Also flips TRI/QUAD in case 2-D cells are present in the UGrid.
    #     - Uses type-aware **odd permutations** consistent with VTK ordering.
    #     """
    
    #     # --- grab arrays ---
    #     pts, cells, ctypes = mesh_to_numpy_connectivity(self)  # you already provide this
    #     if ctypes is None or len(ctypes) != len(cells):
    #         # fall back: let numpy_to_vtk_connectivity infer later, but keep a parallel
    #         # list for control-flow; None markers mean "unknown"
    #         ctypes = [None] * len(cells)
    
    #     pts = np.asarray(pts, dtype=float)
    
    #     # --------  type-aware odd permutations that flip handedness  --------
    #     # VTK node order reference permutations that invert orientation:
    #     PERM = {
    #         vtk.VTK_TETRA:       np.array([0, 2, 1, 3], dtype=int),                    # swap 1<->2
    #         vtk.VTK_HEXAHEDRON:  np.array([0, 3, 2, 1, 4, 7, 6, 5], dtype=int),        # reverse each quad ring
    #         vtk.VTK_WEDGE:       np.array([0, 2, 1, 3, 5, 4], dtype=int),              # swap last two of each tri
    #         vtk.VTK_PYRAMID:     np.array([0, 3, 2, 1, 4], dtype=int),                 # reverse base quad
    #         # 2D (just in case you carry surface cells in the UGrid)
    #         'TRI':                np.array([0, 2, 1], dtype=int),
    #         'QUAD':               np.array([0, 3, 2, 1], dtype=int),
    #     }
    
    #     # A minimal length->guess if type is missing
    #     def _guess_key(cell):
    #         n = len(cell)
    #         if n == 3:  return 'TRI'
    #         if n == 4:  return 'QUAD'  # if really a tet, ctypes will say so
    #         if n == 5:  return vtk.VTK_PYRAMID
    #         if n == 6:  return vtk.VTK_WEDGE
    #         if n == 8:  return vtk.VTK_HEXAHEDRON
    #         return None
    
    #     # --------  signed volume via consistent tet splits  --------
    #     # Positive => right-handed; Negative => inverted
    #     def _signed_tet_vol(p0, p1, p2, p3):
    #         M = np.stack([p1 - p0, p2 - p0, p3 - p0], axis=1)
    #         return np.linalg.det(M) / 6.0
    
    #     # Standard decompositions in terms of cell-local node ids
    #     TET_SPLITS = {
    #         vtk.VTK_TETRA:      [[0,1,2,3]],                                           # identity
    #         vtk.VTK_HEXAHEDRON: [[0,1,3,4], [1,2,3,6], [1,3,6,4], [4,6,7,3], [1,6,4,5]],
    #         vtk.VTK_WEDGE:      [[0,1,2,3], [3,4,5,1], [1,2,3,5]],
    #         vtk.VTK_PYRAMID:    [[0,1,3,4], [1,2,3,4]],
    #     }
    
    #     def _cell_signed_volume(cell, ctype):
    #         key = ctype if ctype in TET_SPLITS else None
    #         if key is None:
    #             # Heuristic: if we at least have 4 nodes, use the first 4 as a tet
    #             if len(cell) >= 4:
    #                 p = pts[np.asarray(cell[:4], dtype=int)]
    #                 return _signed_tet_vol(p[0], p[1], p[2], p[3])
    #             return 0.0
    #         tot = 0.0
    #         c = np.asarray(cell, dtype=int)
    #         for t in TET_SPLITS[key]:
    #             p = pts[c[t]]
    #             tot += _signed_tet_vol(p[0], p[1], p[2], p[3])
    #         return tot
    
    #     # --------  build new connectivity  --------
    #     new_cells = []
    #     _EPS = 1e-14
    #     for cell, ct in zip(cells, ctypes):
    #         # pick a permutation to flip orientation
    #         perm_key = ct if ct in PERM else _guess_key(cell)
    #         perm = PERM.get(perm_key, None)
    
    #         if perm is None or len(perm) != len(cell):
    #             # Unknown type: as a last resort, make an odd permutation by swapping 1?2 if possible.
    #             c = list(cell)
    #             if len(c) >= 3:
    #                 c[1], c[2] = c[2], c[1]
    #                 new_cells.append(np.asarray(c, dtype=int))
    #             else:
    #                 new_cells.append(np.asarray(cell, dtype=int))
    #             continue
    
    #         c_arr = np.asarray(cell, dtype=int)
    
    #         if ensure_positive:
    #             # only fix cells that are actually inverted
    #             vol = _cell_signed_volume(c_arr, ct)
    #             if vol < -_EPS:
    #                 new_cells.append(c_arr[perm])
    #             else:
    #                 new_cells.append(c_arr)
    #         else:
    #             # flip all cells unconditionally
    #             new_cells.append(c_arr[perm])
    
    #     # --------  write back  --------
    #     ugrid = numpy_to_vtk_connectivity(pts, [c.tolist() for c in new_cells], ctypes)
    #     if inplace:
    #         self._set_vtk_unstructured_grid(ugrid)
    #         self._generate_pid_field()
    #         return self
    #     else:
    #         out = self.copy()
    #         out._set_vtk_unstructured_grid(ugrid)
    #         out._generate_pid_field()
    #         return out


    def _merge_meshes(self, meshes):
        """
        Merge multiple meshes with shared connectivity using efficient NumPy operations.

        Parameters:
            meshes (list): List of meshes to merge.

        Returns:
            tuple: Merged points and updated cell connectivity.
        """
        sorted_point0 = np.vstack([mesh[0] for mesh in meshes])
        updated_cells = []
        point_offset = 0
        
        for points, cells in meshes:
            updated_cells_i = [np.array(cell) + point_offset for cell in cells]
            updated_cells.append(updated_cells_i)
            point_offset += len(points)
        
        fused_cells = []
        for i in range(len(updated_cells) - 1):
            for cell0, cell1 in zip(updated_cells[i], updated_cells[i + 1]):
                fused_cells.append(np.concatenate([cell0, cell1]))
        
        return sorted_point0, fused_cells

    def _merge_interpolated_meshes(self, pts0, pts1, updated_cells0, n=None, grading=1, progression='linear', t=None):
        """
        Merge meshes using either legacy (n/grading/progression) or explicit t.
        """
        interpolated_pts = self._interpolate_points(pts0, pts1, n, grading, progression, t=t)
        meshes = [[interp_pts, updated_cells0] for interp_pts in interpolated_pts]
        return self._merge_meshes(meshes)

    # def _merge_interpolated_meshes(self, pts0, pts1, updated_cells0, n, grading=1, progression = 'linear'):
    #     """
    #     Merge meshes with interpolated points between pts0 and pts1.

    #     Parameters:
    #         pts0, pts1 (np.ndarray): Two sets of points between which to interpolate.
    #         updated_cells0 (list): Updated cell connectivity for the first set of points.
    #         n (int): Number of interpolation layers.
    #         grading (float): Grading factor.
    #         progression (str): Progression type.

    #     Returns:
    #         tuple: Merged points and cells.
    #     """
    #     interpolated_pts = self._interpolate_points(pts0, pts1, n, grading, progression)
    #     meshes = [[interp_pts, updated_cells0] for interp_pts in interpolated_pts]
    #     return self._merge_meshes(meshes)

    def _build_ugrid(self, s0, s1, n, size,  grading, progression):
        """
        Build unstructured grid by interpolating between two surfaces (s0 and s1).

        Parameters:
            s0, s1 (Mesh): The two surfaces to interpolate between.
            n (int): The number of interpolation layers.
            size (float): Size of the mesh elements.
            grading (float): Grading factor for mesh element size progression.
            progression (str): Type of progression ('linear' or 'geometric').
        """
        # Step 3: Convert the surfaces to numpy connectivity
        pts0, cells0, _ = mesh_to_numpy_connectivity(s0)
        pts1, _, _ = mesh_to_numpy_connectivity(s1)
        
        if (n, size) == (None, None):
            n = 1
        elif size is not None :
            distances = np.linalg.norm(pts0 - pts1, axis=1)
            largest_distance = np.max(distances)
            n = int(largest_distance / size)
        
        # Step 4: Sort the points
        sorted_pts0, sorted_pts1, sorted_indices, _ = sort_points(pts0, pts1, lexsort = self._lexsort)
        
        # Step 5: Update the connectivity based on the sorted points
        updated_cells0 = self._update_cell_connectivity(cells0, sorted_indices)
        
        # Step 6: Decide spacing mode
        t = None
        if self._profile is not None:
            t = self._t_from_profile(self._profile)
        else:
            if (n, size) == (None, None):
                n = 1
            elif size is not None:
                distances = np.linalg.norm(sorted_pts0 - sorted_pts1, axis=1)
                largest_distance = float(np.max(distances))
                n = max(1, int(np.ceil(largest_distance / float(size))))
        
        # Step 7: Interpolate between surfaces and merge
        # merged_point, merged_cells = self._merge_interpolated_meshes(sorted_pts0, sorted_pts1, updated_cells0, n, grading, progression = 'linear')
        merged_point, merged_cells = self._merge_interpolated_meshes(
            sorted_pts0, sorted_pts1, updated_cells0, n=n, grading=grading, progression=progression, t=t
        )
        
        # Step 8: Convert to vtk and store in the unstructured grid
        ugrid = numpy_to_vtk_connectivity(merged_point, merged_cells)
        self._set_vtk_unstructured_grid(ugrid)
        self._generate_pid_field()
    @classmethod
    def help(cls):
        """
        Return helpful information about the Volume class and its methods.

        The help text includes usage details for the constructor, attributes, public methods,
        and the functionality of the class to create and manipulate 3D meshes.

        Returns:
            str: A multi-line string with usage instructions.
        """
        help_text = """
Volume Class
------------
A class for creating and manipulating 3D meshes such as hex meshes or tetrahedral meshes. 
The Volume class interpolates between two surfaces to generate a 3D unstructured grid.

Constructor:
-------------
\033[1;32mVolume(s0, s1, n=None, size=None, grading=1, progression='linear', pid=0)\033[0m
  - \033[1;32ms0, s1\033[0m: Two surfaces (Mesh objects) used for interpolation. Must be homeomorphic.
  - \033[1;32mn\033[0m: Number of interpolation layers. Defaults to None.
  - \033[1;32msize\033[0m: Size of the mesh elements. If provided, overrides `n`.
  - \033[1;32mgrading\033[0m: Grading factor for mesh element size progression (default: 1).
  - \033[1;32mprogression\033[0m: Type of progression ('linear' or 'geometric').
  - \033[1;32mpid\033[0m: Part ID, used to differentiate mesh entities (default: 0).

Inherited Methods:
------------------
\033[1;34mtranslate(dx, dy, dz)\033[0m
    Translate all points in the line by the vector (dx, dy, dz).
\033[1;34mrotate(center, pA, pB, axis, angle, angles, points)\033[0m
    \033[1;34mrotate(center=(0, 0, 0), axis=(0, 0, 1), angle=45)\033[0m
    Rotate all points around the specified axis ('x', 'y', or 'z') by a given angle in degrees.
    \033[1;34mrotate(center, angles=(30, 45, 60))\033[0m
    Rotate all points by specified angles around the X, Y, and Z axes, respectively.
    \033[1;34mrotate(pA=(1, 1, 1), pB=(2, 2, 2), angle=90)\033[0m
    Rotate all points around an axis defined by two points (pA and pB), by a given angle in degrees.
    
    \033[1;34mcenter\033[0m default to (0, 0, 0)
    Point class or tuple may be used for \033[1;34mcenter\033[0m, \033[1;34mpA\033[0m, \033[1;34mpB\033[0m
\033[1;34mscale(center, sx, sy, sz)\033[0m
    Scale all points by factors (sx, sy, sz) about the center (default to center of mass).
\033[1;34mget_vtk_unstructured_grid()\033[0m
    Retrieve the underlying vtkUnstructuredGrid.
\033[1;34mreverse_orientation()\033[0m
    Reverse the orientation.
\033[1;34mmerge_duplicate_nodes(verbose=False, tol=1e-5)\033[0m
    Merge duplicate nodes in the line within a specified tolerance (default: 1e-5).
\033[1;34mpid\033[0m
    Accessor and setter for the part ID (pid). The pid uniquely identifies the element
    as a mesh entity with its own characteristics (e.g., material, function).
"""
        return help_text

"""
spatiopath.engine
=================

Batch-capable SpatioPath engine with:
 - add_patch(...) to add any number of patches (single or many)
 - compute_pooling() to aggregate into a global pooled result
 - SpatioPathResult class that encapsulates KTable, IndecesTable, LevelSetsTable, etc.
 - SpatioPathResult.plot_k0(...) for single or pooled K0 plotting
 - SpatioPathResult.save(...) / SpatioPathResult.load(...) helpers for persistence

Logger: module-level logger (`spatiopath`) is used but NOT configured here.
Callers should configure handlers/formatters in __main__ or top-level app.
"""


import os
import json
import pickle
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Polygon
from scipy.ndimage import distance_transform_edt
import cv2

# Local helpers (your cleaned helpers.py)
from .helpers import (
    getZoneMapAndDistFromDistanceMap,
    computeOmegaAndLevelSetAreas,
    generateLevelSetTable,
    computeKTable,
    getIndeciesAndCellsTable,
    getAnalysis,
)

# Module-level logger — DO NOT configure handlers/formatters here.
# Users (or __main__) should configure logging globally, e.g.:
# logging.basicConfig(level=logging.INFO, format="...") or add handlers.
logger = logging.getLogger("spatiopath")


class SpatioPathResult:
    """
    Encapsulates a single analysis result (patch-level or pooled/global).

    Attributes
    ----------
    name : str
        Identifier (patch name or "GLOBAL").
    analysis : pd.DataFrame
        Single-row DataFrame returned by getAnalysis containing summary stats.
    KTable, IndecesTable, LevelSetsTable, CellsTable : pd.DataFrame
        Tables produced by the pipeline.
    omega : float
        Total available area used in K computations.
    total_points : int
        Number of points used in the analysis.
    zoneMap, distMap : np.ndarray or None
        Optional arrays (may be large) — not saved by default unless pickled.
    """

    def __init__(
        self,
        name: str,
        analysis: pd.DataFrame,
        KTable: pd.DataFrame,
        IndecesTable: pd.DataFrame,
        LevelSetsTable: pd.DataFrame,
        CellsTable: pd.DataFrame,
        omega: float,
        total_points: int,
        zoneMap: Optional[np.ndarray] = None,
        distMap: Optional[np.ndarray] = None,
    ):
        self.name = name
        self.analysis = analysis
        self.KTable = KTable
        self.IndecesTable = IndecesTable
        self.LevelSetsTable = LevelSetsTable
        self.CellsTable = CellsTable
        self.omega = float(omega)
        self.total_points = int(total_points)
        self.zoneMap = zoneMap
        self.distMap = distMap

    # -------------------------
    # Plot helpers
    # -------------------------
    def plot_k0(self, ax: Optional[plt.Axes] = None, colors: Optional[List] = None, title: Optional[str] = None) -> plt.Axes:
        """
        Plot K0 barplot for this SpatioPathResult.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axis to draw on. If None, a new figure/axis is created.
        colors : list-like, optional
            Palette to use (3 colors recommended).
        title : str, optional
            Title for the plot. Defaults to "<name> K0 values".

        Returns
        -------
        matplotlib.axes.Axes
            Axis containing the plot.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 5))

        sns.set_theme(style="ticks")
        KTable = self.KTable.copy()
        threshold = float(self.IndecesTable["Threshold"].iloc[0])

        KTable["hue"] = 0
        KTable.loc[KTable["K0"] >= threshold, "hue"] = 1
        KTable.loc[KTable["K0"] <= -threshold, "hue"] = 2
        KTable["hue"] = KTable["hue"].astype(int)

        if colors is None:
            pal = sns.color_palette("Paired")
            colors = [pal[3], pal[0], pal[5]]

        uniq = np.unique(KTable["hue"])
        plot_colors = [colors[i] for i in uniq]

        # seaborn barplot does not support mapping numeric hue arrays directly to palettes reliably,
        # so we create a categorical column with string labels for plotting.
        KTable["_hue_cat"] = KTable["hue"].astype(str)

        sns.barplot(x=KTable.index.astype(str), y="K0", data=KTable, ax=ax, palette=plot_colors, hue="_hue_cat", dodge=False)
        ax.axhline(y=threshold, color="r", linestyle="--")
        ax.axhline(y=-threshold, color="r", linestyle="--")

        # vertical marker for last above-threshold bar (if any)
        mask = (KTable["K0"] > threshold).values
        if mask.any():
            # find last index where mask True
            idxs = np.where(mask)[0]
            last_idx = idxs[-1]
            ax.axvline(x=last_idx + 0.5, color="black", linestyle="--")

        legend_labels = ["ACI", "SAI", "ASI", r"$\delta$"]
        legend_values = [
            self.IndecesTable["ACI"].iloc[0],
            self.IndecesTable["SAI"].iloc[0],
            self.IndecesTable["MODIFIED_ASI"].iloc[0],
            self.IndecesTable["meanCouplingDistance"].iloc[0],
        ]
        legend_text = [f"{l}: {v:.3f}" for l, v in zip(legend_labels, legend_values)]
        ax.legend(legend_text, fontsize=12, handlelength=0, handletextpad=0, fancybox=True, labelcolor="black")
        ax.set_title(title or f"{self.name} — K₀ values")
        ax.set_xlabel("Zone")
        ax.set_ylabel("K₀")
        return ax

    # -------------------------
    # Persistence
    # -------------------------
    def save(self, path: str, format: str = "dir", include_arrays: bool = False) -> None:
        """
        Save the SpatioPathResult to disk.

        Parameters
        ----------
        path : str
            Directory path (if format='dir') or file path (if format='pickle').
        format : {'dir', 'pickle'}
            'dir' -> create folder `path` and write CSVs + JSON summary.
            'pickle' -> pickle the whole SpatioPathResult (includes arrays).
        include_arrays : bool
            If True and format=='dir', save zoneMap/distMap as numpy .npz inside folder.
            For 'pickle', arrays are always included.
        """
        if format not in ("dir", "pickle"):
            raise ValueError("format must be 'dir' or 'pickle'")

        if format == "pickle":
            with open(path, "wb") as f:
                pickle.dump(self, f)
            logger.info(f"SpatioPathResult pickled to {path}")
            return

        # format == "dir"
        os.makedirs(path, exist_ok=True)
        # save tables as CSV
        self.analysis.to_csv(os.path.join(path, "analysis.csv"), index=False)
        self.KTable.to_csv(os.path.join(path, "KTable.csv"))
        self.IndecesTable.to_csv(os.path.join(path, "IndecesTable.csv"))
        self.LevelSetsTable.to_csv(os.path.join(path, "LevelSetsTable.csv"))
        self.CellsTable.to_csv(os.path.join(path, "CellsTable.csv"))

        meta = {
            "name": self.name,
            "omega": float(self.omega),
            "total_points": int(self.total_points),
        }
        with open(os.path.join(path, "meta.json"), "w") as f:
            json.dump(meta, f)

        if include_arrays and (self.zoneMap is not None or self.distMap is not None):
            np.savez(os.path.join(path, "arrays.npz"), zoneMap=self.zoneMap, distMap=self.distMap)

        logger.info(f"SpatioPathResult saved to folder {path}")

    @staticmethod
    def load(path: str) -> "SpatioPathResult":
        """
        Load a SpatioPathResult saved with format='dir' (folder) or a pickled SpatioPathResult.

        If path is a .pkl/.pickle file, it loads the pickled SpatioPathResult; otherwise
        it expects a folder with analysis.csv and tables.
        """
        if path.endswith(".pkl") or path.endswith(".pickle"):
            with open(path, "rb") as f:
                obj = pickle.load(f)
            if not isinstance(obj, SpatioPathResult):
                raise TypeError("Pickle did not contain a spatiopath.SpatioPathResult")
            return obj

        # assume directory
        analysis = pd.read_csv(os.path.join(path, "analysis.csv"))
        KTable = pd.read_csv(os.path.join(path, "KTable.csv"), index_col=0)
        IndecesTable = pd.read_csv(os.path.join(path, "IndecesTable.csv"), index_col=0)
        LevelSetsTable = pd.read_csv(os.path.join(path, "LevelSetsTable.csv"), index_col=0)
        CellsTable = pd.read_csv(os.path.join(path, "CellsTable.csv"), index_col=0)
        meta_path = os.path.join(path, "meta.json")
        meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
        arrays_path = os.path.join(path, "arrays.npz")
        arrays = np.load(arrays_path) if os.path.exists(arrays_path) else {}
        zoneMap = arrays.get("zoneMap", None)
        distMap = arrays.get("distMap", None)

        return SpatioPathResult(
            name=meta.get("name", os.path.basename(path)),
            analysis=analysis,
            KTable=KTable,
            IndecesTable=IndecesTable,
            LevelSetsTable=LevelSetsTable,
            CellsTable=CellsTable,
            omega=meta.get("omega", np.nan),
            total_points=meta.get("total_points", 0),
            zoneMap=zoneMap,
            distMap=distMap,
        )


class SpatioPath:
    """
    Stateful, patch-accumulating SpatioPath engine.

    Use-case:
      - Create one engine per patient / slide / experiment.
      - Call add_patch(...) repeatedly (single patch or many).
      - When ready, call compute_pooling() to get a pooled SpatioPathResult object.

    The engine never configures logging handlers — configure logging from __main__.
    """

    def __init__(
        self,
        zone_width: float = 10.0,
        analysis_zone: float = 400.0,
        pixel_size: float = 1.0,
        height: int = 4096,
        width: int = 4096,
    ):
        self.zone_width = float(zone_width)
        self.analysis_zone = float(analysis_zone)
        self.pixel_size = float(pixel_size)
        self.height = int(height)
        self.width = int(width)

        # internal list of SpatioPathResult-like dicts (not fully serialized SpatioPathResult objects yet)
        self._patch_store: List[Dict[str, Any]] = []
        logger.debug(
            f"SpatioPath engine created (zone_width={self.zone_width}, analysis_zone={self.analysis_zone}, pixel_size={self.pixel_size})"
        )

    # -------------------------
    # Add patch
    # -------------------------
    def add_patch(self, name: str, setA, setB, roi: Optional[Polygon] = None) -> SpatioPathResult:
        """
        Analyze one patch and keep its data in memory.

        Parameters
        ----------
        name : str
            Patch identifier.
        setA : list of polygons (xi, yi)
            Polygons describing region A.
        setB : array-like Nx2 of points
            Points for region B.
        roi : shapely.geometry.Polygon, optional
            Region-of-interest polygon. Defaults to full image.

        Returns
        -------
        SpatioPathResult
            A SpatioPathResult instance for this patch (also stored internally).
        """
        logger.info(f"add_patch: {name}")
        if roi is None:
            roi = Polygon([(0, 0), (self.width, 0), (self.width, self.height), (0, self.height)])

        # create maskA
        maskA = np.zeros((self.height, self.width), dtype=np.uint8)
        for polygon in setA:
            xi, yi = polygon
            pts = np.array([np.column_stack((xi, yi)).astype(np.int32)])
            cv2.fillPoly(maskA, pts, color=1)

        # distance map (signed)
        distance = distance_transform_edt(1 - maskA)
        distance[distance == 0] = -distance_transform_edt(maskA)[distance == 0]
        distanceMap = distance * self.pixel_size

        # roi mask
        maskWindowRoi = np.zeros((self.height, self.width), dtype=np.uint8)
        coords = np.column_stack((roi.exterior.xy[0], roi.exterior.xy[1])).astype(np.int32)
        cv2.fillPoly(maskWindowRoi, [coords], color=1)

        numberOfLevelsets = int(np.ceil(self.analysis_zone / self.zone_width))
        points = np.asarray(setB)

        zoneMap, distMap = getZoneMapAndDistFromDistanceMap(points, distanceMap, self.zone_width, numberOfLevelsets)
        omega, levelSetsAreas = computeOmegaAndLevelSetAreas(maskA, maskWindowRoi, distanceMap, self.zone_width, numberOfLevelsets, self.pixel_size)
        LevelSetsTable = generateLevelSetTable(zoneMap, levelSetsAreas)
        KTable = computeKTable(LevelSetsTable, omega, len(points))
        IndecesTable, CellsTable, tmpTable = getIndeciesAndCellsTable(KTable, LevelSetsTable, zoneMap, distMap, omega, len(points))
        analysis_df = getAnalysis(name, IndecesTable, KTable, LevelSetsTable, CellsTable, tmpTable, omega, len(points), self.pixel_size, self.zone_width, numberOfLevelsets)

        result = SpatioPathResult(
            name=name,
            analysis=analysis_df,
            KTable=KTable,
            IndecesTable=IndecesTable,
            LevelSetsTable=LevelSetsTable,
            CellsTable=CellsTable,
            omega=omega,
            total_points=len(points),
            zoneMap=zoneMap,
            distMap=distMap,
        )

        # store minimal info (SpatioPathResult object is fine)
        self._patch_store.append(result)
        logger.debug(f"Patch '{name}' added (points={len(points)}, omega={omega:.2f})")
        return result

    # -------------------------
    # Pooling
    # -------------------------
    def compute_pooling(self) -> Optional[SpatioPathResult]:
        """
        Pool all accumulated patches into a single global SpatioPathResult.

        Returns
        -------
        SpatioPathResult
            Pooled/global result, or None if no patches present.
        """
        if not self._patch_store:
            logger.warning("compute_pooling called but no patches have been added.")
            return None

        logger.info(f"Computing pooling for {len(self._patch_store)} patches...")
        # collect tables
        LevelSetsTables = [r.LevelSetsTable for r in self._patch_store]
        omega_total = sum(r.omega for r in self._patch_store)
        total_points = sum(r.total_points for r in self._patch_store)

        # concat and reduce level sets by Zone
        LevelSetsTables_concat = pd.concat(LevelSetsTables, axis=0)
        LevelSetsTables_grouped = LevelSetsTables_concat.groupby("Zone").sum()

        numberOfLevelsets = int(np.ceil(self.analysis_zone / self.zone_width))
        KTable = computeKTable(LevelSetsTables_grouped, omega_total, total_points)
        IndecesTable, CellsTable, tmpTable = getIndeciesAndCellsTable(KTable, LevelSetsTables_grouped, None, None, omega_total, total_points)
        analysis_df = getAnalysis("GLOBAL", IndecesTable, KTable, LevelSetsTables_grouped, CellsTable, tmpTable, omega_total, total_points, -1, self.zone_width, numberOfLevelsets)

        pooled_result = SpatioPathResult(
            name="GLOBAL",
            analysis=analysis_df,
            KTable=KTable,
            IndecesTable=IndecesTable,
            LevelSetsTable=LevelSetsTables_grouped,
            CellsTable=CellsTable,
            omega=omega_total,
            total_points=total_points,
            zoneMap=None,
            distMap=None,
        )

        logger.info("Pooling finished.")
        return pooled_result

    # -------------------------
    # Utilities
    # -------------------------
    def list_patches(self) -> List[str]:
        """Return list of patch names added so far."""
        return [r.name for r in self._patch_store]

    def reset(self) -> None:
        """Remove all stored patches."""
        self._patch_store.clear()
        logger.info("Engine reset; all patches removed.")

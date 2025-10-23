"""
spatiopath.helpers
==================

Helper functions for the SpatioPath toolkit.

This module implements the mathematical and statistical steps required
for spatial interaction analysis, including distance-based zone mapping,
level-set area computation, and the derivation of various spatial indices
(ACI, SAI, ASI, etc.).
"""

import itertools
import os
import numpy as np
import pandas as pd
from math import sqrt, log, pi
from typing import Tuple


def getZoneMapAndDistFromDistanceMap(
    points: np.ndarray,
    distanceMap: np.ndarray,
    zoneWidth: float,
    numberOfLevelsets: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute zone indices and distances for each point in `points`
    based on the distance map.

    Parameters
    ----------
    points : np.ndarray
        Array of shape (N, 2) with (x, y) coordinates.
    distanceMap : np.ndarray
        Distance map of the scene.
    zoneWidth : float
        Width of each distance zone.
    numberOfLevelsets : int
        Total number of level sets to analyze.

    Returns
    -------
    zoneMap : np.ndarray
        Zone index (-1 if outside the valid range) for each point.
    distMap : np.ndarray
        Distance values at each point location.
    """
    if len(points) == 0:
        return np.full((0, 1), -1), np.zeros((0, 1))

    distMap = distanceMap[points[:, 1].astype(int), points[:, 0].astype(int)]
    zoneMap = distMap // zoneWidth
    zoneMap[(zoneMap >= numberOfLevelsets) | (zoneMap < 0)] = -1
    return zoneMap, distMap


def computeOmegaAndLevelSetAreas(
    maskA: np.ndarray,
    windowMask: np.ndarray,
    distanceMap: np.ndarray,
    zoneWidth: float,
    numberOfLevelsets: int,
    pixelSize: float
) -> Tuple[float, np.ndarray]:
    """
    Compute total omega (background area) and area of each level set.

    Parameters
    ----------
    maskA : np.ndarray
        Binary mask of the reference region (e.g., tumor).
    windowMask : np.ndarray
        Binary mask of the ROI window.
    distanceMap : np.ndarray
        Distance map from the region A boundary.
    zoneWidth : float
        Width of each analysis ring.
    numberOfLevelsets : int
        Number of zones (rings) to compute.
    pixelSize : float
        Pixel size (microns per pixel).

    Returns
    -------
    omega : float
        Total available area (in µm²) outside region A but within ROI.
    levelSetAreas : np.ndarray
        Array of zone areas (in µm²).
    """
    levelSetAreas = np.zeros((numberOfLevelsets,))
    for i in range(numberOfLevelsets):
        levelSetAreas[i] = np.sum(
            (distanceMap <= zoneWidth * i) != (distanceMap < zoneWidth * (i + 1))
        )

    omega = (windowMask - maskA).sum() * pixelSize**2
    levelSetAreas = levelSetAreas * pixelSize**2

    return omega, levelSetAreas


def generateLevelSetTable(
    zoneMap: np.ndarray,
    levelSetAreas: np.ndarray
) -> pd.DataFrame:
    """
    Create a DataFrame summarizing point counts and area per level set.

    Parameters
    ----------
    zoneMap : np.ndarray
        Zone index for each point.
    levelSetAreas : np.ndarray
        Area of each zone (µm²).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ["NumberOfPoints", "Area"] indexed by zone.
    """
    numberOfPoints = np.array(
        [np.sum(zoneMap == i) for i in range(len(levelSetAreas))]
    )

    df = pd.DataFrame({
        "NumberOfPoints": numberOfPoints,
        "Area": levelSetAreas
    })
    df.index.name = "Zone"
    return df


def computeKTable(
    levelSetsTable: pd.DataFrame,
    omega: float,
    numberOfPointsTotal: int
) -> pd.DataFrame:
    """
    Compute K-function statistics for each level set.

    Parameters
    ----------
    levelSetsTable : pd.DataFrame
        Table with "NumberOfPoints" and "Area" columns.
    omega : float
        Total analyzed area (µm²).
    numberOfPointsTotal : int
        Total number of points in set B.

    Returns
    -------
    pd.DataFrame
        Table with columns ["K0", "K", "MU", "SIG"].
    """
    KTable = np.zeros((len(levelSetsTable), 4))
    KTable[:, 2] = levelSetsTable["Area"]  # MU
    KTable[:, 3] = np.sqrt(
        levelSetsTable["Area"] * (omega - levelSetsTable["Area"]) / numberOfPointsTotal
    )  # SIG
    KTable[:, 1] = levelSetsTable["NumberOfPoints"] * omega / numberOfPointsTotal  # K

    non_zero_indices = np.where(KTable[:, 3] != 0)
    KTable[non_zero_indices, 0] = (
        (KTable[non_zero_indices, 1] - KTable[non_zero_indices, 2])
        / KTable[non_zero_indices, 3]
    )

    df = pd.DataFrame(KTable, columns=["K0", "K", "MU", "SIG"])
    df.index.name = "Zone"
    return df


def getIndeciesAndCellsTable(
    KTable: pd.DataFrame,
    levelSetsTable: pd.DataFrame,
    zoneMap: np.ndarray,
    distMap: np.ndarray,
    omega: float,
    numberOfPointsTotal: int
):
    """
    Compute spatial interaction indices (ACI, SAI, ASI, etc.) and related tables.

    Returns
    -------
    IndecesTable : pd.DataFrame
        Global metrics (ACI, SAI, ASI, etc.)
    CellsTable : pd.DataFrame
        Per-cell data (distance, zone, probability).
    tmpTable : pd.DataFrame
        Intermediate per-level set statistics.
    """
    Threshold = sqrt(2 * log(len(KTable)))

    prob_levelset = (KTable["K0"] > Threshold) * (
        (KTable["K"] - KTable["MU"]) / KTable["K"]
    )

    numberOfPositiveProb = (prob_levelset > 0) * levelSetsTable["NumberOfPoints"]
    totalSigCouples = (KTable["K0"] > Threshold) * (KTable["K"] - KTable["MU"])
    denom = prob_levelset * numberOfPositiveProb

    probMap = np.zeros((len(zoneMap),))
    if len(zoneMap) != 0:
        probMap[zoneMap != -1] = prob_levelset[zoneMap[zoneMap != -1]]

    distTimesProb = distMap * probMap
    coupelingDistancePerLevelset = np.array([-1] * len(KTable["K0"]))

    if numberOfPointsTotal != 0:
        ACI = levelSetsTable["NumberOfPoints"].sum() / numberOfPointsTotal
        SAI = numberOfPositiveProb.sum() / numberOfPointsTotal
        ASI = totalSigCouples.sum() / omega
        coupelingDistancePerLevelset = np.array(
            [distTimesProb[zoneMap == i].sum() for i in range(len(KTable["K0"]))]
        )
    else:
        ACI = SAI = ASI = -1

    p = ((levelSetsTable["Area"] * (KTable["K0"] > Threshold)).sum()) / omega
    MODIFIED_ASI = ASI / (1.0 - p) if (1.0 - p) != 0 else -1

    if denom.sum() == 0:
        meanCouplingDistance = -1
    else:
        meanCouplingDistance = coupelingDistancePerLevelset.sum() / denom.sum()

    L = len(KTable["K0"])
    Z = np.max(KTable["K0"] * (KTable["K0"] > Threshold))
    X = Z / sqrt(2)
    if X == 0:
        Y = 0
        logPValue = 0
    else:
        Y = L / (2 * sqrt(pi * X))
        logPValue = (np.log(Y) - 2**X) / np.log(10)

    IndecesTable = pd.DataFrame({
        "ACI": [ACI],
        "SAI": [SAI],
        "ASI": [ASI],
        "MODIFIED_ASI": [MODIFIED_ASI],
        "Threshold": [Threshold],
        "log p-value": [logPValue],
        "meanCouplingDistance": [meanCouplingDistance],
    })

    if len(zoneMap) != 0:
        CellsTable = pd.DataFrame({
            "Distance": distMap,
            "Zone": zoneMap,
            "Prob": probMap,
        })
    else:
        CellsTable = pd.DataFrame(columns=["Distance", "Zone", "Prob"])

    tmpTable = pd.DataFrame({
        "NumberOfPositiveProb": numberOfPositiveProb,
        "TotalSigCouples": totalSigCouples,
        "Denom": denom,
        "prob_levelset": prob_levelset,
        "coupelingDistancePerLevelset": coupelingDistancePerLevelset,
    })

    return IndecesTable, CellsTable, tmpTable


def getAnalysis(
    imageName: str,
    IndecesTable: pd.DataFrame,
    KTable: pd.DataFrame,
    LevelSetsTable: pd.DataFrame,
    CellsTable: pd.DataFrame,
    tmpTable: pd.DataFrame,
    omega: float,
    numberOfPoints: int,
    pixelSize: float,
    zoneWidth: float,
    numberOfLevelsets: int
) -> pd.DataFrame:
    """
    Aggregate all results into a single summarized analysis DataFrame.
    """
    return pd.DataFrame({
        "imageName": [imageName],
        "pixelSize": [pixelSize],
        "totalNumberOfPoints": [numberOfPoints],
        "zoneWidth": [zoneWidth],
        "numberOfLevelsets": [numberOfLevelsets],
        "Threshold": [IndecesTable["Threshold"].iloc[0]],
        "omega": [omega],
        "levelsetsArea": [LevelSetsTable["Area"].sum()],
        "ACI": [IndecesTable["ACI"].iloc[0]],
        "SAI": [IndecesTable["SAI"].iloc[0]],
        "ASI": [IndecesTable["ASI"].iloc[0]],
        "MODIFIED_ASI": [IndecesTable["MODIFIED_ASI"].iloc[0]],
        "log p-value": [IndecesTable["log p-value"].iloc[0]],
        "meanCouplingDistance": [IndecesTable["meanCouplingDistance"].iloc[0]],
    })







# SpatioPath

SpatioPath is a comprehensive framework designed for spatial statistical analysis of cell-to-cell and region-to-cell interactions. The framework provides robust, reproducible tools for generating simulation data, visualizing results, and analyzing real microscopy images to derive quantitative insights from spatial patterns in the tissue microenvironment.

Key design goals are clarity, separation of concerns, and reproducibility: core numerical routines remain pure and unit-testable, visualization and persistence are encapsulated in a `Result` object, and logging is controlled by the application (caller) rather than the library.

---

## Highlights

- Incremental, batch-first API: add any number of patches (single or many) and compute pooled results when required.
- Clear separation of concerns:
  - numerical/statistical code in helper modules,
  - state + lifecycle in `SpatioPath` engine,
  - visualization + persistence in `SpatioPathResult`.
- No implicit file I/O or logging configuration — the caller controls persistence and logger formatting.
- Small, human-readable persistence by default (CSV + JSON); optional binary pickle for full fidelity (arrays).

---

## Install

Requires Python 3.9+.

Recommended install (editable for development):

```bash
python -m venv .venv
source .venv/bin/activate         # macOS / Linux
# .venv\Scripts\activate          # Windows PowerShell
pip install -e .
````

Minimum runtime dependencies (also listed in `pyproject.toml`):

```
numpy
pandas
scipy
scikit-image
opencv-python
matplotlib
seaborn
shapely
tqdm
```

---

## Concepts

### Patch, Engine, Result

* **Patch** — a single analysis unit. Each patch is defined by:

  * `setA`: polygonal regions (e.g., tumor or tissue compartments),
  * `setB`: points (e.g., cell centroids),
  * `roi`: region-of-interest (optional, defaults to full image).
* **Engine (`SpatioPath`)** — stateful object that accepts patches via `add_patch(...)` and accumulates computed patch-level `Result` objects.
* **Result (`SpatioPathResult`)** — encapsulates all outputs for a patch or a pooled/global analysis: summary metrics, `KTable`, `IndecesTable`, `LevelSetsTable`, `CellsTable`, optional arrays (`zoneMap`, `distMap`), plotting and save/load helpers.

### Regions-of-Interest (ROI)

ROIs are represented using the `shapely` geometry library. The engine expects ROI polygons as instances of `shapely.geometry.Polygon`. This enables robust, standard geometric operations and easy interoperability with common geo / spatial toolchains.

**Example ROI creation (Shapely):**

```python
from shapely.geometry import Polygon

# rectangle ROI spanning a 4096×4096 image
roi = Polygon([(0, 0), (4096, 0), (4096, 4096), (0, 4096)])
```

When `roi` is omitted in `add_patch(...)`, the engine uses a default full-image ROI based on the engine's `width` and `height`.

---

## Quick start

```python
import logging
from spatiopath import SpatioPath, SpatioPathResult
from shapely.geometry import Polygon

# Configure logging in your application (library does not configure root handlers)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Create engine (global parameters fixed at init)
engine = SpatioPath(zone_width=10.0, analysis_zone=400.0, pixel_size=0.5, height=4096, width=4096)

# Prepare patch inputs
# setA: list of polygons, each polygon is (xi_array, yi_array)
# setB: Nx2 array-like of (x, y) points
setA_1 = [([100, 200, 200, 100], [100, 100, 200, 200])]
setB_1 = [(150, 150), (300, 300), (350, 180)]
roi = Polygon([(0, 0), (4096, 0), (4096, 4096), (0, 4096)])

# Add one or more patches
patch_result = engine.add_patch(name="patch_01", setA=setA_1, setB=setB_1, roi=roi)

# Patch-level inspection
print(patch_result.analysis)        # one-row DataFrame of summary metrics
print(patch_result.KTable.head())   # KTable per zone

# Add more patches as needed...
# engine.add_patch(...)

# Pool across all added patches
global_result: SpatioPathResult = engine.compute_pooling()

# Plot pooled K0
ax = global_result.plot_k0(title="Global K₀")
import matplotlib.pyplot as plt
plt.show()

# Save results (as CSVs + JSON)
global_result.save("results/patient001/global_result", format="dir", include_arrays=False)

# Optional: save full pickled result (includes arrays)
global_result.save("results/patient001/global_result.pkl", format="pickle")
```

---

## API reference (concise)

### `SpatioPath(zone_width, analysis_zone, pixel_size, height=4096, width=4096)`

Create a stateful analysis engine.

**Methods**

* `add_patch(name: str, setA, setB, roi: shapely.geometry.Polygon | None = None) -> SpatioPathResult`
  Analyze the patch, return a `SpatioPathResult` and keep it in the engine store.
* `compute_pooling() -> Optional[SpatioPathResult]`
  Pool all stored patches and return a single pooled `SpatioPathResult`. Returns `None` if no patches exist.
* `list_patches() -> List[str]`
  Names of stored patches.
* `reset() -> None`
  Clear stored patches.

### `SpatioPathResult`

Encapsulates a single analysis outcome.

**Attributes**

* `name` — identifier (patch name or `"GLOBAL"`).
* `analysis` — one-row `pandas.DataFrame` containing summary statistics (`MODIFIED_ASI`, `meanCouplingDistance`, `log p-value`, etc.).
* `KTable`, `IndecesTable`, `LevelSetsTable`, `CellsTable` — `pandas.DataFrame`s produced by the pipeline.
* `omega`, `total_points` — numeric metadata.
* `zoneMap`, `distMap` — optional `numpy` arrays (may be `None`).

**Methods**

* `plot_k0(ax: Optional[matplotlib.axes.Axes] = None, colors: Optional[List] = None, title: Optional[str] = None) -> matplotlib.axes.Axes`
  Plot K₀ barplot for this result (patch or pooled).
* `save(path: str, format: str = "dir" | "pickle", include_arrays: bool = False) -> None`
  Persist the result. `'dir'` writes CSVs + JSON; `'pickle'` pickles the full object (includes arrays).
* `load(path: str) -> SpatioPathResult` (static/classmethod)
  Load a previously saved result (folder or pickle).

---

## Logging

The package exposes a module-level logger `spatiopath` but intentionally **does not configure handlers or formatters**. This allows calling applications to centrally configure logging behavior. Example:

```python
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("spatiopath").setLevel(logging.DEBUG)
```

Use standard logging levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) in your application.

---

## Persistence & Interoperability

* Default persistence format (`format='dir'`) stores human-readable CSVs and a JSON summary for easy inspection and version control.
* Optionally use pickled results (`format='pickle'`) when you need to preserve large arrays (`zoneMap`, `distMap`) or Python objects — note that pickles are not cross-version stable and should be used with caution for long-term archives.
* The output tables (`KTable`, `LevelSetsTable`, `IndecesTable`, `CellsTable`) are standard `pandas.DataFrame`s and can be exported to any format supported by pandas.

---

## Development & Contribution


---

## License

MIT — see `LICENSE` for full text.

---

## Citation

If you use SpatioPath in published work, please cite it and include a brief description of the analysis parameters (zone width, pixel size, pooling mode) for reproducibility.
```js
@article{Benimam2025,
   doi = {10.1038/s41467-025-57943-y},
   issn = {2041-1723},
   issue = {1},
   journal = {Nature Communications 2025 16:1},
   keywords = {Bioinformatics,Biomedical engineering,Predictive markers,Statistical methods,Tumour immunology},
   month = {3},
   pages = {1-20},
   pmid = {40164621},
   publisher = {Nature Publishing Group},
   title = {Statistical analysis of spatial patterns in tumor microenvironment images},
   volume = {16},
   url = {https://www.nature.com/articles/s41467-025-57943-y},
   year = {2025}
}
```

```
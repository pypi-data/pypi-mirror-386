# cpp_py_oil_simulator

A C++ oil spill simulator with Python bindings (pybind11). This repository provides a performant core simulator written in C++ and a small pybind11 wrapper so the simulator can be used from Python as the `oilspillsim` package.

Highlights
- Core numerical code uses Eigen for linear algebra (bundled under `src/Eigen`).
- Python bindings implemented in `src/utils/pywrap/pywrap.cpp` using pybind11.
- Minimal example and utilities live under `src/` and `utils/`.

## Quick install

Install using pip from the project root:

```bash
pip install .
```

This builds the extension module (`oilspillsim`) with pybind11. Ensure you have a C++ toolchain and CMake available on your platform.

## Build (developer)

Build the native extension directly using the provided CMake and setuptools integration:

```bash
# from project root
pip install -e .
```

Or build with CMake in `src/` (native build):

```bash
mkdir -p build && cd build
cmake ../src
cmake --build .
```

## Usage (Python)

After installation the package exposes the `oilspillsim` extension module. Example (the exact API is defined in the pybind wrapper):

```py
import oilspillsim

# Create simulator (example — check `src/utils/pywrap/pywrap.cpp` for real args)
sim = oilspillsim.oilspillsim("src/mapas/defuniak_map.csv")
sim.step()
density = sim.get_normalized_density()
```

## Accessible functions (API)

The `oilspillsim` extension exposes a class named `oilspillsim` (C++ type `SIMULATOR`). Below is a concise summary of constructors, methods and read-only attributes provided by the pybind11 wrapper. For exact function signatures and default values see `src/utils/pywrap/pywrap.cpp`.

- Class: `oilspillsim` (C++: `SIMULATOR`)
  - Constructor:
    - `oilspillsim(_filepath: str, **kwargs)`
      - Create the simulator by loading a map from a file (CSV or supported format by the core).
    - `oilspillsim(base_matrix: numpy.ndarray or Eigen::MatrixXi, **kwargs)`
      - Create the simulator from an in-memory base matrix (map, usually a 2D array, 0 for obstacle 1 for valid position).
  - Contructor kwargs:
    - `_dt`: (float=10.0) internal time variable. Each time oilspillsim.step() is called, particles will move relative to this.
    - `_kw`: (float=0.5) wind gain. wind component affecting particles is weighted by this value
    - `_kc`: (float=1.0) current gain. current components affecting particles are weighted by this value.
    - `_gamma`: (float=1.0) brownian movement gain. Random movement due to particle intereffects are weighet by this value
    - `_flow`: (float=50.0) ammount of particles liberated to the environment normalized for _dt =1 at each sourcepoint
    - `_number_of_sources`: (int=3) ammount of sources that liberate oil to the environment
    - `_max_contamination_value`: (int=5) value to dictate maximun concentration of contamination per node. No more than "_max_contamination_value" particles can be present in the same node.
    - `_source_fuel`: (int=1000) maximum fuel a source can liberate to the environment, once a source liberates "_source_fuel" particles, it stops liberating
    - `_random_seed`: (int=-1) seed to relive experiments, leave to -1 to allways use a different seed
    - `_triangular`: (bool=False) special condition promoving a different particle behaviour where particles moves following a cross shape.

  - Main methods:
    - `step()`
      - Advance the simulation by one time step. The GIL is released during execution for performance.
    - `reset(_seed: int = -1, Eigen::MatrixXi _source_points_pos)`
      - Reset the simulation state. If `_seed` is provided the RNG is seeded for reproducibility. -1 used for random seed.
      - If `_source_points_pos` is provided, source points will take chosen position, otherwise seed source points will be taken 
    - `get_normalized_density(gaussian: bool = True) -> numpy.ndarray`
      - Return the normalized density matrix (optionally smoothed using a Gaussian kernel if `gaussian=True`).

  - Read-only attributes (accessible from Python):
    - `source_points` — coordinates of contamination sources (list/array).
    - `contamination_position` — array containing all the discrete particles positions (list/array).
    - `density` — raw hydrocarbon density matrix (not normalized).
    - `x`, `y` — spatial coordinate vectors associated with the grid.
    - `u`, `v` — velocity fields (x/y components) used by the simulation to simulate currents (array).
    - `wind_speed` — wind speed value or field used in the model (array(2)).

Notes:
- For exact signatures and default values check `src/utils/pywrap/pywrap.cpp`.
- Exposed structures (for example Eigen matrices) are converted to/from NumPy arrays via `pybind11/eigen.h`.

## Tests

There is a small test script used by CI in `src/tests/test.py` (also referenced in `pyproject.toml`) accesible from [github](https://github.com/AloePacci/cpp_oil_simulator). Run it with:

```bash
python src/tests/test.py
```



## Contributing

Contributions and bug reports are welcome. Please open issues or pull requests on the GitHub repository: https://github.com/AloePacci/cpp_oil_simulator

## Authors

Alejandro Casado Pérez — acasado4@us.es

Acknowledgements: Samuel Yanes Luis (help and guidance).

## License

This project is provided under the terms in `LICENSE`.

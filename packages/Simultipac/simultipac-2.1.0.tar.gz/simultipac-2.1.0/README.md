# About this package
This package is a set of utils oriented towards multipacting analysis.
In particular:
 - Load parameter sweeps and PIC Position Monitor data from CST Particle Studio.
 - Load results from SPARK3D.
 - Post-treat electron vs time results from these tools: multipactor trend, (TODO: multipactor order).
 - Post-treat CST's PIC Position Monitor:
  - Distribution of emission energies.
  - Distribution of impact energies.
  - Distribution of impact angles.
  - Visualize trajectories.

# Installation
## Requirements
You will need a recent version of Python (at least 3.12).

## Installation
### Simple installation
1. Create a dedicated Python environment, activate it.
2. Run `pip install simultipac`

> [!NOTE]
> If you are completely new to Python and these instructions are unclear, check [this tutorial](https://python-guide.readthedocs.io/en/latest/).
> In particular, you will want to:
> 1. [Install Python](https://python-guide.readthedocs.io/en/latest/starting/installation/) 3.12 or higher.
> 2. [Learn to use Python environments](https://python-guide.readthedocs.io/en/latest/dev/virtualenvs/), `pipenv` or `virtualenv`.
> 3. [Install a Python IDE](https://python-guide.readthedocs.io/en/latest/dev/env/#ides) such as Spyder or VSCode.

### Building form source
1. Navigate to the library installation folder.
2. `git clone git@github.com:AdrienPlacais/Simulia_Multipactor_lib.git` (or download it a `zip`).
3. Navigate to `Simulia_Multipactor_lib`
4. Create a dedicated python environment.
5. `pip install -e .`

# How to use
## Documentation
Documentation is available at [this link](https://simultipac.readthedocs.io/en/latest/).

## Tutorial
Examples are provided in the `examples` folder and [in the documentation](https://simultipac.readthedocs.io/en/latest/manual/examples_jupyter_notebooks.html).

# Gallery
## Compute exponential growth factor
### From SPARK3D
![Evolution of exponential growth factor with accelerating field](docs/manual/images/exp_growth_spark.png)

### From CST
Results of a parametric study on the number of seed electrons.
![Evolution of exponential growth factor with accelerating field](docs/manual/images/exp_growth_cst.png)

## Treat CST PIC Monitor data
### Emission energies
![Distribution of emission energies](docs/manual/images/emission_energy_distribution.png)

### Collision energies
![Distribution of collision energies](docs/manual/images/collision_energy_distribution.png)

### Collision angles
![Distribution of collision angles](docs/manual/images/collision_angle_distribution.png)

### Trajectory plots
Here we represented in red the collision points and in green the emission points.
Electrons without a green point are seed electrons.

![Plot of some trajectories](docs/manual/images/trajectories_1.png)

![Plot of some trajectories](docs/manual/images/trajectories_2.png)

[See also: interactive trajectory plot](https://simultipac.readthedocs.io/en/latest/_static/k3d_tesla_example.html)

# TO DO

- [ ] Avoid git warnigns

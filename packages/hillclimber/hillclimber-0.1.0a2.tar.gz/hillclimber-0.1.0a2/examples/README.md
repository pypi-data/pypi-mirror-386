# Hillclimber Examples

This directory contains comprehensive examples demonstrating the capabilities of the Hillclimber package for enhanced sampling simulations using PLUMED with ASE and IPSuite.

## Overview

Each example is a complete, runnable script that showcases specific features of Hillclimber. All examples use:
- **IPSuite** for system generation and molecular dynamics
- **SMILES/Packmol** for creating molecular systems
- **MACEMPModel** for ML force field calculations
- **zntrack** for reproducible workflow management

## Examples

### 01_distance_metad.py - Basic Distance Metadynamics
**Difficulty:** Beginner
**Runtime:** ~5-10 minutes

Introduction to well-tempered metadynamics using a simple distance collective variable.

**System:** 3 water molecules + 1 ethanol molecule
**CV:** Distance between water and ethanol centers of mass
**Features:**
- VirtualAtom with COM reduction
- DistanceCV with pairwise options
- Well-tempered metadynamics basics
- PrintAction for monitoring

**Learning objectives:**
- Setting up a molecular system with IPSuite
- Defining collective variables
- Configuring metadynamics parameters
- Running biased MD simulations

---

### 02_torsion_metad.py - Torsional Metadynamics
**Difficulty:** Intermediate
**Runtime:** ~10-15 minutes

Classic PLUMED tutorial exploring backbone conformations of alanine dipeptide.

**System:** Alanine dipeptide (Ace-Ala-Nme)
**CV:** Phi backbone dihedral angle (C-N-CA-C)
**Features:**
- TorsionCV with SMARTS pattern matching
- Mapped atoms for precise selection
- Geometry optimization before MD
- Periodic CV handling

**Learning objectives:**
- Using SMARTS patterns with mapped atoms
- Working with torsional collective variables
- Exploring conformational free energy landscapes
- Analyzing Ramachandran space

---

### 03_coordination_number.py - Ion Solvation
**Difficulty:** Intermediate
**Runtime:** ~8-12 minutes

Study ion solvation dynamics using coordination number as a CV.

**System:** 1 Na+ ion + 20 water molecules
**CV:** Coordination number of water oxygens around Na+
**Features:**
- CoordinationNumberCV with switching function
- Tuning r_0, nn, mm parameters
- Ion-water solvation structure

**Learning objectives:**
- Understanding coordination number CVs
- Configuring switching functions
- Studying solvation shell dynamics
- Interpreting discrete-valued CVs

---

### 04_2d_metad.py - 2D Ramachandran Exploration
**Difficulty:** Advanced
**Runtime:** ~20-30 minutes

THE classic PLUMED tutorial: 2D metadynamics on phi and psi angles.

**System:** Alanine dipeptide
**CVs:** Both phi and psi backbone dihedral angles
**Features:**
- Multiple CVs with different parameters
- 2D metadynamics
- Full Ramachandran plot exploration
- Multiple conformational basins

**Learning objectives:**
- Running multi-dimensional metadynamics
- Different sigma for each CV
- Reconstructing 2D free energy surfaces
- Assessing convergence in 2D

---

### 05_opes_sampling.py - Modern Enhanced Sampling
**Difficulty:** Intermediate
**Runtime:** ~8-12 minutes

OPES (On-the-fly Probability Enhanced Sampling) as an alternative to metadynamics.

**System:** 2 ethanol molecules
**CV:** Distance between ethanol centers of mass
**Features:**
- OPESModel instead of MetaDynamicsModel
- Adaptive sigma
- BARRIER parameter tuning
- Explore mode option

**Learning objectives:**
- Understanding OPES vs metadynamics
- When to use OPES
- Configuring adaptive sampling
- Faster convergence strategies

---

### 06_walls_restraints.py - Constrained Sampling
**Difficulty:** Advanced
**Runtime:** ~8-12 minutes

Combining metadynamics with walls and restraints for controlled sampling.

**System:** 1 water + 1 benzene
**CV:** Distance between water and benzene COMs
**Features:**
- LowerWallBias to prevent close contacts
- UpperWallBias to limit separation
- RestraintBias for harmonic constraints
- Multiple bias potentials combined

**Learning objectives:**
- Using walls to prevent unphysical values
- Adding experimental constraints
- Combining multiple biases
- Understanding when to use each type

---

## Prerequisites

Before running these examples, ensure you have installed:

```bash
# Install hillclimber and dependencies
pip install hillclimber ipsuite zntrack

# Install PLUMED (if not already installed)
conda install -c conda-forge plumed

# Install packmol for system generation
conda install -c conda-forge packmol
```

## Running the Examples

Each example is a standalone Python script. To run:

```bash
# Navigate to the examples directory
cd examples/

# Run any example
python 01_distance_metad.py
```

The examples use zntrack for workflow management, which will:
1. Create a `.zntrack` directory for tracking
2. Generate DVC configuration files
3. Store outputs in organized node directories

## Output Files

Each example generates:

- **HILLS**: Deposited Gaussian hills (metadynamics only)
- **KERNELS**: OPES kernels (OPES only)
- **COLVAR**: Collective variable trajectory
- **Trajectory**: MD trajectory in atoms.h5 format
- **Workflow files**: DVC and zntrack configuration

## Analyzing Results

### Computing Free Energy Surfaces

```bash
# For 1D metadynamics
plumed sum_hills --hills HILLS

# For 2D metadynamics
plumed sum_hills --hills HILLS  # Creates fes.dat

# Check convergence over time
plumed sum_hills --hills HILLS --stride 100 --mintozero
```

### Visualizing Trajectories

```python
import ase.io
from ase.visualize import view

# Load trajectory
traj = ase.io.read("nodes/ASEMD/atoms.h5", ":")

# Visualize
view(traj)
```

### Plotting Collective Variables

```python
import numpy as np
import matplotlib.pyplot as plt

# Load COLVAR file
data = np.loadtxt("COLVAR", comments="#")
time = data[:, 0]
cv_values = data[:, 1]

plt.plot(time, cv_values)
plt.xlabel("Time (fs)")
plt.ylabel("CV Value")
plt.show()
```

## Key Concepts

### Well-Tempered Metadynamics

All metadynamics examples use **well-tempered** metadynamics with:
- **HEIGHT**: Initial Gaussian height (kJ/mol)
- **PACE**: Deposition frequency (steps)
- **BIASFACTOR** (γ): Controls convergence (typically 6-15)
- **SIGMA**: Gaussian width (~1/5 to 1/10 of CV range)

The bias factor γ determines the asymptotic temperature:
```
T_asymptotic = T × γ
```

### Collective Variables

Each CV type has specific use cases:
- **DistanceCV**: Molecular association/dissociation
- **TorsionCV**: Conformational changes
- **CoordinationNumberCV**: Solvation, binding events
- **AngleCV**: Angular changes, bending modes
- **RadiusOfGyrationCV**: Molecular compactness

### Choosing Parameters

**SIGMA (Gaussian width):**
- Rule of thumb: 1/5 to 1/10 of CV fluctuation range
- Too small: Slow convergence, rough FES
- Too large: Poor resolution, missed barriers

**PACE (deposition frequency):**
- Shorter: Faster exploration, but may overfill wells
- Longer: Better accuracy, but slower convergence
- Typical: 500-2000 steps

**BIASFACTOR (γ):**
- Lower (6-8): Faster convergence, less exploration
- Higher (10-15): Better exploration, slower convergence
- For 2D: Use lower values (6-8)

## Common Pitfalls

1. **SIGMA too large** → Poor resolution, missed fine features
2. **PACE too short** → Overfilling, inaccurate barriers
3. **Insufficient simulation time** → Unconverged FES
4. **Wrong CV choice** → Sampling wrong degrees of freedom
5. **Grid too coarse** → Loss of detail in FES

## Tips for Success

1. **Start with 1D** before attempting multi-dimensional metadynamics
2. **Check convergence** by computing FES at different times
3. **Use walls** to prevent unphysical CV values
4. **Monitor CVs** during simulation to ensure proper sampling
5. **Compare with unbiased** MD to validate CV choice

## Further Resources

- **PLUMED Documentation:** https://www.plumed.org/doc-master/user-doc/html/
- **PLUMED Tutorials:** https://www.plumed.org/doc-master/user-doc/html/tutorials.html
- **PLUMED-NEST:** https://www.plumed-nest.org/ (Example repository)
- **IPSuite Documentation:** https://ipsuite.zincware.org/
- **Hillclimber Documentation:** https://github.com/zincware/hillclimber

## Troubleshooting

### "SMARTS pattern not found"
- Check molecule connectivity in the system
- Verify SMILES strings are correct
- Use simpler SMARTS patterns for testing

### "Grid boundaries exceeded"
- Increase `grid_max` or decrease `grid_min`
- Add walls to prevent CV from leaving grid
- Check if CV values are physical

### "Simulation crashes"
- Reduce timestep (try 0.5 → 0.25 fs)
- Add equilibration before metadynamics
- Check for atomic overlaps in initial structure

### "FES not converging"
- Increase simulation time
- Reduce Gaussian height
- Check if CV is appropriate for the process
- Verify all relevant regions are being sampled

## Citation

If you use Hillclimber in your research, please cite:

```bibtex
@software{hillclimber,
  title = {Hillclimber: A Python Wrapper for PLUMED Enhanced Sampling},
  author = {[Author names]},
  year = {2025},
  url = {https://github.com/zincware/hillclimber}
}
```

And the underlying methods:

```bibtex
@article{plumed2,
  title = {PLUMED 2: New feathers for an old bird},
  author = {Tribello, Gareth A. and others},
  journal = {Computer Physics Communications},
  volume = {185},
  pages = {604--613},
  year = {2014}
}

@article{welltempered,
  title = {Well-Tempered Metadynamics: A Smoothly Converging and Tunable Free-Energy Method},
  author = {Barducci, Alessandro and others},
  journal = {Physical Review Letters},
  volume = {100},
  pages = {020603},
  year = {2008}
}
```

## Contributing

Found a bug or want to add an example? Please open an issue or pull request on the [Hillclimber GitHub repository](https://github.com/zincware/hillclimber).

---

Happy sampling! 🎉

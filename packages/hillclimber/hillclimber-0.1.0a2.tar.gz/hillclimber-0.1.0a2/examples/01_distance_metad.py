"""
Example 01: Distance-Based Well-Tempered Metadynamics
======================================================

This example demonstrates basic well-tempered metadynamics using a distance
collective variable (CV) between water and ethanol molecules.

Learning Objectives:
- Setting up a molecular system using SMILES and packmol
- Defining collective variables with DistanceCV
- Using VirtualAtom to compute centers of mass
- Configuring well-tempered metadynamics
- Running biased molecular dynamics with ASE

System:
- 3 water molecules
- 1 ethanol molecule
- CV: Distance between water center of mass and ethanol center of mass

Reference:
https://www.plumed.org/doc-master/user-doc/html/_m_e_t_a_d.html
"""

import ase
import ase.md
import ase.units
import hillclimber as hc
import ipsuite as ips
import zntrack

# Configure the simulation parameters
TEMPERATURE = 300.0  # Kelvin
TIMESTEP = 0.5  # fs
N_STEPS = 10_000  # Number of MD steps


def main():
    """Run distance-based metadynamics simulation."""

    # Create a zntrack project for workflow management
    project = zntrack.Project()

    with project:
        # ===================================================================
        # Step 1: Generate the molecular system
        # ===================================================================

        # First, generate individual molecules using SMILES notation
        water = ips.Smiles2Atoms(smiles="O")       # Water molecule
        ethanol = ips.Smiles2Atoms(smiles="CCO")   # Ethanol molecule

        # Pack molecules into a box using Packmol
        # data: list of frame lists from each molecule
        # count: list of integers specifying how many of each molecule
        data_gen = ips.Packmol(
            data=[water.frames, ethanol.frames],
            count=[3, 1],     # 3 water, 1 ethanol
            density=800,      # kg/m³
            tolerance=2.0     # Minimum distance between atoms (Angstrom)
        )

        # ===================================================================
        # Step 2: Define atom selectors
        # ===================================================================

        # Select all water molecules (SMARTS pattern "O")
        water_selector = hc.SMARTSSelector(pattern="O")

        # Select the ethanol molecule (SMARTS pattern "CCO")
        ethanol_selector = hc.SMARTSSelector(pattern="CCO")

        # ===================================================================
        # Step 3: Create virtual atoms (centers of mass)
        # ===================================================================

        # Compute center of mass for all water molecules
        # reduction="com" creates a COM virtual atom for each water
        water_coms = hc.VirtualAtom(
            atoms=water_selector,
            reduction="com",
            label="water"
        )

        # Compute center of mass for the ethanol molecule
        # Since we only have one ethanol, this creates a single COM
        ethanol_com = hc.VirtualAtom(
            atoms=ethanol_selector,
            reduction="com",
            label="ethanol"
        )

        # ===================================================================
        # Step 4: Define the collective variable (CV)
        # ===================================================================

        # Create a distance CV between water COMs and ethanol COM
        # With 3 waters and 1 ethanol, this creates 3 distance CVs
        distance_cv = hc.DistanceCV(
            x1=water_coms,
            x2=ethanol_com,
            prefix="d_water_ethanol",
            pairwise="all"  # Compute all water-ethanol distances
        )

        # ===================================================================
        # Step 5: Configure metadynamics bias for the CV
        # ===================================================================

        # Define the bias parameters for this CV
        # SIGMA should be ~1/5 to 1/10 of the CV fluctuation range
        metad_bias = hc.MetadBias(
            cv=distance_cv,
            sigma=0.2,        # Width of Gaussian hills (Angstroms)
            grid_min=0.0,     # Minimum grid value (Angstroms)
            grid_max=15.0,    # Maximum grid value (Angstroms)
            grid_bin=300      # Number of grid bins for performance
        )

        # ===================================================================
        # Step 6: Configure global metadynamics parameters
        # ===================================================================

        # Set up well-tempered metadynamics
        # Reference: https://www.plumed.org/doc-master/user-doc/html/_m_e_t_a_d.html
        metad_config = hc.MetaDynamicsConfig(
            height=1.2,         # Height of Gaussian hills (kJ/mol)
            pace=500,           # Deposit hill every 500 steps
            biasfactor=10.0,    # Well-tempered bias factor (γ)
            temp=TEMPERATURE,   # Temperature (K)
            file="HILLS"        # Output file for deposited hills
        )

        # ===================================================================
        # Step 7: Add output actions
        # ===================================================================

        # Print CV values during simulation for monitoring
        print_action = hc.PrintAction(
            cvs=[distance_cv],
            stride=100,         # Print every 100 steps
            file="COLVAR"       # Output file
        )

        # ===================================================================
        # Step 8: Create the metadynamics model
        # ===================================================================

        # The MetaDynamicsModel wraps a base calculator with PLUMED
        metad_model = hc.MetaDynamicsModel(
            config=metad_config,
            bias_cvs=[metad_bias],
            actions=[print_action],
            data=data_gen.atoms,
            data_idx=-1,                    # Use last frame
            model=ips.MACEMPModel(),        # ML force field
            timestep=TIMESTEP
        )

        # ===================================================================
        # Step 9: Run molecular dynamics with metadynamics
        # ===================================================================

        # Configure ASE MD with Langevin thermostat
        md_simulation = ips.ASEMD(
            data=data_gen.atoms,
            data_id=-1,
            model=metad_model,
            thermostat=ips.LangevinThermostat(
                temperature=TEMPERATURE,
                friction=0.01  # Friction coefficient (1/fs)
            ),
            steps=N_STEPS,
            sampling_rate=10,   # Save trajectory every 10 steps
            dump_rate=100       # Print status every 100 steps
        )

    # ===================================================================
    # Step 10: Execute the workflow
    # ===================================================================

    print("Building and executing workflow...")
    project.build()

    print("\n" + "="*70)
    print("Simulation completed successfully!")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  - HILLS: Deposited Gaussian hills")
    print(f"  - COLVAR: Collective variable trajectory")
    print(f"  - Trajectory: {md_simulation.nout}/atoms.h5")
    print("\nAnalysis suggestions:")
    print("  1. Plot CV values from COLVAR file")
    print("  2. Compute free energy with: plumed sum_hills --hills HILLS")
    print("  3. Visualize trajectory with ASE or other MD visualization tools")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

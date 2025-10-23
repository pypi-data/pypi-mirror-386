"""
Example 06: Walls and Restraints for Constrained Sampling
===========================================================

This example demonstrates how to use walls and harmonic restraints to keep
collective variables within specific ranges during enhanced sampling.

Walls and restraints are useful for:
- Preventing unphysical CV values (e.g., negative distances)
- Keeping sampling within relevant regions
- Adding experimental constraints
- Combining with metadynamics for focused exploration

Learning Objectives:
- Using UpperWallBias to prevent CV from exceeding a maximum
- Using LowerWallBias to prevent CV from going below a minimum
- Using RestraintBias to add harmonic restraints
- Combining multiple bias potentials
- Understanding when to use walls vs restraints

System:
- Water molecule and benzene ring
- CVs: Distance between water and benzene centers

Reference:
https://www.plumed.org/doc-master/user-doc/html/_u_p_p_e_r__w_a_l_l_s.html
https://www.plumed.org/doc-master/user-doc/html/_l_o_w_e_r__w_a_l_l_s.html
https://www.plumed.org/doc-master/user-doc/html/_r_e_s_t_r_a_i_n_t.html
"""

import hillclimber as hc
import ipsuite as ips
import zntrack

# Configure the simulation parameters
TEMPERATURE = 300.0  # Kelvin
TIMESTEP = 0.5  # fs
N_STEPS = 30_000  # Number of MD steps


def main():
    """Run metadynamics with walls and restraints."""

    # Create a zntrack project for workflow management
    project = zntrack.Project()

    with project:
        # ===================================================================
        # Step 1: Generate the system (water + benzene)
        # ===================================================================

        # Create molecules
        water = ips.Smiles2Atoms(smiles="O")
        benzene = ips.Smiles2Atoms(smiles="c1ccccc1")  # Aromatic benzene

        # Pack molecules into a box
        data_gen = ips.Packmol(
            data=[water.frames, benzene.frames],
            count=[1, 1],     # 1 water, 1 benzene
            density=800,      # kg/m³
            tolerance=2.0     # Minimum distance between atoms (Angstrom)
        )

        # ===================================================================
        # Step 2: Define atom selectors
        # ===================================================================

        # Select water
        water_selector = hc.SMARTSSelector(pattern="O")

        # Select benzene (aromatic 6-membered ring)
        benzene_selector = hc.SMARTSSelector(pattern="c1ccccc1")

        # ===================================================================
        # Step 3: Create virtual atoms (centers of mass)
        # ===================================================================

        water_com = hc.VirtualAtom(
            atoms=water_selector,
            reduction="com",
            label="water"
        )

        benzene_com = hc.VirtualAtom(
            atoms=benzene_selector,
            reduction="com",
            label="benzene"
        )

        # ===================================================================
        # Step 4: Define the collective variable (CV)
        # ===================================================================

        # Distance between water and benzene COMs
        distance_cv = hc.DistanceCV(
            x1=water_com,
            x2=benzene_com,
            prefix="d_water_benzene"
        )

        # ===================================================================
        # Step 5: Configure metadynamics bias
        # ===================================================================

        # Standard metadynamics bias on the distance
        metad_bias = hc.MetadBias(
            cv=distance_cv,
            sigma=0.2,        # Width of Gaussian hills (Angstroms)
            grid_min=0.0,     # Minimum grid value
            grid_max=15.0,    # Maximum grid value
            grid_bin=300      # Number of grid bins
        )

        # ===================================================================
        # Step 6: Add LOWER WALL to prevent very small distances
        # ===================================================================

        # Lower wall prevents the distance from going below 2.0 Angstrom
        # This prevents water from getting too close to benzene ring
        # The potential is: kappa * (at - d)^exp  if d < at, else 0
        lower_wall = hc.LowerWallBias(
            cv=distance_cv,
            at=2.0,           # Wall position (Angstroms)
            kappa=500.0,      # Force constant (kJ/(mol·Å^2))
            exp=2             # Exponent (2 = harmonic wall)
        )

        # ===================================================================
        # Step 7: Add UPPER WALL to prevent very large distances
        # ===================================================================

        # Upper wall prevents the distance from exceeding 12.0 Angstrom
        # This keeps molecules from drifting too far apart
        # The potential is: kappa * (d - at)^exp  if d > at, else 0
        upper_wall = hc.UpperWallBias(
            cv=distance_cv,
            at=12.0,          # Wall position (Angstroms)
            kappa=500.0,      # Force constant (kJ/(mol·Å^2))
            exp=2,            # Exponent (2 = harmonic wall)
            eps=0.0,          # Small offset for smoothness
            offset=0.0        # Additional offset
        )

        # ===================================================================
        # Step 8: Add HARMONIC RESTRAINT around optimal distance
        # ===================================================================

        # Harmonic restraint gently pulls the system toward a target value
        # This is useful for incorporating experimental constraints
        # The potential is: (1/2) * kappa * (d - at)^2
        harmonic_restraint = hc.RestraintBias(
            cv=distance_cv,
            kappa=100.0,      # Force constant (kJ/(mol·Å^2))
            at=5.0,           # Target distance (Angstroms)
            label="restraint_water_benzene"
        )

        # ===================================================================
        # Step 9: Configure global metadynamics parameters
        # ===================================================================

        metad_config = hc.MetaDynamicsConfig(
            height=1.0,         # Height of Gaussian hills (kJ/mol)
            pace=1000,          # Deposit hill every 1000 steps
            biasfactor=10.0,    # Well-tempered bias factor
            temp=TEMPERATURE,   # Temperature (K)
            file="HILLS"        # Output file for deposited hills
        )

        # ===================================================================
        # Step 10: Add output actions
        # ===================================================================

        # Print CV values during simulation
        print_action = hc.PrintAction(
            cvs=[distance_cv],
            stride=100,         # Print every 100 steps
            file="COLVAR"       # Output file
        )

        # ===================================================================
        # Step 11: Create the metadynamics model with ALL biases
        # ===================================================================

        # IMPORTANT: The 'actions' parameter includes:
        # - Print actions
        # - Restraints
        # - Walls
        # These are PLUMED actions that are not metadynamics biases
        metad_model = hc.MetaDynamicsModel(
            config=metad_config,
            bias_cvs=[metad_bias],  # Metadynamics bias
            actions=[
                print_action,        # Print CV values
                lower_wall,          # Lower wall constraint
                upper_wall,          # Upper wall constraint
                harmonic_restraint   # Harmonic restraint
            ],
            data=data_gen.frames,
            data_idx=-1,                    # Use last frame
            model=ips.MACEMPModel(),        # ML force field
            timestep=TIMESTEP
        )

        # ===================================================================
        # Step 12: Run molecular dynamics with metadynamics + walls + restraints
        # ===================================================================

        md_simulation = ips.ASEMD(
            data=data_gen.frames,
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
    # Step 13: Execute the workflow
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
    print("\nWalls and Restraints explanation:")
    print("  - LOWER WALL (at=2.0 Å): Prevents contact distance < 2.0 Å")
    print("  - UPPER WALL (at=12.0 Å): Prevents separation > 12.0 Å")
    print("  - RESTRAINT (at=5.0 Å): Gently biases toward 5.0 Å separation")
    print("\nWhen to use:")
    print("  - Lower walls: Prevent unphysical close contacts")
    print("  - Upper walls: Keep molecules from escaping the relevant region")
    print("  - Restraints: Incorporate experimental data or keep near a value")
    print("  - Combined with metadynamics: Explore within constrained region")
    print("\nAnalysis suggestions:")
    print("  1. Plot distance from COLVAR - should stay between 2-12 Å")
    print("  2. Check if lower/upper walls are activated (high forces)")
    print("  3. Compute FES: plumed sum_hills --hills HILLS")
    print("  4. The restraint will shift the FES minimum toward 5.0 Å")
    print("  5. Walls create steep barriers at the boundaries")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

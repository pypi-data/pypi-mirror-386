"""
Example 03: Coordination Number Metadynamics for Ion Solvation
================================================================

This example demonstrates metadynamics using a coordination number
collective variable (CV) to study ion solvation dynamics.

The coordination number CV counts how many water molecules are in the
first solvation shell of a sodium ion using a smooth switching function.

Learning Objectives:
- Using CoordinationNumberCV to count neighbors
- Studying ion-water solvation structure
- Tuning switching function parameters (r_0, nn, mm)
- Biasing coordination numbers for shell exchange events

System:
- 1 Na+ ion (represented as neutral Na for simplicity)
- 20 water molecules
- CV: Coordination number of waters around Na+

Reference:
https://www.plumed.org/doc-master/user-doc/html/_c_o_o_r_d_i_n_a_t_i_o_n.html
"""

import hillclimber as hc
import ipsuite as ips
import zntrack

# Configure the simulation parameters
TEMPERATURE = 300.0  # Kelvin
TIMESTEP = 0.5  # fs
N_STEPS = 30_000  # Number of MD steps


def main():
    """Run coordination number metadynamics for ion solvation."""

    # Create a zntrack project for workflow management
    project = zntrack.Project()

    with project:
        # ===================================================================
        # Step 1: Generate the solvated ion system
        # ===================================================================

        # Create individual molecules
        # Note: Using Na (neutral) as a proxy for Na+ ion
        # In a real simulation, you'd want to use proper ion parameters
        sodium = ips.Smiles2Atoms(smiles="[Na]")
        water = ips.Smiles2Atoms(smiles="O")

        # Pack molecules into a box
        # 1 sodium ion + 20 water molecules
        data_gen = ips.Packmol(
            data=[sodium.frames, water.frames],
            count=[1, 20],    # 1 Na, 20 waters
            density=1000,     # kg/m³
            tolerance=2.0     # Minimum distance between atoms (Angstrom)
        )

        # ===================================================================
        # Step 2: Define atom selectors
        # ===================================================================

        # Select the sodium ion
        na_selector = hc.SMARTSSelector(pattern="[Na]")

        # Select all water oxygen atoms
        # We're interested in the oxygen positions for coordination
        water_o_selector = hc.SMARTSSelector(pattern="O")

        # ===================================================================
        # Step 3: Create virtual atoms
        # ===================================================================

        # For coordination number, we use the actual atomic positions
        # Use reduction="first" to get atom positions without creating COMs
        na_atom = hc.VirtualAtom(
            atoms=na_selector,
            reduction="first",  # Just use the atom itself
            label="na"
        )

        water_oxygens = hc.VirtualAtom(
            atoms=water_o_selector,
            reduction="first",  # Use actual oxygen positions
            label="water_o"
        )

        # ===================================================================
        # Step 4: Define the coordination number CV
        # ===================================================================

        # Coordination number uses a switching function to count neighbors:
        # s(r) = (1 - (r/r_0)^nn) / (1 - (r/r_0)^mm)
        #
        # Parameters:
        # - r_0: Reference distance (first shell cutoff, ~2.4 Å for Na-O)
        # - nn: Numerator exponent (typically 6)
        # - mm: Denominator exponent (typically 12, or 0 for no denominator)
        #
        # This creates a smooth function that is ~1 for r < r_0 and ~0 for r > r_0

        coordination_cv = hc.CoordinationNumberCV(
            x1=na_atom,
            x2=water_oxygens,
            prefix="cn_na_water",
            r_0=2.4,          # Na-O first shell distance (Angstroms)
            nn=6,             # Numerator exponent
            mm=12,            # Denominator exponent
            d_0=0.0,          # Offset (usually 0)
            pairwise="all"    # Compute with all water oxygens
        )

        # ===================================================================
        # Step 5: Configure metadynamics bias for coordination number
        # ===================================================================

        # The coordination number typically ranges from 4 to 8 for Na+
        # in aqueous solution
        cn_bias = hc.MetadBias(
            cv=coordination_cv,
            sigma=0.1,        # Width of Gaussian hills
            grid_min=0.0,     # Minimum CN value
            grid_max=12.0,    # Maximum CN value
            grid_bin=120      # Number of grid bins
        )

        # ===================================================================
        # Step 6: Configure global metadynamics parameters
        # ===================================================================

        metad_config = hc.MetaDynamicsConfig(
            height=0.5,         # Height of Gaussian hills (kJ/mol)
            pace=1000,          # Deposit hill every 1000 steps
            biasfactor=15.0,    # Well-tempered bias factor
            temp=TEMPERATURE,   # Temperature (K)
            file="HILLS"        # Output file for deposited hills
        )

        # ===================================================================
        # Step 7: Add output actions
        # ===================================================================

        # Print coordination number during simulation
        print_action = hc.PrintAction(
            cvs=[coordination_cv],
            stride=100,         # Print every 100 steps
            file="COLVAR"       # Output file
        )

        # ===================================================================
        # Step 8: Create the metadynamics model
        # ===================================================================

        metad_model = hc.MetaDynamicsModel(
            config=metad_config,
            bias_cvs=[cn_bias],
            actions=[print_action],
            data=data_gen.frames,
            data_idx=-1,                    # Use last frame
            model=ips.MACEMPModel(),        # ML force field
            timestep=TIMESTEP
        )

        # ===================================================================
        # Step 9: Run molecular dynamics with metadynamics
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
    # Step 10: Execute the workflow
    # ===================================================================

    print("Building and executing workflow...")
    project.build()

    print("\n" + "="*70)
    print("Simulation completed successfully!")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  - HILLS: Deposited Gaussian hills")
    print(f"  - COLVAR: Coordination number trajectory")
    print(f"  - Trajectory: {md_simulation.nout}/atoms.h5")
    print("\nAnalysis suggestions:")
    print("  1. Plot coordination number from COLVAR to observe dynamics")
    print("  2. Compute free energy profile:")
    print("     plumed sum_hills --hills HILLS")
    print("  3. The FES should show minima at integer CN values")
    print("     (e.g., 4, 5, 6 water molecules in first shell)")
    print("  4. Barriers between minima represent the free energy cost")
    print("     of water exchange events in the first solvation shell")
    print("  5. Visualize trajectory to see water molecules entering/leaving")
    print("     the first shell around the Na+ ion")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

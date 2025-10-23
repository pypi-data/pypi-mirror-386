"""
Example 02: Torsional Metadynamics on Alanine Dipeptide
==========================================================

This example demonstrates well-tempered metadynamics using a torsional
collective variable (CV) on the phi backbone dihedral angle of alanine dipeptide.

This is a classic PLUMED tutorial - exploring the conformational free energy
landscape of a small peptide by biasing its backbone torsion angles.

Learning Objectives:
- Using TorsionCV with SMARTS pattern matching
- Mapping specific atoms for torsion angle calculation
- Exploring Ramachandran space (phi dihedral angle)
- Well-tempered metadynamics on periodic CVs

System:
- Alanine dipeptide: Ace-Ala-Nme (CNC(=O)[C@H](C)NC(C)=O)
- CV: Phi backbone dihedral angle (C-N-CA-C)

Reference:
https://www.plumed.org/doc-master/user-doc/html/_t_o_r_s_i_o_n.html
https://www.plumed.org/doc-master/user-doc/html/belfast-6.html
"""

import hillclimber as hc
import ipsuite as ips
import zntrack

# Configure the simulation parameters
TEMPERATURE = 300.0  # Kelvin
TIMESTEP = 0.5  # fs
N_STEPS = 50_000  # Number of MD steps


def main():
    """Run torsional metadynamics on alanine dipeptide."""

    # Create a zntrack project for workflow management
    project = zntrack.Project()

    with project:
        # ===================================================================
        # Step 1: Generate the alanine dipeptide molecule
        # ===================================================================

        # Alanine dipeptide SMILES: Ace-Ala-Nme
        # This is the standard system for Ramachandran plot exploration
        alanine_dipeptide = ips.Smiles2Atoms(
            smiles="CNC(=O)[C@H](C)NC(C)=O"
        )

        # Optimize geometry before MD
        geoopt = ips.ASEGeoOpt(
            data=alanine_dipeptide.frames,
            model=ips.MACEMPModel(),
            optimizer="FIRE",
            run_kwargs={"fmax": 0.05}  # Convergence criterion (eV/Angstrom)
        )

        # ===================================================================
        # Step 2: Define the phi backbone dihedral angle
        # ===================================================================

        # The phi dihedral is defined by four atoms: C-N-CA-C
        # We use SMARTS pattern matching with mapped atoms to select them
        #
        # Pattern explanation:
        # - [C:1] = carbonyl carbon (mapped as atom 1)
        # - [N:2] = backbone nitrogen (mapped as atom 2)
        # - [C@H:3] = alpha carbon with stereochemistry (mapped as atom 3)
        # - [C:4] = carbonyl carbon of next residue (mapped as atom 4)
        #
        # The mapped numbers [:1], [:2], [:3], [:4] ensure we get exactly
        # 4 atoms in the correct order for the TORSION calculation

        phi_selector = hc.SMARTSSelector(
            pattern="[C:1][N:2][C@H:3]([C:4])"
        )

        # Create the torsion CV
        # This will compute the dihedral angle formed by the 4 mapped atoms
        phi_cv = hc.TorsionCV(
            atoms=phi_selector,
            prefix="phi",
            multi_group="first"  # Use first match if multiple found
        )

        # ===================================================================
        # Step 3: Configure metadynamics bias for phi
        # ===================================================================

        # For torsional angles, the range is -π to π (periodic)
        # SIGMA should be ~0.3-0.5 rad based on PLUMED tutorials
        phi_bias = hc.MetadBias(
            cv=phi_cv,
            sigma=0.35,        # Width of Gaussian hills (radians)
            grid_min=-3.14159, # -π (periodic boundary)
            grid_max=3.14159,  # +π (periodic boundary)
            grid_bin=200       # Number of grid bins
        )

        # ===================================================================
        # Step 4: Configure global metadynamics parameters
        # ===================================================================

        # Well-tempered metadynamics settings based on PLUMED tutorials
        # Reference: https://www.plumed.org/doc-master/user-doc/html/belfast-6.html
        metad_config = hc.MetaDynamicsConfig(
            height=1.2,         # Height of Gaussian hills (kJ/mol)
            pace=500,           # Deposit hill every 500 steps
            biasfactor=10.0,    # Well-tempered bias factor (γ)
            temp=TEMPERATURE,   # Temperature (K)
            file="HILLS"        # Output file for deposited hills
        )

        # ===================================================================
        # Step 5: Add output actions
        # ===================================================================

        # Print phi angle during simulation
        print_action = hc.PrintAction(
            cvs=[phi_cv],
            stride=100,         # Print every 100 steps
            file="COLVAR"       # Output file
        )

        # ===================================================================
        # Step 6: Create the metadynamics model
        # ===================================================================

        metad_model = hc.MetaDynamicsModel(
            config=metad_config,
            bias_cvs=[phi_bias],
            actions=[print_action],
            data=geoopt.frames,
            data_idx=-1,                    # Use optimized geometry
            model=ips.MACEMPModel(),        # ML force field
            timestep=TIMESTEP
        )

        # ===================================================================
        # Step 7: Run molecular dynamics with metadynamics
        # ===================================================================

        # Use Langevin thermostat for NVT ensemble
        md_simulation = ips.ASEMD(
            data=geoopt.frames,
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
    # Step 8: Execute the workflow
    # ===================================================================

    print("Building and executing workflow...")
    project.build()

    print("\n" + "="*70)
    print("Simulation completed successfully!")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  - HILLS: Deposited Gaussian hills")
    print(f"  - COLVAR: Phi dihedral angle trajectory")
    print(f"  - Trajectory: {md_simulation.nout}/atoms.h5")
    print("\nAnalysis suggestions:")
    print("  1. Plot phi values from COLVAR file to see sampling")
    print("  2. Compute 1D free energy profile:")
    print("     plumed sum_hills --hills HILLS")
    print("  3. Check convergence with time-dependent FES:")
    print("     plumed sum_hills --hills HILLS --stride 100 --mintozero")
    print("  4. The free energy surface should show multiple minima")
    print("     corresponding to different peptide conformations")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

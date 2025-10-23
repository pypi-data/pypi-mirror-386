"""
Example 04: 2D Metadynamics on Phi and Psi Dihedral Angles
============================================================

This example demonstrates 2D well-tempered metadynamics using both phi and psi
backbone dihedral angles of alanine dipeptide to explore the full Ramachandran
plot (conformational free energy landscape).

This is THE classic PLUMED tutorial example, exploring peptide conformational
space by biasing both backbone torsion angles simultaneously.

Learning Objectives:
- Running 2D metadynamics with multiple CVs
- Each CV can have different sigma and grid parameters
- Exploring the Ramachandran plot (phi-psi space)
- Reconstructing 2D free energy surfaces
- Understanding well-tempered metadynamics convergence

System:
- Alanine dipeptide: Ace-Ala-Nme
- CVs: Phi and Psi backbone dihedral angles

Reference:
https://www.plumed.org/doc-master/user-doc/html/belfast-6.html
https://www.plumed.org/doc-master/user-doc/html/aaaa-lugano-3.html
"""

import hillclimber as hc
import ipsuite as ips
import zntrack

# Configure the simulation parameters
TEMPERATURE = 300.0  # Kelvin
TIMESTEP = 0.5  # fs
N_STEPS = 100_000  # Number of MD steps (longer for 2D convergence)


def main():
    """Run 2D metadynamics on alanine dipeptide phi/psi angles."""

    # Create a zntrack project for workflow management
    project = zntrack.Project()

    with project:
        # ===================================================================
        # Step 1: Generate and optimize alanine dipeptide
        # ===================================================================

        # Alanine dipeptide SMILES: Ace-Ala-Nme
        alanine_dipeptide = ips.Smiles2Atoms(
            smiles="CNC(=O)[C@H](C)NC(C)=O"
        )

        # Optimize geometry before MD
        geoopt = ips.ASEGeoOpt(
            data=alanine_dipeptide.frames,
            model=ips.MACEMPModel(),
            optimizer="FIRE",
            run_kwargs={"fmax": 0.05}
        )

        # ===================================================================
        # Step 2: Define phi backbone dihedral angle (C-N-CA-C)
        # ===================================================================

        # Phi is defined by: C(-1) - N - CA - C
        # We use SMARTS with mapped atoms to select the exact 4 atoms
        phi_selector = hc.SMARTSSelector(
            pattern="[C:1][N:2][C@H:3]([C:4])"
        )

        phi_cv = hc.TorsionCV(
            atoms=phi_selector,
            prefix="phi",
            multi_group="first"
        )

        # ===================================================================
        # Step 3: Define psi backbone dihedral angle (N-CA-C-N)
        # ===================================================================

        # Psi is defined by: N - CA - C - N(+1)
        # This requires a different SMARTS pattern
        psi_selector = hc.SMARTSSelector(
            pattern="[N:1][C@H:2]([C:3](=[O])[N:4])"
        )

        psi_cv = hc.TorsionCV(
            atoms=psi_selector,
            prefix="psi",
            multi_group="first"
        )

        # ===================================================================
        # Step 4: Configure metadynamics biases for BOTH CVs
        # ===================================================================

        # Bias for phi
        # Both angles are periodic with range [-π, π]
        phi_bias = hc.MetadBias(
            cv=phi_cv,
            sigma=0.35,        # Width of Gaussian hills (radians)
            grid_min=-3.14159, # -π
            grid_max=3.14159,  # +π
            grid_bin=200       # Number of grid bins
        )

        # Bias for psi
        # Can use different sigma for each CV if needed
        psi_bias = hc.MetadBias(
            cv=psi_cv,
            sigma=0.35,        # Width of Gaussian hills (radians)
            grid_min=-3.14159, # -π
            grid_max=3.14159,  # +π
            grid_bin=200       # Number of grid bins
        )

        # ===================================================================
        # Step 5: Configure global metadynamics parameters
        # ===================================================================

        # For 2D metadynamics, we use the same global parameters
        # The HEIGHT and PACE apply to all CVs
        # Reference: PLUMED tutorial belfast-6
        metad_config = hc.MetaDynamicsConfig(
            height=1.2,         # Height of Gaussian hills (kJ/mol)
            pace=500,           # Deposit hill every 500 steps
            biasfactor=6.0,     # Well-tempered bias factor (lower for 2D)
            temp=TEMPERATURE,   # Temperature (K)
            file="HILLS"        # Output file for deposited hills
        )

        # ===================================================================
        # Step 6: Add output actions
        # ===================================================================

        # Print both phi and psi during simulation
        # This allows us to visualize the trajectory in 2D space
        print_action = hc.PrintAction(
            cvs=[phi_cv, psi_cv],
            stride=100,         # Print every 100 steps
            file="COLVAR"       # Output file
        )

        # ===================================================================
        # Step 7: Create the metadynamics model with BOTH biases
        # ===================================================================

        # IMPORTANT: Pass both bias_cvs in a list
        # This creates a 2D metadynamics simulation
        metad_model = hc.MetaDynamicsModel(
            config=metad_config,
            bias_cvs=[phi_bias, psi_bias],  # Both CVs!
            actions=[print_action],
            data=geoopt.frames,
            data_idx=-1,                    # Use optimized geometry
            model=ips.MACEMPModel(),        # ML force field
            timestep=TIMESTEP
        )

        # ===================================================================
        # Step 8: Run molecular dynamics with 2D metadynamics
        # ===================================================================

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
    # Step 9: Execute the workflow
    # ===================================================================

    print("Building and executing workflow...")
    project.build()

    print("\n" + "="*70)
    print("Simulation completed successfully!")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  - HILLS: Deposited Gaussian hills (2D)")
    print(f"  - COLVAR: Phi and psi angle trajectories")
    print(f"  - Trajectory: {md_simulation.nout}/atoms.h5")
    print("\nAnalysis suggestions:")
    print("  1. Plot 2D trajectory in phi-psi space from COLVAR")
    print("  2. Compute 2D free energy surface:")
    print("     plumed sum_hills --hills HILLS")
    print("     This creates fes.dat with columns: phi psi FES")
    print("  3. Check convergence by computing FES at different times:")
    print("     plumed sum_hills --hills HILLS --stride 200 --mintozero")
    print("  4. The 2D FES should show multiple basins:")
    print("     - C7eq (right-handed α-helix region)")
    print("     - C7ax (left-handed α-helix region)")
    print("     - αR (extended region)")
    print("     - αL (left-handed α-helix)")
    print("  5. Visualize the 2D FES as a heatmap/contour plot")
    print("  6. The FES converges when basins stop changing shape/depth")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

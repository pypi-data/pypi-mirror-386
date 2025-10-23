"""
Example 05: OPES Enhanced Sampling
===================================

This example demonstrates OPES (On-the-fly Probability Enhanced Sampling),
a modern alternative to metadynamics for enhanced sampling.

OPES is often more efficient than traditional metadynamics, especially for
systems with multiple barriers. It adapts the bias on-the-fly based on the
sampled probability distribution.

Learning Objectives:
- Using OPESModel instead of MetaDynamicsModel
- Configuring OPES parameters (barrier, pace, explore mode)
- Understanding adaptive sigma in OPES
- Comparing OPES vs traditional metadynamics

System:
- 2 ethanol molecules
- CV: Distance between their centers of mass

Reference:
https://www.plumed.org/doc-master/user-doc/html/_o_p_e_s__m_e_t_a_d.html
"""

import hillclimber as hc
import ipsuite as ips
import zntrack

# Configure the simulation parameters
TEMPERATURE = 300.0  # Kelvin
TIMESTEP = 0.5  # fs
N_STEPS = 30_000  # Number of MD steps


def main():
    """Run OPES enhanced sampling on ethanol dimer."""

    # Create a zntrack project for workflow management
    project = zntrack.Project()

    with project:
        # ===================================================================
        # Step 1: Generate the ethanol dimer system
        # ===================================================================

        # Create ethanol molecules
        ethanol = ips.Smiles2Atoms(smiles="CCO")

        # Pack 2 ethanol molecules into a box
        data_gen = ips.Packmol(
            data=[ethanol.frames],
            count=[2],        # 2 ethanol molecules
            density=800,      # kg/m³
            tolerance=2.0     # Minimum distance between atoms (Angstrom)
        )

        # ===================================================================
        # Step 2: Define atom selectors
        # ===================================================================

        # Select all ethanol molecules
        ethanol_selector = hc.SMARTSSelector(pattern="CCO")

        # ===================================================================
        # Step 3: Create virtual atoms (centers of mass)
        # ===================================================================

        # Compute center of mass for each ethanol molecule
        ethanol_coms = hc.VirtualAtom(
            atoms=ethanol_selector,
            reduction="com",
            label="ethanol"
        )

        # ===================================================================
        # Step 4: Define the collective variable (CV)
        # ===================================================================

        # Distance between the two ethanol COMs
        # This measures association/dissociation
        distance_cv = hc.DistanceCV(
            x1=ethanol_coms[0],  # First ethanol COM
            x2=ethanol_coms[1],  # Second ethanol COM
            prefix="d_ethanol",
            pairwise="diagonal"  # Pair corresponding indices
        )

        # ===================================================================
        # Step 5: Configure OPES bias for the CV
        # ===================================================================

        # OPES uses adaptive sigma by default
        # You can specify "ADAPTIVE" or a fixed value
        opes_bias = hc.OPESBias(
            cv=distance_cv,
            sigma="ADAPTIVE"  # Let OPES determine sigma adaptively
            # Alternatively: sigma=0.2 for fixed width
        )

        # ===================================================================
        # Step 6: Configure global OPES parameters
        # ===================================================================

        # OPES configuration is different from metadynamics
        # Key parameter: BARRIER = highest free energy barrier to cross
        opes_config = hc.OPESConfig(
            barrier=100.0,      # Estimated highest barrier (kJ/mol)
            pace=500,           # Kernel deposition frequency
            temp=TEMPERATURE,   # Temperature (K)
            explore_mode=False, # False = OPES_METAD, True = OPES_METAD_EXPLORE
            biasfactor=None,    # Optional: well-tempered factor
            compression_threshold=1.0  # Kernel compression threshold
        )

        # ===================================================================
        # Step 7: Add output actions
        # ===================================================================

        # Print CV values during simulation
        print_action = hc.PrintAction(
            cvs=[distance_cv],
            stride=100,         # Print every 100 steps
            file="COLVAR"       # Output file
        )

        # ===================================================================
        # Step 8: Create the OPES model
        # ===================================================================

        # Use OPESModel instead of MetaDynamicsModel
        opes_model = hc.OPESModel(
            config=opes_config,
            bias_cvs=[opes_bias],
            actions=[print_action],
            data=data_gen.frames,
            data_idx=-1,                    # Use last frame
            model=ips.MACEMPModel(),        # ML force field
            timestep=TIMESTEP
        )

        # ===================================================================
        # Step 9: Run molecular dynamics with OPES
        # ===================================================================

        md_simulation = ips.ASEMD(
            data=data_gen.frames,
            data_id=-1,
            model=opes_model,
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
    print(f"  - COLVAR: Collective variable trajectory")
    print(f"  - KERNELS: OPES kernels file (instead of HILLS)")
    print(f"  - Trajectory: {md_simulation.nout}/atoms.h5")
    print("\nOPES vs Metadynamics:")
    print("  - OPES adapts the bias based on sampled probability")
    print("  - Often converges faster than traditional metadynamics")
    print("  - Adaptive sigma automatically adjusts kernel width")
    print("  - BARRIER parameter guides exploration efficiency")
    print("\nAnalysis suggestions:")
    print("  1. Plot distance values from COLVAR")
    print("  2. Reconstruct free energy with OPES reweighting:")
    print("     plumed driver --plumed plumed_reweight.dat --ixtc traj.xtc")
    print("  3. Compare convergence speed vs traditional metadynamics")
    print("  4. The FES should show minima at contact and separated states")
    print("  5. EXPLORE mode can be used for broader conformational sampling")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

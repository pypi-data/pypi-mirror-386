import hillclimber as pn
import pytest

def test_distance_cv_corresponding_strategy(small_ethnol_water):
    """Test diagonal/corresponding strategy - pair by index."""
    x1_selector = pn.SMILESSelector(smiles="CCO")
    x2_selector = pn.SMILESSelector(smiles="O")

    distance_cv = pn.DistanceCV(
        x1=pn.VirtualAtom(x1_selector, "com"),
        x2=pn.VirtualAtom(x2_selector, "com"),
        prefix="d12",
        pairwise="diagonal",
    )

    biased_distance_cv = pn.MetadBias(
        cv=distance_cv,
        sigma=0.1,
        grid_min=0.0,
        grid_max=10.0,
        grid_bin=100,
    )

    meta_d_config = pn.MetaDynamicsConfig(
        height=0.5,
        pace=150,
        biasfactor=10.0,
        temp=300.0,
        file="HILLS",
        adaptive="NONE",
        flush=None,
    )

    meta_d_model = pn.MetaDynamicsModel(
        config=meta_d_config,
        data=small_ethnol_water,
        bias_cvs=[biased_distance_cv],
        actions=[pn.PrintAction(cvs=[distance_cv], stride=100)],
        model=None,  # type: ignore
    )

    assert meta_d_model.to_plumed(small_ethnol_water) == [
        "UNITS LENGTH=A TIME=0.010180505671156723 ENERGY=96.48533288249877",
        "d12_x1_0: COM ATOMS=1,2,3,4,5,6,7,8,9",
        "d12_x1_1: COM ATOMS=10,11,12,13,14,15,16,17,18",
        "d12_x2_0: COM ATOMS=19,20,21",
        "d12_x2_1: COM ATOMS=22,23,24",
        "d12_0: DISTANCE ATOMS=d12_x1_0,d12_x2_0",
        "d12_1: DISTANCE ATOMS=d12_x1_1,d12_x2_1",
        "metad: METAD ARG=d12_0,d12_1 HEIGHT=0.5 PACE=150 TEMP=300.0 FILE=HILLS ADAPTIVE=NONE BIASFACTOR=10.0 SIGMA=0.1 GRID_MIN=0.0 GRID_MAX=10.0 GRID_BIN=100",
        "PRINT ARG=d12_0,d12_1 STRIDE=100 FILE=COLVAR",
    ]


def test_distance_cv_first_strategy(small_ethnol_water):
    """Test default FIRST strategy - only first groups."""
    x1_selector = pn.SMILESSelector(smiles="CCO")
    x2_selector = pn.SMILESSelector(smiles="O")

    distance_cv = pn.DistanceCV(
        x1=pn.VirtualAtom(x1_selector[0], "com"),
        x2=pn.VirtualAtom(x2_selector[0], "com"),
        prefix="d12",
    )

    biased_distance_cv = pn.MetadBias(
        cv=distance_cv,
        sigma=0.1,
        grid_min=0.0,
        grid_max=10.0,
        grid_bin=100,
    )

    meta_d_config = pn.MetaDynamicsConfig(
        height=0.5,
        pace=150,
        biasfactor=10.0,
        temp=300.0,
        file="HILLS",
        adaptive="NONE",
        flush=100,
    )

    meta_d_model = pn.MetaDynamicsModel(
        config=meta_d_config,
        data=small_ethnol_water,
        bias_cvs=[biased_distance_cv],
        actions=[pn.PrintAction(cvs=[distance_cv], stride=100)],
        model=None,  # type: ignore
    )

    assert meta_d_model.to_plumed(small_ethnol_water) == [
        "UNITS LENGTH=A TIME=0.010180505671156723 ENERGY=96.48533288249877",
        "d12_x1: COM ATOMS=1,2,3,4,5,6,7,8,9",
        "d12_x2: COM ATOMS=19,20,21",
        "d12: DISTANCE ATOMS=d12_x1,d12_x2",
        "metad: METAD ARG=d12 HEIGHT=0.5 PACE=150 TEMP=300.0 FILE=HILLS ADAPTIVE=NONE BIASFACTOR=10.0 SIGMA=0.1 GRID_MIN=0.0 GRID_MAX=10.0 GRID_BIN=100",
        "PRINT ARG=d12 STRIDE=100 FILE=COLVAR",
        'FLUSH STRIDE=100',
    ]

def test_duplicate_cv_prefix(small_ethnol_water):
    x1_selector = pn.SMILESSelector(smiles="CCO")
    x2_selector = pn.SMILESSelector(smiles="O")

    distance_cv = pn.DistanceCV(
        x1=pn.VirtualAtom(x1_selector[0], "com"),
        x2=pn.VirtualAtom(x2_selector[0], "com"),
        prefix="d12",
    )

    biased_distance_cv = pn.MetadBias(
        cv=distance_cv,
        sigma=0.1,
        grid_min=0.0,
        grid_max=10.0,
        grid_bin=100,
    )

    meta_d_config = pn.MetaDynamicsConfig(
        height=0.5,
        pace=150,
        biasfactor=10.0,
        temp=300.0,
        file="HILLS",
        adaptive="NONE",
    )

    meta_d_model = pn.MetaDynamicsModel(
        config=meta_d_config,
        data=small_ethnol_water,
        bias_cvs=[biased_distance_cv, biased_distance_cv], # duplicate entry
        actions=[],  # PrintCVAction is automatically added
        model=None,  # type: ignore
    )

    with pytest.raises(ValueError, match="Duplicate CV prefix found: d12"):
        meta_d_model.to_plumed(small_ethnol_water)
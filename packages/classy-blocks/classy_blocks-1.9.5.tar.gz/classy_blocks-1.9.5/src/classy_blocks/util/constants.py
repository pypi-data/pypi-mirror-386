import numpy as np

from classy_blocks.cbtyping import DirectionType, OrientType

# data type
DTYPE = np.float64

# geometric tolerance for searching/merging points
TOL = 1e-7
# a small-ish value, named after OpenFOAM's constant
VSMALL = 1e-6
# a big-ish value
VBIG = 1e12

# Block definition:
# a more intuitive and quicker way to set patches,
# according to this sketch: https://www.openfoam.com/documentation/user-guide/blockMesh.php
# the same for all blocks
FACE_MAP: dict[OrientType, tuple[int, int, int, int]] = {
    "bottom": (0, 1, 2, 3),
    "top": (4, 5, 6, 7),
    "left": (4, 0, 3, 7),
    "right": (5, 1, 2, 6),
    "front": (4, 5, 1, 0),
    "back": (7, 6, 2, 3),
}

SIDES_MAP: list[OrientType] = [
    "front",
    "right",
    "back",
    "left",
]

# Connects block axis (direction) and orients
# (read: Direction 0 goes from right to left, etc.
DIRECTION_MAP: dict[DirectionType, tuple[OrientType, OrientType]] = {
    0: ("left", "right"),
    1: ("front", "back"),
    2: ("bottom", "top"),
}

# pairs of corner indexes along axes
AXIS_PAIRS = (
    ((0, 1), (3, 2), (7, 6), (4, 5)),  # x
    ((0, 3), (1, 2), (5, 6), (4, 7)),  # y
    ((0, 4), (1, 5), (2, 6), (3, 7)),  # z
)

# pairs of corner indexes that define edges (and not diagonals)
EDGE_PAIRS = list(AXIS_PAIRS[0]) + list(AXIS_PAIRS[1]) + list(AXIS_PAIRS[2])


# number formatting
def vector_format(vector) -> str:
    """Output for point/vertex definitions"""
    # ACHTUNG, keep about the same order of magnitude than TOL
    return f"({vector[0]:.8f} {vector[1]:.8f} {vector[2]:.8f})"


MESH_HEADER = (
    "/*---------------------------------------------------------------------------*\\\n"
    "| =========                |                                                 |\n"
    "| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |\n"
    "|  \\    /   O peration     | Script: {script:<40s}|\n"
    "|   \\  /    A nd           | Time: {timestamp:<42s}|\n"
    "|    \\/     M anipulation  |                                                 |\n"
    "\\*---------------------------------------------------------------------------*/\n"
    "FoamFile\n"
    "{{\n"
    "    version     2.0;\n"
    "    format      ascii;\n"
    "    class       dictionary;\n"
    "    object      blockMeshDict;\n"
    "}}\n"
    "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n\n"
)

MESH_FOOTER = (
    "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n"
    "// Created with classy_blocks: https://github.com/damogranlabs/classy_blocks //\n"
    "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n"
)

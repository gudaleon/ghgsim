"""Holos crop residue N: same published IPCC 2019 Eq 11.6 / 11.7. No holos_as_coded fork."""

from ghgsim.modules.ipcc2019.crop_residue import IPCC2019CropResidue


class HolosCropResidue(IPCC2019CropResidue):
    """Published IPCC residue equations; Holos methodology cites IPCC Chapter 11."""

    id = "holos.crop_residue"
    version = "1.0.0"

"""Main module."""

import logging
import os
import pathlib
import sys

from fw_utils import AnyPath
from monai.config.type_definitions import PathLike
from monai.transforms import (
    Compose,
    LoadImage,
    LoadImaged,
    Randomizable,
    SaveImage,
    SaveImaged,
)

from fw_gear_monai_transforms.utils import _load_transform

log = logging.getLogger(__name__)


def validate_transform(transform: Compose):
    """Returns the validation errors found in the transform."""
    errs = []
    if len(transform.transforms) == 0:
        errs.append("Transform is empty")
        return errs
    if not isinstance(transform.transforms[0], (LoadImage, LoadImaged)):
        errs.append("Transform first item must be a LoadImaged")
    if not isinstance(transform.transforms[-1], (SaveImage, SaveImaged)):
        errs.append("Transform last item must be a SaveImaged")
    return errs


def get_transform(transform: Compose, n: int):
    """Returns the n-th component of the Compose transformation."""
    return transform.transforms[n]


def update_transforms_saver(transform: Compose, output_dir: PathLike = None):
    """Returns the transform with an updated SaveImage[d] step (if present)."""
    if not hasattr(transform, "transforms") or not transform.transforms:
        return transform

    last = get_transform(transform, -1)

    if isinstance(last, SaveImaged):
        # SaveImaged wraps a SaveImage instance at .saver
        last.saver.folder_layout.output_dir = output_dir

    elif isinstance(last, SaveImage):
        # SaveImage *is* the saver
        last.folder_layout.output_dir = output_dir

    return transform


def is_rand(transform: Compose):
    """Returns True if type is Randomizable, False otherwise."""
    return isinstance(transform, Randomizable)


def remove_file_extensions(filename: str):
    """Remove any file extension from filename."""
    filename = os.path.basename(filename)
    suffixes = pathlib.Path(filename).suffixes

    for x in suffixes:
        filename = filename.replace(x, "")

    return filename


def rename_transforms(transform: Compose, input_file):
    """Rename transformed output."""
    filename = os.path.basename(input_file)
    new_name = remove_file_extensions(filename)

    if isinstance(get_transform(transform, -1), SaveImaged):
        transform.transforms[-1].saver.folder_layout.postfix = new_name

    if isinstance(get_transform(transform, -1), SaveImage):
        transform.transforms[-1].folder_layout.postfix = new_name

    return transform


def check_rand_transformation(transform: Compose):
    """Returns true if one of the Compose transformation is Randomizable ."""
    conditions = []
    for idx in range(len(transform.transforms)):
        tr = get_transform(transform, idx)
        conditions.append(is_rand(tr))

    return any(conditions)


def apply_transform(
    input_file: AnyPath,
    input_mod_path: AnyPath,
    output_dir: AnyPath = None,
    iter_num: int = 1,
):
    """Run transforms on ``input_file`` and save output to ``output_dir``.

    Args:
        input_file (AnyPath): Path to input imaging file.
        input_mod_path (AnyPath): Path to where the module defining the transforms is
            located.
        output_dir (AnyPath): Root folder path where to save the output file.
        iter_num (int): number of iteractions in case of stochastic Transformations.
    """
    mod = _load_transform(input_mod_path)
    transform = mod.transform
    if errs := validate_transform(transform):
        log.error(errs)
        sys.exit(1)
    transform = update_transforms_saver(transform, output_dir=output_dir)

    if check_rand_transformation(transform) is False:
        if isinstance(get_transform(transform, 0), LoadImaged):
            transform({"img": input_file})
        if isinstance(get_transform(transform, 0), LoadImage):
            transform(input_file)
        if iter_num == 1:
            pass
        elif iter_num > 1:
            log.warning(
                "Number of iterations greater than 1 but Transform is not Randomizable. Transformation will be "
                "applied as "
                "a single iteration. "
            )
    elif check_rand_transformation(transform) is True and iter_num > 1:
        transform = rename_transforms(transform, input_file)
        for i in range(iter_num):
            if isinstance(get_transform(transform, 0), LoadImaged):
                transform({"img": input_file})
            if isinstance(get_transform(transform, 0), LoadImage):
                transform(input_file)

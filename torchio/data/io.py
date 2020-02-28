from pathlib import Path
from typing import Union, Tuple, TypeVar
import torch
import numpy as np
import nibabel as nib
import SimpleITK as sitk
from .. import TypePath, TypeData
from ..utils import nib_to_sitk, sitk_to_nib


def read_image(
        path: TypePath,
        itk_first: bool = False,
        ) -> Tuple[torch.Tensor, np.ndarray]:
    if itk_first:
        try:
            result = _read_sitk(path)
        except RuntimeError:  # try with NiBabel
            result = _read_nibabel(path)
    else:
        try:
            result = _read_nibabel(path)
        except nib.loadsave.ImageFileError:  # try with ITK
            result = _read_sitk(path)
    return result


def _read_nibabel(path: TypePath) -> Tuple[torch.Tensor, np.ndarray]:
    nii = nib.load(str(path), mmap=False)
    data = nii.get_fdata(dtype=np.float32)
    tensor = torch.from_numpy(data)
    affine = nii.affine
    return tensor, affine


def _read_sitk(path: TypePath) -> Tuple[torch.Tensor, np.ndarray]:
    image = sitk.ReadImage(str(path))
    data, affine = sitk_to_nib(image)
    if data.dtype != np.float32:
        data = data.astype(np.float32)
    tensor = torch.from_numpy(data)
    return tensor, affine


def write_image(
        tensor: torch.Tensor,
        affine: TypeData,
        path: TypePath,
        itk_first: bool = False,
        ) -> None:
    if itk_first:
        try:
            _write_sitk(tensor, affine, path)
        except RuntimeError:  # try with NiBabel
            _write_nibabel(tensor, affine, path)
    else:
        try:
            _write_nibabel(tensor, affine, path)
        except nib.loadsave.ImageFileError:  # try with ITK
            _write_sitk(tensor, affine, path)


def _write_nibabel(
        tensor: torch.Tensor,
        affine: TypeData,
        path: TypePath,
        ) -> None:
    """
    Expects a path with an extension that can be used by nibabel.save
    to write a NIfTI-1 image, such as '.nii.gz' or '.img'
    """
    nii = nib.Nifti1Image(tensor.numpy(), affine)
    nii.header['qform_code'] = 1
    nii.header['sform_code'] = 0
    nii.to_filename(str(path))


def _write_sitk(
        tensor: torch.Tensor,
        affine: TypeData,
        path: TypePath,
        ) -> None:
    image = nib_to_sitk(tensor, affine)
    sitk.WriteImage(image, str(path))

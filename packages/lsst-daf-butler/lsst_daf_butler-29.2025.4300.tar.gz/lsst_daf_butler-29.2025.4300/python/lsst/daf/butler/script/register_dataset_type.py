# This file is part of daf_butler.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This software is dual licensed under the GNU General Public License and also
# under a 3-clause BSD license. Recipients may choose which of these licenses
# to use; please see the files gpl-3.0.txt and/or bsd_license.txt,
# respectively.  If you choose the GPL option then the following text applies
# (but note that there is still no warranty even if you opt for BSD instead):
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import annotations

__all__ = ("register_dataset_type",)

from .._butler import Butler
from .._dataset_type import DatasetType


def register_dataset_type(
    repo: str,
    dataset_type: str,
    storage_class: str,
    dimensions: tuple[str, ...],
    is_calibration: bool = False,
) -> bool:
    """Register a new dataset type.

    Parameters
    ----------
    repo : `str`
        URI string of the Butler repo to use.
    dataset_type : `str`
        The name of the new dataset type.
    storage_class : `str`
        The name of the storage class associated with this dataset type.
    dimensions : `tuple` [`str`]
        Dimensions associated with this dataset type. Can be empty.
    is_calibration : `bool`
        If `True` this dataset type may be included in calibration
        collections.

    Returns
    -------
    inserted : `bool`
        `True` if the dataset type was added; `False` if it was already
        there.

    Raises
    ------
    ValueError
        Raised if an attempt is made to register a component dataset type.
        Component dataset types are not real dataset types and so can not
        be created by this command. They are always derived from the composite
        dataset type.
    """
    butler = Butler.from_config(repo, writeable=True, without_datastore=True)

    _, component = DatasetType.splitDatasetTypeName(dataset_type)
    if component:
        raise ValueError("Component dataset types are created automatically when the composite is created.")

    datasetType = DatasetType(
        dataset_type,
        butler.dimensions.conform(dimensions),
        storage_class,
        parentStorageClass=None,
        isCalibration=is_calibration,
        universe=butler.dimensions,
    )

    return butler.registry.registerDatasetType(datasetType)

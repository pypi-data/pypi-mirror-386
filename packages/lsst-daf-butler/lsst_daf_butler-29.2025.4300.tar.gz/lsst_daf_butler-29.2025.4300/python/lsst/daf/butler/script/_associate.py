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

import itertools
from collections.abc import Iterable

from .._butler import Butler
from .._collection_type import CollectionType
from .queryDatasets import QueryDatasets


def associate(
    repo: str,
    collection: str,
    dataset_type: Iterable[str],
    collections: Iterable[str],
    where: str,
    find_first: bool,
    limit: int,
) -> None:
    """Add existing datasets to a CHAINED collection.

    Parameters
    ----------
    repo : `str`
        The Butler repository location.
    collection : `str`
        Name of the tagged collection to place datasets.
    dataset_type : `~collections.abc.Iterable` of `str`
        Names of dataset types.
    collections : `~collections.abc.Iterable`
        Collections to use in the query.
    where : `str`
        Query string.
    find_first : `bool`
        Whether to find the first match or not.
    limit : `int`
        Limit the number of results to be returned. A value of 0 means
        unlimited. A negative value is used to specify a cap where a warning
        is issued if that cap is hit.
    """
    butler = Butler.from_config(repo, writeable=True, without_datastore=True)

    butler.collections.register(collection, CollectionType.TAGGED)

    results = QueryDatasets(
        butler=butler,
        glob=dataset_type,
        collections=collections,
        where=where,
        find_first=find_first,
        limit=limit,
        order_by=(),
        show_uri=False,
        repo=None,
    )

    butler.registry.associate(collection, itertools.chain(*results.getDatasets()))

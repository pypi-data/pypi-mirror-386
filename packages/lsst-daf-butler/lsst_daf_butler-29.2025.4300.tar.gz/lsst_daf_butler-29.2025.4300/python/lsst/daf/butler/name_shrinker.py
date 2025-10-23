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

__all__ = ["NameShrinker"]

import hashlib
from collections.abc import Iterator


class NameShrinker:
    """A utility class for `Database` implementations that need a nontrivial
    implementation of `Database.shrinkDatabaseEntityName` and
    `Database.expandDatabaseEntityName`.

    Parameters
    ----------
    maxLength : `int`
        The maximum number of characters in a database entity name.
    hashSize : `int`, optional
        The size of the hash (in bytes) to use for the tail of the shortened
        name.  The hash is written in hexadecimal and prefixed with a "_", so
        the number of characters the hash occupies is ``hashSize*2 + 1``, and
        hence the number of characters preserved from the beginning of the
        original name is ``maxLength - hashSize*2 - 1``.
    """

    def __init__(self, maxLength: int, hashSize: int = 4):
        self.maxLength = maxLength
        self.hashSize = hashSize
        self._by_shrunk: dict[str, str] = {}
        self._by_original: dict[str, str] = {}

    def shrink(self, original: str) -> str:
        """Shrink a name and remember the mapping between the original name and
        its shrunk form.

        Parameters
        ----------
        original : `str`
            The original name.

        Returns
        -------
        shrunk : `str`
            The shrunk form.
        """
        if len(original) <= self.maxLength:
            return original
        if original in self._by_original:
            return self._by_original[original]
        message = hashlib.blake2b(digest_size=self.hashSize)
        message.update(original.encode("ascii"))
        trunc = self.maxLength - 2 * self.hashSize - 1
        shrunk = f"{original[:trunc]}_{message.digest().hex()}"
        assert len(shrunk) == self.maxLength
        self._by_shrunk[shrunk] = original
        self._by_original[original] = shrunk
        return shrunk

    def expand(self, shrunk: str) -> str:
        """Return the original name that was passed to a previous call to
        `shrink`.

        Parameters
        ----------
        shrunk : `str`
            The shrunk form.

        Returns
        -------
        expanded : `str`
            The expanded form. If the given name was not passed to `shrink`
            or was not modified by it, it is returned unmodified.
        """
        return self._by_shrunk.get(shrunk, shrunk)

    def __iter__(self) -> Iterator[tuple[str, str]]:
        return iter(self._by_original.items())

    def __len__(self) -> int:
        return len(self._by_original)

    def update(self, other: NameShrinker) -> None:
        """Add all original <-> shrunk mappings from ``other`` to ``self``.

        Parameters
        ----------
        other : `NameShrinker`
            Object to extract name mappings from.
        """
        self._by_original.update(other._by_original)
        self._by_shrunk.update(other._by_shrunk)

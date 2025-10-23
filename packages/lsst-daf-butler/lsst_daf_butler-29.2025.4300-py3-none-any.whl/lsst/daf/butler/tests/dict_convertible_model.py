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

__all__ = ()

from collections.abc import Mapping

from pydantic import BaseModel, Field


class DictConvertibleModel(BaseModel):
    """A Pydantic model to/from dict conversion in which the `dict`
    representation is intentionally different from Pydantic's own `dict`
    conversions.
    """

    content: dict[str, float | str] = Field(default_factory=dict)
    """Content of the logical dict that this object converts to (`dict`).
    """

    extra: str = Field(default="")
    """Extra content that is not included in the dict representation (`str`).
    """

    @classmethod
    def from_dict(cls, content: Mapping[str, str], extra: str = "from_dict") -> DictConvertibleModel:
        """Construct an instance from a `dict`.

        Parameters
        ----------
        content : `~collections.abc.Mapping`
            Content of the logical dict that this object converts to.
        extra : `str`, optional
            Extra content that is not included in the dict representation.

        Returns
        -------
        model : `DictConvertibleModel`
            New model.
        """
        return cls(content=dict(content), extra=extra)

    def to_dict(self) -> dict[str, float | str]:
        """Convert the model to a dictionary.

        Returns
        -------
        content : `dict`
            Copy of ``self.content``.
        """
        return self.content.copy()

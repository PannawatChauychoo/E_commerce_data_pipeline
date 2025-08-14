# serialization.py
from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from typing import Any, ClassVar, Dict, List

import numpy as np
from scipy.stats import gaussian_kde

"""
Converting the classes into dictionaries
"""


class Serialization:
    """
    Mix-in that flattens/scaffolds gaussian_kde attrs so pyarrow can persist them.
    """

    _kde_attrs: ClassVar[List[str]] = []  # override in subclass
    _dict_attrs: ClassVar[List[str]] = []

    # any attribute you do *not* want to save verbatim
    _EXCLUDE = {"model"}

    def _coerce(self, v):
        """
        Return something that `json.dumps` can handle.
        Possible attribute types: str, int, float, dict, gaussian_kde, lists, datetime
        """

        # primitives already OK
        if isinstance(v, (int, float, str, bool)) or v is None:
            return v

        # dictionaries (stringify key, recurse on value)
        if isinstance(v, dict):
            return {str(k): self._coerce(val) for k, val in v.items()}

        # lists/tuples
        if isinstance(v, (list, tuple)):
            return [self._coerce(x) for x in v]

        # datetime
        if isinstance(v, (dt.datetime, dt.date, dt.time)):
            return v.isoformat()

        print(f"{v} is an unaccounted type, {type(v)}")
        raise AttributeError

    @staticmethod
    def uncoerce(v):
        # datetime first
        if isinstance(v, str):
            try:
                v = dt.datetime.fromisoformat(v)
            except ValueError:
                pass  # not an ISO date → keep string

        if isinstance(v, (list, tuple)):
            return [Serialization.uncoerce(x) for x in v]

        if isinstance(v, dict):
            return {k: Serialization.uncoerce(x) for k, x in v.items()}

        return v

    def to_row(self) -> dict[str, Any]:
        """
        Converting an agent class into dictionary for parquet/json files
        """
        row: dict[str, Any] = {"type": self.__class__.__name__}

        # regular attributes
        for k, v in self.__dict__.items():
            if k in self._EXCLUDE or k in self._kde_attrs:
                continue
            row[k] = self._coerce(v=v)

        # flatten KDEs
        for attr in self._kde_attrs:
            kde = getattr(self, attr, None)
            if kde is None:
                continue
            row[f"{attr}_data"] = np.asarray(kde.dataset, dtype=np.float64).tolist()
            row[f"{attr}_bw"] = float(kde.factor)

        return row

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Serialization":
        """
        Loading the row into its respective classes using only plain dicts.
        """
        META = {"type"}

        base: Dict[str, Any] = {
            k: cls.uncoerce(v)
            for k, v in row.items()
            if not (k.endswith("_data") or k.endswith("_bw") or k in META)
        }

        # Construct the object
        try:
            obj = cls(**base)
        except TypeError:
            # fallback: recreate the agent instance
            obj = cls.__new__(cls)
            for k, v in base.items():
                setattr(obj, k, v)

        # Ensure dict-attributes are plain dicts
        for attr in getattr(cls, "_dict_attrs", []):
            current = getattr(obj, attr, None)
            if current is None:
                setattr(obj, attr, {})
            elif isinstance(current, dict):
                # already a plain dict — keep as-is
                pass
            elif isinstance(current, Mapping):
                # convert mapping-like (e.g., was defaultdict before) to dict
                setattr(obj, attr, dict(current))
            else:
                # unexpected type — coerce to empty dict
                setattr(obj, attr, {})

        # Rebuild KDE attributes
        for attr in getattr(cls, "_kde_attrs", []):
            data_key = f"{attr}_data"
            bw_key = f"{attr}_bw"
            if data_key in row and bw_key in row:
                data = np.asarray(row[data_key], dtype=np.float64)
                bw = row[bw_key]
                setattr(obj, attr, gaussian_kde(data, bw_method=bw))

        return obj

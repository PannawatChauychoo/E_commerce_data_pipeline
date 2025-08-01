# serialization.py
from __future__ import annotations
from typing import ClassVar, Dict, Any, List
import numpy as np
from scipy.stats import gaussian_kde
from collections import defaultdict
import datetime as dt

"""
Converting the classes into dictionaries
"""

class ParquetSerialization:
    """
    Mix-in that flattens/scaffolds gaussian_kde attrs so pyarrow can persist them.
    """
    _kde_attrs: ClassVar[List[str]] = []   # override in subclass
    _dict_attrs: ClassVar[List[str]] = []  
    
    # any attribute you do *not* want to save verbatim
    _EXCLUDE = {"model"}

    
    def _coerce(self, v):
        """
        Return something that `json.dumps` can handle.
        Possible attribute types: str, int, float, dict, kde gaussian, lists, datetime
        """
        
        # primitives already OK ─────────────────────────────
        if isinstance(v, (int, float, str, bool)) or v is None:
            return v

        # dictionaries  (stringify key, recurse on value)
        if isinstance(v, (dict, defaultdict)):
            return {str(k): self._coerce(val) for k, val in v.items()}

        # lists/tuples
        if isinstance(v, (list,tuple)):
            return [self._coerce(x) for x in v]
        
        #datetime
        if isinstance(v, (dt.datetime, dt.date, dt.time)):  
            return v.isoformat()

        print(f'{v} is an unaccounted type, {type(v)}')
        raise AttributeError
    
    @staticmethod
    def uncoerce(v):
        # datetime first
        if isinstance(v, str):
            try:
                v = dt.datetime.fromisoformat(v)
            except ValueError:
                pass                   # not an ISO date → keep string
        
        if isinstance(v, (list, tuple)):
            return [ParquetSerialization.uncoerce(x) for x in v]

        if isinstance(v, dict):
            return {k: ParquetSerialization.uncoerce(x) for k, x in v.items()}
        
        return v
        


    def to_row(self) -> dict[str, Any]:
        """
        Converting an agent class into dictionary for parquet files
        """
        row: dict[str, Any] = {"type": self.__class__.__name__}

        # regular attributes
        for k, v in self.__dict__.items():
            if k in self._EXCLUDE or k in self._kde_attrs:
                continue
            row[k] = self._coerce(v = v)
        
        # flatten KDEs
        for attr in self._kde_attrs:
            kde = getattr(self, attr, None)
            if kde is None:
                continue
            row[f"{attr}_data"] = np.asarray(kde.dataset, dtype=np.float64).tolist()
            row[f"{attr}_bw"]   = float(kde.factor)
        
        return row
    
    
    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "ParquetSerialization":
        """
        Loading the row into its respective classes
        """
        META = {"type"}
       
        base: Dict[str, Any] = {
            k: cls.uncoerce(v) for k, v in row.items()
            if not (k.endswith("_data") or k.endswith("_bw") or k in META)
        }
        
        # Load all str/int/float/dict attributes
        try:
            obj = cls(**base)
        except TypeError:
            # fallback: recreate the agent instance
            obj = cls.__new__(cls)
            for k, v in base.items():
                setattr(obj, k, v)
        
        # Load dictionaries
        for attr in cls._dict_attrs:
            current = getattr(obj, attr, None)
            if not isinstance(current, defaultdict):
                setattr(obj, attr, defaultdict(list, current or {}))

        # Load KDE attributes
        for attr in cls._kde_attrs:
            data_key = f"{attr}_data"
            bw_key   = f"{attr}_bw"
            if data_key in row and bw_key in row:
                data = np.asarray(row[data_key], dtype=np.float64)
                bw   = row[bw_key]
                setattr(obj, attr, gaussian_kde(data, bw_method=bw))

        return obj



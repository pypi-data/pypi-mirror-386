#!/usr/bin/env python3

# 2025 (c) Micha Johannes Birklbauer
# https://github.com/michabirklbauer/
# micha.birklbauer@gmail.com

from __future__ import annotations

import warnings
import pandas as pd

from ..constants import AMINO_ACIDS

from typing import List
from typing import Dict
from typing import Any


def __serialize_pandas_series(
    pds: pd.Series, nan_values: List[str] = ["", "nan", "null", "none"]
) -> Dict[str, Any]:
    r"""Serialize a pandas Series to a python native dictionary with native types.

    Parameters
    ----------
    pds : pd.Series
        The pandas Series to serialize.
    nan_values : list of str, default = ["", "nan", "null", "none"]
        List of strings that should be considered as missing values.

    Returns
    -------
    dict of str, any
        The serialized pandas Series.

    Notes
    -----
    This function should not be called directly, it is called from all parsers to serialize input.
    """
    serialized_pds = dict()
    for key in pds.index.tolist():
        val = None
        raw_val = pds[key]
        if isinstance(raw_val, int):
            val = int(raw_val)
        elif isinstance(raw_val, float):
            if not pd.isna(raw_val):  # pyright: ignore[reportGeneralTypeIssues]
                val = float(raw_val)
        else:
            if not pd.isna(raw_val):  # pyright: ignore[reportGeneralTypeIssues]
                str_val = str(val)
                if str_val.lower().strip() not in nan_values:
                    val = str_val
        serialized_pds[key] = val
    return serialized_pds


def format_sequence(
    sequence: str, remove_non_aa: bool = True, remove_lower: bool = True
) -> str:
    r"""Formats the given amino acid sequence into common represenation.

    The given amino acid sequence is re-formatted by converting all amino acids to upper case and optionally removing non-encoding and
    lower case characters.

    Parameters
    ----------
    sequence : str
        The amino acid sequence that should be formatted. Post-translational-modifications can be included in lower case but will
        be removed.
    remove_non_aa : bool, default = True
        Whether or not to remove characters that do not encode amino acids.
    remove_lower : bool, default = True
        Whether or not to remove lower case characters, this should be true if the amino acid sequence encodes post-translational-modifications
        in lower case.

    Returns
    -------
    str
        The formatted sequence.

    Examples
    --------
    >>> from pyXLMS.parser_util import format_sequence
    >>> format_sequence("PEP[K]TIDE")
    'PEPKTIDE'

    >>> from pyXLMS.parser_util import format_sequence
    >>> format_sequence("PEPKdssoTIDE")
    'PEPKTIDE'

    >>> from pyXLMS.parser_util import format_sequence
    >>> format_sequence("peptide", remove_lower=False)
    'PEPTIDE'
    """
    fmt_seq = ""
    for aa in str(sequence).strip():
        if aa.isupper():
            if aa not in AMINO_ACIDS:
                if remove_non_aa:
                    continue
                else:
                    warnings.warn(
                        f"The sequence {sequence} contains non-valid characters.",
                        RuntimeWarning,
                    )
            fmt_seq += aa
        elif remove_lower:
            continue
        else:
            if aa.upper() not in AMINO_ACIDS:
                if remove_non_aa:
                    continue
                else:
                    warnings.warn(
                        f"The sequence {sequence} contains non-valid characters.",
                        RuntimeWarning,
                    )
            fmt_seq += aa.upper()
    return fmt_seq


def get_bool_from_value(value: Any) -> bool:
    r"""Parse a bool value from the given input.

    Tries to parse a boolean value from the given input object. If the object is of instance ``bool`` it will return the object, if it is of
    instance ``int`` it will return ``True`` if the object is ``1`` or ``False`` if the object is ``0``, any other number will raise a
    ``ValueError``. If the object is of instance ``str`` it will return ``True`` if the lower case version contains the letter ``t`` and
    otherwise ``False``. If the object is none of these types a ``ValueError`` will be raised.

    Parameters
    ----------
    value : any
        The value to parse from.

    Returns
    -------
    bool
        The parsed boolean value.

    Raises
    ------
    ValueError
        If the object could not be parsed to bool.

    Examples
    --------
    >>> from pyXLMS.parser_util import get_bool_from_value
    >>> get_bool_from_value(0)
    False

    >>> from pyXLMS.parser_util import get_bool_from_value
    >>> get_bool_from_value("T")
    True
    """
    if isinstance(value, bool):
        return value
    elif isinstance(value, int):
        if value in [0, 1]:
            return bool(value)
        else:
            raise ValueError(f"Cannot parse bool value from the given input {value}.")
    elif isinstance(value, str):
        return "t" in value.lower()
    else:
        raise ValueError(f"Cannot parse bool value from the given input {value}.")
    return False

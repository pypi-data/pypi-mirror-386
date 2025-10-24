# -*- coding: utf-8 -*-
#!/usr/bin/env python3

# Author: Luis Bonah
# Description : SPFIT/SPCAT wrapping library


import os
import io
import subprocess
import tempfile
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor

## Constants
SENTINEL = np.iinfo(np.int64).min
"""int: Value representing an empyt quantum number.

The value is chosen to be np.iinfo(np.int64).min which allows to use
quantum numbers from -9223372036854775807 to 9223372036854775807.

"""

ZEROTHRESHOLD = 1e-30
"""float: Upper bound for magnitude of values to count as 0.

This is needed, as SPFIT/SPCAT use very small values to indicate a 0
rather than using an actual 0.

"""

ZERO = 1e-37
"""float: Value used by the program to represent 0.

This is needed, as SPFIT/SPCAT use very small values to indicate a 0
rather than using an actual 0.

"""

WN_TO_MHZ = 299792458e-4
"""float: Conversion factor from wavenumbers to MHz."""

SPFIT_PATH = os.environ.get("PYCKETT_SPFIT_PATH")
"""str or None: Path to SPFIT program."""

SPCAT_PATH = os.environ.get("PYCKETT_SPCAT_PATH")
"""str or None: Path to SPCAT program."""

QUANTA = 6
"""bool or None: If 10 quanta format should be used."""


def qnlabels_from_quanta(n=6):
    """Create the qnlabels for n quanta.

    Parameters
    ----------
    n: int
        Number of quanta

    Returns
    -------
    dict
        List holding the quantum number labels for n quanta.
    """

    n = max(6, n)
    return [f"qn{ul}{i+1}" for ul in ("u", "l") for i in range(n)]


QNLABELS = qnlabels_from_quanta()
"""list of str: Labels used for the quantum numbers of transitions."""


def qnlabels_energy_from_quanta(n=6):
    """Create the qnlabels for energy levels for n quanta.

    Parameters
    ----------
    n: int
        Number of quanta

    Returns
    -------
    dict
        List holding the quantum number labels for energies for n quanta.
    """

    n = max(6, n)
    return [f"qn{i+1}" for i in range(n)]


QNLABELS_ENERGY = qnlabels_energy_from_quanta()
"""list of str: Labels used for the quantum numbers of energy levels."""


class pickett_int(np.int64):
    """Integer type that can convert Pickett specific notation."""

    def __new__(cls, value):
        if type(value) is np.int64:
            return value

        value = value.strip()
        if not value:
            return SENTINEL

        init_char = value[0]
        if init_char.isnumeric() or init_char == "-":
            return np.int64(value)

        elif init_char.isalpha():
            init_char_ord = ord(init_char)
            if 97 <= init_char_ord <= 122:
                return np.int64(str(96 - ord(init_char)) + value[1:])
            elif 65 <= init_char_ord <= 90:
                return np.int64(str(ord(init_char) - 55) + value[1:])
            else:
                raise ValueError(f"Could not convert '{value}' to integer.")

        # Special case for ERHAM *.cat files
        # ERHAM writes ** for quantum numbers higher than 99
        elif all([x == "*" for x in value]):
            return np.int64(99)


def cat_dtypes_from_quanta(n=6):
    """
    Create a dtype dict for a *.cat file with n quanta.

    Parameters
    ----------
    n: int
        Number of quanta

    Returns
    -------
    dict
        Dictionary holding the *.cat dtypes.
    """

    n = max(6, n)
    dtype_dict = {
        "x": np.float64,
        "error": np.float64,
        "y": np.float64,
        "degfreed": np.int8,
        "elower": np.float64,
        "usd": pickett_int,
        "tag": np.int32,
        "qnfmt": np.int16,
        **{f"qn{ul}{i+1}": pickett_int for ul in ("u", "l") for i in range(n)},
    }
    return dtype_dict


cat_dtypes = cat_dtypes_from_quanta()
"""dict: The data types of the *.cat format."""


def cat_widths_from_quanta(n=6):
    """Create a widhts dict for a *.cat file with n quanta.

    Parameters
    ----------
    n: int
        Number of quanta

    Returns
    -------
    dict
        Dictionary holding the *.cat widths.
    """

    n = max(6, n)
    width_dict = {
        "x": 13,
        "error": 8,
        "y": 8,
        "degfreed": 2,
        "elower": 10,
        "usd": 3,
        "tag": 7,
        "qnfmt": 4,
        **{f"qn{ul}{i+1}": 2 for ul in ("u", "l") for i in range(n)},
    }
    return width_dict


cat_widths = cat_widths_from_quanta()
"""dict: The widths of the *.cat format."""


def lin_dtypes_from_quanta(n=6):
    """Create a dtype dict for a *.lin file with n quanta.

    Parameters
    ----------
    n: int
        Number of quanta

    Returns
    -------
    dict
        Dictionary holding the *.lin dtypes.
    """

    n = max(6, n)
    dtype_dict = {
        **{f"qn{ul}{i+1}": pickett_int for ul in ("u", "l") for i in range(n)},
        "x": np.float64,
        "error": np.float64,
        "weight": np.float64,
        "comment": str,
    }
    return dtype_dict


lin_dtypes = lin_dtypes_from_quanta()
"""dict: The data types of the *.lin format."""


def egy_dtypes_from_quanta(n=6):
    """Create a dtype dict for a *.egy file with n quanta.

    Parameters
    ----------
    n: int
        Number of quanta

    Returns
    -------
    dict
        Dictionary holding the *.egy dtypes.
    """

    n = max(6, n)
    dtype_dict = {
        "iblk": np.int64,
        "indx": np.int64,
        "egy": np.float64,
        "err": np.float64,
        "pmix": np.float64,
        "we": np.int64,
        ":": str,
        **{f"qn{i+1}": pickett_int for i in range(n)},
    }
    return dtype_dict


egy_dtypes = egy_dtypes_from_quanta()
"""dict: The data types of the *.egy format."""


def egy_widths_from_quanta(n=6):
    """Create a widths dict for a *.egy file with n quanta.

    Parameters
    ----------
    n: int
        Number of quanta

    Returns
    -------
    dict
        Dictionary holding the *.egy widths.
    """

    n = max(6, n)
    width_dict = {
        "iblk": 6,
        "indx": 5,
        "egy": 18,
        "err": 18,
        "pmix": 11,
        "we": 5,
        ":": 1,
        **{f"qn{i+1}": 3 for i in range(n)},
    }
    return width_dict


egy_widths = egy_widths_from_quanta()
"""dict: The widths of the *.egy format."""


# IS1,IS2,JQ,NQ,J,NN,FREQ,BLE,ER
erham_dtypes = {
    "is1": np.int64,
    "is2": np.int64,
    "qnu1": np.int64,
    "tauu": np.int64,
    "qnl1": np.int64,
    "taul": np.int64,
    "x": np.float64,
    "weight": np.float64,
    "error": np.float64,
    "comment": str,
}
"""dict: The data types of ERHAM output files."""

# If NPAR and NLINE are too large it causes problems with spfit and spcat compiled for MacOs
# If NPAR and NLINE should be set bigger, this can be done safely with scientific notation
PARUPDATE = {
    "NPAR": 999999,
    "NLINE": 999999,
    "NITR": 20,
    "THRESH": 0,
}
"""dict: Parameters of the *.par file that should be updated before fitting a finalized fit."""


# Helper functions
def str_to_stream(string):
    """Convert string to stream.

    Parameters
    ----------
    string: str
        The string to be converted.

    Returns
    -------
    io.StringIO
        Stream of string.

    """
    return io.StringIO(string)


def format_(value, formatspecifier):
    """Format value to the appropriate SPFIT/SPCAT format.

    Parameters
    ----------
    value: number
        Value to be formatted.
    formatspecifier: str
        Format to be used.

    Returns
    -------
    str
        Formatted string of value.
    """

    if formatspecifier.endswith("p"):
        totallength = int(formatspecifier[:-1])

        value = int(value)
        sign = np.sign(value)
        quotient, modulo = divmod(abs(value), 10 ** (totallength - 1))
        quotient *= sign

        if quotient >= 36 or quotient <= -27:
            return "*" * totallength

        if quotient == 0:
            quotient = "-" if sign == -1 else " "
        elif quotient > 9:
            quotient = chr(55 + quotient)
        elif quotient < 0:
            quotient = chr(96 - quotient)

        quotient = f"{{:{totallength-1}}}".format(quotient)
        return f"{quotient}{modulo}"
        
    else:
        if formatspecifier.endswith("d"):
            totallength = int(formatspecifier[:-1])
        else:
            totallength = int(formatspecifier[:-1].split(".")[0])
        tmp = f"{{:{formatspecifier}}}".format(value)

        if len(tmp) > totallength:
            return "*" * totallength
        else:
            return tmp


def get_active_qns(df, quanta=None):
    """Return active quantum numbers.

    Parameters
    ----------
    df: dataframe
        Dataframe representing *.lin or *.cat file.
    quanta: int or None
        The number of used quanta. None means use global setting.

    Returns
    -------
    dict
        Dictionary with the quantum numbers as keys and their activenesses as the values.
    """

    quanta = max(6, quanta or QUANTA)

    if not len(df):
        raise Exception(
            "You are trying to get the active quantum numbers of an empty dataframe."
        )

    qns = {f"qn{ul}{i+1}": True for ul in ("u", "l") for i in range(quanta)}
    for qn in qns.keys():
        unique_values = df[qn].unique()
        if len(unique_values) == 1 and unique_values[0] == SENTINEL:
            qns[qn] = False

    return qns


def get_vib_digits(par):
    """Return number of vibrational states digits."""
    vib_digits = int(np.log10(abs(par["NVIB"]))) + 1
    return vib_digits


def get_all_states(vib_digits):
    """Return the vibrational state code that corresponds to all states."""
    all_states = 10 ** (vib_digits) - 1
    return all_states


def get_par_digits(vib_digits):
    """Return the digits for the parameter coding."""
    return {
        "v1": vib_digits,
        "v2": vib_digits,
        "NSQ": 1,
        "KSQ": 1,
        "TYP": 2,
        "NS": 1,
        "I1": 1,
        "I2": 1,
        "FF": 2,
        "EX": 1,
    }


def parse_fit_result(message, var_dict):
    """Find relevant stats in SPFIT output.

    Parameters
    ----------
    message: str
        The SPFIT output.
    var_dict: dict
        The dict holding the *.var file data.

    Returns
    -------
    dict
        Holds the following stats: rms, wrms, wrms_old, rejected_lines,
        diverging, paramuncertainties.
    """

    results = {}

    startindex = message.rfind("MICROWAVE RMS =") + len("MICROWAVE RMS =")
    stopindex = message.find(" MHz", startindex)
    rms = float(message[startindex:stopindex])

    results["rms"] = rms

    startindex = message.rfind("RMS ERROR=") + len("RMS ERROR=")
    stopindex = message.find("\n", startindex)
    OLDWRMS, WRMS = message[startindex:stopindex].split()

    # @Luis: Why did we keep this beforehand as a string value?
    results["wrms_old"] = float(OLDWRMS)
    results["wrms"] = float(WRMS)

    start_of_last_cycle = message.rfind("Finished Quantum")

    rejected_index = message.rfind("Lines rejected from fit")
    if rejected_index != -1 and rejected_index > start_of_last_cycle:
        tmp_index = message.rfind("\n", 0, rejected_index)
        rejected_lines = int(message[tmp_index:rejected_index])
    else:
        rejected_lines = 0

    results["rejected_lines"] = rejected_lines

    fit_diverging = message.rfind("Fit Diverging")

    if fit_diverging > start_of_last_cycle:
        fit_diverging = "LAST"
    elif fit_diverging > -1:
        fit_diverging = "PREVIOUS"
    else:
        fit_diverging = "NEVER"

    results["diverging"] = fit_diverging

    results["paramuncertainties"] = check_uncertainties(var_dict)

    return results


def check_uncertainties(var_dict):
    """Calcualte relative parameter uncertainties.

    Parameters
    ----------
    var_dict: dict
        The dict holding the *.var file data.

    Returns
    -------
    dict
        Keys are parameter ids and values are relative uncertainties.
    """
    params = var_dict["PARAMS"]
    rel_uncs = {}
    for par in params:
        id, value, uncertainty = par[:3]
        if value == 0:
            rel_unc = np.inf
        else:
            rel_unc = abs(uncertainty / value)
        rel_uncs[id] = rel_unc

    return rel_uncs


def parse_param_id(param_id, vib_digits):
    """Parse parameter id to parameter dictionary."""
    param_id = abs(param_id)
    result = {}
    for label, digits in get_par_digits(vib_digits).items():
        if digits == 0:
            continue
        param_id, result[label] = divmod(param_id, 10**digits)
    return result


def format_param_id(dict_, vib_digits):
    """Format parameter dictionary to parameter id."""
    param_id = 0
    factor = 1
    for label, digits in get_par_digits(vib_digits).items():
        if digits == 0:
            continue
        # @Luis: Think about throwing an error here when the value is higher than the digits value!
        param_id += dict_.get(label, 0) * factor
        factor *= 10**digits
    return param_id


# Format functions
def cat_to_df(fname, sort=False, quanta=None):
    """Convert *.cat file to dataframe.

    Parameters
    ----------
    fname: str, path object, or file-like object
        String, path, or file-like object holding the *.cat data.
    sort: bool
        If the data should be sorted by the x column.
    zeroes_as_empty: bool
        If all zero columns should be interpreted as inactive columns.
    quanta: int or None
        The number of used quanta. None means use global setting.

    Returns
    -------
    dataframe
        Dataframe holding the *.cat data.
    """

    quanta = max(6, quanta or QUANTA)

    dtypes = cat_dtypes_from_quanta(quanta)
    widths = cat_widths_from_quanta(quanta)

    widths = widths.values()
    columns = dtypes.keys()
    converters = dtypes.copy()

    data = pd.read_fwf(
        fname,
        widths=widths,
        names=columns,
        converters=converters,
        skip_blank_lines=True,
        comment="#",
    ).astype(dtypes)
    data["y"] = 10 ** data["y"]
    data["filename"] = str(fname)

    if sort:
        data.sort_values("x", inplace=True)
    return data


def lin_to_df(fname, sort=False, zeroes_as_empty=False, quanta=None, convert_to_MHz=False):
    """Convert *.lin file to dataframe.

    Parameters
    ----------
    fname: path, or file-like object
        Path, or file-like object holding the *.lin data.
    sort: bool
        If the data should be sorted by the x column.
    zeroes_as_empty: bool
        If all zero columns should be interpreted as inactive columns.
    quanta: int or None
        The number of used quanta. None means use global setting.
    convert_to_MHz: bool
        If values in wavenumbers should be converted to MHz.

    Returns
    -------
    dataframe
            Dataframe holding the *.lin data.
    """

    quanta = max(6, quanta or QUANTA)
    dtypes = lin_dtypes_from_quanta(quanta)

    chars_for_qns = 3 * 2 * quanta
    widths = range(0, chars_for_qns + 1, 3)
    column_names = list(dtypes.keys())
    qns_labels = column_names[0 : 2 * quanta]

    data = []
    tmp_file = open(fname, "r") if not isinstance(fname, io.StringIO) else fname
    with tmp_file as file:
        for line in file:
            if not line.strip() or line.startswith(("#", "/", "\\")):
                continue

            tmp = line[chars_for_qns:]
            if '/' in tmp:
                tmp, comment = tmp.split('/', maxsplit=1)
                tmp = tmp.split(maxsplit=2) + [comment]
            else:
                tmp = tmp.split(maxsplit=3)

            tmp[0] = dtypes["x"](tmp[0])
            tmp[1] = dtypes["error"](tmp[1])

            if len(tmp) == 2:
                tmp.extend((1, ""))
            elif len(tmp) >= 3:
                dtype = dtypes["weight"]
                try:
                    tmp[2] = dtype(tmp[2])
                    if len(tmp) == 3:
                        tmp.append("")
                    else:
                        tmp[3] = tmp[3].strip()
                except ValueError:
                    comment = " ".join(tmp[2:]).strip()
                    if len(tmp) == 3:
                        tmp.append(comment)
                    else:
                        tmp[3] = comment
                    tmp[2] = 1

            tmp_line_content = [
                pickett_int(line[i:j]) for i, j in zip(widths[:-1], widths[1:])
            ] + tmp
            data.append(tmp_line_content)

    data = pd.DataFrame(data, columns=column_names).astype(dtypes)
    data["filename"] = str(fname)

    # Set correct columns for data
    noq = len(qns_labels)
    for i in range(len(qns_labels)):
        if all(SENTINEL == data[qns_labels[i]]):
            noq = i
            break

        # Zeros_as_empty supports AABS format where empty quantum numbers are denoted as zero
        # This can lead to ambiguous results if there are all-zero columns
        if zeroes_as_empty and all(0 == data[qns_labels[i]]):
            following_columns_are_zero = [
                all(0 == data[qns_labels[j]]) for j in range(i + 1, len(qns_labels))
            ]
            if all(following_columns_are_zero):
                # Return even value as we might otherwise neglect the column with all zeroes for the state
                noq = i + (i % 2 == 1)
                # Unset the following columns
                for j in range(noq, len(qns_labels)):
                    data[qns_labels[j]] = SENTINEL

                break

    noq = noq // 2

    columns_qn = [f"qn{ul}{i+1}" for ul in ("u", "l") for i in range(noq)] + [
        f"qn{ul}{i+1}" for ul in ("u", "l") for i in range(noq, quanta)
    ]
    data.columns = columns_qn + list(data.columns[2 * quanta :])

    if convert_to_MHz:
        mask = (data['error'] < 0)
        data.loc[mask, 'error'] *= -WN_TO_MHZ
        data.loc[mask, 'x'] *= WN_TO_MHZ

    if sort:
        # Sort by x and by error to keep blends together
        data.sort_values(["x", "error"], inplace=True)
    return data


def df_to_cat(df, quanta=None):
    """Convert dataframe to *.cat format.

    Parameters
    ----------
    df: dataframe
        Dataframe holding the *.cat data.
    quanta: int or None
        The number of used quanta. None means use global setting.

    Returns
    -------
    str
        Data of the dataframe in *.cat format.
    """

    quanta = max(6, quanta or QUANTA)
    qnlabels = qnlabels_from_quanta(quanta)

    lines = []

    for index, row in df.iterrows():
        freq = format_(row["x"], "13.4f")
        error = format_(row["error"], "8.4f")
        intens = np.log10(row["y"]) if row["y"] > 0 else 0
        intens = format_(intens, "8.4f")
        dof = format_(row["degfreed"], "2d")
        elower = format_(row["elower"], "10.4f")
        usd = format_(row["usd"], "3p")
        tag = format_(row["tag"], "7d")
        qnfmt = format_(row["qnfmt"], "4d")

        qnsstring = ""
        for qnlabel in qnlabels:
            qn = row[qnlabel]
            if qn == SENTINEL:
                qnsstring += "  "
            else:
                qnsstring += format_(row[qnlabel], "2p")

        lines.append(f"{freq}{error}{intens}{dof}{elower}{usd}{tag}{qnfmt}{qnsstring}")
    lines.append("")

    return "\n".join(lines)


def df_to_lin(df, quanta=None, custom_freq_format=None):
    """Convert dataframe to *.lin format.

    Parameters
    ----------
    df: dataframe
        Dataframe holding the *.lin data.
    quanta: int or None
        The number of used quanta. None means use global setting.

    Returns
    -------
    str
        Data of the dataframe in *.lin format.
    """

    quanta = max(6, quanta or QUANTA)
    qnlabels = qnlabels_from_quanta(quanta)

    lines = []

    for _, row in df.iterrows():
        qnsstring = ""
        padstring = ""
        for qnlabel in qnlabels:
            if SENTINEL == row[qnlabel]:
                padstring += "   "
            else:
                qnsstring += format_(row[qnlabel], "3d")
        qnsstring = qnsstring + padstring
        comment = row["comment"].strip() if row["comment"] else ""

        freq_format = "15.4f" if row["error"] >= 0 else "15.10f"
        if custom_freq_format:
            freq_format = custom_freq_format
        freq = f"{{:{freq_format}}}".format(row["x"])

        error = (
            format_(row["error"], "8.4f")
            if abs(row["error"]) >= 1e-3
            else f'{row["error"]:-8.1e}'
        )
        weight = format_(row["weight"], "13.4f")
        lines.append(f"{qnsstring} {freq} {error} {weight}  {comment}")
    lines.append("")

    return "\n".join(lines)


def egy_to_df(fname, sort=False, quanta=None):
    """Convert *.egy file to dataframe.

    Parameters
    ----------
    fname: str, path object, or file-like object
        String, path, or file-like object holding the *.egy data.
    sort: bool
        If the data should be sorted by the egy column.
    quanta: int or None
        The number of used quanta. None means use global setting.

    Returns
    -------
    dataframe
        Dataframe holding the *.egy data.
    """

    quanta = max(6, quanta or QUANTA)

    widths = egy_widths_from_quanta(quanta)
    dtypes = egy_dtypes_from_quanta(quanta)

    widths = widths.values()
    columns = dtypes.keys()
    converters = dtypes

    data = pd.read_fwf(
        fname,
        widths=widths,
        names=columns,
        converters=converters,
        skip_blank_lines=True,
        comment="#",
    ).astype(dtypes)

    data = data.drop(columns=[":"])
    data["filename"] = str(fname)

    if sort:
        data.sort_values("egy", inplace=True)
    return data


def df_to_egy(df, quanta=None):
    """Convert dataframe to *.egy format.

    Parameters
    ----------
    df: dataframe
        Dataframe holding the *.egy data.
    quanta: int or None
        The number of used quanta. None means use global setting.

    Returns
    -------
    str
        Data of the dataframe in *.egy format.
    """

    quanta = max(6, quanta or QUANTA)
    qnlabels_energy = qnlabels_energy_from_quanta(quanta)

    lines = []

    for index, row in df.iterrows():
        iblk = format_(row["iblk"], "5d")
        indx = format_(row["indx"], "5d")
        egy = format_(row["egy"], "18.6f")
        err = format_(row["err"], "18.6f")
        pmix = format_(row["pmix"], "11.6f")
        we = format_(row["we"], "5d")

        qnsstring = ""
        for qnlabel in qnlabels_energy:
            qn = row[qnlabel]
            if qn == SENTINEL:
                qnsstring += "   "
            else:
                qnsstring += format_(row[qnlabel], "3d")

        lines.append(f" {iblk}{indx}{egy}{err}{pmix}{we}:{qnsstring}")
    lines.append("")

    return "\n".join(lines)


def parvar_to_dict(fname):
    """Convert *.par or *.var file to dict.

    Parameters
    ----------
    fname: str, or path object, or file-like object
        String, path, or file-like object holding the *.par or *.var data.

    Returns
    -------
    dict
        Dictionary holding the *.par/*.var data.
    """
    result = {}
    tmp_file = open(fname, "r") if not isinstance(fname, io.StringIO) else fname
    with tmp_file as file:
        result["TITLE"] = file.readline().replace("\n", "")

        keys = ["NPAR", "NLINE", "NITR", "NXPAR", "THRESH", "ERRTST", "FRAC", "CAL"]
        result.update({key: value for key, value in zip(keys, file.readline().split())})

        keys = [
            "CHR",
            "SPIND",
            "NVIB",
            "KNMIN",
            "KNMAX",
            "IXX",
            "IAX",
            "WTPL",
            "WTMN",
            "VSYM",
            "EWT",
            "DIAG",
            "XOPT",
        ]
        result.update({key: value for key, value in zip(keys, file.readline().split())})

        for key, value in result.items():
            if key not in ["TITLE", "CHR"]:
                value = np.float64(value)
                if value % 1 == 0:
                    result[key] = int(value)
                else:
                    result[key] = value

        result["STATES"] = []

        states_keys = [
            "CHR",
            "SPIND",
            "NVIB",
            "KNMIN",
            "KNMAX",
            "IXX",
            "IAX",
            "WTPL",
            "WTMN",
            "VSYM",
            "EWT",
            "DIAG",
            "XOPT",
        ]
        tmp_vsym = result.get("VSYM", 0)
        while tmp_vsym < 0:
            linecontent = file.readline().split()
            if not linecontent:
                break

            try:
                chr = ""
                spind = int(linecontent[0])
                linecontent = linecontent[1:]

            except ValueError:
                chr = linecontent[0]
                spind = int(linecontent[1]) if len(linecontent) > 1 else 1
                linecontent = linecontent[2:]

            linecontent = {
                key: int(value) for key, value in zip(states_keys[2:], linecontent)
            }
            linecontent.update({"CHR": chr, "SPIND": spind})
            tmp_vsym = linecontent.get("VSYM", 0)

            result["STATES"].append(linecontent)

        result["PARAMS"] = []
        for line in file:
            try:
                if not line.strip():
                    continue
                keys = [
                    "IDPAR",
                    "PAR",
                    "ERPAR",
                    "LABEL",
                ]  # Only here in case list is changed to dict
                funcs = [int, np.float64, np.float64, lambda x: x.replace("/", "")]
                paramline = [
                    func(value) for key, value, func in zip(keys, line.split(), funcs)
                ]

                result["PARAMS"].append(paramline)
            except Exception:
                break

    return result


def dict_to_parvar(dict_):
    """Convert dict to *.par/*.var format.

    Parameters
    ----------
    dict_: dict
        Dict holdign the *.par/*.var data.

    Returns
    -------
    str
        Data of the dict in *.par/*.var format.
    """
    output = []
    output.append(dict_["TITLE"])

    formats = [
        "{:4.0f}",
        " {:6.0f}",
        " {:5.0f}",
        " {:4.0f}",
        "   {: .4e}",
        "   {: .4e}",
        "   {: .4e}",
        " {:13.4f}",
    ]

    values = [
        dict_[key]
        for key in ["NPAR", "NLINE", "NITR", "NXPAR", "THRESH", "ERRTST", "FRAC", "CAL"]
        if key in dict_
    ]
    line = "".join([fs.format(x) for x, fs in zip(values, formats)])
    output.append(line)

    formats = [
        "{:2}",
        " {:4.0f}",
        " {:3.0f}",
        " {:3.0f}",
        " {:4.0f}",
        " {:4.0f}",
        " {:4.0f}",
        " {:4.0f}",
        " {:4.0f}",
        " {: 7.0f}",
        " {:4.0f}",
        " {:1.0f}",
        " {:4.0f}",
    ]
    states_keys = [
        "CHR",
        "SPIND",
        "NVIB",
        "KNMIN",
        "KNMAX",
        "IXX",
        "IAX",
        "WTPL",
        "WTMN",
        "VSYM",
        "EWT",
        "DIAG",
        "XOPT",
    ]

    for state in [dict_] + dict_["STATES"]:
        line = []
        for fs, key in zip(formats, states_keys):
            if key not in state:
                break
            tmp = state[key]
            line.append(fs.format(tmp))

        output.append("".join(line))

    for param in dict_["PARAMS"]:
        comment = ""
        if len(param) > 3:
            comment = f"/{param[3]}"
        output.append(f"{param[0]:13} {param[1]: .15e} {param[2]: .8e} {comment}")

    output = "\n".join(output)
    return output


def int_to_dict(fname):
    """Convert *.int file to dict.

    Parameters
    ----------
    fname: str, or path object, or file-like object
        String, path, or file-like object holding the *.int data.

    Returns
    -------
    dict
        Dictionary holding the *.int data.
    """
    result = {}
    tmp_file = open(fname, "r") if not isinstance(fname, io.StringIO) else fname
    with tmp_file as file:
        result["TITLE"] = file.readline().replace("\n", "")

        keys = [
            "FLAGS",
            "TAG",
            "QROT",
            "FBGN",
            "FEND",
            "STR0",
            "STR1",
            "FQLIM",
            "TEMP",
            "MAXV",
        ]
        funcs = [
            int,
            int,
            np.float64,
            int,
            int,
            np.float64,
            np.float64,
            np.float64,
            np.float64,
            int,
        ]
        result.update(
            {
                key: func(value)
                for key, value, func in zip(keys, file.readline().split(), funcs)
            }
        )

        result["INTS"] = []
        for line in file:
            keys = ["IDIP", "DIPOLE"]
            funcs = [int, np.float64]
            intline = [
                func(value) for key, value, func in zip(keys, line.split(), funcs)
            ]

            if intline:
                result["INTS"].append(intline)

    return result


def dict_to_int(dict_):
    """Convert dict to *.int format.

    Parameters
    ----------
    dict_: dict
        Dict holdign the *.int data.

    Returns
    -------
    str
        Data of the dict in *.int format.
    """
    output = []
    output.append(dict_["TITLE"])

    formats = [
        "{:4.0f}",
        " {:7.0f}",
        " {:13.4f}",
        " {:4.0f}",
        " {:4.0f}",
        " {: 6.2f}",
        " {: 6.2f}",
        " {:13.4f}",
        " {:13.4f}",
        " {:4.0f}",
    ]

    values = [
        dict_[key]
        for key in [
            "FLAGS",
            "TAG",
            "QROT",
            "FBGN",
            "FEND",
            "STR0",
            "STR1",
            "FQLIM",
            "TEMP",
            "MAXV",
        ]
        if key in dict_
    ]
    line = "".join([fs.format(x) for x, fs in zip(values, formats)])
    output.append(line)

    for param in dict_["INTS"]:
        output.append(f" {param[0]: d}  {param[1]:.4f}")

    output = "\n".join(output)
    return output


def erhamlines_to_df(fname, sort=False):
    """Convert ERHAM line data to dataframe.

    Parameters
    ----------
    fname: path, or file-like object
        Path, or file-like object holding the *.lin data.
    sort: bool
        If the data should be sorted by the x column.

    Returns
    -------
    dataframe
        Dataframe holding the *.lin data.
    """
    noc = len(erham_dtypes)
    data = []
    tmp_file = open(fname, "r") if not isinstance(fname, io.StringIO) else fname
    with tmp_file as file:
        for line in file:
            if line.strip() == "" or line.startswith("#"):
                continue

            tmp = line.split(maxsplit=noc - 1)
            if len(tmp) == noc - 1:
                tmp.append("")

            data.append(tmp)

    column_names = list(erham_dtypes.keys())
    data = pd.DataFrame(data, columns=column_names).astype(erham_dtypes)

    data["qnu2"] = data["tauu"] // 2
    data["qnl2"] = data["taul"] // 2

    data["qnu3"] = data["qnu1"] - (data["tauu"] - 1) // 2
    data["qnl3"] = data["qnl1"] - (data["taul"] - 1) // 2

    data["qnu4"] = data["is1"]
    data["qnl4"] = data["is2"]

    data["qnu5"] = data["qnu6"] = data["qnl5"] = data["qnl6"] = SENTINEL

    data["filename"] = str(fname)

    return data


def df_to_erhamlines(df):
    """Convert dataframe to ERHAM line list.

    Parameters
    ----------
    df: dataframe
        Dataframe holding the *.lin data.

    Returns
    -------
    str
        Data of the dataframe in ERHAM line list format.
    """
    lines = []

    df["blended"] = False
    col_blended = df.columns.get_loc("blended")
    col_x = df.columns.get_loc("x")

    df.iloc[:-1, col_blended] = df.iloc[1:, col_x].values == df.iloc[:-1, col_x].values

    in_blend = False
    for index, row in df.iterrows():
        is1, is2 = row["qnu4"], row["qnl4"]
        qnu1, qnl1 = row["qnu1"], row["qnl1"]
        tauu, taul = (
            row["qnu2"] - row["qnu3"] + qnu1 + 1,
            row["qnl2"] - row["qnl3"] + qnl1 + 1,
        )

        x = format_(row["x"], "19.6f")

        if in_blend:
            if row["blended"]:
                blend = row["weight"]
            else:
                blend = -row["weight"]
                in_blend = False
        else:
            if row["blended"]:
                blend = row["weight"]
                in_blend = True
            else:
                blend = 0
                in_blend = False

        blend = format_(blend, "6.3f")
        error = format_(row["error"], "11.6f")

        lines.append(
            f"{is1:3.0f}{is2:3.0f}  {qnu1:3.0f}{tauu:3.0f}  {qnl1:3.0f}{taul:3.0f} {x} {blend} {error}"
        )
    lines.append("")

    return "\n".join(lines)


## SPFIT/SPCAT functions
def run_spfit(fname, parameterfile="", path=None, wd=None):
    """Run SPFIT.

    Parameters
    ----------
    fname: str
        Name of the *.lin file or basename for *.lin and *.par file.
    parameterfile: str
        Name of the *.par file.
    path: str
        Path of SPFIT. If falsy, the environment variable will be tried.
    wd: str, or path object
        Working directory to be used. The working directory should contain the *.lin and *.par file.

    Returns
    -------
    str
        Output message of the SPFIT run.
    """
    if path:
        path = os.path.abspath(path)
    else:
        if SPFIT_PATH:
            path = SPFIT_PATH
        else:
            path = "spfit"

    command = [path, fname, parameterfile]
    return run_subprocess(command, wd)


def run_spcat(fname, parameterfile="", path=None, wd=None):
    """Run SPCAT.

    Parameters
    ----------
    fname: str
        Name of the *.int file or basename for *.int and *.var file.
    parameterfile: str
        Name of the *.var file.
    path: str
        Path of SPCAT. If falsy, the environment variable will be tried.
    wd: str, or path object
        Working directory to be used. The working directory should contain the *.int and *.var file.

    Returns
    -------
    str
        Output message of the SPCAT run.
    """
    if path:
        path = os.path.abspath(path)
    else:
        if SPCAT_PATH:
            path = SPCAT_PATH
        else:
            path = "spcat"

    command = [path, fname, parameterfile]
    return run_subprocess(command, wd)


def run_subprocess(command, wd=None):
    """Run a subprocess specified by a command.

    Parameters
    ----------
    command: str
        Command to be executed.
    wd: str, or path object
        Working directory to be used.

    Returns
    -------
    str
        Output of the executed command.
    """
    if wd is None:
        wd = os.getcwd()
    output = subprocess.check_output(command, cwd=wd)
    output = output.decode("utf-8")
    return output


def run_spfit_v(par_dict, lin_df, spfit_path=None):
    """Run SPFIT virtually.

    Parameters
    ----------
    par_dict: dict
        The *.par data in dict form.
    lin_df: dataframe
        The *.lin data in DataFrame form.
    spfit_path: str
        Path of SPFIT. If falsy, the environment variable will be tried.

    Returns
    -------
    dict
        Holds the resulting files and the output message.
    """
    with tempfile.TemporaryDirectory(prefix="pyckett_") as tmp_dir:
        with open(os.path.join(tmp_dir, "tmp.par"), "w+") as par_file, open(
            os.path.join(tmp_dir, "tmp.lin"), "w+"
        ) as lin_file:
            lin_file.write(df_to_lin(lin_df))
            par_file.write(dict_to_parvar(par_dict))

        message = run_spfit("tmp", path=spfit_path, wd=tmp_dir)

        result = {
            "msg": message,
            "bak": parvar_to_dict(os.path.join(tmp_dir, "tmp.bak")),
            "par": parvar_to_dict(os.path.join(tmp_dir, "tmp.par")),
            "var": parvar_to_dict(os.path.join(tmp_dir, "tmp.var")),
        }

        for ext in ("fit", "bin"):
            tmp_filename = os.path.join(tmp_dir, f"tmp.{ext}")
            if os.path.isfile(tmp_filename):
                with open(tmp_filename, "r") as file:
                    result[ext] = file.read()

    return result


def run_spcat_v(var_dict, int_dict, spcat_path=None):
    """Run SPCAT virtually.

    Parameters
    ----------
    var_dict: dict
        The *.var data in dict form.
    int_dict: dict
        The *.int data in dict form.
    spcat_path: str
        Path of SPCAT. If falsy, the environment variable will be tried.

    Returns
    -------
    dict
        Holds the resulting files and the output message.
    """
    with tempfile.TemporaryDirectory(prefix="pyckett") as tmp_dir:
        with open(os.path.join(tmp_dir, "tmp.var"), "w+") as var_file, open(
            os.path.join(tmp_dir, "tmp.int"), "w+"
        ) as int_file:
            int_file.write(dict_to_int(int_dict))
            var_file.write(dict_to_parvar(var_dict))

        message = run_spcat("tmp", path=spcat_path, wd=tmp_dir)

        result = {
            "msg": message,
            "cat": cat_to_df(os.path.join(tmp_dir, "tmp.cat")),
            "egy": (
                egy_to_df(os.path.join(tmp_dir, "tmp.egy"))
                if os.path.isfile(os.path.join(tmp_dir, "tmp.egy"))
                else None
            ),
        }

        for ext in (".out", ".str"):
            tmp_filename = os.path.join(tmp_dir, f"tmp.{ext}")
            if os.path.isfile(tmp_filename):
                with open(tmp_filename, "r") as file:
                    result[ext] = file.read()

    return result


## Main actions
def check_crossings(egy_df, states, kas, Jmax=60):
    """Check energy level series for crossings.

    This function is currently specific to asymmetric molecules where the state is the 4th quantum number
    and Ka is the second quantum number.

    Parameters
    ----------
    egy_df: dataframe
        The *.egy data in dataframe form.
    states: dict
        The states that should be checked.
    kas: iterable of ints
        Kas to be checked for each state.

    Returns
    -------
    str
        Report of the crossings in string format.
    """
    output = []
    series_list = []
    for state in states:
        for ka in kas:
            qnsums = (0, 1) if ka != 0 else (0,)
            for qnsum in qnsums:
                tmp_df = egy_df.query(
                    f"qn2 == {ka} and qn4 == {state} and qn1 + {qnsum} == qn2+qn3 and qn1 < {Jmax}"
                ).copy()
                xmin = (
                    tmp_df["qn1"].to_numpy().min()
                    if len(tmp_df["qn1"].to_numpy()) != 0
                    else 0
                )
                ys = tmp_df["egy"].to_numpy()

                series_list.append(((state, ka, qnsum), xmin, ys))

    crossings = []
    for i in range(len(series_list)):
        for j in range(i + 1, len(series_list)):
            desc_1, xmin_1, ys_1 = series_list[i]
            desc_2, xmin_2, ys_2 = series_list[j]

            xdiff = xmin_1 - xmin_2
            xstart = max(xmin_1, xmin_2)

            if xdiff > 0:
                ys_2 = ys_2[xdiff:]
            elif xdiff < 0:
                ys_1 = ys_1[abs(xdiff) :]

            ydiff = ys_1 - ys_2
            ytmp = [ydiff[k] * ydiff[k + 1] for k in range(len(ydiff) - 1)]

            for k in range(len(ytmp)):
                if ytmp[k] < 0:
                    crossings.append((desc_1, desc_2, xstart + k))

    crossings = sorted(crossings, key=lambda x: (x[0][0], x[1][0]))

    output.append("Format is state1, state2 @ ka1, J-ka1-kc1 & ka2, J-ka2-kc2 @ Ji, Jf")
    for crossing in crossings:
        J = crossing[2]
        output.append(
            f"{crossing[0][0]:3d}, {crossing[1][0]:3d} @ {crossing[0][1]:3d}, {crossing[0][2]:1d} & {crossing[1][1]:3d}, {crossing[1][2]:1d} @ {J:3d}, {J+1:3d}"
        )

    output.append(f"\nFound {len(crossings)} crossings in total.")
    output = "\n".join(output)

    return output


def mixing_coefficient(egy_df, query_strings, save_fname=None, cmap="plasma_r"):
    """Plot the mixing coefficients of energy levels.

    Parameters
    ----------
    egy_df: dataframe
        The *.egy data in dataframe form.
    query_string: str or iterable of strs
        Query condition(s) to select a subset of energy levels.
    save_fname: str or None
        If truthy, the filename of the output file.

    Returns
    -------
        None
    """

    if isinstance(query_strings, str):
        query_strings = [query_strings]

    N = len(query_strings)

    gs = matplotlib.gridspec.GridSpec(
        1, 2 + N, width_ratios=[1] * N + [0.2, 0.1], hspace=0, wspace=0
    )
    fig = plt.figure()

    pmix_axes = [fig.add_subplot(gs[0, i]) for i in range(N)]

    eax = fig.add_subplot(gs[0, -2])
    eax.axis("off")
    cbax = fig.add_subplot(gs[0, -1])

    for ax, query in zip(pmix_axes, query_strings):
        ax.set_xlabel("$J$")
        ax.yaxis.set_visible(False)

        tmp_df = egy_df.query(query).copy()

        if any(tmp_df.duplicated(["qn1", "qn2"])):
            print("There are duplicate entries in your z-matrix.")

        xs = tmp_df["qn1"].to_numpy()
        ys = tmp_df["qn2"].to_numpy()
        zs = tmp_df["pmix"].abs().to_numpy()

        df = pd.DataFrame({"x": xs, "y": ys, "z": zs})
        zmatrix = df.pivot_table(values="z", index="y", columns="x")
        zmatrix = zmatrix.to_numpy()

        if len(xs) == 0 or len(ys) == 0:
            print("No data found.")
            return ()

        xs = [x - 0.5 for x in sorted(list(set(xs)))]
        xs.append(max(xs) + 1)
        ys = [y - 0.5 for y in sorted(list(set(ys)))]
        ys.append(max(ys) + 1)

        tmp = ax.pcolormesh(xs, ys, zmatrix, cmap=cmap, vmin=0.5, vmax=1)
        ax.set_xlim(min(xs), max(xs))
        ax.set_ylim(min(xs), max(ys))

    ax = pmix_axes[0]
    ax.set_ylabel("$K_{a}$")
    ax.yaxis.set_visible(True)

    cb = fig.colorbar(tmp, cax=cbax, orientation="vertical")
    cb.set_label("Mixing Coefficient", labelpad=10)

    fig.tight_layout()
    if save_fname is None:
        plt.show()
    elif isinstance(save_fname, str):
        plt.savefig(save_fname)
        plt.close()

    return fig


def add_parameter(
    par_dict, lin_df, param_candidates, sort=True, spfit_path=None, sort_by_wrms=False
):
    """Check which parameter should be added to a *.par file.

    Parameters
    ----------
    par_dict: dict
        The *.par data in dict form.
    lin_df: dataframe
        The *.lin data in dataframe form.
    param_candidates: iterable of ints, or iterables of ints
        The parameter ids to be checked or the tuple (id, value, unc) of the parameter to be checked.
    sort: bool
        If the returned runs should be sorted by rms.
    spfit_path:
        The path to SPFIT that is passed to the underlying :func:`run_spfit_v`.

    Returns
    -------
    runs: list of dicts
        The results for each parameter in dictionary format. Each result consists of id, rms, par, stats.
    """
    runs = []

    def worker(i):
        params = param_candidates[i]
        if isinstance(params, (int, float, complex)):
            params = [[params, 1e-37, 1e37]]
        else:
            params = list(params)
        ids = [x[0] for x in params]

        tmp_par_dict = par_dict.copy()
        tmp_par_dict["PARAMS"] = tmp_par_dict["PARAMS"] + params
        results = run_spfit_v(tmp_par_dict, lin_df, spfit_path)
        stats = parse_fit_result(results["msg"], results["var"])
        rms = stats["rms"]
        wrms = stats["wrms"]
        return {
            "id": ids,
            "rms": rms,
            "wrms": wrms,
            "par": results["par"]["PARAMS"].copy(),
            "stats": stats,
            "params": params,
        }

    with ThreadPoolExecutor() as executor:
        futures = {i: executor.submit(worker, i) for i in range(len(param_candidates))}
        runs = [f.result() for f in futures.values()]

    if sort:
        sort_key = "wrms" if sort_by_wrms else "rms"
        runs = sorted(runs, key=lambda x: x[sort_key])
    return runs


def omit_parameter(
    par_dict, lin_df, param_ids, sort=True, spfit_path=None, sort_by_wrms=False
):
    """Check which parameter should be omitted from a *.par file.

    Parameters
    ----------
    par_dict: dict
        The *.par data in dict form.
    lin_df: dataframe
        The *.lin data in dataframe form.
    param_ids: iterable of ints
        The parameter ids to be checked.
    sort: bool
        If the returned runs should be sorted by rms.
    spfit_path:
        The path to SPFIT that is passed to the underlying :func:`run_spfit_v`.

    Returns
    -------
    runs: list of dicts
        The results for each parameter in dictionary format. Each result consists of id, rms, par, stats.
    """
    runs = []

    def worker(param_id):
        tmp_par_dict = par_dict.copy()
        tmp_par_dict["PARAMS"] = [x for x in tmp_par_dict["PARAMS"] if x[0] != param_id]
        try:
            results = run_spfit_v(tmp_par_dict, lin_df, spfit_path)
            stats = parse_fit_result(results["msg"], results["var"])
        except subprocess.CalledProcessError:
            stats = {"rms": None, "wrms": None}
        rms = stats["rms"]
        wrms = stats["wrms"]
        return {
            "id": param_id,
            "rms": rms,
            "wrms": wrms,
            "par": tmp_par_dict["PARAMS"].copy(),
            "stats": stats,
        }

    with ThreadPoolExecutor() as executor:
        futures = {
            param_id: executor.submit(worker, param_id) for param_id in param_ids
        }
        runs = [f.result() for f in futures.values()]

    if sort:
        sort_key = "wrms" if sort_by_wrms else "rms"
        failed_runs = [x for x in runs if x[sort_key] is None]
        normal_runs = [x for x in runs if x[sort_key] is not None]
        runs = (
            sorted(
                normal_runs, key=lambda x: (x["stats"]["rejected_lines"], x[sort_key])
            )
            + failed_runs
        )
    return runs


def finalize(cat_df=pd.DataFrame(), lin_df=pd.DataFrame(), qn_tdict={}, qn=4):
    """Finalize the *.cat and *.lin files of a fit.

    Parameters
    ----------
    cat_df: dataframe
        The *.cat data in dataframe form.
    lin_df: dataframe
        The *.lin data in dataframe form.
    qn_tdict: dict
        The quantum number translation dict. Keys is a tuple consisting of the value for the upper and
        lower quantum number value, values are the corresponding values they should be mapped to.
    qn: int
        The quantum number position that the qn_tdict should be applied to.

    Returns
    -------
    cat_df: dataframe
        The resulting *.cat dataframe, with duplicates being summed up and *.lin data being merged in.
    lin_df: dataframe
        The resulting *.lin dataframe.
    """
    cat_df = cat_df.copy()
    lin_df = lin_df.copy()

    # Merge cat and lin file
    if len(lin_df) and len(cat_df):
        lin_qns, cat_qns = get_active_qns(lin_df), get_active_qns(cat_df)
        lin_qns = set([key for key, value in lin_qns.items() if value])
        cat_qns = set([key for key, value in cat_qns.items() if value])

        if lin_qns != cat_qns:
            raise Exception(
                f"The active quantum numbers of the lin and cat file do not match.\nQuantum numbers of the cat file: {cat_qns}\nQuantum numbers of the lin file: {lin_qns}"
            )

        tmp_lin_df = lin_df.drop(
            set(lin_df.columns) - lin_qns - set(("x", "error")), axis=1
        )
        cat_df = pd.merge(cat_df, tmp_lin_df, how="left", on=list(cat_qns))

        mask = ~cat_df["x_y"].isna()
        cat_df.loc[mask, "x_x"] = cat_df.loc[mask, "x_y"]
        cat_df.loc[mask, "error_x"] = cat_df.loc[mask, "error_y"]
        cat_df.loc[mask, "tag"] = -abs(cat_df.loc[mask, "tag"])
        cat_df = cat_df.drop(["x_y", "error_y"], axis=1)
        cat_df = cat_df.rename({"x_x": "x", "error_x": "error"}, axis=1)

    # Sum up duplicate rows
    if len(cat_df):
        cat_df = (
            cat_df.groupby(list(set(cat_df.columns) - set("y"))).sum().reset_index()
        )
        cat_df = cat_df.sort_values("x").reset_index(drop=True)

    # Translate quantum numbers for the state
    if qn_tdict and qn:
        qnu, qnl = f"qnu{qn}", f"qnl{qn}"
        if len(cat_df):
            if qnu not in cat_qns or qnl not in cat_qns:
                raise Exception(
                    f"The quantum numbers for the state translation, '{qnl}' and '{qnu}', are no active quantum numbers in the cat file."
                )
            cat_df["tmp"] = cat_df.apply(
                lambda row: qn_tdict[(row[qnu], row[qnl])], axis=1
            )
            cat_df[qnu] = cat_df[qnl] = cat_df["tmp"]
            cat_df.drop("tmp", axis=1)

        if len(lin_df):
            if qnu not in lin_qns or qnl not in lin_qns:
                raise Exception(
                    f"The quantum numbers for the state translation, '{qnl}' and '{qnu}', are no active quantum numbers in the lin file."
                )
            lin_df["tmp"] = lin_df.apply(
                lambda row: qn_tdict[(row[qnu], row[qnl])], axis=1
            )
            lin_df[qnu] = lin_df[qnl] = lin_df["tmp"]
            lin_df.drop("tmp", axis=1)

    return (cat_df, lin_df)


def get_dr_candidates(df1, df2, quanta=None):
    """Get candidates for double-resonance measurements.

    Parameters
    ----------
    df1: dataframe
        The *.cat/*.lin data for the first source in dataframe form.
    df2: dataframe
        The *.cat/*.lin data for the second source in dataframe form.
    quanta: int or None
            The number of used quanta. None means use global setting.

    Returns
    -------
    dataframe
        Dataframe containing the double-resonance candidates.
    """

    quanta = max(6, quanta or QUANTA)

    qns_active1, qns_active2 = get_active_qns(df1, quanta=quanta), get_active_qns(
        df2, quanta=quanta
    )
    qns_upper = [
        f"qnu{i+1}"
        for i in range(quanta)
        if qns_active1[f"qnu{i+1}"] and qns_active2[f"qnu{i+1}"]
    ]
    qns_lower = [
        f"qnl{i+1}"
        for i in range(quanta)
        if qns_active1[f"qnl{i+1}"] and qns_active2[f"qnl{i+1}"]
    ]

    qns_inactive = [
        f"qn{ul}{i+1}"
        for i in range(quanta)
        for ul in ("u", "l")
        if not (qns_active1[f"qnu{i+1}"] and qns_active2[f"qnu{i+1}"])
    ]

    schemes = {
        "pro_ul": (qns_upper, qns_lower),
        "pro_lu": (qns_lower, qns_upper),
        "reg_uu": (qns_upper, qns_upper),
        "reg_ll": (qns_lower, qns_lower),
    }

    results = []
    for label, (qns_left, qns_right) in schemes.items():
        tmp = pd.merge(
            df1.drop(columns=qns_inactive),
            df2.drop(columns=qns_inactive),
            how="inner",
            left_on=qns_left,
            right_on=qns_right,
        )
        tmp["scheme"] = label
        results.append(tmp)

    results = pd.concat(results, ignore_index=True)
    results = results[results["x_x"] != results["x_y"]]

    for qn in qns_upper + qns_lower:
        mask = results[qn + "_x"].isna() & results[qn + "_y"].isna()
        results.loc[mask, qn + "_x"] = results.loc[mask, qn + "_y"] = results.loc[
            mask, qn
        ]
    results = (
        results.drop(columns=qns_upper).drop(columns=qns_lower).reset_index(drop=True)
    )

    return results


def create_report(lin_df, cat_df=None, *, noq=None, blends=True):
    results = {}
    report = []

    if not len(lin_df):
        return('Your *.lin file is empty.', results)

    if noq is None:
        qnu_labels = [f"qnu{i+1}" for i in range(QUANTA)]
        noq = len(qnu_labels)
        for i, qnu_label in enumerate(qnu_labels):
            unique_values = lin_df[qnu_label].unique()
            if len(unique_values) == 1 and unique_values[0] == SENTINEL:
                noq = i
                break
    
    qns_visible = [f"qn{ul}{n+1}" for ul in ("u", "l") for n in range(noq)]

    results["not"] = len(lin_df)
    results["nol"] = lin_df["x"].nunique()
    results["non"] = len(lin_df[lin_df["weight"] == 0])
    results["nod"] = sum(lin_df.duplicated(subset=qns_visible))

    report.append((f"Transitions:", results["not"]))
    report.append((f"Lines:", results["nol"]))
    report.append((f"Unweighted Transitions:", results["non"]))
    report.append((f"Duplicates:", results["nod"]))
    report.append(("", ""))

    results[f"x_min"] = lin_df["x"].min()
    results[f"x_max"] = lin_df["x"].max()
    report.append((f"Frequency min:", results["x_min"]))
    report.append((f"Frequency max:", results["x_max"]))

    for i in range(noq):
        for ul in ("u", "l"):
            tag = f"qn{ul}{i+1}"
            results[f"{tag}_min"] = lin_df[tag].min()
            results[f"{tag}_max"] = lin_df[tag].max()
            report.append((f"{tag} min:", results[f"{tag}_min"]))
            report.append((f"{tag} max:", results[f"{tag}_max"]))

    if cat_df is not None:
        results["nocd"] = sum(cat_df.duplicated(subset=qns_visible))
        if results["nocd"]:
            cat_df = cat_df.drop_duplicates(qns_visible, keep="first")

        df = pd.merge(lin_df, cat_df, how="inner", on=qns_visible)
        df.rename(
            columns={
                "x_x": "x_lin",
                "x_y": "x_cat",
                "error_x": "error_lin",
                "error_y": "error_cat",
                "filename_x": "filename_lin",
                "filename_y": "filename_cat",
            },
            inplace=True,
        )
        df.reset_index(drop=True, inplace=True)

        if blends:
            mask = df["weight"] != 0
            df_view = df[mask]
            tmp_dict = (
                df_view.groupby(df_view.x_lin)
                .apply(lambda x: np.average(x.x_cat, weights=x.weight))
                .to_dict()
            )
            df["x_cat"] = df["x_lin"].map(lambda x: tmp_dict.get(x, x))

        df["diff"] = abs(df["x_cat"] - df["x_lin"])
        df["wdiff"] = abs(df["x_cat"] - df["x_lin"]) / abs(df["error_lin"])

        results["nom"] = len(df)
        results["max_deviation"] = df["diff"].max()
        results["max_wdeviation"] = df["wdiff"].max()

        report.append(("", ""))
        report.append(("Assignments with matching predict.:", results["nom"]))
        report.append(
            ("Assignments w/o  matching predict.:", results["not"] - results["nom"])
        )
        report.append(("Highest absolute deviation:", results["max_deviation"]))
        report.append(("Highest relative deviation:", results["max_wdeviation"]))

        results["rms"] = np.sqrt((df["diff"] ** 2).mean())
        results["wrms"] = np.sqrt((df["wdiff"] ** 2).mean())

        report.append(("", ""))
        report.append(("RMS:", results["rms"]))
        report.append(("WRMS:", results["wrms"]))

    # List number of transitions for transition types
    delta_labels = []
    for i in range(noq):
        label = f'Δqn{i+1}'
        lin_df[label] = lin_df[f'qnu{i+1}'] -  lin_df[f'qnl{i+1}']
        delta_labels.append(label)
    delta_df = lin_df.groupby(delta_labels).count()['x'].reset_index()
    table_string = ['\n\nNumber of transitions by transition type:\n']
    all_labels = [f'{label:>6}' for label in delta_labels] + ['Transitions']
    table_header = '| ' + ' | '.join(all_labels) + ' |'
    table_string.append(table_header)
    all_seps = ['-' * 6 for _ in range(noq)] + ['-' * 11]
    table_sep = '| ' + ' | '.join(all_seps) + ' |'
    table_string.append(table_sep)

    for i, row in delta_df.iterrows():
        row_string = []
        for label in delta_labels:
            row_string.append(f'{row[label]:6d}')
        n_lines = row['x']
        row_string.append(f'{n_lines:11d}')

        row_string = '| ' + ' | '.join(row_string)+ ' |'
        table_string.append(row_string)
    table_string.append('')

    report = [
        f"{title: <36}{value:16.4f}" if title else "" for title, value in report
    ]

    if cat_df is not None:
        if results["nocd"]:
            report.append(
                f"\nWARNING: {results['nocd']} duplicates were found in your predictions. Each first occurence was kept."
            )
        if results["not"] != results["nom"]:
            report.append(
                f"\nWARNING: {results['not']-results['nom']} assignments have no matching prediction. This affects i.a. the RMS and WRMS."
            )
        if any(df["error_lin"] == 0):
            report.append(
                f"\nWARNING: Some errors (uncertainties) of your assignments are zero. This leads to infinity values for the relative deviation and the WRMS. Consider using 'error != 0' in the query field."
            )

    report.extend(table_string)
    report = "\n".join(report)
    return(report, results)


# Constants for adding the correct parameters to fits
INITIAL_PARAMS_ROTATION = {100, 200, 300}

POSSIBLE_PARAMS_A = {
    100: ("A", (2, 11, 20, 401, 410)),
    200: ("B", (2, 11, 20, 401, 410)),
    300: ("C", (2, 11, 20, 401, 410)),
    2: ("-DeltaJ", (3, 12, 402)),
    11: ("-DeltaJK", (12, 21, 411)),
    20: ("-DeltaK", (21, 30, 420)),
    401: ("-deltaJ", (402, 411)),
    410: ("-deltaK", (411, 420)),
    3: ("PhiJ", (4, 13, 403)),
    12: ("PhiJK", (13, 22, 412)),
    21: ("PhiKJ", (22, 31, 421)),
    30: ("PhiK", (31, 40, 430)),
    402: ("phiJ", (403, 412)),
    411: ("phiJK", (412, 421)),
    420: ("phiK", (421, 430)),
    4: ("LJ", (5, 14, 404)),
    13: ("LJJK", (14, 23, 413)),
    22: ("LJK", (23, 32, 422)),
    31: ("LKKJ", (32, 41, 431)),
    40: ("LK", (41, 50, 440)),
    403: ("lJ", (404, 413)),
    412: ("lJK", (413, 422)),
    421: ("lKJ", (422, 431)),
    430: ("lK", (431, 440)),
    5: ("PJ", ()),
    14: ("PJJK", ()),
    23: ("PJK", ()),
    32: ("PKJ", ()),
    41: ("PKKJ", ()),
    50: ("PK", ()),
    404: ("pJ", ()),
    413: ("pJJK", ()),
    422: ("pJK", ()),
    431: ("pKKJ", ()),
    440: ("pK", ()),
}

POSSIBLE_PARAMS_S = {
    100: ("A", (2, 11, 20, 401, 500)),
    200: ("B", (2, 11, 20, 401, 500)),
    300: ("C", (2, 11, 20, 401, 500)),
    2: ("-DJ", (3, 12, 402)),
    11: ("-DJK", (12, 21)),
    20: ("-DK", (21, 30)),
    401: ("d1", (402, 501)),
    500: ("d2", (501, 600)),
    3: ("HJ", (4, 13, 403)),
    12: ("HJK", (13, 22)),
    21: ("HKJ", (22, 31)),
    30: ("HK", (31, 40)),
    402: ("h1", (403, 502)),
    501: ("h2", (502, 601)),
    600: ("h3", (601, 700)),
    4: ("LJ", (5, 14, 404)),
    13: ("LJJK", (14, 23)),
    22: ("LJK", (23, 32)),
    31: ("LKKJ", (32, 41)),
    40: ("LK", (41, 50)),
    403: ("l1", (404, 503)),
    502: ("l2", (503, 602)),
    601: ("l3", (602, 701)),
    700: ("l4", (701, 800)),
    5: ("PJ", ()),
    14: ("PJJK", ()),
    23: ("PJK", ()),
    32: ("PKJ", ()),
    41: ("PKKJ", ()),
    50: ("PK", ()),
    404: ("p1", ()),
    503: ("p2", ()),
    602: ("p3", ()),
    701: ("p4", ()),
    800: ("p5", ()),
}

POSSIBLE_PARAMS_LINEAR = {
    1: ("B", (2,)),
    2: ("-D", (3,)),
    3: ("H", (4,)),
    4: ("L", (5,)),
    5: ("P", ()),
}


INITIAL_PARAMS_INTERACTION = {2000, 2100, 4000, 4100, 6000, 6100, 0, 400}

POSSIBLE_PARAMS_INTERACTION = {
    2000: ("Ga", (2001, 2010, 2200)),
    2001: ("GaJ", ()),
    2010: ("GaK", ()),
    2100: ("Fbc", (2101, 2110, 2300)),
    2101: ("FbcJ", ()),
    2110: ("FbcK", ()),
    2200: ("G2a", (2201, 2210)),
    2201: ("G2aJ", ()),
    2210: ("G2aK", ()),
    2300: ("F2bc", (2301, 2310)),
    2301: ("F2bcJ", ()),
    2310: ("F2bcK", ()),
    4000: ("Gb", (4001, 4010, 4200)),
    4001: ("GbJ", ()),
    4010: ("GbK", ()),
    4100: ("Fac", (4101, 4110, 4300)),
    4101: ("FacJ", ()),
    4110: ("FacK", ()),
    4200: ("G2b", (4201, 4210)),
    4201: ("G2bJ", ()),
    4210: ("G2bK", ()),
    4300: ("F2ac", (4301, 4310)),
    4301: ("F2acJ", ()),
    4310: ("F2acK", ()),
    6000: ("Gc", (6001, 6010, 6200)),
    6001: ("GcJ", ()),
    6010: ("GcK", ()),
    6100: ("Fab", (6101, 6110, 6300)),
    6101: ("FabJ", ()),
    6110: ("FabK", ()),
    6200: ("G2c", (6201, 6210)),
    6201: ("G2cJ", ()),
    6210: ("G2cK", ()),
    6300: ("F2ab", (6301, 6310)),
    6301: ("F2abJ", ()),
    6310: ("F2abK", ()),
    0: ("F", (1, 10)),
    1: ("FJ", ()),
    10: ("FK", ()),
    400: ("F2", (401, 410)),
    401: ("F2J", ()),
    410: ("F2K", ()),
}

if __name__ == "__main__":
    pass

    # var_dict = parvar_to_dict(r"path/to/your/project/molecule.var")
    # par_dict = parvar_to_dict(r"path/to/your/project/molecule.par")
    # int_dict = int_to_dict(r"path/to/your/project/molecule.int")
    # lin_df = lin_to_df(r"path/to/your/project/molecule.lin")
    # cat_df = cat_to_df(r"path/to/your/project/molecule.cat")
    # egy_df = egy_to_df(r"path/to/your/project/molecule.egy")

    ## Best Candidate to add to Fit
    # cands = [[140101, 0.0, 1e+37], [410101, 0.0, 1e+37]]
    # add_parameter(par_dict, lin_df, cands, r"SPFIT_SPCAT")

    ## Best Candidate to neglect from Fit
    # cands = [320101, 230101]
    # omit_parameter(par_dict, lin_df, cands, r"SPFIT_SPCAT")

    ## Check Crossings
    # check_crossings(egy_df, [1], range(10))

    ## Plot Mixing Coefficients
    # mixing_coefficient(egy_df, "qn4 == 1 and qn2 < 20 and qn1 < 20 and qn1==qn2+qn3")

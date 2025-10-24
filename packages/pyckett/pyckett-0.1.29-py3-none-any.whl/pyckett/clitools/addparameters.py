#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Luis Bonah
# Description : CLI tool for checking which parameter to add to fit

import os.path
import pyckett
import argparse
from concurrent.futures import ThreadPoolExecutor

# @Luis: Provide option for symmetric, linear molecules
# @Luis: Maybe infer from Kmin and Kmax


def addparameters():
    parser = argparse.ArgumentParser(prog="Add Parameters")

    parser.add_argument("linfile", type=str, help="Filename of the .lin file")
    parser.add_argument(
        "parfile", type=str, nargs="?", help="Filename of the .par file"
    )

    parser.add_argument(
        "--skipinterstate",
        action="store_true",
        help="Do not test interstate parameters",
    )
    parser.add_argument(
        "--skiprotational",
        action="store_true",
        help="Do not test pure rotational parameters",
    )
    parser.add_argument(
        "--skipfixed", action="store_true", help="Do not test fixed parameters"
    )
    parser.add_argument(
        "--skipglobal", action="store_true", help="Do not test global parameters"
    )

    parser.add_argument(
        "--skipparupdate",
        action="store_true",
        help="Do not reset .par parametes NPAR, NLINE, THRESH",
    )

    parser.add_argument(
        "--newinteraction",
        type=int,
        nargs="+",
        help="States to find new interactions for",
    )
    parser.add_argument(
        "--initialvalues",
        nargs="*",
        type=float,
        help="Initial values to test for parameters (default 1E-37)",
    )
    parser.add_argument(
        "--skipsavebest",
        action="store_true",
        help='Do not save the best run to "best.par"',
    )
    parser.add_argument(
        "--stateqn", default=4, type=int, help="Quantum number index for state"
    )

    parser.add_argument(
        "--areduction",
        dest="parameters",
        action="store_const",
        const="a_reduction",
        help="Use A-Reduction parameters",
    )
    parser.add_argument(
        "--sreduction",
        dest="parameters",
        action="store_const",
        const="s_reduction",
        help="Use S-Reduction parameters",
    )
    parser.add_argument(
        "--linear",
        dest="parameters",
        action="store_const",
        const="linear",
        help="Use linear parameters",
    )

    parser.add_argument(
        "--paramids",
        type=int,
        nargs="+",
        help="Manually specify the to-be-tested parameter IDs",
    )
    parser.add_argument(
        "--overwritepar",
        action="store_true",
        help="Overwrite the .par file with the best fit",
    )
    parser.add_argument(
        "--sortwrms",
        action="store_true",
        help="Sort results by their WRMS values instead of their RMS value",
    )

    args = parser.parse_args()

    linfname = args.linfile
    base, ext = os.path.splitext(linfname)
    if not ext:
        linfname = linfname + ".lin"

    parfname = args.parfile if args.parfile else linfname.replace(".lin", ".par")

    lin = pyckett.lin_to_df(linfname, sort=False)
    par = pyckett.parvar_to_dict(parfname)

    if not args.skipparupdate:
        par.update(pyckett.PARUPDATE)

    VIB_DIGITS = pyckett.get_vib_digits(par)
    ALL_STATES = pyckett.get_all_states(VIB_DIGITS)

    qnu, qnl = f"qnu{args.stateqn:1.0f}", f"qnl{args.stateqn:1.0f}"

    bestparfile = "best.par"
    if args.skipsavebest:
        bestparfile = None
    if args.overwritepar:
        bestparfile = parfname

    kwargs = {
        "VIB_DIGITS": VIB_DIGITS,
        "ALL_STATES": ALL_STATES,
        "skipglobal": args.skipglobal,
        "skipfixed": args.skipfixed,
        "skipinterstate": args.skipinterstate,
        "skiprotational": args.skiprotational,
        "qnu": qnu,
        "qnl": qnl,
        "parameters": args.parameters,
        "newinteraction": args.newinteraction,
        "initialvalues": args.initialvalues,
        "parameters_to_test": args.paramids,
        "bestparfile": bestparfile,
        "sort_by_wrms": args.sortwrms,
    }

    addparameters_core(par, lin, **kwargs)


def prit(condition, text=""):
    if condition:
        print(text)


def addparameters_core(
    par,
    lin,
    VIB_DIGITS=1,
    ALL_STATES=9,
    qnu="qnu4",
    qnl="qnl4",
    parameters=None,
    skipfixed=False,
    skipinterstate=False,
    skiprotational=False,
    skipglobal=False,
    newinteraction=None,
    initialvalues=None,
    bestparfile=None,
    parameters_to_test=None,
    report=True,
    sort_by_wrms=False,
):
    if not initialvalues:
        initialvalues = [1e-37]

    # Case of manually specified parameter list
    if parameters_to_test:
        candidates = [(id, "") for id in parameters_to_test]

    # Case of infering parameter to test
    else:
        INTERSTATE_PARAMS = pyckett.POSSIBLE_PARAMS_INTERACTION

        if parameters == "linear":
            ROTATIONAL_PARAMS = pyckett.POSSIBLE_PARAMS_LINEAR
        elif parameters == "s_reduction":
            ROTATIONAL_PARAMS = pyckett.POSSIBLE_PARAMS_S
        else:
            ROTATIONAL_PARAMS = pyckett.POSSIBLE_PARAMS_A

        rotational_cands = set()
        interstate_cands = set()
        present_params = set()

        interstates = set()
        rotationstates = set()

        for param in par["PARAMS"]:
            isfixed = abs(param[2]) < pyckett.ZEROTHRESHOLD
            if isfixed and skipfixed:
                continue
            id = param[0]
            present_params.add(id)

            param_dict = pyckett.parse_param_id(id, VIB_DIGITS)
            base_id = pyckett.format_param_id(param_dict, 0)

            isrotational = param_dict["v1"] == param_dict["v2"]
            ud = {"v1": param_dict["v1"], "v2": param_dict["v2"]}

            if skipglobal and param_dict["v1"] == param_dict["v2"] == ALL_STATES:
                continue

            if isrotational:
                params = ROTATIONAL_PARAMS
                cands = rotational_cands
                rotationstates.add(ud["v1"])

            else:
                params = INTERSTATE_PARAMS
                cands = interstate_cands
                interstates.add((ud["v2"], ud["v1"]))

            comment, next_params_ids = params.get(base_id, (None, None))
            if next_params_ids is None:
                prit(report, f"Did not find any candidates for parameter {id}.")
                continue

            next_params_dicts = [
                {**ud, **pyckett.parse_param_id(id, 0)} for id in next_params_ids
            ]
            cands.update(
                [
                    pyckett.format_param_id(dict_, VIB_DIGITS)
                    for dict_ in next_params_dicts
                ]
            )

        if par["NVIB"] < 2:
            lin_states = set()
        else:
            lin_states = set(lin[qnu].unique()) & set(lin[qnl].unique())
        update_base_states = lambda ud, bs: [
            pyckett.format_param_id({**ud, **pyckett.parse_param_id(id, 0)}, VIB_DIGITS)
            for id in bs
        ]

        # Add base parameters for all rotational states
        for v in rotationstates | lin_states:
            ud = {"v1": v, "v2": v}
            rotational_cands.update(
                update_base_states(ud, pyckett.INITIAL_PARAMS_ROTATION)
            )

        # Add base parameters for all interaction states
        if newinteraction:
            interstates.update(
                [
                    tuple(sorted((v1, v2)))
                    for v1 in newinteraction
                    for v2 in newinteraction
                    if v1 != v2
                ]
            )

        for v2, v1 in interstates:
            ud = {"v1": v1, "v2": v2}
            interstate_cands.update(
                update_base_states(ud, pyckett.INITIAL_PARAMS_INTERACTION)
            )

        rotational_cands = rotational_cands - present_params
        get_comment = lambda id: ROTATIONAL_PARAMS.get(
            pyckett.format_param_id(pyckett.parse_param_id(id, VIB_DIGITS), 0), ("",)
        )[0]
        rotational_cands = [(id, get_comment(id)) for id in rotational_cands]

        interstate_cands = interstate_cands - present_params
        get_comment = lambda id: INTERSTATE_PARAMS.get(
            pyckett.format_param_id(pyckett.parse_param_id(id, VIB_DIGITS), 0), ("",)
        )[0]
        interstate_cands = [(id, get_comment(id)) for id in interstate_cands]

        candidates = []
        if not skiprotational:
            candidates.extend(rotational_cands)
        if not skipinterstate:
            candidates.extend(interstate_cands)

    # Set initial values
    tmp = []
    for id, comment in candidates:
        tmp.extend([[[id, initvalue, 1e37, comment]] for initvalue in initialvalues])
    candidates = tmp

    # Calculate initial stats
    init_stats = pyckett.add_parameter(par, lin, [[]], sort=False)[0]
    init_stats["id"] = ["INITIAL"]
    results = pyckett.add_parameter(
        par, lin, candidates, sort=True, sort_by_wrms=sort_by_wrms
    )
    sort_key = "wrms" if sort_by_wrms else "rms"

    # Test new candidate parameters
    header = "         ID    |    RMS [kHz] |   WRMS | RejLines |  Diverging | Init Value | Final Value "
    prit(report, "")
    prit(report, header)
    prit(report, "-" * len(header))

    best_stats = init_stats
    for i, stats in enumerate(results):
        if (
            stats[sort_key] < best_stats[sort_key]
            and stats["stats"]["rejected_lines"]
            <= best_stats["stats"]["rejected_lines"]
            and stats["stats"]["diverging"] != "LAST"
        ):
            best_stats = stats

        id = stats["id"][0]
        rms = stats["rms"] * 1000
        wrms = stats["stats"]["wrms"]
        initial = stats["params"][-1][1]
        final = stats["par"][-1][1]
        rejected_lines = stats["stats"]["rejected_lines"]
        diverging = stats["stats"]["diverging"]

        prit(
            report,
            f"{id:14} | {rms:12.2f} | {wrms:6.2f} | {rejected_lines:8.0f} | {diverging:10} | {initial:10.2e} | {final:10.2e} ",
        )

    # Final report
    init_value = f'{init_stats[sort_key]*1000 :.2f} kHz' if sort_key == 'rms' else f'{init_stats[sort_key]:.2f}'
    prit(
        report,
        f'\nInitial values were an {sort_key.upper()} of {init_value}, {init_stats["stats"]["rejected_lines"]} rejected lines, and diverging {init_stats["stats"]["diverging"]}.',
    )
    best_value = f'{best_stats[sort_key]*1000 :.2f} kHz' if sort_key == 'rms' else f'{best_stats[sort_key]:.2f}'
    prit(
        report,
        f'\nBest run is parameter {best_stats["id"][0]} with a final parameter value of {best_stats["par"][-1][1]:.2e}, {sort_key.upper()} of {best_value}, {best_stats["stats"]["rejected_lines"]} rejected lines, and diverging {best_stats["stats"]["diverging"]}.',
    )

    if bestparfile is not None:
        with open(bestparfile, "w+") as file:
            save_par = par.copy()
            save_par["PARAMS"] = best_stats["par"]
            file.write(pyckett.dict_to_parvar(save_par))
        prit(report, '\nWrote the best run to "best.par".')
    return (init_stats, best_stats, results)

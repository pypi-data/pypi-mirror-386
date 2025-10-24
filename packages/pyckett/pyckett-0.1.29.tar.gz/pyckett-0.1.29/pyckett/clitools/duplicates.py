#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Luis Bonah
# Description : CLI tool for showing parameter uncertainties

import os
import argparse
import pyckett

def duplicates():
    parser = argparse.ArgumentParser(prog="Remove duplicates from *.lin file")

    parser.add_argument("linfile", type=str, help="Filename of the .lin file")
    parser.add_argument(
        "--keep",
        type=str,
        nargs=1,
        help="Which values to keep ('first' or 'last')",
        default='last',
    )
    parser.add_argument("--sort", action='store_true')

    args = parser.parse_args()


    linfname = args.linfile
    keep = args.keep
    sort = args.sort

    try:
        lin = pyckett.lin_to_df(linfname, sort=False)
    except FileNotFoundError:
        linfname = str(linfname) + '.lin'
        lin = pyckett.lin_to_df(linfname, sort=False)
    
    if '.lin' in linfname:
        duplicatesfname = linfname.replace('.lin', '_duplicates.lin')
    else:
        duplicatesfname = f'{linfname}_duplicates.lin'


    qn_labels = [f'qn{ul}{i+1}' for ul in 'ul' for i in range(pyckett.QUANTA)]
    duplicates = lin[lin.duplicated(subset=qn_labels, keep=keep)]
    n_duplicates = len(duplicates)
    non_duplicates = lin.drop_duplicates(subset=qn_labels, keep=keep)

    if sort:
        non_duplicates = non_duplicates.sort_values(["x", "error"])
        duplicates = duplicates.sort_values(["x", "error"])

    with open(duplicatesfname, 'w+') as file:
        file.write(pyckett.df_to_lin(duplicates))
    
    with open(linfname, 'w+') as file:
        file.write(pyckett.df_to_lin(non_duplicates))


    print(f'Removed {n_duplicates} duplicates from your *.lin file.')
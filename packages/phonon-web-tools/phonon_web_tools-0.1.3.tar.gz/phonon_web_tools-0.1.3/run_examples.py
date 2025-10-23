#!/usr/bin/env python

from pathlib import Path

from phonon_web_tools import convert_qe_phonon_folder

base_folder = Path(__file__).parent.parent / "./data"

required_files = {"scf.in", "scf.out", "matdyn.modes"}

for folder in base_folder.iterdir():
    if folder.is_dir():
        files = {f.name for f in folder.iterdir() if f.is_file()}
        if required_files.issubset(files):
            print("----")
            print(f"Converting {folder}")
            out_file = base_folder / f"{folder.name}.json"
            convert_qe_phonon_folder(folder, out_file=out_file)

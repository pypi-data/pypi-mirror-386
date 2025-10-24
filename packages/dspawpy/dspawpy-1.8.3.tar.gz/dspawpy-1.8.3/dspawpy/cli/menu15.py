import os
from typing import Literal

from loguru import logger
from prompt_toolkit import prompt

from dspawpy import auto_test_cli
from dspawpy.cli import list_ds, pc_h5
from dspawpy.cli.menu_prompts import Dio, Dresponse, Dselect


def s15_1(language: Literal["EN", "CN"]) -> dict:
    """View the HDF5 data structure.

    h5glance name.h5
    """
    if auto_test_cli:
        for D in list_ds:
            if D["menu"] == 151:
                os.system(f"h5glance {D['h5file']}")
        D = {}
    else:
        D = {}
        D["menu"] = 151
        D["h5file"] = prompt(Dio[language]["h5file"], completer=pc_h5)
        os.system(f"h5glance {D['h5file']}")
    return D


def s15_2(language: Literal["EN", "CN"]) -> dict:
    """View the contents of HDF5 data.

    Supports viewing data for a single key, and Unix systems also support viewing data for all keys (using less for pagination)
    Windows systems do not have less; they will print out all the content directly.
    (Suggest using the HDFViewer window program instead of dspawpy)

    h5glance name.h5 -
    ptdump -d name.h5
    """
    if auto_test_cli:
        from platform import system as cli_system

        for D in list_ds:
            if D["menu"] == 152:
                if D["is_all"] == "y":
                    if cli_system() == "Windows":
                        cmd = f"ptdump -d {D['h5file']}"
                    else:
                        cmd = f"ptdump -d {D['h5file']} | less"
                    os.system(cmd)
                else:
                    cmd = f"h5glance {D['h5file']} -"
                    os.system(cmd)
        D = {}
    else:
        D = {}
        D["menu"] = 152
        D["h5file"] = prompt(Dio[language]["h5file"], completer=pc_h5)
        D["is_all"] = prompt(Dselect[language][18])
        if D["is_all"] == "y":
            from platform import system

            # requires PyTables, `pip install tables`
            if system() == "Windows":
                cmd = f"ptdump -d {D['h5file']}"
            else:
                cmd = f"ptdump -d {D['h5file']} | less"

            os.system(cmd)
        else:
            while True:
                logger.info(Dresponse[language][15])
                cmd = f"h5glance {D['h5file']} -"
                os.system(cmd)
                if prompt(Dselect[language][19]) != "y":
                    break
    return D

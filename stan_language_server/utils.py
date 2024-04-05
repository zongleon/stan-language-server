from typing import Tuple, List
from urllib.parse import urlparse

import csv
import re
import subprocess

FUNCTIONS = "stan-functions.txt"

def query_stanc_ast(uri: str) -> str:
    stanc = subprocess.run(
        ["stanc", "--debug-decorated-ast", uri], stdout=subprocess.PIPE
    )
    ast = stanc.stdout.decode()

    return str(ast)


def get_stanc_errors(file: str, path: str) -> str:
    """Ask stanc to compile, return errors if they exist."""
    stanc = subprocess.run(
        ["stanc", "--filename-in-msg", urlparse(file).path, "--warn-pedantic", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out = stanc.stderr.decode()
    return out


def parse_location(err: str) -> Tuple[int, int, int]:
    """From the error string, parse out the location of the error."""
    sections = err.split(",")
    line = sections[1]
    cols = sections[2].split("to")

    lineno = re.search(r"line (\d+)", line)
    
    if lineno == None:
        return (0, 0, 0)
    
    lineno = int(lineno.group(1))
    start = end = int(re.search(r"column (\d+)", cols[0]).group(1))

    if len(cols) == 2:
        end = int(re.search(r"column (\d+)", cols[1]).group(1))

    return (lineno - 1, start, end)


def get_signatures() -> List[Tuple[str, str, str, str]]:
    """Get a list of function signatures."""
    funcs = []
    with open(FUNCTIONS, "r") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        for row in reader:
            sig = row["Arguments"] + " -> " + row["ReturnType"]
            funcs.append((row["StanFunction"], sig, row["Documentation"]))

    return funcs
from typing import Tuple
from urllib.parse import urlparse

import re
import subprocess


def query_stanc_ast(uri: str) -> str:
    stanc = subprocess.run(
        ["stanc", "--debug-decorated-ast", uri], stdout=subprocess.PIPE
    )
    ast = stanc.stdout.decode()

    return str(ast)


def get_stanc_errors(uri: str) -> str:
    """Ask stanc to compile, return errors if they exist."""
    path = urlparse(uri).path
    stanc = subprocess.run(
        ["stanc", "--warn-pedantic", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out = stanc.stderr.decode()
    return out


def parse_location(err: str) -> Tuple[int, int, int]:
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

    return (lineno - 1, start - 1, end - 1)

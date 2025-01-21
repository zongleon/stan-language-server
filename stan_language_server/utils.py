from typing import Tuple, List, Dict
from urllib.parse import urlparse

import csv

# from functools import lru_cache
import json
import os
import re
import subprocess
import tempfile

from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionItemLabelDetails,
)

FUNCTIONS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "stan-functions.txt"
)
KEYWORDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stan-keywords.txt")

STAN_PATH = None

def set_stan_path(stan_path):
    global STAN_PATH
    STAN_PATH = stan_path

def get_completions() -> List[CompletionItem]:
    func_list = read_signatures()
    items = []
    for name, sig, doc in func_list:
        item = CompletionItem(
            label=name,
            label_details=CompletionItemLabelDetails(detail=sig),
            documentation=doc,
            kind=CompletionItemKind.Function,
        )
        items.append(item)

    return items


def get_keywords() -> List[CompletionItem]:
    kw_list = read_keywords()
    items = []
    for name, type in kw_list:
        kind = CompletionItemKind.Keyword
        if type == "function":
            kind = CompletionItemKind.Function
        item = CompletionItem(
            label=name,
            kind=kind,
        )
        items.append(item)

    return items

def query_stanc_ast(uri: str) -> str:
    stanc = subprocess.run(
        [STAN_PATH, "--debug-decorated-ast", uri], stdout=subprocess.PIPE
    )
    ast = stanc.stdout.decode()

    return str(ast)


def get_stanc_errors(uri: str, src: str) -> str:
    """Ask stanc to compile, return errors if they exist."""

    tf = tempfile.NamedTemporaryFile("w", delete=False)
    tf.write(src)
    tf.close()

    stanc = subprocess.run(
        [
            STAN_PATH,
            "--filename-in-msg",
            urlparse(uri).path,
            "--warn-pedantic",
            tf.name,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out = stanc.stderr.decode()

    os.unlink(tf.name)
    return out


def parse_stanc_info(stanc_info: Dict) -> List[CompletionItem]:

    blocks = ["inputs", "parameters", "transformed parameters", "generated quantities"]
    items = []
    for block in blocks:
        stan_block = stanc_info[block]
        for name, info in stan_block.items():
            item = CompletionItem(
                label=name,
                label_details=CompletionItemLabelDetails(detail=info["type"]),
                kind=CompletionItemKind.Variable,
            )
            items.append(item)

    return items


def get_variables(src: str) -> List[CompletionItem]:
    """"""
    tf = tempfile.NamedTemporaryFile("w", delete=False)
    tf.write(src)
    tf.close()

    stanc = subprocess.run(
        [STAN_PATH, "--info", tf.name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stanc_info = json.loads(stanc.stdout.decode())

    os.unlink(tf.name)
    return parse_stanc_info(stanc_info)


def parse_location(err: str) -> Tuple[int, int, int]:
    """From the error string, parse out the location of the error."""
    sections = err.split(",")
    if len(sections) < 3:
        return (0, 0, 0)
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


def read_signatures() -> List[Tuple[str, str, str, str]]:
    """Get a list of function signatures."""
    funcs = []
    with open(FUNCTIONS, "r") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        for row in reader:
            sig = row["Arguments"] + " -> " + row["ReturnType"]
            funcs.append((row["StanFunction"], sig, row["Documentation"]))

    return funcs


def read_keywords() -> List[Tuple[str, str]]:
    """"""
    kws = []
    with open(KEYWORDS, "r") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        for row in reader:
            kws.append((row["Name"], row["Type"]))

    return kws

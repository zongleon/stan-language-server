from typing import Optional

from .utils import (
    get_stanc_errors,
    parse_location,
    get_variables,
    get_completions,
    get_keywords,
)

from pygls.server import LanguageServer
from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    DiagnosticSeverity,
    CompletionList,
    CompletionOptions,
    CompletionParams,
    Diagnostic,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidCloseTextDocumentParams,
    MessageType,
    Range,
    Position,
)
import os
from . import __version__

SERVER = LanguageServer(
    name="stan-language-server",
    version=__version__,
)

COMPLETIONS = get_completions()
KEYWORDS = get_keywords()


@SERVER.feature(
    TEXT_DOCUMENT_COMPLETION,
)
def completion(
    server: LanguageServer, params: CompletionParams
) -> Optional[CompletionList]:
    """Return a list of completions."""
    uri = params.text_document.uri
    src = server.workspace.get_document(uri).source
    lines = src.split("\n")
    line = lines[params.position.line]
    rest = "\n".join(lines[: params.position.line] + lines[params.position.line + 1 :])
    variables = get_variables(rest)

    server.show_message_log(f"# Variables: {len(variables)}", MessageType.Debug)
    server.show_message_log(f"# Funcs: {len(COMPLETIONS)}", MessageType.Debug)

    # rhs of assignment
    if line.find("=") != -1 and line.index("=") < params.position.character:
        return CompletionList(is_incomplete=False, items=COMPLETIONS + variables)
    # rhs of distribution
    elif line.find("~") != -1 and line.index("~") < params.position.character:
        return CompletionList(is_incomplete=False, items=COMPLETIONS)

    # lhs / newline
    return CompletionList(is_incomplete=False, items=variables + KEYWORDS)


def create_diagnostic(
    line: int, start: int, end: int, msg: str, severity: DiagnosticSeverity
) -> Diagnostic:
    """Creates diagnostic based on params"""
    rng = Range(
        start=Position(line=line, character=start),
        end=Position(line=line, character=end),
    )
    diag = Diagnostic(range=rng, message=msg, severity=severity)
    return diag


def refresh_diagnostics(server: LanguageServer, params):
    """Get and parse diagnostic list from stanc utils"""
    uri = params.text_document.uri
    src = server.workspace.get_document(uri).source

    out = get_stanc_errors(uri, src)

    diags = []
    if len(out) == 0:
        server.publish_diagnostics(uri=uri, diagnostics=diags)
        return

    lines = out.split("\n")

    err_type = err_str = None
    errs = []
    for line in lines:
        if line.startswith(("Syntax", "Semantic", "Warning")):
            if err_str != None:
                errs.append((err_type, err_str))
            err_type = line.split(":", maxsplit=1)[0].split(" ", maxsplit=1)[0]
            err_str = ""
        err_str += "\n" + line.strip()
    errs.append((err_type, err_str))

    for typ, err in errs:
        server.show_message_log(err, MessageType.Error)
        lineno, start, end = parse_location(err)
        if typ in ["Syntax", "Semantic"]:
            msg = " ".join(err.split("-\n")[-1].split("\n"))
            diags.append(
                create_diagnostic(lineno, start, end, msg, DiagnosticSeverity.Error)
            )
        else:
            msg = " ".join(err.split("\n")[1:])
            diags.append(
                create_diagnostic(lineno, start, end, msg, DiagnosticSeverity.Warning)
            )

    server.publish_diagnostics(uri=uri, diagnostics=diags)


@SERVER.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(server: LanguageServer, params: DidChangeTextDocumentParams) -> None:
    """Handle document change notification."""
    refresh_diagnostics(server, params)


@SERVER.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(server: LanguageServer, params: DidOpenTextDocumentParams) -> None:
    """Handle document opened notification."""
    refresh_diagnostics(server, params)


@SERVER.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: LanguageServer, params: DidCloseTextDocumentParams) -> None:
    refresh_diagnostics(server, params)

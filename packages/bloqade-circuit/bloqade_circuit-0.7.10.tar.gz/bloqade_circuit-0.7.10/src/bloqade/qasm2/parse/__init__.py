import pathlib

from rich.console import Console

from . import ast as ast
from .build import Build
from .print import Printer as Printer
from .parser import qasm2_parser as lark_parser
from .visitor import Visitor as Visitor


def loads(txt: str):
    raw = lark_parser.parse(txt)
    return Build().build_mainprogram(raw)


def loadfile(file: str | pathlib.Path):
    with open(file) as f:
        return loads(f.read())


def pprint(node: ast.Node, *, console: Console | None = None, no_color: bool = False):
    if console:
        printer = Printer(console)
    else:
        printer = Printer()
    printer.console.no_color = no_color
    printer.visit(node)


def spprint(node: ast.Node, *, console: Console | None = None, no_color: bool = False):
    if console:
        printer = Printer(console)
    else:
        printer = Printer()

    printer.console.no_color = no_color
    with printer.string_io() as stream:
        printer.visit(node)
        return stream.getvalue()

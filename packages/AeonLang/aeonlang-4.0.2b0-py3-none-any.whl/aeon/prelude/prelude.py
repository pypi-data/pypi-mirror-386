from __future__ import annotations

import importlib
from typing import Any

from aeon.sugar.parser import parse_type
from aeon.sugar.stypes import SType
from aeon.utils.name import Name

INTEGER_ARITHMETIC_OPERATORS = ["+", "*", "-", "/", "%"]
COMPARISON_OPERATORS = ["<", ">", "<=", ">="]
LOGICAL_OPERATORS = ["&&", "||"]
EQUALITY_OPERATORS = ["==", "!="]

ALL_OPS = INTEGER_ARITHMETIC_OPERATORS + COMPARISON_OPERATORS + LOGICAL_OPERATORS + EQUALITY_OPERATORS


def p(x):
    print(str(x))
    return 0


def native_import(name):
    return importlib.import_module(name)


native_types: list[Name] = [Name("Unit", 0), Name("Bool", 0), Name("Int", 0), Name("Float", 0), Name("String", 0)]

# TODO: polymorphic signatures
prelude = [
    ("native", "forall a:B, (x:String) -> {x:a | false}", eval),
    ("native_import", "forall a:B, (x:String) -> {x:a | false}", native_import),
    ("print", "forall a:B, (x:a) -> Unit", p),
    ("==", "forall a:B, (x:a) -> (y:a) -> Bool", lambda x: lambda y: x == y),
    ("!=", "forall a:B, (x:a) -> (y:a) -> Bool", lambda x: lambda y: x != y),
    ("<", "forall a:B, (x:a) -> (y:a) -> Bool", lambda x: lambda y: x < y),
    ("<=", "forall a:B, (x:a) -> (y:a) -> Bool", lambda x: lambda y: x <= y),
    (">", "forall a:B, (x:a) -> (y:a) -> Bool", lambda x: lambda y: x > y),
    (">=", "forall a:B, (x:a) -> (y:a) -> Bool", lambda x: lambda y: x >= y),
    ("+", "forall a:B, (x:a) -> (y:a) -> a", lambda x: lambda y: x + y),
    ("-", "forall a:B, (x:a) -> (y:a) -> a", lambda x: lambda y: x - y),
    ("*", "forall a:B, (x:a) -> (y:a) -> a", lambda x: lambda y: x * y),
    ("/", "forall a:B, (x:a) -> (y:a) -> a", lambda x: lambda y: x / y),
    ("%", "(x:Int) -> (y:Int) -> Int", lambda x: lambda y: x % y),
    ("&&", "(x:Bool) -> (y:Bool) -> Bool", lambda x: lambda y: x and y),
    ("||", "(x:Bool) -> (y:Bool) -> Bool", lambda x: lambda y: x or y),
    ("!", "(x:Bool) -> Bool", lambda x: not x),
]

typing_vars: dict[Name, SType] = {}
evaluation_vars: dict[Name, Any] = {}


for n, ty, ex in prelude:
    nn = Name(n, 0)
    typing_vars[nn] = parse_type(ty)
    evaluation_vars[nn] = ex

"""Ein Taschenrechner als Tool.

Sprachmodelle sind überraschend schlecht im Rechnen (sie "raten" die nächste Ziffer).
Mit einem Rechner-Tool rechnet Python – und das rechnet richtig.

Hinweis: Wir benutzen NICHT eval(), denn damit könnte das LLM beliebigen Python-Code
ausführen lassen. Stattdessen erlauben wir nur Zahlen, + - * / ** % und ein paar Funktionen.
"""

import ast
import math
import operator

from agent import tool

# Erlaubte Rechenzeichen
OPERATOREN = {
    ast.Add: operator.add,        # +
    ast.Sub: operator.sub,        # -
    ast.Mult: operator.mul,       # *
    ast.Div: operator.truediv,    # /
    ast.FloorDiv: operator.floordiv,  # //
    ast.Mod: operator.mod,        # %
    ast.Pow: operator.pow,        # **
    ast.USub: operator.neg,       # -x
    ast.UAdd: operator.pos,       # +x
}

# Erlaubte Funktionen und Konstanten
FUNKTIONEN = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "abs": abs, "round": round,
}
KONSTANTEN = {"pi": math.pi, "e": math.e}


def _auswerten(knoten):
    """Rechnet einen (bereits zerlegten) Ausdruck Stück für Stück aus."""
    if isinstance(knoten, ast.Constant) and isinstance(knoten.value, (int, float)):
        return knoten.value
    if isinstance(knoten, ast.BinOp) and type(knoten.op) in OPERATOREN:
        return OPERATOREN[type(knoten.op)](_auswerten(knoten.left), _auswerten(knoten.right))
    if isinstance(knoten, ast.UnaryOp) and type(knoten.op) in OPERATOREN:
        return OPERATOREN[type(knoten.op)](_auswerten(knoten.operand))
    if isinstance(knoten, ast.Name) and knoten.id in KONSTANTEN:
        return KONSTANTEN[knoten.id]
    if isinstance(knoten, ast.Call) and getattr(knoten.func, "id", None) in FUNKTIONEN:
        return FUNKTIONEN[knoten.func.id](*[_auswerten(a) for a in knoten.args])
    raise ValueError("Nicht erlaubter Ausdruck. Erlaubt: Zahlen, + - * / ** %, Klammern, "
                     + ", ".join(list(FUNKTIONEN) + list(KONSTANTEN)))


@tool
def rechner(ausdruck: str) -> dict:
    """Berechnet einen mathematischen Ausdruck exakt. Benutze dieses Tool für JEDE Rechnung,
    statt selbst zu rechnen.

    ausdruck: Rechenausdruck in Python-Schreibweise, z. B. "(17 + 4) * 3", "2 ** 10" oder "sqrt(2)"
    """
    ausdruck = ausdruck.replace("^", "**").replace(",", ".")  # 2^3 und 1,5 auch erlauben
    ergebnis = _auswerten(ast.parse(ausdruck, mode="eval").body)
    return {"ausdruck": ausdruck, "ergebnis": ergebnis}

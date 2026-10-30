"""Exact, dependency-free reconstruction of the accompanying polynomial tables.

Run with Python 3.10 or newer. Input expressions use a restricted arithmetic
parser, never eval/exec. All calculations use fractions.Fraction.
This verifies the stated scalar certificates, not the analytic reductions from
tree messages to these polynomials; those reductions remain in the manuscript.
"""
from __future__ import annotations

import argparse
import ast
from fractions import Fraction as F
import hashlib
import itertools
import json
from math import comb
from pathlib import Path


class Poly:
    def __init__(self, data=0):
        if isinstance(data, Poly):
            self.a = dict(data.a)
        elif isinstance(data, dict):
            self.a = {tuple(k): F(v) for k, v in data.items() if v}
        else:
            self.a = {(0, 0): F(data)} if data else {}

    def __add__(self, rhs):
        out = dict(self.a)
        for e, c in Poly(rhs).a.items():
            out[e] = out.get(e, F(0)) + c
        return Poly(out)

    __radd__ = __add__

    def __neg__(self):
        return Poly({e: -c for e, c in self.a.items()})

    def __sub__(self, rhs):
        return self + (-Poly(rhs))

    def __rsub__(self, lhs):
        return Poly(lhs) - self

    def __mul__(self, rhs):
        out = {}
        for a, b in itertools.product(self.a.items(), Poly(rhs).a.items()):
            e = tuple(x + y for x, y in zip(a[0], b[0]))
            out[e] = out.get(e, F(0)) + a[1] * b[1]
        return Poly(out)

    __rmul__ = __mul__

    def __truediv__(self, rhs):
        divisor = Poly(rhs).a
        if len(divisor) != 1:
            raise ValueError("Only exact monomial/constant division is allowed")
        e, c = next(iter(divisor.items()))
        out = {}
        for p, q in self.a.items():
            k = tuple(a - b for a, b in zip(p, e))
            if min(k) < 0:
                raise ValueError("Nonpolynomial quotient; cancellation must be exact")
            out[k] = q / c
        return Poly(out)

    def __rtruediv__(self, lhs):
        return Poly(lhs) / self

    def __pow__(self, n):
        if not isinstance(n, int) or not 0 <= n <= 128:
            raise ValueError("Exponent must be an integer between zero and 128")
        out, base = Poly(1), self
        while n:
            if n % 2:
                out = out * base
            base = base * base
            n //= 2
        return out

    def derivative(self, axis):
        out = {}
        for e, c in self.a.items():
            if e[axis]:
                p = list(e)
                p[axis] -= 1
                out[tuple(p)] = c * e[axis]
        return Poly(out)

    def compose(self, substitutions):
        out = Poly(0)
        cache = [{0: Poly(1)}, {0: Poly(1)}]
        for e, c in self.a.items():
            term = Poly(c)
            for k in range(2):
                if e[k] not in cache[k]:
                    cache[k][e[k]] = substitutions[k] ** e[k]
                term = term * cache[k][e[k]]
            out = out + term
        return out


X = Poly({(1, 0): F(1)})
Y = Poly({(0, 1): F(1)})


def expression(text, names):
    def read(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return Poly(node.value)
        if isinstance(node, ast.Name) and node.id in names:
            return names[node.id]
        if isinstance(node, ast.UnaryOp):
            a = read(node.operand)
            if isinstance(node.op, ast.USub):
                return -a
            if isinstance(node.op, ast.UAdd):
                return a
        if isinstance(node, ast.BinOp):
            a, b = read(node.left), read(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            if isinstance(node.op, ast.Div):
                return a / b
            if isinstance(node.op, ast.Pow):
                exponent = b.a.get((0, 0), F(0))
                if set(b.a) - {(0, 0)} or exponent.denominator != 1:
                    raise ValueError("Noninteger exponent")
                return a ** int(exponent)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "diff" and len(node.args) == 2 and not node.keywords:
                a, symbol = read(node.args[0]), read(node.args[1])
                if symbol.a == X.a:
                    return a.derivative(0)
                if symbol.a == Y.a:
                    return a.derivative(1)
        raise ValueError("Unsupported expression: " + ast.dump(node))
    return read(ast.parse(text, mode="eval").body)


def coefficients(poly, degree):
    n, m = degree
    if any(i > n or j > m for i, j in poly.a):
        raise ValueError("Printed degree does not cover the polynomial")
    return {(r, s): sum((c * F(comb(r, i), comb(n, i))
                        * F(comb(s, j), comb(m, j))
                        for (i, j), c in poly.a.items() if i <= r and j <= s), F(0))
            for r in range(n + 1) for s in range(m + 1)}


def reconstruct(betas, degree):
    n, m = degree
    out = Poly()
    for (r, s), c in betas.items():
        out += c * comb(n, r) * comb(m, s) * X ** r * (1-X) ** (n-r) * Y ** s * (1-Y) ** (m-s)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).with_name("polynomial_certificates.json"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--check-source", type=Path,
                        help="Optional paper/jgt directory: verify the manifest against these TeX files")
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    results, count = [], 0
    for row in data["certificates"]:
        if len(row["symbols"]) != 2:
            raise ValueError("Exactly two formal symbols are required")
        names = dict(zip(row["symbols"], [X, Y]))
        for name, formula in row["definitions"]:
            if name in names:
                raise ValueError("Duplicate definition " + name)
            names[name] = expression(formula, names)
        original = expression(row["polynomial"], names)
        sub = [expression(row["substitution"][name], {"x": X, "y": Y}) for name in row["symbols"]]
        poly = original.compose(sub)
        expected_power = {tuple(a["degree"]): F(a["coefficient"]) for a in row["power_coefficients"] if F(a["coefficient"])}
        if poly.a != expected_power:
            raise AssertionError(row["id"] + ": polynomial differs from the original defining formulas")
        beta = coefficients(poly, row["degree"])
        expected = {tuple(a["degree"]): F(a["coefficient"]) for a in row["bernstein_coefficients"]}
        if beta != expected or len(expected) != len(row["bernstein_coefficients"]):
            raise AssertionError(row["id"] + ": complete coefficient list mismatch")
        if reconstruct(beta, row["degree"]).a != poly.a:
            raise AssertionError(row["id"] + ": reverse reconstruction mismatch")
        minimum = min(beta.values())
        lower_bound = F(row["lower_bound"])
        if lower_bound < 0 or minimum != F(row["minimum"]) or minimum < 0 or minimum < lower_bound:
            raise AssertionError(row["id"] + ": nonnegative coefficient lower bound mismatch")
        normalization = row.get("coefficient_normalization")
        if normalization:
            normalizer = beta[tuple(normalization["index"])]
            if normalizer <= F(normalization["strict_lower_bound"]):
                raise AssertionError(row["id"] + ": coefficient normalizer lower bound mismatch")
            if minimum < normalizer * F(normalization["relative_lower_bound"]):
                raise AssertionError(row["id"] + ": normalized coefficient lower bound mismatch")
        count += len(beta)
        results.append(dict(id=row["id"], coefficients=len(beta), minimum=str(minimum), passed=True))
    source_checks = []
    if args.check_source:
        for row in data["sources"]:
            relative = Path(row["file"])
            target = (args.check_source / relative).resolve()
            if not target.is_relative_to(args.check_source.resolve()):
                raise ValueError("Source path escapes the selected project")
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != row["sha256"]:
                raise AssertionError("Source revision mismatch: " + row["file"])
            source_checks.append(row["file"])
    report = dict(scope=data["scope"], certificates=len(results), coefficients=count,
                  source_files_checked=source_checks, unexpected_failures=0, results=results)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()

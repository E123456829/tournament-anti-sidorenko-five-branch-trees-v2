"""Exact checks for finite expansions that are not in the certificate tables.

The program recomputes, with fractions.Fraction only:

* Q164.4: the B5 and B4 polynomials obtained from (Q164.4.2);
* Q164.5: the rational point c = 3/8;
* R47.5: the convolution (1-d)R(d)N(d) and the listed coefficients;
* Q75.7.1: the listed rational comparisons.

It checks arithmetic identities, not who performed the computation.  Run with
Python 3.10 or newer; no third-party packages are required.
"""
from fractions import Fraction as F
import json


def add(p, q):
    n = max(len(p), len(q))
    r = [F(0)] * n
    for i, x in enumerate(p):
        r[i] += x
    for i, x in enumerate(q):
        r[i] += x
    return r


def scale(p, c):
    return [c * x for x in p]


def mul(p, q):
    r = [F(0)] * (len(p) + len(q) - 1)
    for i, x in enumerate(p):
        for j, y in enumerate(q):
            r[i + j] += x * y
    return r


def deriv(p):
    return [i * p[i] for i in range(1, len(p))]


def evaluate(p, x):
    out = F(0)
    for c in reversed(p):
        out = out * x + c
    return out


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append({"id": name, "passed": True})


checks = []

# Q164.4: B_a(t) = -4+8*theta^2+a*theta+(4+2a/3)t+(-19/8+61a/16)t^2
theta = F(13, 32)
a5 = [F(11), F(0), F(-24), F(0), F(16)]
a4 = [F(11), F(0), F(-12), F(0), F(4)]


def q164_B(a):
    b = [F(-4) + 8 * theta * theta, F(0), F(-19, 8)]
    b = add(b, scale(a, theta))
    b = add(b, [F(0), F(4)])
    b = add(b, [F(0)] + scale(a, F(2, 3)))
    b = add(b, [F(0), F(0)] + scale(a, F(61, 16)))
    return b


B5_expected = [F(229, 128), F(34, 3), F(477, 16), F(-16), F(-85), F(32, 3), F(61)]
B4_expected = [F(229, 128), F(34, 3), F(555, 16), F(-8), F(-353, 8), F(8, 3), F(61, 4)]
check("Q164.4/B5", q164_B(a5) == B5_expected)
check("Q164.4/B4", q164_B(a4) == B4_expected)

# Q164.5: R0(c) and R0'(c) at c = 3/8
R0 = [F(539, 128), F(-34, 3), F(-189, 16), F(0), F(1414, 15)]
c = F(3, 8)
check("Q164.5/R0(c)", evaluate(R0, c) == F(1679, 10240))
check("Q164.5/R0'(c)", evaluate(deriv(R0), c) == F(-37, 120))

# R47.5: P(d) = (1-d) R(d) N(d)
R = [F(1), F(-413, 57), F(1591, 57), F(-125, 3), F(33, 8), F(127, 8)]
N = [F(1), F(102, 19), F(7995, 722), F(8105, 722), F(34665, 5776), F(588, 361), F(64, 361)]
P = mul(R, N)
P = P[:12]
expected = {
    1: F(-107, 57),
    2: F(191, 2166),
    3: F(1612016, 41154),
    4: F(4671427, 329232),
    5: F(-50007635, 329232),
    6: F(-59573162, 329232),
    7: F(5337151, 329232),
}
for j, value in expected.items():
    check(f"R47.5/c{j}", P[j] == value)
n = {j: N[j] for j in range(1, 7)}
check("R47.5/c8", P[8] == F(127, 8) * n[3] + F(33, 8) * n[4] - F(125, 3) * n[5] + F(1591, 57) * n[6])
check("R47.5/c9", P[9] == F(127, 8) * n[4] + F(33, 8) * n[5] - F(125, 3) * n[6])
check("R47.5/c10", P[10] == F(127, 8) * n[5] + F(33, 8) * n[6])
check("R47.5/c11", P[11] == F(127, 8) * n[6])
check("R47.5/c3<40", P[3] < 40)
check("R47.5/c4<15", P[4] < 15)
check("R47.5/c5<-151", P[5] < -151)
check("R47.5/c6>-182", P[6] > -182)
check("R47.5/c7>0", P[7] > 0)
check("R47.5/c8>0", P[8] > 0)
check("R47.5/c9>0", P[9] > 0)
check("R47.5/c10>0", P[10] > 0)
check("R47.5/c11>0", P[11] > 0)

# Q75.7.1: exact rational comparisons
left = F(1184625, 1048576)
check("Q75.7.1/left<113/100", left < F(113, 100))
diff = F(2947, 2592) - F(113, 100)
check("Q75.7.1/difference", diff == F(451, 64800))
check("Q75.7.1/difference>1/160", diff > F(1, 160))
check("Q75.7.1/combination<-1/160", -F(2947, 2592) + left < -F(1, 160))

print(json.dumps({"scope": "Exact finite expansions not covered by the certificate tables",
                  "checks": len(checks), "unexpected_failures": 0}, indent=2))

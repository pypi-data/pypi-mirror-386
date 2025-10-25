# QTQP

The cutie QP solver implements a primal-dual interior point method for solving
convex quadratic programs (QPs). It solves primal QP problem:

```
    min. (1/2) x.T @ p @ x + c.T @ x
    s.t. a @ x + s = b
         s[:z] == 0
         s[z:] >= 0
```

With dual:

```
    max. -(1/2) x.T @ p @ x - b.T @ y
    s.t. p @ x + a.T @ y = -c
         y[z:] >= 0
```

With data `a, b, c, p, z` and variables `x, y, s`. It will return a primal-dual
solution should one exist, or a certificate of primal or dual infeasibility
otherwise.

The current status is 'early research prototype, not ready for prime time'.

## Installation

To install, first clone the repository:

```bash
git clone https://github.com/google-deepmind/qtqp.git
cd qtqp
```

Then, assuming conda is installed, create a new conda environment:

```bash
conda create -n tmp python=3.12
conda activate tmp
```

Finally, install the package:

```bash
python -m pip install .
```

To run the tests, inside the qtqp directory:

```bash
python -m pytest .
```

Note tests will fail for linear solvers that are not installed on your system.

## Usage

Here is an example usage (taken from
[here](https://www.cvxgrp.org/scs/examples/python/basic_qp.html#py-basic-qp)):

```python
import qtqp
import scipy
import numpy as np

# Set up the problem data
p = scipy.sparse.csc_matrix([[3.0, -1.0], [-1.0, 2.0]])
a = scipy.sparse.csc_matrix([[-1.0, 1.0], [1.0, 0.0], [0.0, 1.0]])
b = np.array([-1, 0.3, -0.5])
c = np.array([-1.0, -1.0])

# Initialize solver
solver = qtqp.QTQP(p=p, a=a, b=b, c=c, z=1)
# Solve!
sol = solver.solve()
print(f'{sol.x=}')
print(f'{sol.y=}')
print(f'{sol.s=}')
```

You should see something like

```
| QTQP v0.0.1: m=3, n=2, z=1, nnz(A)=4, nnz(P)=4, linear_solver=SCIPY
|------|------------|------------|----------|----------|----------|----------|----------|----------|----------|----------|----------|
| iter |      pcost |      dcost |     pres |     dres |      gap |   infeas |       mu |    sigma |    alpha |  q, p, c |     time |
|------|------------|------------|----------|----------|----------|----------|----------|----------|----------|----------|----------|
|    0 |  1.205e+00 |  1.298e+00 | 2.18e-01 | 6.17e-01 | 9.36e-02 | 1.67e+00 | 1.09e+00 | 5.69e-04 | 1.00e+00 |  1, 1, 1 | 1.39e-02 |
|    1 |  1.161e+00 |  1.211e+00 | 3.16e-02 | 5.23e-02 | 5.01e-02 | 1.35e+00 | 1.04e-01 | 1.65e-03 | 9.04e-01 |  1, 1, 1 | 1.46e-02 |
|    2 |  1.234e+00 |  1.235e+00 | 3.77e-04 | 8.61e-04 | 6.64e-04 | 1.30e+00 | 7.67e-03 | 4.87e-06 | 9.98e-01 |  1, 1, 1 | 1.52e-02 |
|    3 |  1.235e+00 |  1.235e+00 | 3.78e-06 | 8.62e-06 | 6.65e-06 | 1.30e+00 | 1.25e-04 | 8.80e-12 | 1.00e+00 |  1, 1, 1 | 1.57e-02 |
|    4 |  1.235e+00 |  1.235e+00 | 3.78e-08 | 8.62e-08 | 6.65e-08 | 1.30e+00 | 1.25e-06 | 8.80e-18 | 1.00e+00 |  1, 1, 1 | 1.63e-02 |
|------|------------|------------|----------|----------|----------|----------|----------|----------|----------|----------|----------|
| Solved
sol.x=array([ 0.29999999, -0.69999997])
sol.y=array([2.69999964e+00, 2.09999968e+00, 3.86572055e-07])
sol.s=array([0.00000000e+00, 7.13141634e-09, 1.99999944e-01])
```

## Linear solvers

By default `scipy.linalg.factorized` is used to factorize the linear systems
that arise in each step of the interior point algorithm (explicitly specified in
the `solve` method via `linear_solver=qtqp.LinearSolver.SCIPY`). However, this
may not be the fastest option. QTQP supports several other linear solvers that
may be faster or more reliable for your problem.

#### MKL Pardiso

Pardiso is available via the pydiso package (only available for Intel CPUs). To
install

```bash
conda install pydiso --channel conda-forge
```

To use

```python
sol = solver.solve(linear_solver=qtqp.LinearSolver.PARDISO)
```

#### QDLDL

To install QDLDL

```bash
python -m pip install qdldl
```

To use

```python
sol = solver.solve(linear_solver=qtqp.LinearSolver.QDLDL)
```

#### CHOLMOD

Cholmod is available in the scikit sparse package. To install

```bash
conda install -c conda-forge scikit-sparse
```

To use

```python
sol = solver.solve(linear_solver=qtqp.LinearSolver.CHOLMOD)
```

#### Nvidia cuDSS

cuDSS uses a GPU accelerated direct solver (requires a GPU). To install

```bash
python -m pip install nvidia-cudss-cu12
python -m pip install nvmath-python[cu12]
```

To use

```python
sol = solver.solve(linear_solver=qtqp.LinearSolver.CUDSS)
```

## Citing this work

Coming soon, in the meantime the closest work is:

```
@article{odonoghue:21,
    author       = {Brendan O'Donoghue},
    title        = {Operator Splitting for a Homogeneous Embedding of the Linear Complementarity Problem},
    journal      = {{SIAM} Journal on Optimization},
    month        = {August},
    year         = {2021},
    volume       = {31},
    issue        = {3},
    pages        = {1999-2023},
}
```

## License and disclaimer

Copyright 2025 Google LLC

All software is licensed under the Apache License, Version 2.0 (Apache 2.0); you
may not use this file except in compliance with the Apache 2.0 license. You may
obtain a copy of the Apache 2.0 license at:
https://www.apache.org/licenses/LICENSE-2.0

All other materials are licensed under the Creative Commons Attribution 4.0
International License (CC-BY). You may obtain a copy of the CC-BY license at:
https://creativecommons.org/licenses/by/4.0/legalcode

Unless required by applicable law or agreed to in writing, all software and
materials distributed here under the Apache 2.0 or CC-BY licenses are
distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied. See the licenses for the specific language governing
permissions and limitations under those licenses.

This is not an official Google product.

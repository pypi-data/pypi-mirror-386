#  Copyright (c) 2025 AIRBUS and its affiliates.
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.
import pytest

from discrete_optimization.binpack.solvers.cpsat import (
    CpSatBinPackSolver,
    ModelingBinPack,
)
from discrete_optimization.generic_tools.cp_tools import ParametersCp


@pytest.mark.parametrize(
    "modeling",
    [ModelingBinPack.BINARY, ModelingBinPack.SCHEDULING],
)
def test_cpsat(modeling, problem, manual_sol, manual_sol2):
    solver = CpSatBinPackSolver(problem=problem)
    solver.init_model(upper_bound=20, modeling=modeling)
    p = ParametersCp.default_cpsat()
    solve_kwargs = dict(
        parameters_cp=p,
        time_limit=3,
    )
    res = solver.solve(**solve_kwargs)
    sol = res[-1][0]
    assert problem.satisfy(sol)

    # check warm start
    if manual_sol.allocation == sol.allocation:
        # ensure using different sol as warm start
        manual_sol = manual_sol2
    assert manual_sol.allocation != sol.allocation
    solver.set_warm_start(manual_sol)
    res = solver.solve(**solve_kwargs)
    sol = res[-1][0]
    assert problem.satisfy(sol)
    assert manual_sol.allocation == sol.allocation

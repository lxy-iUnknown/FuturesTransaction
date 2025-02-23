import dataclasses


@dataclasses.dataclass(eq=False, frozen=True)
class OptimizeParams:
    seed: int
    iteration_count: int
    initial_x: tuple[float, ...] | None


# 253895.63999999993
OPTIMIZE_PARAMS = OptimizeParams(42, 10000000, (
    4, 2196, 483, 35.09047031280772, 5.008687445577936, 253.76285553792354, 0.028627550629621343
))

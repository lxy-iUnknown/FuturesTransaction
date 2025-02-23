from nevergrad.parametrization.data import Scalar


class Real(Scalar):
    def __init__(self, name: str, lower: float | None = None, upper: float | None = None):
        if lower is None and upper is None:
            init = 0.0
        elif lower is None:
            init = upper
        elif upper is None:
            init = lower
        else:
            init = (lower + upper) / 2.0
        super().__init__(init=init, lower=lower, upper=upper)
        self.set_name(name)


class Integer(Real):
    def __init__(self, name: str, lower: int | None = None, upper: int | None = None):
        super().__init__(name, float(lower), float(upper))
        self.set_integer_casting()

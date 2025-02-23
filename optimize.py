import os
import pathlib
from concurrent.futures import ProcessPoolExecutor

from nevergrad.optimization.optimizerlib import DifferentialEvolution
from nevergrad.parametrization.parameter import Instrumentation
from numpy.random import RandomState

from core.transaction_profit import TransactionProfit
from data.data_io import load_data
from util.optimize_params import OPTIMIZE_PARAMS
from util.param_logger import ParamLogger
from util.parameter import Integer, Real
from util.transaction_params import TransactionParams


class Worker:
    # Each worker process has its own copy of this variable
    transaction: TransactionProfit

    @classmethod
    def initializer(cls):
        # This function will be executed ONCE per worker process
        # So pickling overhead is minimized
        cls.transaction = TransactionProfit()

    @classmethod
    def objective_function(cls, *args):
        return -cls.transaction.with_params(TransactionParams(*args)).transact()


if __name__ == '__main__':
    length = len(load_data())


    def constraint_function(args):
        x = args[0]
        # T + M <= length - 1 and R <= length - T
        return x[0] + x[1] <= length - 1 and x[0] + x[2] <= length


    # Parameter ranges
    parameters = Instrumentation(
        Integer('T', 1, length - 1),
        Integer('M', 1, length),
        Integer('R', 1, length),
        Real('N', 0),
        Real('K', 0),
        Real('P', 0),
        Real('Q', 0, 1),
    ).set_name(TransactionParams.__name__)
    # Constraints
    parameters.register_cheap_constraint(constraint_function)

    # Set global random seed to produce deterministic results
    parameters.random_state = RandomState(OPTIMIZE_PARAMS.seed)

    num_workers = min(os.cpu_count() or 1, 1)  # At least one
    CustomDE = DifferentialEvolution(
        crossover='twopoints',  # noqa
        high_speed=True,
        popsize='large',
        propagate_heritage=True,
    )
    optimizer = CustomDE(
        budget=OPTIMIZE_PARAMS.iteration_count,
        num_workers=num_workers,
        parametrization=parameters,
    )

    initial_x = OPTIMIZE_PARAMS.initial_x
    if initial_x:
        optimizer.suggest(*initial_x)

    with open(pathlib.Path(__file__).parent / 'params.log', 'w', encoding='utf-8') as f:
        optimizer.register_callback('tell', ParamLogger(f))
        with ProcessPoolExecutor(num_workers, initializer=Worker.initializer) as executor:
            # noinspection PyTypeChecker
            result = optimizer.minimize(
                Worker.objective_function,
                batch_mode=False,
                executor=executor,
            )
            print(result.args, result.loss)

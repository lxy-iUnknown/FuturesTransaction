import datetime
import math
import typing

import tqdm

from nevergrad.optimization import Optimizer
from nevergrad.parametrization.core import Parameter


class ParamLogger:
    def __init__(self, file: typing.IO):
        self._min_loss = math.inf
        self._progress = None
        self._file = file

    def __call__(self, optimizer: Optimizer, candidate: Parameter, loss: float):
        progress = self._progress
        if progress is None:
            progress = self._progress = tqdm.tqdm(total=optimizer.budget)
        min_loss = self._min_loss
        if loss < min_loss:
            min_loss = self._min_loss = loss
            min_loss_str = f'min loss: {min_loss}'
            progress.set_postfix_str(min_loss_str, refresh=False)
            self._file.write(f'[{datetime.datetime.now().isoformat(sep=' ')}]'
                             f'{min_loss_str}, args: {candidate.args}\n')
            self._file.flush()
        progress.update(1)

from enum import Enum
from typing import Callable, Protocol, Union
import pandas as pd


class EffectDirection(Enum):
    positive = 1
    negative = -1
    # bounded = "bounded"


class PerturbationDirection(Enum):
    increasing = 1  # X increase
    decreasing = -1  # X decrease
    binary = 0

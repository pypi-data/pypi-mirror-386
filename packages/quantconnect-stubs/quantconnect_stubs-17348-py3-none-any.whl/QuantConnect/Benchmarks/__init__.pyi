from typing import overload
from enum import IntEnum
import abc
import datetime
import typing

import QuantConnect
import QuantConnect.Benchmarks
import QuantConnect.Data.Market
import QuantConnect.Securities
import System


class IBenchmark(metaclass=abc.ABCMeta):
    """Specifies how to compute a benchmark for an algorithm"""

    def evaluate(self, time: typing.Union[datetime.datetime, datetime.date]) -> float:
        """
        Evaluates this benchmark at the specified time
        
        :param time: The time to evaluate the benchmark at
        :returns: The value of the benchmark at the specified time.
        """
        ...


class SecurityBenchmark(System.Object, QuantConnect.Benchmarks.IBenchmark):
    """Creates a benchmark defined by the closing price of a security instance"""

    @property
    def security(self) -> QuantConnect.Securities.Security:
        """The benchmark security"""
        ...

    def __init__(self, security: QuantConnect.Securities.Security) -> None:
        """Initializes a new instance of the SecurityBenchmark class"""
        ...

    @staticmethod
    def create_instance(securities: QuantConnect.Securities.SecurityManager, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract]) -> QuantConnect.Benchmarks.SecurityBenchmark:
        """
        Helper function that will create a security with the given SecurityManager
        for a specific symbol and then create a SecurityBenchmark for it
        
        :param securities: SecurityService to create the security
        :param symbol: The symbol to create a security benchmark with
        :returns: The new SecurityBenchmark.
        """
        ...

    def evaluate(self, time: typing.Union[datetime.datetime, datetime.date]) -> float:
        """
        Evaluates this benchmark at the specified time in units of the account's currency.
        
        :param time: The time to evaluate the benchmark at
        :returns: The value of the benchmark at the specified time
        in units of the account's currency.
        """
        ...


class FuncBenchmark(System.Object, QuantConnect.Benchmarks.IBenchmark):
    """Creates a benchmark defined by a function"""

    @overload
    def __init__(self, py_func: typing.Any) -> None:
        """
        Create a function benchmark from a Python function
        
        :param py_func: 
        """
        ...

    @overload
    def __init__(self, benchmark: typing.Callable[[datetime.datetime], float]) -> None:
        """
        Initializes a new instance of the FuncBenchmark class
        
        :param benchmark: The functional benchmark implementation
        """
        ...

    def evaluate(self, time: typing.Union[datetime.datetime, datetime.date]) -> float:
        """
        Evaluates this benchmark at the specified time
        
        :param time: The time to evaluate the benchmark at
        :returns: The value of the benchmark at the specified time.
        """
        ...



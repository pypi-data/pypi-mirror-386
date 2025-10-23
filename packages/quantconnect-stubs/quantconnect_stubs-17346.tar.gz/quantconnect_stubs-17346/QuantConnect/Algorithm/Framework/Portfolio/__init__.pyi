from typing import overload
from enum import IntEnum
import abc
import datetime
import typing

import QuantConnect
import QuantConnect.Algorithm
import QuantConnect.Algorithm.Framework
import QuantConnect.Algorithm.Framework.Alphas
import QuantConnect.Algorithm.Framework.Portfolio
import QuantConnect.Data.Market
import QuantConnect.Data.UniverseSelection
import QuantConnect.Indicators
import QuantConnect.Interfaces
import QuantConnect.Python
import QuantConnect.Scheduling
import QuantConnect.Securities
import System
import System.Collections.Generic

LinearConstraint = typing.Any


class ReturnsSymbolData(System.Object):
    """Contains returns specific to a symbol required for optimization model"""

    @property
    def roc(self) -> QuantConnect.Indicators.RateOfChange:
        """The symbol's asset rate of change indicator"""
        ...

    @property
    def returns(self) -> System.Collections.Generic.Dictionary[datetime.datetime, float]:
        """Historical returns"""
        ...

    def __init__(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], lookback: int, period: int) -> None:
        """
        Initializes a new instance of the ReturnsSymbolData class
        
        :param symbol: The symbol of the data that updates the indicators
        :param lookback: Look-back period for the RateOfChange indicator
        :param period: Size of rolling window that contains historical RateOfChange
        """
        ...

    def add(self, time: typing.Union[datetime.datetime, datetime.date], value: float) -> None:
        """
        Adds an item to this window and shifts all other elements
        
        :param time: The time associated with the value
        :param value: The value to use to update this window
        """
        ...

    def reset(self) -> None:
        """Resets all indicators of this object to its initial state"""
        ...

    def update(self, time: typing.Union[datetime.datetime, datetime.date], value: float) -> bool:
        """
        Updates the state of the RateOfChange with the given value and returns true
        if this indicator is ready, false otherwise
        
        :param time: The time associated with the value
        :param value: The value to use to update this indicator
        :returns: True if this indicator is ready, false otherwise.
        """
        ...


class ReturnsSymbolDataExtensions(System.Object):
    """Extension methods for ReturnsSymbolData"""

    @staticmethod
    def form_returns_matrix(symbol_data: System.Collections.Generic.Dictionary[QuantConnect.Symbol, QuantConnect.Algorithm.Framework.Portfolio.ReturnsSymbolData], symbols: typing.List[QuantConnect.Symbol]) -> typing.List[float]:
        """
        Converts a dictionary of ReturnsSymbolData keyed by Symbol into a matrix
        
        :param symbol_data: Dictionary of ReturnsSymbolData keyed by Symbol to be converted into a matrix
        :param symbols: List of Symbol to be included in the matrix
        """
        ...


class IPortfolioOptimizer(metaclass=abc.ABCMeta):
    """Interface for portfolio optimization algorithms"""

    def optimize(self, historical_returns: typing.List[float], expected_returns: typing.List[float] = None, covariance: typing.List[float] = None) -> typing.List[float]:
        """
        Perform portfolio optimization for a provided matrix of historical returns and an array of expected returns
        
        :param historical_returns: Matrix of annualized historical returns where each column represents a security and each row returns for the given date/time (size: K x N).
        :param expected_returns: Array of double with the portfolio annualized expected returns (size: K x 1).
        :param covariance: Multi-dimensional array of double with the portfolio covariance of annualized returns (size: K x K).
        :returns: Array of double with the portfolio weights (size: K x 1).
        """
        ...


class UnconstrainedMeanVariancePortfolioOptimizer(System.Object, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer):
    """Provides an implementation of a portfolio optimizer with unconstrained mean variance."""

    def optimize(self, historical_returns: typing.List[float], expected_returns: typing.List[float] = None, covariance: typing.List[float] = None) -> typing.List[float]:
        """
        Perform portfolio optimization for a provided matrix of historical returns and an array of expected returns
        
        :param historical_returns: Matrix of historical returns where each column represents a security and each row returns for the given date/time (size: K x N).
        :param expected_returns: Array of double with the portfolio annualized expected returns (size: K x 1).
        :param covariance: Multi-dimensional array of double with the portfolio covariance of annualized returns (size: K x K).
        :returns: Array of double with the portfolio weights (size: K x 1).
        """
        ...


class IPortfolioTarget(metaclass=abc.ABCMeta):
    """
    Represents a portfolio target. This may be a percentage of total portfolio value
    or it may be a fixed number of shares.
    """

    @property
    @abc.abstractmethod
    def symbol(self) -> QuantConnect.Symbol:
        """Gets the symbol of this target"""
        ...

    @property
    @abc.abstractmethod
    def quantity(self) -> float:
        """Gets the quantity of this symbol the algorithm should hold"""
        ...

    @property
    @abc.abstractmethod
    def tag(self) -> str:
        """Portfolio target tag with additional information"""
        ...


class IPortfolioConstructionModel(QuantConnect.Algorithm.Framework.INotifiedSecurityChanges, metaclass=abc.ABCMeta):
    """Algorithm framework model that"""

    def create_targets(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> typing.Iterable[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]:
        """
        Create portfolio targets from the specified insights
        
        :param algorithm: The algorithm instance
        :param insights: The insights to create portfolio targets from
        :returns: An enumerable of portfolio targets to be sent to the execution model.
        """
        ...


class PortfolioConstructionModelPythonWrapper(QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModel):
    """Provides an implementation of IPortfolioConstructionModel that wraps a PyObject object"""

    @property
    def rebalance_on_security_changes(self) -> bool:
        """True if should rebalance portfolio on security changes. True by default"""
        ...

    @rebalance_on_security_changes.setter
    def rebalance_on_security_changes(self, value: bool) -> None:
        ...

    @property
    def rebalance_on_insight_changes(self) -> bool:
        """True if should rebalance portfolio on new insights or expiration of insights. True by default"""
        ...

    @rebalance_on_insight_changes.setter
    def rebalance_on_insight_changes(self, value: bool) -> None:
        ...

    def __init__(self, model: typing.Any) -> None:
        """
        Constructor for initialising the IPortfolioConstructionModel class with wrapped PyObject object
        
        :param model: Model defining how to build a portfolio from alphas
        """
        ...

    def create_targets(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> typing.Iterable[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]:
        """
        Create portfolio targets from the specified insights
        
        :param algorithm: The algorithm instance
        :param insights: The insights to create portfolio targets from
        :returns: An enumerable of portfolio targets to be sent to the execution model.
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Will determine the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: The active insights to generate a target for
        :returns: A target percent for each insight.
        """
        ...

    def get_target_insights(self) -> typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]:
        """
        Gets the target insights to calculate a portfolio target percent for
        
        
        This codeEntityType is protected.
        
        :returns: An enumerable of the target insights.
        """
        ...

    def is_rebalance_due(self, insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight], algorithm_utc: typing.Union[datetime.datetime, datetime.date]) -> bool:
        """
        Determines if the portfolio should be rebalanced base on the provided rebalancing func,
        if any security change have been taken place or if an insight has expired or a new insight arrived
        If the rebalancing function has not been provided will return true.
        
        
        This codeEntityType is protected.
        
        :param insights: The insights to create portfolio targets from
        :param algorithm_utc: The current algorithm UTC time
        :returns: True if should rebalance.
        """
        ...

    def on_securities_changed(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Event fired each time the we add/remove securities from the data feed
        
        :param algorithm: The algorithm instance that experienced the change in securities
        :param changes: The security additions and removals from the algorithm
        """
        ...

    def should_create_target_for_insight(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> bool:
        """
        Method that will determine if the portfolio construction model should create a
        target for this insight
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: True if the portfolio should create a target for the insight.
        """
        ...


class PortfolioConstructionModel(System.Object, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioConstructionModel):
    """Provides a base class for portfolio construction models"""

    @property
    def rebalance_on_security_changes(self) -> bool:
        """True if should rebalance portfolio on security changes. True by default"""
        ...

    @rebalance_on_security_changes.setter
    def rebalance_on_security_changes(self, value: bool) -> None:
        ...

    @property
    def rebalance_on_insight_changes(self) -> bool:
        """True if should rebalance portfolio on new insights or expiration of insights. True by default"""
        ...

    @rebalance_on_insight_changes.setter
    def rebalance_on_insight_changes(self, value: bool) -> None:
        ...

    @property
    def algorithm(self) -> QuantConnect.Interfaces.IAlgorithm:
        """
        The algorithm instance
        
        
        This codeEntityType is protected.
        """
        ...

    @property
    def python_wrapper(self) -> QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModelPythonWrapper:
        """
        This is required due to a limitation in PythonNet to resolved overriden methods.
        When Python calls a C# method that calls a method that's overriden in python it won't
        run the python implementation unless the call is performed through python too.
        
        
        This codeEntityType is protected.
        """
        ...

    @python_wrapper.setter
    def python_wrapper(self, value: QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModelPythonWrapper) -> None:
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]]) -> None:
        """
        Initialize a new instance of PortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime] = None) -> None:
        """
        Initialize a new instance of PortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance UTC time.
        Returning current time will trigger rebalance. If null will be ignored
        """
        ...

    def create_targets(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> typing.Iterable[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]:
        """
        Create portfolio targets from the specified insights
        
        :param algorithm: The algorithm instance
        :param insights: The insights to create portfolio targets from
        :returns: An enumerable of portfolio targets to be sent to the execution model.
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Will determine the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: The active insights to generate a target for
        :returns: A target percent for each insight.
        """
        ...

    @staticmethod
    def filter_invalid_insight_magnitude(algorithm: QuantConnect.Interfaces.IAlgorithm, insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]:
        """
        Helper class that can be used by the different IPortfolioConstructionModel
        implementations to filter Insight instances with an invalid
        Insight.magnitude value based on the IAlgorithmSettings
        
        This codeEntityType is protected.
        
        :param algorithm: The algorithm instance
        :param insights: The insight collection to filter
        :returns: Returns a new array of insights removing invalid ones.
        """
        ...

    def get_target_insights(self) -> typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]:
        """
        Gets the target insights to calculate a portfolio target percent for
        
        
        This codeEntityType is protected.
        
        :returns: An enumerable of the target insights.
        """
        ...

    def is_rebalance_due(self, insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight], algorithm_utc: typing.Union[datetime.datetime, datetime.date]) -> bool:
        """
        Determines if the portfolio should be rebalanced base on the provided rebalancing func,
        if any security change have been taken place or if an insight has expired or a new insight arrived
        If the rebalancing function has not been provided will return true.
        
        
        This codeEntityType is protected.
        
        :param insights: The insights to create portfolio targets from
        :param algorithm_utc: The current algorithm UTC time
        :returns: True if should rebalance.
        """
        ...

    def on_securities_changed(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Event fired each time the we add/remove securities from the data feed
        
        :param algorithm: The algorithm instance that experienced the change in securities
        :param changes: The security additions and removals from the algorithm
        """
        ...

    def refresh_rebalance(self, algorithm_utc: typing.Union[datetime.datetime, datetime.date]) -> None:
        """
        Refresh the next rebalance time and clears the security changes flag
        
        
        This codeEntityType is protected.
        """
        ...

    def set_python_wrapper(self, python_wrapper: QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModelPythonWrapper) -> None:
        """
        Used to set the PortfolioConstructionModelPythonWrapper instance if any
        
        
        This codeEntityType is protected.
        """
        ...

    def set_rebalancing_func(self, rebalance: typing.Any) -> None:
        """
        Python helper method to set the rebalancing function.
        This is required due to a python net limitation not being able to use the base type constructor, and also because
        when python algorithms use C# portfolio construction models, it can't convert python methods into func nor resolve
        the correct constructor for the date rules, timespan parameter.
        For performance we prefer python algorithms using the C# implementation
        
        
        This codeEntityType is protected.
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        """
        ...

    def should_create_target_for_insight(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> bool:
        """
        Method that will determine if the portfolio construction model should create a
        target for this insight
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: True if the portfolio should create a target for the insight.
        """
        ...


class PortfolioBias(IntEnum):
    """Specifies the bias of the portfolio (Short, Long/Short, Long)"""

    SHORT = -1
    """Portfolio can only have short positions (-1)"""

    LONG_SHORT = 0
    """Portfolio can have both long and short positions (0)"""

    LONG = 1
    """Portfolio can only have long positions (1)"""


class EqualWeightingPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModel):
    """
    Provides an implementation of IPortfolioConstructionModel that gives equal weighting to all
    securities. The target percent holdings of each security is 1/N where N is the number of securities. For
    insights of direction InsightDirection.UP, long targets are returned and for insights of direction
    InsightDirection.DOWN, short targets are returned.
    """

    @overload
    def __init__(self, rebalance: typing.Any, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of EqualWeightingPortfolioConstructionModel
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, rebalancing_date_rules: QuantConnect.Scheduling.IDateRule, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of EqualWeightingPortfolioConstructionModel
        
        :param rebalancing_date_rules: The date rules used to define the next expected rebalance time
        in UTC
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of EqualWeightingPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of EqualWeightingPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance UTC time.
        Returning current time will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, time_span: datetime.timedelta, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of EqualWeightingPortfolioConstructionModel
        
        :param time_span: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, resolution: QuantConnect.Resolution = ..., portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of EqualWeightingPortfolioConstructionModel
        
        :param resolution: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Will determine the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: The active insights to generate a target for
        :returns: A target percent for each insight.
        """
        ...

    def respect_portfolio_bias(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> bool:
        """
        Method that will determine if a given insight respects the portfolio bias
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: True if the insight respects the portfolio bias.
        """
        ...


class InsightWeightingPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.EqualWeightingPortfolioConstructionModel):
    """
    Provides an implementation of IPortfolioConstructionModel that generates percent targets based on the
    Insight.weight. The target percent holdings of each Symbol is given by the Insight.weight
    from the last active Insight for that symbol.
    For insights of direction InsightDirection.UP, long targets are returned and for insights of direction
    InsightDirection.DOWN, short targets are returned.
    If the sum of all the last active Insight per symbol is bigger than 1, it will factor down each target
    percent holdings proportionally so the sum is 1.
    It will ignore Insight that have no Insight.weight value.
    """

    @overload
    def __init__(self, rebalance: typing.Any, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of InsightWeightingPortfolioConstructionModel
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, rebalancing_date_rules: QuantConnect.Scheduling.IDateRule, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of InsightWeightingPortfolioConstructionModel
        
        :param rebalancing_date_rules: The date rules used to define the next expected rebalance time
        in UTC
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of InsightWeightingPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance.
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of InsightWeightingPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance UTC time.
        Returning current time will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, time_span: datetime.timedelta, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of InsightWeightingPortfolioConstructionModel
        
        :param time_span: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, resolution: QuantConnect.Resolution = ..., portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of InsightWeightingPortfolioConstructionModel
        
        :param resolution: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Will determine the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: The active insights to generate a target for
        :returns: A target percent for each insight.
        """
        ...

    def get_value(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> float:
        """
        Method that will determine which member will be used to compute the weights and gets its value
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: The value of the selected insight member.
        """
        ...

    def should_create_target_for_insight(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> bool:
        """
        Method that will determine if the portfolio construction model should create a
        target for this insight
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: True if the portfolio should create a target for the insight.
        """
        ...


class RiskParityPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModel):
    """Risk Parity Portfolio Construction Model"""

    @overload
    def __init__(self, rebalance: typing.Any, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 252, resolution: QuantConnect.Resolution = ..., optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, rebalancing_date_rules: QuantConnect.Scheduling.IDateRule, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 252, resolution: QuantConnect.Resolution = ..., optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalancing_date_rules: The date rules used to define the next expected rebalance time in UTC
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, rebalance_resolution: QuantConnect.Resolution = ..., portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 252, resolution: QuantConnect.Resolution = ..., optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalance_resolution: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, time_span: datetime.timedelta, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 252, resolution: QuantConnect.Resolution = ..., optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param time_span: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 252, resolution: QuantConnect.Resolution = ..., optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance UTC time.
        Returning current time will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 252, resolution: QuantConnect.Resolution = ..., optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance.
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Will determine the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: The active insights to generate a target for
        :returns: A target percent for each insight.
        """
        ...

    def on_securities_changed(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Event fired each time the we add/remove securities from the data feed
        
        :param algorithm: The algorithm instance that experienced the change in securities
        :param changes: The security additions and removals from the algorithm
        """
        ...


class BlackLittermanOptimizationPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModel):
    """
    Provides an implementation of Black-Litterman portfolio optimization. The model adjusts equilibrium market
    returns by incorporating views from multiple alpha models and therefore to get the optimal risky portfolio
    reflecting those views. If insights of all alpha models have None magnitude or there are linearly dependent
    vectors in link matrix of views, the expected return would be the implied excess equilibrium return.
    The interval of weights in optimization method can be changed based on the long-short algorithm.
    The default model uses the 0.0025 as weight-on-views scalar parameter tau. The optimization method
    maximizes the Sharpe ratio with the weight range from -1 to 1.
    """

    @overload
    def __init__(self, rebalance: typing.Any, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., risk_free_rate: float = 0.0, delta: float = 2.5, tau: float = 0.05, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param risk_free_rate: The risk free rate
        :param delta: The risk aversion coeffficient of the market portfolio
        :param tau: The model parameter indicating the uncertainty of the CAPM prior
        :param optimizer: The portfolio optimization algorithm. If no algorithm is explicitly provided then the default will be max Sharpe ratio optimization.
        """
        ...

    @overload
    def __init__(self, time_span: datetime.timedelta, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., risk_free_rate: float = 0.0, delta: float = 2.5, tau: float = 0.05, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param time_span: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param risk_free_rate: The risk free rate
        :param delta: The risk aversion coeffficient of the market portfolio
        :param tau: The model parameter indicating the uncertainty of the CAPM prior
        :param optimizer: The portfolio optimization algorithm. If no algorithm is explicitly provided then the default will be max Sharpe ratio optimization.
        """
        ...

    @overload
    def __init__(self, rebalance_resolution: QuantConnect.Resolution = ..., portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., risk_free_rate: float = 0.0, delta: float = 2.5, tau: float = 0.05, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalance_resolution: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param risk_free_rate: The risk free rate
        :param delta: The risk aversion coeffficient of the market portfolio
        :param tau: The model parameter indicating the uncertainty of the CAPM prior
        :param optimizer: The portfolio optimization algorithm. If no algorithm is explicitly provided then the default will be max Sharpe ratio optimization.
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., risk_free_rate: float = 0.0, delta: float = 2.5, tau: float = 0.05, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance UTC time.
        Returning current time will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param risk_free_rate: The risk free rate
        :param delta: The risk aversion coeffficient of the market portfolio
        :param tau: The model parameter indicating the uncertainty of the CAPM prior
        :param optimizer: The portfolio optimization algorithm. If no algorithm is explicitly provided then the default will be max Sharpe ratio optimization.
        """
        ...

    @overload
    def __init__(self, rebalancing_date_rules: QuantConnect.Scheduling.IDateRule, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., risk_free_rate: float = 0.0, delta: float = 2.5, tau: float = 0.05, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalancing_date_rules: The date rules used to define the next expected rebalance time
        in UTC
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param risk_free_rate: The risk free rate
        :param delta: The risk aversion coeffficient of the market portfolio
        :param tau: The model parameter indicating the uncertainty of the CAPM prior
        :param optimizer: The portfolio optimization algorithm. If no algorithm is explicitly provided then the default will be max Sharpe ratio optimization.
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., risk_free_rate: float = 0.0, delta: float = 2.5, tau: float = 0.05, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance.
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param risk_free_rate: The risk free rate
        :param delta: The risk aversion coeffficient of the market portfolio
        :param tau: The model parameter indicating the uncertainty of the CAPM prior
        :param optimizer: The portfolio optimization algorithm. If no algorithm is explicitly provided then the default will be max Sharpe ratio optimization.
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Will determine the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: The active insights to generate a target for
        :returns: A target percent for each insight.
        """
        ...

    def get_equilibrium_returns(self, returns: typing.List[float], σ: typing.Optional[typing.List[float]]) -> typing.Tuple[typing.List[float], typing.List[float]]:
        """
        Calculate equilibrium returns and covariance
        
        :param returns: Matrix of returns where each column represents a security and each row returns for the given date/time (size: K x N)
        :param σ: Multi-dimensional array of double with the portfolio covariance of returns (size: K x K).
        :returns: Array of double of equilibrium returns.
        """
        ...

    def get_target_insights(self) -> typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]:
        """
        Gets the target insights to calculate a portfolio target percent for
        
        
        This codeEntityType is protected.
        
        :returns: An enumerable of the target insights.
        """
        ...

    def on_securities_changed(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Event fired each time the we add/remove securities from the data feed
        
        :param algorithm: The algorithm instance that experienced the change in securities
        :param changes: The security additions and removals from the algorithm
        """
        ...

    def should_create_target_for_insight(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> bool:
        """
        Method that will determine if the portfolio construction model should create a
        target for this insight
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: True if the portfolio should create a target for the insight.
        """
        ...

    def try_get_views(self, insights: System.Collections.Generic.ICollection[QuantConnect.Algorithm.Framework.Alphas.Insight], p: typing.Optional[typing.List[float]], q: typing.Optional[typing.List[float]]) -> typing.Tuple[bool, typing.List[float], typing.List[float]]:
        """
        Generate views from multiple alpha models
        
        
        This codeEntityType is protected.
        
        :param insights: Array of insight that represent the investors' views
        :param p: A matrix that identifies the assets involved in the views (size: K x N)
        :param q: A view vector (size: K x 1)
        """
        ...


class ConfidenceWeightedPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.InsightWeightingPortfolioConstructionModel):
    """
    Provides an implementation of IPortfolioConstructionModel that generates percent targets based on the
    Insight.confidence. The target percent holdings of each Symbol is given by the Insight.confidence
    from the last active Insight for that symbol.
    For insights of direction InsightDirection.UP, long targets are returned and for insights of direction
    InsightDirection.DOWN, short targets are returned.
    If the sum of all the last active Insight per symbol is bigger than 1, it will factor down each target
    percent holdings proportionally so the sum is 1.
    It will ignore Insight that have no Insight.confidence value.
    """

    @overload
    def __init__(self, rebalance: typing.Any, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of ConfidenceWeightedPortfolioConstructionModel
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, rebalancing_date_rules: QuantConnect.Scheduling.IDateRule, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of ConfidenceWeightedPortfolioConstructionModel
        
        :param rebalancing_date_rules: The date rules used to define the next expected rebalance time
        in UTC
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of ConfidenceWeightedPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of ConfidenceWeightedPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance UTC time.
        Returning current time will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, time_span: datetime.timedelta, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of ConfidenceWeightedPortfolioConstructionModel
        
        :param time_span: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    @overload
    def __init__(self, resolution: QuantConnect.Resolution = ..., portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ...) -> None:
        """
        Initialize a new instance of ConfidenceWeightedPortfolioConstructionModel
        
        :param resolution: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        """
        ...

    def get_value(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> float:
        """
        Method that will determine which member will be used to compute the weights and gets its value
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: The value of the selected insight member.
        """
        ...

    def should_create_target_for_insight(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> bool:
        """
        Method that will determine if the portfolio construction model should create a
        target for this insight
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: True if the portfolio should create a target for the insight.
        """
        ...


class MaximumSharpeRatioPortfolioOptimizer(System.Object, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer):
    """
    Provides an implementation of a portfolio optimizer that maximizes the portfolio Sharpe Ratio.
    The interval of weights in optimization method can be changed based on the long-short algorithm.
    The default model uses flat risk free rate and weight for an individual security range from -1 to 1.
    """

    def __init__(self, lower: float = -1, upper: float = 1, risk_free_rate: float = 0.0) -> None:
        """
        Initialize a new instance of MaximumSharpeRatioPortfolioOptimizer
        
        :param lower: Lower constraint
        :param upper: Upper constraint
        :param risk_free_rate: 
        """
        ...

    def get_boundary_conditions(self, size: int) -> typing.Iterable[LinearConstraint]:
        """
        Boundary constraints on weights: lw ≤ w ≤ up
        
        
        This codeEntityType is protected.
        
        :param size: number of variables
        :returns: enumeration of linear constraint objects.
        """
        ...

    def get_budget_constraint(self, size: int) -> typing.Any:
        """
        Sum of all weight is one: 1^T w = 1 / Σw = 1
        
        
        This codeEntityType is protected.
        
        :param size: number of variables
        :returns: linear constraint object.
        """
        ...

    def optimize(self, historical_returns: typing.List[float], expected_returns: typing.List[float] = None, covariance: typing.List[float] = None) -> typing.List[float]:
        """
        Perform portfolio optimization for a provided matrix of historical returns and an array of expected returns
        
        :param historical_returns: Matrix of annualized historical returns where each column represents a security and each row returns for the given date/time (size: K x N).
        :param expected_returns: Array of double with the portfolio annualized expected returns (size: K x 1).
        :param covariance: Multi-dimensional array of double with the portfolio covariance of annualized returns (size: K x K).
        :returns: Array of double with the portfolio weights (size: K x 1).
        """
        ...


class AccumulativeInsightPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModel):
    """
    Provides an implementation of IPortfolioConstructionModel that allocates percent of account
    to each insight, defaulting to 3%.
    For insights of direction InsightDirection.UP, long targets are returned and
    for insights of direction InsightDirection.DOWN, short targets are returned.
    By default, no rebalancing shall be done.
    Rules:
       1. On active Up insight, increase position size by percent
       2. On active Down insight, decrease position size by percent
       3. On active Flat insight, move by percent towards 0
       4. On expired insight, and no other active insight, emits a 0 target'''
    """

    @overload
    def __init__(self, rebalance: typing.Any, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., percent: float = 0.03) -> None:
        """
        Initialize a new instance of AccumulativeInsightPortfolioConstructionModel
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param percent: The percentage amount of the portfolio value to allocate
        to a single insight. The value of percent should be in the range <0,1>.
        The default value is 0.03.
        """
        ...

    @overload
    def __init__(self, rebalancing_date_rules: QuantConnect.Scheduling.IDateRule, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., percent: float = 0.03) -> None:
        """
        Initialize a new instance of AccumulativeInsightPortfolioConstructionModel
        
        :param rebalancing_date_rules: The date rules used to define the next expected rebalance time
        in UTC
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param percent: The percentage amount of the portfolio value to allocate
        to a single insight. The value of percent should be in the range <0,1>.
        The default value is 0.03.
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]] = None, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., percent: float = 0.03) -> None:
        """
        Initialize a new instance of AccumulativeInsightPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param percent: The percentage amount of the portfolio value to allocate
        to a single insight. The value of percent should be in the range <0,1>.
        The default value is 0.03.
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., percent: float = 0.03) -> None:
        """
        Initialize a new instance of AccumulativeInsightPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance UTC time.
        Returning current time will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param percent: The percentage amount of the portfolio value to allocate
        to a single insight. The value of percent should be in the range <0,1>.
        The default value is 0.03.
        """
        ...

    @overload
    def __init__(self, time_span: datetime.timedelta, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., percent: float = 0.03) -> None:
        """
        Initialize a new instance of AccumulativeInsightPortfolioConstructionModel
        
        :param time_span: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param percent: The percentage amount of the portfolio value to allocate
        to a single insight. The value of percent should be in the range <0,1>.
        The default value is 0.03.
        """
        ...

    @overload
    def __init__(self, resolution: QuantConnect.Resolution, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., percent: float = 0.03) -> None:
        """
        Initialize a new instance of AccumulativeInsightPortfolioConstructionModel
        
        :param resolution: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param percent: The percentage amount of the portfolio value to allocate
        to a single insight. The value of percent should be in the range <0,1>.
        The default value is 0.03.
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Determines the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: The active insights to generate a target for
        :returns: A target percent for each insight.
        """
        ...

    def get_target_insights(self) -> typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]:
        """
        Gets the target insights to calculate a portfolio target percent for
        
        
        This codeEntityType is protected.
        
        :returns: An enumerable of the target insights.
        """
        ...


class MinimumVariancePortfolioOptimizer(System.Object, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer):
    """
    Provides an implementation of a minimum variance portfolio optimizer that calculate the optimal weights
    with the weight range from -1 to 1 and minimize the portfolio variance with a target return of 2%
    """

    def __init__(self, lower: float = -1, upper: float = 1, target_return: float = 0.02) -> None:
        """
        Initialize a new instance of MinimumVariancePortfolioOptimizer
        
        :param lower: Lower bound
        :param upper: Upper bound
        :param target_return: Target return
        """
        ...

    def get_boundary_conditions(self, size: int) -> typing.Iterable[LinearConstraint]:
        """
        Boundary constraints on weights: lw ≤ w ≤ up
        
        
        This codeEntityType is protected.
        
        :param size: number of variables
        :returns: enumeration of linear constaraint objects.
        """
        ...

    def get_budget_constraint(self, size: int) -> typing.Any:
        """
        Sum of all weight is one: 1^T w = 1 / Σw = 1
        
        
        This codeEntityType is protected.
        
        :param size: number of variables
        :returns: linear constaraint object.
        """
        ...

    def optimize(self, historical_returns: typing.List[float], expected_returns: typing.List[float] = None, covariance: typing.List[float] = None) -> typing.List[float]:
        """
        Perform portfolio optimization for a provided matrix of historical returns and an array of expected returns
        
        :param historical_returns: Matrix of annualized historical returns where each column represents a security and each row returns for the given date/time (size: K x N).
        :param expected_returns: Array of double with the portfolio annualized expected returns (size: K x 1).
        :param covariance: Multi-dimensional array of double with the portfolio covariance of annualized returns (size: K x K).
        :returns: Array of double with the portfolio weights (size: K x 1).
        """
        ...


class AlphaStreamsPortfolioConstructionModel(System.Object, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioConstructionModel):
    """Base alpha streams portfolio construction model"""

    def create_targets(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> typing.Iterable[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]:
        """
        Create portfolio targets from the specified insights
        
        :param algorithm: The algorithm instance
        :param insights: The insights to create portfolio targets from
        :returns: An enumerable of portfolio targets to be sent to the execution model.
        """
        ...

    def get_alpha_weight(self, alpha_id: str) -> float:
        """
        Get's the weight for an alpha
        
        :param alpha_id: The algorithm instance that experienced the change in securities
        :returns: The alphas weight.
        """
        ...

    def on_securities_changed(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Event fired each time the we add/remove securities from the data feed
        
        :param algorithm: The algorithm instance that experienced the change in securities
        :param changes: The security additions and removals from the algorithm
        """
        ...


class PortfolioOptimizerPythonWrapper(QuantConnect.Python.BasePythonWrapper[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer], QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer):
    """Python wrapper for custom portfolio optimizer"""

    def __init__(self, portfolio_optimizer: typing.Any) -> None:
        """
        Creates a new instance
        
        :param portfolio_optimizer: The python model to wrapp
        """
        ...

    def optimize(self, historical_returns: typing.List[float], expected_returns: typing.List[float] = None, covariance: typing.List[float] = None) -> typing.List[float]:
        """
        Perform portfolio optimization for a provided matrix of historical returns and an array of expected returns
        
        :param historical_returns: Matrix of annualized historical returns where each column represents a security and each row returns for the given date/time (size: K x N).
        :param expected_returns: Array of double with the portfolio annualized expected returns (size: K x 1).
        :param covariance: Multi-dimensional array of double with the portfolio covariance of annualized returns (size: K x K).
        :returns: Array of double with the portfolio weights (size: K x 1).
        """
        ...


class RiskParityPortfolioOptimizer(System.Object, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer):
    """
    Provides an implementation of a risk parity portfolio optimizer that calculate the optimal weights
    with the weight range from 0 to 1 and equalize the risk carried by each asset
    """

    def __init__(self, lower: typing.Optional[float] = None, upper: typing.Optional[float] = None) -> None:
        """
        Initialize a new instance of RiskParityPortfolioOptimizer
        
        :param lower: The lower bounds on portfolio weights
        :param upper: The upper bounds on portfolio weights
        """
        ...

    def optimize(self, historical_returns: typing.List[float], expected_returns: typing.List[float] = None, covariance: typing.List[float] = None) -> typing.List[float]:
        """
        Perform portfolio optimization for a provided matrix of historical returns and an array of expected returns
        
        :param historical_returns: Matrix of annualized historical returns where each column represents a security and each row returns for the given date/time (size: K x N).
        :param expected_returns: Risk budget vector (size: K x 1).
        :param covariance: Multi-dimensional array of double with the portfolio covariance of annualized returns (size: K x K).
        :returns: Array of double with the portfolio weights (size: K x 1).
        """
        ...

    def risk_parity_newton_method_optimization(self, number_of_variables: int, covariance: typing.List[float], budget: typing.List[float], tolerance: float = ..., maximum_iteration: int = 15000) -> typing.List[float]:
        """
        Newton method of minimization
        
        
        This codeEntityType is protected.
        
        :param number_of_variables: The number of variables (size of weight vector).
        :param covariance: Covariance matrix (size: K x K).
        :param budget: The risk budget (size: K x 1).
        :param tolerance: Tolerance level of objective difference with previous steps to accept minimization result.
        :param maximum_iteration: Maximum iteration per optimization.
        :returns: Array of double of argumented minimization.
        """
        ...


class SectorWeightingPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.EqualWeightingPortfolioConstructionModel):
    """
    Provides an implementation of IPortfolioConstructionModel that generates percent targets based on the
    CompanyReference.IndustryTemplateCode.
    The target percent holdings of each sector is 1/S where S is the number of sectors and
    the target percent holdings of each security is 1/N where N is the number of securities of each sector.
    For insights of direction InsightDirection.UP, long targets are returned and for insights of direction
    InsightDirection.DOWN, short targets are returned.
    It will ignore Insight for symbols that have no CompanyReference.IndustryTemplateCode value.
    """

    @overload
    def __init__(self, rebalance: typing.Any) -> None:
        """
        Initialize a new instance of SectorWeightingPortfolioConstructionModel
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        """
        ...

    @overload
    def __init__(self, rebalancing_date_rules: QuantConnect.Scheduling.IDateRule) -> None:
        """
        Initialize a new instance of SectorWeightingPortfolioConstructionModel
        
        :param rebalancing_date_rules: The date rules used to define the next expected rebalance time
        in UTC
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]]) -> None:
        """
        Initialize a new instance of SectorWeightingPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime]) -> None:
        """
        Initialize a new instance of SectorWeightingPortfolioConstructionModel
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance UTC time.
        Returning current time will trigger rebalance. If null will be ignored
        """
        ...

    @overload
    def __init__(self, time_span: datetime.timedelta) -> None:
        """
        Initialize a new instance of SectorWeightingPortfolioConstructionModel
        
        :param time_span: Rebalancing frequency
        """
        ...

    @overload
    def __init__(self, resolution: QuantConnect.Resolution = ...) -> None:
        """
        Initialize a new instance of SectorWeightingPortfolioConstructionModel
        
        :param resolution: Rebalancing frequency
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Will determine the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: The active insights to generate a target for
        :returns: A target percent for each insight.
        """
        ...

    def get_sector_code(self, security: QuantConnect.Securities.Security) -> str:
        """
        Gets the sector code
        
        
        This codeEntityType is protected.
        
        :param security: The security to create a sector code for
        :returns: The value of the sector code for the security.
        """
        ...

    def on_securities_changed(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Event fired each time the we add/remove securities from the data feed
        
        :param algorithm: The algorithm instance that experienced the change in securities
        :param changes: The security additions and removals from the algorithm
        """
        ...

    def should_create_target_for_insight(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> bool:
        """
        Method that will determine if the portfolio construction model should create a
        target for this insight
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: True if the portfolio should create a target for the insight.
        """
        ...


class MeanReversionPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModel):
    """Implementation of On-Line Moving Average Reversion (OLMAR)"""

    @overload
    def __init__(self, rebalance: typing.Any, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., reversion_threshold: float = 1, window_size: int = 20, resolution: QuantConnect.Resolution = ...) -> None:
        """
        Initializes a new instance of the MeanReversionPortfolioConstructionModel class
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param reversion_threshold: Reversion threshold
        :param window_size: Window size of mean price
        :param resolution: The resolution of the history price and rebalancing
        """
        ...

    @overload
    def __init__(self, rebalancing_date_rules: QuantConnect.Scheduling.IDateRule, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., reversion_threshold: float = 1, window_size: int = 20, resolution: QuantConnect.Resolution = ...) -> None:
        """
        Initializes a new instance of the MeanReversionPortfolioConstructionModel class
        
        :param rebalancing_date_rules: The date rules used to define the next expected rebalance time
        in UTC
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param reversion_threshold: Reversion threshold
        :param window_size: Window size of mean price
        :param resolution: The resolution of the history price and rebalancing
        """
        ...

    @overload
    def __init__(self, rebalance_resolution: QuantConnect.Resolution = ..., portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., reversion_threshold: float = 1, window_size: int = 20, resolution: QuantConnect.Resolution = ...) -> None:
        """
        Initializes a new instance of the MeanReversionPortfolioConstructionModel class
        
        :param rebalance_resolution: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param reversion_threshold: Reversion threshold
        :param window_size: Window size of mean price
        :param resolution: The resolution of the history price and rebalancing
        """
        ...

    @overload
    def __init__(self, time_span: datetime.timedelta, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., reversion_threshold: float = 1, window_size: int = 20, resolution: QuantConnect.Resolution = ...) -> None:
        """
        Initializes a new instance of the MeanReversionPortfolioConstructionModel class
        
        :param time_span: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param reversion_threshold: Reversion threshold
        :param window_size: Window size of mean price
        :param resolution: The resolution of the history price and rebalancing
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., reversion_threshold: float = 1, window_size: int = 20, resolution: QuantConnect.Resolution = ...) -> None:
        """
        Initializes a new instance of the MeanReversionPortfolioConstructionModel class
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored.
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param reversion_threshold: Reversion threshold
        :param window_size: Window size of mean price
        :param resolution: The resolution of the history price and rebalancing
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., reversion_threshold: float = 1, window_size: int = 20, resolution: QuantConnect.Resolution = ...) -> None:
        """
        Initializes a new instance of the MeanReversionPortfolioConstructionModel class
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance.
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param reversion_threshold: Reversion threshold
        :param window_size: Window size of mean price
        :param resolution: The resolution of the history price and rebalancing
        """
        ...

    @staticmethod
    def cumulative_sum(sequence: typing.List[float]) -> typing.Iterable[float]:
        """
        Cumulative Sum of a given sequence
        
        :param sequence: sequence to obtain cumulative sum
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Will determine the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: list of active insights
        """
        ...

    def get_price_relatives(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> typing.List[float]:
        """
        Get price relatives with reference level of SMA
        
        
        This codeEntityType is protected.
        
        :param active_insights: list of active insights
        """
        ...

    def on_securities_changed(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Event fired each time the we add/remove securities from the data feed
        
        :param algorithm: The algorithm instance that experienced the change in securities
        :param changes: The security additions and removals from the algorithm
        """
        ...

    @staticmethod
    def simplex_projection(vector: typing.List[float], total: float = 1) -> typing.List[float]:
        """
        Normalize the updated portfolio into weight vector:
        v_{t+1} = arg min || v - v_{t+1} || ^ 2
        
        :param vector: unnormalized weight vector
        :param total: regulator, default to be 1, making it a probabilistic simplex
        """
        ...


class MeanVarianceOptimizationPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModel):
    """
    Provides an implementation of Mean-Variance portfolio optimization based on modern portfolio theory.
    The interval of weights in optimization method can be changed based on the long-short algorithm.
    The default model uses the last three months daily price to calculate the optimal weight
    with the weight range from -1 to 1 and minimize the portfolio variance with a target return of 2%
    """

    @overload
    def __init__(self, rebalance: typing.Any, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., target_return: float = 0.02, optimizer: typing.Any = None) -> None:
        """
        Initialize the model
        
        :param rebalance: Rebalancing func or if a date rule, timedelta will be converted into func.
        For a given algorithm UTC DateTime the func returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param target_return: The target portfolio return
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, rebalancing_date_rules: QuantConnect.Scheduling.IDateRule, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., target_return: float = 0.02, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalancing_date_rules: The date rules used to define the next expected rebalance time
        in UTC
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param target_return: The target portfolio return
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, rebalance_resolution: QuantConnect.Resolution = ..., portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., target_return: float = 0.02, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalance_resolution: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param target_return: The target portfolio return
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, time_span: datetime.timedelta, portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., target_return: float = 0.02, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param time_span: Rebalancing frequency
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param target_return: The target portfolio return
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], datetime.datetime], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., target_return: float = 0.02, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance UTC time.
        Returning current time will trigger rebalance. If null will be ignored
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param target_return: The target portfolio return
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    @overload
    def __init__(self, rebalancing_func: typing.Callable[[datetime.datetime], typing.Optional[datetime.datetime]], portfolio_bias: QuantConnect.Algorithm.Framework.Portfolio.PortfolioBias = ..., lookback: int = 1, period: int = 63, resolution: QuantConnect.Resolution = ..., target_return: float = 0.02, optimizer: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioOptimizer = None) -> None:
        """
        Initialize the model
        
        :param rebalancing_func: For a given algorithm UTC DateTime returns the next expected rebalance time
        or null if unknown, in which case the function will be called again in the next loop. Returning current time
        will trigger rebalance.
        :param portfolio_bias: Specifies the bias of the portfolio (Short, Long/Short, Long)
        :param lookback: Historical return lookback period
        :param period: The time interval of history price to calculate the weight
        :param resolution: The resolution of the history price
        :param target_return: The target portfolio return
        :param optimizer: The portfolio optimization algorithm. If the algorithm is not provided then the default will be mean-variance optimization.
        """
        ...

    def determine_target_percent(self, active_insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> System.Collections.Generic.Dictionary[QuantConnect.Algorithm.Framework.Alphas.Insight, float]:
        """
        Will determine the target percent for each insight
        
        
        This codeEntityType is protected.
        
        :param active_insights: The active insights to generate a target for
        :returns: A target percent for each insight.
        """
        ...

    def on_securities_changed(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Event fired each time the we add/remove securities from the data feed
        
        :param algorithm: The algorithm instance that experienced the change in securities
        :param changes: The security additions and removals from the algorithm
        """
        ...

    def should_create_target_for_insight(self, insight: QuantConnect.Algorithm.Framework.Alphas.Insight) -> bool:
        """
        Method that will determine if the portfolio construction model should create a
        target for this insight
        
        
        This codeEntityType is protected.
        
        :param insight: The insight to create a target for
        :returns: True if the portfolio should create a target for the insight.
        """
        ...


class NullPortfolioConstructionModel(QuantConnect.Algorithm.Framework.Portfolio.PortfolioConstructionModel):
    """Provides an implementation of IPortfolioConstructionModel that does nothing"""

    def create_targets(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, insights: typing.List[QuantConnect.Algorithm.Framework.Alphas.Insight]) -> typing.Iterable[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]:
        """
        Create Targets; Does nothing in this implementation and returns an empty IEnumerable
        
        :returns: Empty IEnumerable of IPortfolioTargets.
        """
        ...


class PortfolioTarget(System.Object, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget):
    """
    Provides an implementation of IPortfolioTarget that specifies a
    specified quantity of a security to be held by the algorithm
    """

    minimum_order_margin_percentage_warning_sent: typing.Optional[bool]
    """
    Flag to determine if the minimum order margin portfolio percentage warning should or has already been sent to the user algorithm
    IAlgorithmSettings.minimum_order_margin_portfolio_percentage
    """

    @property
    def symbol(self) -> QuantConnect.Symbol:
        """Gets the symbol of this target"""
        ...

    @property
    def quantity(self) -> float:
        """Gets the target quantity for the symbol"""
        ...

    @property
    def tag(self) -> str:
        """Portfolio target tag with additional information"""
        ...

    @overload
    def __init__(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], quantity: float, tag: str = ...) -> None:
        """
        Initializes a new instance of the PortfolioTarget class
        
        :param symbol: The symbol this target is for
        :param quantity: The target quantity
        :param tag: The target tag with additional information
        """
        ...

    @overload
    def __init__(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], quantity: int, tag: str = ...) -> None:
        """
        Initializes a new instance of the PortfolioTarget class
        
        :param symbol: The symbol this target is for
        :param quantity: The target quantity
        :param tag: The target tag with additional information
        """
        ...

    @overload
    def __init__(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], insight_direction: QuantConnect.Algorithm.Framework.Alphas.InsightDirection, tag: str = ...) -> None:
        """
        Initializes a new instance of the PortfolioTarget class
        
        :param symbol: The symbol this target is for
        :param insight_direction: The insight direction, which will be used to calculate the target quantity
        (1 for Up, 0 for flat, -1 for down)
        :param tag: The target tag with additional information
        """
        ...

    @staticmethod
    @overload
    def percent(algorithm: QuantConnect.Interfaces.IAlgorithm, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], percent: float) -> QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget:
        """
        Creates a new target for the specified percent
        
        :param algorithm: The algorithm instance, used for getting total portfolio value and current security price
        :param symbol: The symbol the target is for
        :param percent: The requested target percent of total portfolio value
        :returns: A portfolio target for the specified symbol/percent.
        """
        ...

    @staticmethod
    @overload
    def percent(algorithm: QuantConnect.Interfaces.IAlgorithm, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], percent: float, tag: str) -> QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget:
        """
        Creates a new target for the specified percent
        
        :param algorithm: The algorithm instance, used for getting total portfolio value and current security price
        :param symbol: The symbol the target is for
        :param percent: The requested target percent of total portfolio value
        :param tag: The target tag with additional information
        :returns: A portfolio target for the specified symbol/percent.
        """
        ...

    @staticmethod
    @overload
    def percent(algorithm: QuantConnect.Interfaces.IAlgorithm, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], percent: float, return_delta_quantity: bool = False, tag: str = ...) -> QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget:
        """
        Creates a new target for the specified percent
        
        :param algorithm: The algorithm instance, used for getting total portfolio value and current security price
        :param symbol: The symbol the target is for
        :param percent: The requested target percent of total portfolio value
        :param return_delta_quantity: True, result quantity will be the Delta required to reach target percent.
        False, the result quantity will be the Total quantity to reach the target percent, including current holdings
        :param tag: The target tag with additional information
        :returns: A portfolio target for the specified symbol/percent.
        """
        ...

    def to_string(self) -> str:
        """
        Returns a string that represents the current object.
        
        :returns: A string that represents the current object.
        """
        ...


class PortfolioTargetCollection(System.Object, System.Collections.Generic.IDictionary[QuantConnect.Symbol, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget], typing.Iterable[System.Collections.Generic.KeyValuePair[QuantConnect.Symbol, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]]):
    """Provides a collection for managing IPortfolioTargets for each symbol"""

    @property
    def count(self) -> int:
        """Gets the number of targets in this collection"""
        ...

    @property
    def is_empty(self) -> bool:
        """True if there is no target in the collection"""
        ...

    @property
    def is_read_only(self) -> bool:
        """Gets `false`. This collection is not read-only."""
        ...

    @property
    def keys(self) -> System.Collections.Generic.ICollection[QuantConnect.Symbol]:
        """Gets the symbol keys for this collection"""
        ...

    @property
    def values(self) -> System.Collections.Generic.ICollection[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]:
        """
        Gets all portfolio targets in this collection
        Careful, will return targets for securities that might have no data yet.
        """
        ...

    def __contains__(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract]) -> bool:
        """
        Determines whether the specified symbol exists as a key in this collection
        
        :param symbol: The symbol key
        :returns: True if the symbol exists in this collection, false otherwise.
        """
        ...

    def __getitem__(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract]) -> QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget:
        """
        Gets or sets the portfolio target for the specified symbol
        
        :param symbol: The symbol
        :returns: The symbol's portfolio target if it exists in this collection, if not a KeyNotFoundException will be thrown.
        """
        ...

    def __iter__(self) -> typing.Iterator[System.Collections.Generic.KeyValuePair[QuantConnect.Symbol, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]]:
        ...

    def __len__(self) -> int:
        ...

    def __setitem__(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], value: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget) -> None:
        """
        Gets or sets the portfolio target for the specified symbol
        
        :param symbol: The symbol
        :returns: The symbol's portfolio target if it exists in this collection, if not a KeyNotFoundException will be thrown.
        """
        ...

    @overload
    def add(self, target: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget) -> None:
        """
        Adds the specified target to the collection. If a target for the same symbol
        already exists it wil be overwritten.
        
        :param target: The portfolio target to add
        """
        ...

    @overload
    def add(self, target: System.Collections.Generic.KeyValuePair[QuantConnect.Symbol, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]) -> None:
        """
        Adds the specified target to the collection. If a target for the same symbol
        already exists it wil be overwritten.
        
        :param target: The portfolio target to add
        """
        ...

    @overload
    def add(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], target: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget) -> None:
        """
        Adds the specified target to the collection. If a target for the same symbol
        already exists it wil be overwritten.
        
        :param symbol: The symbol key
        :param target: The portfolio target to add
        """
        ...

    def add_range(self, targets: typing.List[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]) -> None:
        """
        Adds the specified targets to the collection. If a target for the same symbol
        already exists it will be overwritten.
        
        :param targets: The portfolio targets to add
        """
        ...

    def clear(self) -> None:
        """Removes all portfolio targets from this collection"""
        ...

    def clear_fulfilled(self, algorithm: QuantConnect.Interfaces.IAlgorithm) -> None:
        """
        Removes fulfilled portfolio targets from this collection.
        Will only take into account actual holdings and ignore open orders.
        """
        ...

    @overload
    def contains(self, target: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget) -> bool:
        """
        Determines whether or not the specified target exists in this collection.
        NOTE: This checks for the exact specified target, not by symbol. Use ContainsKey
        to check by symbol.
        
        :param target: The portfolio target to check for existence.
        :returns: True if the target exists, false otherwise.
        """
        ...

    @overload
    def contains(self, target: System.Collections.Generic.KeyValuePair[QuantConnect.Symbol, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]) -> bool:
        """
        Determines whether the specified symbol/target pair exists in this collection
        
        :param target: The symbol/target pair
        :returns: True if the pair exists, false otherwise.
        """
        ...

    def contains_key(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract]) -> bool:
        """
        Determines whether the specified symbol exists as a key in this collection
        
        :param symbol: The symbol key
        :returns: True if the symbol exists in this collection, false otherwise.
        """
        ...

    @overload
    def copy_to(self, array: typing.List[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget], array_index: int) -> None:
        """
        Copies the targets in this collection to the specified array
        
        :param array: The destination array to copy to
        :param array_index: The index in the array to start copying to
        """
        ...

    @overload
    def copy_to(self, array: typing.List[System.Collections.Generic.KeyValuePair[QuantConnect.Symbol, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]], array_index: int) -> None:
        """
        Copies the targets in this collection to the specified array
        
        :param array: The destination array to copy to
        :param array_index: The index in the array to start copying to
        """
        ...

    def get_enumerator(self) -> System.Collections.Generic.IEnumerator[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]:
        """
        Gets an enumerator to iterator over all portfolio targets in this collection.
        This is the default enumerator for this collection.
        
        :returns: Portfolio targets enumerator.
        """
        ...

    def order_by_margin_impact(self, algorithm: QuantConnect.Interfaces.IAlgorithm) -> typing.Iterable[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]:
        """
        Returned an ordered enumerable where position reducing orders are executed first
        and the remaining orders are executed in decreasing order value.
        Will NOT return targets for securities that have no data yet.
        Will NOT return targets for which current holdings + open orders quantity, sum up to the target quantity
        
        :param algorithm: The algorithm instance
        """
        ...

    @overload
    def remove(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract]) -> bool:
        """
        Removes the target for the specified symbol if it exists in this collection.
        
        :param symbol: The symbol to remove
        :returns: True if the symbol's target was removed, false if it doesn't exist in the collection.
        """
        ...

    @overload
    def remove(self, target: System.Collections.Generic.KeyValuePair[QuantConnect.Symbol, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]) -> bool:
        """
        Removes the target for the specified symbol/target pair if it exists in this collection.
        
        :param target: The symbol/target pair to remove
        :returns: True if the symbol's target was removed, false if it doesn't exist in the collection.
        """
        ...

    @overload
    def remove(self, target: QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget) -> bool:
        """
        Removes the target if it exists in this collection.
        
        :param target: The target to remove
        :returns: True if the target was removed, false if it doesn't exist in the collection.
        """
        ...

    def try_get_value(self, symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], target: typing.Optional[QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]) -> typing.Tuple[bool, QuantConnect.Algorithm.Framework.Portfolio.IPortfolioTarget]:
        """
        Attempts to retrieve the target for the specified symbol
        
        :param symbol: The symbol
        :param target: The portfolio target for the symbol, or null if not found
        :returns: True if the symbol's target was found, false if it does not exist in this collection.
        """
        ...



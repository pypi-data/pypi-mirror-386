from typing import overload
from enum import IntEnum
import datetime
import typing

import QuantConnect
import QuantConnect.Algorithm
import QuantConnect.Algorithm.Framework.Selection
import QuantConnect.Algorithm.Selection
import QuantConnect.Data
import QuantConnect.Data.UniverseSelection
import QuantConnect.Securities
import System.Collections.Specialized


class OptionChainedUniverseSelectionModel(QuantConnect.Algorithm.Framework.Selection.UniverseSelectionModel):
    """
    This universe selection model will chain to the security changes of a given Universe selection
    output and create a new OptionChainUniverse for each of them
    """

    @overload
    def __init__(self, universe: QuantConnect.Data.UniverseSelection.Universe, option_filter: typing.Any, universe_settings: QuantConnect.Data.UniverseSelection.UniverseSettings = None) -> None:
        """
        Creates a new instance of OptionChainedUniverseSelectionModel
        
        :param universe: The universe we want to chain to
        :param option_filter: The python option filter universe to use
        :param universe_settings: Universe settings define attributes of created subscriptions, such as their resolution and the minimum time in universe before they can be removed
        """
        ...

    @overload
    def __init__(self, universe: QuantConnect.Data.UniverseSelection.Universe, option_filter: typing.Callable[[QuantConnect.Securities.OptionFilterUniverse], QuantConnect.Securities.OptionFilterUniverse], universe_settings: QuantConnect.Data.UniverseSelection.UniverseSettings = None) -> None:
        """
        Creates a new instance of OptionChainedUniverseSelectionModel
        
        :param universe: The universe we want to chain to
        :param option_filter: The option filter universe to use
        :param universe_settings: Universe settings define attributes of created subscriptions, such as their resolution and the minimum time in universe before they can be removed
        """
        ...

    def create_universes(self, algorithm: QuantConnect.Algorithm.QCAlgorithm) -> typing.Iterable[QuantConnect.Data.UniverseSelection.Universe]:
        """
        Creates the universes for this algorithm. Called once after IAlgorithm.Initialize
        
        :param algorithm: The algorithm instance to create universes for
        :returns: The universes to be used by the algorithm.
        """
        ...

    def get_next_refresh_time_utc(self) -> datetime.datetime:
        """Gets the next time the framework should invoke the `CreateUniverses` method to refresh the set of universes."""
        ...


class OptionContractUniverse(QuantConnect.Data.UniverseSelection.UserDefinedUniverse):
    """This universe will hold single option contracts and their underlying, managing removals and additions"""

    def __init__(self, configuration: QuantConnect.Data.SubscriptionDataConfig, universe_settings: QuantConnect.Data.UniverseSelection.UniverseSettings) -> None:
        """
        Creates a new empty instance
        
        :param configuration: The universe configuration to use
        :param universe_settings: The universe settings to use
        """
        ...

    @staticmethod
    def create_symbol(market: str, security_type: QuantConnect.SecurityType) -> QuantConnect.Symbol:
        """
        Creates a user defined universe symbol
        
        :param market: The market
        :param security_type: The underlying option security type
        :returns: A symbol for user defined universe of the specified security type and market.
        """
        ...

    def on_collection_changed(self, e: System.Collections.Specialized.NotifyCollectionChangedEventArgs) -> None:
        """
        Event invocator for the UserDefinedUniverse.collection_changed event
        
        
        This codeEntityType is protected.
        
        :param e: The notify collection changed event arguments
        """
        ...

    def select_symbols(self, utc_time: typing.Union[datetime.datetime, datetime.date], data: QuantConnect.Data.UniverseSelection.BaseDataCollection) -> typing.Iterable[QuantConnect.Symbol]:
        """
        Returns the symbols defined by the user for this universe
        
        :param utc_time: The current utc time
        :param data: The symbols to remain in the universe
        :returns: The data that passes the filter.
        """
        ...



from typing import overload
from enum import IntEnum
import abc
import typing

import QuantConnect.Algorithm
import QuantConnect.Algorithm.Framework
import QuantConnect.Data.UniverseSelection
import QuantConnect.Securities
import System
import System.Collections.Generic


class NotifiedSecurityChanges(System.Object):
    """Provides convenience methods for updating collections in responses to securities changed events"""

    @staticmethod
    def update(changes: QuantConnect.Data.UniverseSelection.SecurityChanges, add: typing.Callable[[QuantConnect.Securities.Security], typing.Any], remove: typing.Callable[[QuantConnect.Securities.Security], typing.Any]) -> None:
        """
        Invokes the provided add and remove functions for each
        
        :param changes: The security changes to process
        :param add: Function called for each added security
        :param remove: Function called for each removed security
        """
        ...

    @staticmethod
    def update_collection(securities: System.Collections.Generic.ICollection[QuantConnect.Securities.Security], changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Adds and removes the security changes to/from the collection
        
        :param securities: The securities collection to be updated with the changes
        :param changes: The changes to be applied to the securities collection
        """
        ...


class INotifiedSecurityChanges(metaclass=abc.ABCMeta):
    """Types implementing this interface will be called when the algorithm's set of securities changes"""

    def on_securities_changed(self, algorithm: QuantConnect.Algorithm.QCAlgorithm, changes: QuantConnect.Data.UniverseSelection.SecurityChanges) -> None:
        """
        Event fired each time the we add/remove securities from the data feed
        
        :param algorithm: The algorithm instance that experienced the change in securities
        :param changes: The security additions and removals from the algorithm
        """
        ...



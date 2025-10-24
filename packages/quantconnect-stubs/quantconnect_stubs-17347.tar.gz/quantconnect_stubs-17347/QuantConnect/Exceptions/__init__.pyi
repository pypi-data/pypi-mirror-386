from typing import overload
from enum import IntEnum
import abc
import typing

import QuantConnect.Exceptions
import System
import System.Reflection


class IExceptionInterpreter(metaclass=abc.ABCMeta):
    """Defines an exception interpreter. Interpretations are invoked on IAlgorithm.RunTimeError"""

    @property
    @abc.abstractmethod
    def order(self) -> int:
        """Determines the order that a class that implements this interface should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception.
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        This provides a link back allowing the inner exceptions to be interpreted using the interpreters
        configured in the IExceptionInterpreter. Individual implementations *may* ignore
        this value if required.
        :returns: The interpreted exception.
        """
        ...


class SystemExceptionInterpreter(System.Object, QuantConnect.Exceptions.IExceptionInterpreter):
    """Base handler that will try get an exception file and line"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception. f
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        :returns: The interpreted exception.
        """
        ...

    @staticmethod
    def try_get_line_and_file(stack_trace: str, file_and_line: typing.Optional[str]) -> typing.Tuple[bool, str]:
        """Helper method to get the file and line from a C# stacktrace"""
        ...


class ClrBubbledExceptionInterpreter(QuantConnect.Exceptions.SystemExceptionInterpreter):
    """Interprets ClrBubbledException instances"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception. f
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        :returns: The interpreted exception.
        """
        ...


class ScheduledEventExceptionInterpreter(System.Object, QuantConnect.Exceptions.IExceptionInterpreter):
    """Interprets ScheduledEventException instances"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception.
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        This provides a link back allowing the inner exceptions to be interpreted using the interpreters
        configured in the IExceptionInterpreter. Individual implementations *may* ignore
        this value if required.
        :returns: The interpreted exception.
        """
        ...


class PythonExceptionInterpreter(System.Object, QuantConnect.Exceptions.IExceptionInterpreter):
    """Interprets PythonExceptionInterpreter instances"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception. f
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        :returns: The interpreted exception.
        """
        ...


class InvalidTokenPythonExceptionInterpreter(QuantConnect.Exceptions.PythonExceptionInterpreter):
    """Interprets InvalidTokenPythonExceptionInterpreter instances"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception.
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        :returns: The interpreted exception.
        """
        ...


class NoMethodMatchPythonExceptionInterpreter(QuantConnect.Exceptions.PythonExceptionInterpreter):
    """Interprets NoMethodMatchPythonExceptionInterpreter instances"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception.
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        :returns: The interpreted exception.
        """
        ...


class DllNotFoundPythonExceptionInterpreter(System.Object, QuantConnect.Exceptions.IExceptionInterpreter):
    """Interprets DllNotFoundPythonExceptionInterpreter instances"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception.
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        :returns: The interpreted exception.
        """
        ...


class StackExceptionInterpreter(System.Object, QuantConnect.Exceptions.IExceptionInterpreter):
    """Interprets exceptions using the configured interpretations"""

    INSTANCE: System.Lazy[QuantConnect.Exceptions.StackExceptionInterpreter] = ...
    """Stack interpreter instance"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    @property
    def interpreters(self) -> typing.Iterable[QuantConnect.Exceptions.IExceptionInterpreter]:
        """Gets the interpreters loaded into this instance"""
        ...

    def __init__(self, interpreters: typing.List[QuantConnect.Exceptions.IExceptionInterpreter]) -> None:
        """
        Initializes a new instance of the StackExceptionInterpreter class
        
        :param interpreters: The interpreters to use
        """
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception.
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    @staticmethod
    def create_from_assemblies(assemblies: typing.List[System.Reflection.Assembly]) -> QuantConnect.Exceptions.StackExceptionInterpreter:
        """
        Creates a new StackExceptionInterpreter by loading implementations with default constructors from the specified assemblies
        
        :param assemblies: The assemblies to scan
        :returns: A new StackExceptionInterpreter containing interpreters from the specified assemblies.
        """
        ...

    def get_exception_message_header(self, exception: System.Exception) -> str:
        """
        Combines the exception messages from this exception and all inner exceptions.
        
        :param exception: The exception to create a collated message from
        :returns: The collate exception message.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter = None) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        This provides a link back allowing the inner exceptions to be interpreted using the intepretators
        configured in the StackExceptionInterpreter. Individual implementations *may* ignore
        this value if required.
        :returns: The interpreted exception.
        """
        ...


class UnsupportedOperandPythonExceptionInterpreter(QuantConnect.Exceptions.PythonExceptionInterpreter):
    """Interprets UnsupportedOperandPythonExceptionInterpreter instances"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception.
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        :returns: The interpreted exception.
        """
        ...


class KeyErrorPythonExceptionInterpreter(QuantConnect.Exceptions.PythonExceptionInterpreter):
    """Interprets KeyErrorPythonExceptionInterpreter instances"""

    @property
    def order(self) -> int:
        """Determines the order that an instance of this class should be called"""
        ...

    def can_interpret(self, exception: System.Exception) -> bool:
        """
        Determines if this interpreter should be applied to the specified exception.
        
        :param exception: The exception to check
        :returns: True if the exception can be interpreted, false otherwise.
        """
        ...

    def interpret(self, exception: System.Exception, inner_interpreter: QuantConnect.Exceptions.IExceptionInterpreter) -> System.Exception:
        """
        Interprets the specified exception into a new exception
        
        :param exception: The exception to be interpreted
        :param inner_interpreter: An interpreter that should be applied to the inner exception.
        :returns: The interpreted exception.
        """
        ...



from abc import ABC, abstractmethod

from praw.models import Message


class CommandProcessor(ABC):
    """
    Class encapsulating objects responsible for
    processing user bot requests/commands
    """

    def __init__(self, command_string: str) -> None:
        self.__command_string = command_string

    @abstractmethod
    def process_message(self, message: Message, *args, **kwargs):
        """Process message command"""
        raise NotImplementedError

    def get_command_string(self) -> str:
        return self.__command_string

    def __eq__(self, o: object) -> bool:
        return isinstance(o, CommandProcessor) and o.__command_string == self.__command_string

    def __hash__(self) -> int:
        return hash(self.__command_string)

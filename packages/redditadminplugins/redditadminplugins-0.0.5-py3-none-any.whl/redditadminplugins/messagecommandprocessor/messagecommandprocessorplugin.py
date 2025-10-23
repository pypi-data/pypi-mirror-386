from typing import Set

from redditadmin import Plugin

from .program.commandprocessor import CommandProcessor
from .program.messagecommandprocessor import MessageCommandProcessor


class MessageCommandProcessorPlugin(Plugin[MessageCommandProcessor]):
    """
    Class responsible for running multiple
    Message Command Processor instances
    """

    def __init__(
            self,
            command_processors: Set[CommandProcessor]
    ):
        super().__init__(
            "msgcommandprocessor"
        )
        self.__command_processors = command_processors

    def get_program(self, reddit_interface):

        praw_reddit = reddit_interface.praw_reddit

        return MessageCommandProcessor(
            self.__command_processors,
            praw_reddit,
            self.is_shut_down
        )

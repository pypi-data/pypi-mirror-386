from typing import Set

from praw import Reddit
from praw.models import Message
from redditadmin import \
    CustomStreamFactory
from redditadmin import StreamProcessingProgram
from redditadmin import consumestransientapierrors

from .commandprocessor import CommandProcessor


class MessageCommandProcessor(StreamProcessingProgram):
    """Program to process message commands"""

    PROGRAM_NAME: str = "Message Command Processor"

    def __init__(
            self,
            command_processors: Set[CommandProcessor],
            praw_reddit: Reddit,
            stop_condition
    ):
        super().__init__(
            CustomStreamFactory(
                lambda: praw_reddit.inbox.unread
            ),
            stop_condition,
            MessageCommandProcessor.PROGRAM_NAME
        )
        self.__command_processors = dict([(c.get_command_string(), c) for c in command_processors])

    @consumestransientapierrors
    def _run_nature_core(self, unread):

        # Process if unread item is Message
        if isinstance(unread, Message):
            message: Message = unread

            # Process if message is message command
            if message.subject.startswith("!"):
                command = message.subject[1:]

                # Process if command is included in
                # provided commands
                if command in self.__command_processors.keys():
                    self._programLogger.debug(
                        'Processing message command "{}" with '
                        'arguments "{}" (Message ID: {})'.format(
                            command,
                            message.body,
                            message.id
                        )
                    )
                    self.__command_processors[command].process_message(
                        message
                    )

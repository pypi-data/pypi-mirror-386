from redditadmin import Plugin

from .program.scheduledposter import ScheduledPoster
from .program.scheduledposterstorage import ScheduledPosterStorage


class ScheduledPosterPlugin(Plugin[ScheduledPoster]):
    """
    Class responsible for running multiple
    Scheduled Poster program instances
    """

    def __init__(
            self,
            scheduled_poster_storage: ScheduledPosterStorage
    ):
        super().__init__(
            "scheduledposter"
        )
        self.__scheduled_poster_storage = scheduled_poster_storage

    def get_program(self, reddit_interface):

        praw_reddit = reddit_interface.praw_reddit

        return ScheduledPoster(
            praw_reddit,
            self.__scheduled_poster_storage,
            self.is_shut_down
        )

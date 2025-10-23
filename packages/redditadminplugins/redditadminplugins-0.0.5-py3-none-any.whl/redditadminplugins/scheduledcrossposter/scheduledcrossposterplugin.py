from concurrent.futures import ThreadPoolExecutor

from redditadmin import Plugin
from redditadmin import SubmissionStreamFactory

from .program.scheduledcrossposter import ScheduledCrossposter
from .program.scheduledcrossposterstorage import ScheduledCrossposterStorage


class ScheduledCrossposterPlugin(Plugin[ScheduledCrossposter]):
    """
    Class responsible for running multiple
    Scheduled Crossposter program instances
    """

    def __init__(
            self,
            scheduled_crossposter_storage: ScheduledCrossposterStorage,
            subreddit: str
    ):
        super().__init__(
            "scheduledcrossposter"
        )
        self.__scheduled_crossposter_storage = scheduled_crossposter_storage
        self.__subreddit = subreddit

    def get_program(self, reddit_interface):

        praw_reddit = reddit_interface.praw_reddit

        submission_stream_factory = SubmissionStreamFactory(
            praw_reddit.subreddit(
                self.__subreddit
            )
        )

        return ScheduledCrossposter(
            submission_stream_factory,
            self.__scheduled_crossposter_storage,
            ThreadPoolExecutor(),
            self.is_shut_down
        )

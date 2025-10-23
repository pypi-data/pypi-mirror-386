from datetime import datetime


class ScheduledSubmission:
    """Class representing a scheduled submission"""

    def __init__(
            self,
            url: str,
            subreddit: str,
            title: str,
            scheduled_time: datetime,
            flair_id: str = None,
            comment_body: str = None
    ):
        self.__url = url
        self.__subreddit = subreddit
        self.__title = title
        self.__scheduledTime = scheduled_time
        self.__flairId = flair_id
        self.__commentBody = comment_body

    @property
    def get_url(self):
        return self.__url

    @property
    def get_subreddit(self):
        return self.__subreddit

    @property
    def get_title(self):
        return self.__title

    @property
    def get_scheduled_time(self):
        return self.__scheduledTime

    @property
    def get_flair_id(self):
        return self.__flairId

    @property
    def get_comment_body(self):
        return self.__commentBody

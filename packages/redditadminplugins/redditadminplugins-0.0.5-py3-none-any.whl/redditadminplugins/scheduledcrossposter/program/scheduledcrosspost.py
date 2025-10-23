from datetime import datetime


class ScheduledCrosspost:
    """Class representing a scheduled crosspost"""

    __url: str
    __subreddit: str
    __scheduledTime: datetime
    __title: str

    def __init__(
            self,
            url: str,
            subreddit: str,
            scheduled_time: datetime,
            title: str = None
    ):
        self.__url = url
        self.__subreddit = subreddit
        self.__scheduledTime = scheduled_time
        self.__title = title

    @property
    def get_url(self):
        return self.__url

    @property
    def get_subreddit(self):
        return self.__subreddit

    @property
    def get_scheduled_time(self):
        return self.__scheduledTime

    @property
    def get_title(self):
        return self.__title

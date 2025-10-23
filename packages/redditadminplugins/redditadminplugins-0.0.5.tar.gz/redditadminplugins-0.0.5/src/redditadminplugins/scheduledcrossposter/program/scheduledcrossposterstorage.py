from .completedcrosspostrepository import CompletedCrosspostRepository
from .scheduledcrosspostrepository import ScheduledCrosspostRepository


class ScheduledCrossposterStorage:
    """
    Class holding storage DAOs used by the
    Scheduled Crossposter
    """

    def __init__(
            self,
            scheduled_crosspost_repository: ScheduledCrosspostRepository,
            completed_crosspost_repository: CompletedCrosspostRepository
    ):
        self.__scheduled_crosspost_repository = scheduled_crosspost_repository
        self.__completed_crosspost_repository = completed_crosspost_repository

    @property
    def get_scheduled_crosspost_repository(self):
        return self.__scheduled_crosspost_repository

    @property
    def get_completed_crosspost_repository(self):
        return self.__completed_crosspost_repository

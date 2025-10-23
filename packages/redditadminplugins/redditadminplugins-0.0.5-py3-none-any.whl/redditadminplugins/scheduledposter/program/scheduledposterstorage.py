from .completedsubmissionrepository import CompletedSubmissionRepository
from .scheduledsubmissionrepository import ScheduledSubmissionRepository


class ScheduledPosterStorage:
    """
    Class holding storage DAOs used by the
    Scheduled Poster
    """

    def __init__(
            self,
            scheduled_submission_repository: ScheduledSubmissionRepository,
            completed_submission_repository: CompletedSubmissionRepository
    ):

        self.__scheduledSubmissionRepository = scheduled_submission_repository
        self.__completedSubmissionRepository = completed_submission_repository

    @property
    def get_scheduled_submission_repository(self):
        return self.__scheduledSubmissionRepository

    @property
    def get_completed_submission_repository(self):
        return self.__completedSubmissionRepository

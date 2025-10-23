import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import ClassVar

from praw.models import Submission
from prawcore import PrawcoreException
from redditadmin import StreamProcessingProgram
from redditadmin import SubmissionStreamFactory
from redditadmin import consumestransientapierrors

from .scheduledcrosspost import ScheduledCrosspost
from .scheduledcrossposterstorage import ScheduledCrossposterStorage


class ScheduledCrossposter(StreamProcessingProgram):
    """
    Program responsible for submitting
    Scheduled Crossposts
    """

    PROGRAM_NAME: str = "Scheduled Crossposter"

    # Lock for concurrent write operations
    __LOCK: ClassVar[threading.Lock] = threading.Lock()

    def __init__(
            self,
            submission_stream_factory: SubmissionStreamFactory,
            scheduled_crossposter_storage: ScheduledCrossposterStorage,
            crosspost_processor: ThreadPoolExecutor,
            stop_condition
    ):
        super().__init__(
            submission_stream_factory,
            stop_condition,
            ScheduledCrossposter.PROGRAM_NAME
        )
        self.__scheduledCrossposterStorage = scheduled_crossposter_storage
        self.__crosspostProcessor = crosspost_processor

    def _run_nature_core(self, submission):

        scheduled_crossposter_storage = self.__scheduledCrossposterStorage

        # Local variable declaration
        scheduled_crosspost_dao = scheduled_crossposter_storage.get_scheduled_crosspost_repository
        completed_crosspost_dao = scheduled_crossposter_storage.get_completed_crosspost_repository

        # Handle if retrieved submission has
        # scheduled crossposts
        if scheduled_crosspost_dao.check_exists(
            submission.url
        ):
            scheduled_crossposts = scheduled_crosspost_dao \
                .get_scheduled_crossposts_for_url(
                    submission.url
                )
            non_completed_crossposts = list(
                filter(
                    lambda scheduled_crosspost:
                    not completed_crosspost_dao.check_completed(
                        scheduled_crosspost
                    ),
                    scheduled_crossposts
                )
            )
            # Process each non-completed crosspost
            for nonCompletedCrosspost in non_completed_crossposts:
                self.__crosspostProcessor.submit(
                    self.__process_non_completed_crosspost,
                    nonCompletedCrosspost,
                    submission
                )

    @consumestransientapierrors
    def __process_non_completed_crosspost(
            self,
            non_completed_crosspost: ScheduledCrosspost,
            submission: Submission
    ):
        """
        Process crossposts which have not been
        completed
        """

        scheduled_time = non_completed_crosspost.get_scheduled_time
        completed_crosspost_dao = self.__scheduledCrossposterStorage \
            .get_completed_crosspost_repository

        self._programLogger.debug(
            'Processing non-completed crosspost to {}, '
            'for submission "{}" (ID: {}) due {}'.format(
                non_completed_crosspost.get_subreddit,
                submission.title,
                submission.id,
                scheduled_time
            )
        )

        while True:
            if datetime.now(tz=timezone.utc) >= scheduled_time:
                try:
                    successful_crosspost = submission.crosspost(
                        subreddit=non_completed_crosspost.get_subreddit,
                        title=non_completed_crosspost.get_title
                    )
                    self._programLogger.debug(
                        'Crosspost "{}" (ID: {}) to {}, for submission "{}" (ID: {}) '
                        'due {} completed'.format(
                            successful_crosspost.title,
                            successful_crosspost.id,
                            non_completed_crosspost.get_subreddit,
                            submission.title,
                            submission.id,
                            scheduled_time
                        )
                    )
                    with ScheduledCrossposter.__LOCK:
                        completed_crosspost_dao.add(non_completed_crosspost)
                        self._programLogger.debug(
                            "Completion of crosspost (ID: {}) successfully "
                            "acknowledged".format(successful_crosspost.id)
                        )
                    break
                except PrawcoreException as ex:
                    self._programLogger.error(
                        'Non-completed crosspost to {} for submission "{}" '
                        '(ID: {}) due {} failed: ' + str(ex.args)
                    )
            time.sleep(1)

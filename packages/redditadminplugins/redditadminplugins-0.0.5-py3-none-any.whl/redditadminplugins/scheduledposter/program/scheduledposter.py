from typing import Callable

from praw import Reddit

from .scheduledposterstorage import ScheduledPosterStorage
from redditadmin import consumestransientapierrors
from redditadmin import RecurringProgram


class ScheduledPoster(RecurringProgram):
    """
    Program responsible for submitting
    scheduled submissions
    """

    PROGRAM_NAME: str = "Scheduled Poster"

    def __init__(
            self,
            praw_reddit: Reddit,
            scheduled_poster_storage: ScheduledPosterStorage,
            stop_condition: Callable[..., bool],
            cooldown: float = 1
    ):
        super().__init__(
            ScheduledPoster.PROGRAM_NAME,
            stop_condition,
            cooldown
        )
        self.__prawReddit = praw_reddit
        self.__scheduledPosterStorage = scheduled_poster_storage

    @consumestransientapierrors
    def _run_nature_core(self, *args, **kwargs):

        # Local variable declaration
        scheduled_poster_storage = self.__scheduledPosterStorage

        scheduled_submission_repository = scheduled_poster_storage \
            .get_scheduled_submission_repository

        completed_submission_repository = scheduled_poster_storage \
            .get_completed_submission_repository

        due_submissions = scheduled_submission_repository.get_due_submissions()

        for dueSubmission in due_submissions:

            # Handle if submission has not been processed
            if not completed_submission_repository.check_exists(dueSubmission):
                self._programLogger.debug(
                    'Processing due submission "{}" to subreddit '
                    '"{}" due {}'.format(
                        dueSubmission.get_title,
                        dueSubmission.get_subreddit,
                        dueSubmission.get_scheduled_time
                    )
                )
                submission = self.__prawReddit.subreddit(
                    dueSubmission.get_subreddit
                ).submit(
                    title=dueSubmission.get_title,
                    url=dueSubmission.get_url,
                    flair_id=dueSubmission.get_flair_id
                )
                self._programLogger.debug(
                    'Post "{}" (ID: {}) to subreddit "{}" due {} '
                    'successfully submitted'.format(
                        dueSubmission.get_title,
                        submission.id,
                        dueSubmission.get_subreddit,
                        dueSubmission.get_scheduled_time
                    )
                )
                completed_submission_repository.add(dueSubmission)
                self._programLogger.debug(
                    'Completed submission (ID: {}) successfully '
                    'acknowledged'.format(submission.id)
                )

                # Processing auto-reply for the given submission
                if bool(dueSubmission.get_comment_body):
                    reply = submission.reply(dueSubmission.get_comment_body)
                    self._programLogger.debug(
                        'Auto reply (ID: {}) for post (ID: {}) '
                        'successfully submitted'.format(
                            reply.id,
                            submission.id
                        )
                    )

# Reddit Admin Plugins

[![pypi](https://img.shields.io/pypi/v/redditadminplugins.svg)](https://pypi.org/project/redditadminplugins/)

Custom plugins for the `redditadmin` bot package (see [here](https://pypi.org/project/redditadmin/)).

## Installation

```console
pip install redditadminplugins
```

For instructions on installing Python and `pip` see "The Hitchhiker's Guide to Python"
[Installation Guides](https://docs.python-guide.org/en/latest/starting/installation/).

## `ScheduledPosterPlugin`

Submits live and past prescheduled posts automatically at the designated times. Takes implementations of `ScheduledSubmissionRepository` and `CompletedSubmissionRepository` as inputs through `ScheduledPosterStorage`.

## `ScheduledCrossposterPlugin`

Submits live and past prescheduled crossposts automatically at the designated times. The crossposter watches all posts in a given subreddit, awaiting a new post with a matching predetermined url, which it then crossposts at the designated time. Takes implementations of `ScheduledCrosspostRepository` and `CompletedCrosspostRepository` as inputs through `ScheduledCrossposterStorage`.

## `MessageCommandProcessorPlugin`

Processes direct message commands issued through direct message subjects, executing corresponding `CommandProcessor`s if there are any. Takes a set of implemented `CommandProcessors` as input.

## See more

-   [reddit-admin](https://github.com/Grod56/reddit-admin)
-   [PRAW](https://github.com/praw-dev/praw)

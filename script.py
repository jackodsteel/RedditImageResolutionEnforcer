#!/usr/bin/env python3
__author__ = "Jack Steel"

import praw
import requests
from PIL import Image
from io import BytesIO

SUBREDDIT = ""

MIN_WIDTH = 1920
ALLOW_TEXT_POSTS = True
ALLOW_NON_IMAGE_LINKS = True
IGNORE_MOD_SUBMISSIONS = False

USERNAME = ""
PASSWORD = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

USER_AGENT = "script:nz.co.jacksteel.imageresenforcer:v0.0.1 (by /u/iPlain)"

REMOVAL_TEXT_POST_MESSAGE = """
Your post has been removed as it is not a valid direct image link. Please resubmit a direct link to an image.
"""
REMOVAL_NON_IMAGE_LINK_MESSAGE = """
Your post has been removed as it is not a valid direct image link. Please resubmit a direct link to an image.
"""

REMOVAL_TOO_SMALL_MESSAGE = f"""
Your post has been removed as its resolution is too small for this subreddit, please submit an image that is at least {MIN_WIDTH}px wide.
"""

IMAGE_FORMAT_PREFIX = "image/"


class NonImageException(Exception):
    pass


def process_submissions(reddit):
    subreddit = reddit.subreddit(SUBREDDIT)
    mods = subreddit.moderator()

    for submission in subreddit.stream.submissions():
        try:
            review_post(submission, mods)
        except Exception as e:
            print(
                f"Unexpected error when processing {submission.id} by {submission.author}, reporting it for manual review.")
            print(e)
            submission.report(
                f"The image size bot encountered an unknown error on this submission, please manually review it.")


def review_post(submission, mods):
    if IGNORE_MOD_SUBMISSIONS and submission.author in mods:
        print(f"Ignoring {submission.id} by {submission.author} as they are a moderator.")
        return

    if submission.is_self:
        if ALLOW_TEXT_POSTS:
            print(f"Ignoring {submission.id} by {submission.author} as it is a text post.")
        else:
            print(f"Removing {submission.id} by {submission.author} as it is a text post.")
            remove_submission(submission, REMOVAL_TEXT_POST_MESSAGE)
        return

    try:
        width, height = get_image_size(submission.url)
    except OSError:
        print(f"Couldn't process {submission.id} by {submission.author}, reporting it for manual review.")
        submission.report(
            "The image size bot could not process this link for some reason, please manually review it.")
        return
    except NonImageException:
        if ALLOW_NON_IMAGE_LINKS:
            print(f"Ignoring {submission.id} by {submission.author} as it is a non image link.")
        else:
            print(f"Removing {submission.id} by {submission.author} as it is a non image link.")
            remove_submission(submission, REMOVAL_TEXT_POST_MESSAGE)
        return

    if width < MIN_WIDTH:
        print(f"Removing {submission.id} by {submission.author} as it is only {width}px wide.")
        remove_submission(submission, REMOVAL_TOO_SMALL_MESSAGE)
    else:
        print(f"Processed {submission.id} by {submission.author} and is a large enough image.")


def remove_submission(submission, reason):
    submission.mod.remove()
    submission.mod.send_removal_message(reason)


def get_image_size(url):
    response = requests.get(url)
    if not response.headers["Content-Type"].startswith(IMAGE_FORMAT_PREFIX):
        raise NonImageException("")
    data = response.content
    im = Image.open(BytesIO(data))
    return im.size


if __name__ == "__main__":
    process_submissions(praw.Reddit(
        username=USERNAME,
        password=PASSWORD,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT
    ))

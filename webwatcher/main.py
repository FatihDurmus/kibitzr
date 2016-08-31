import functools
import time
import logging

import schedule

from .fetcher import fetch, cleanup_fetchers
from .storage import report_changes
from .notifier import notify
from .conf import settings


logger = logging.getLogger(__name__)


def main(once=False, log_level=logging.INFO):
    logging.getLogger("").setLevel(log_level)
    logger.info("Arguments: %r",
                {"once": once, "log_level": log_level})
    logger.debug("Configration: %r", settings.PAGES)
    try:
        check_all_pages(settings.PAGES)
        if not once:
            schedule_checks(settings.PAGES)
            logger.info("Starting infinite loop")
            while True:
                schedule.run_pending()
                time.sleep(60)
    finally:
        cleanup_fetchers()


def schedule_checks(page_confs):
    for conf in page_confs:
        period = conf.get("period", 300)
        logger.info(
            "Scheduling checks for %r every %r seconds",
            conf["name"],
            period,
        )
        schedule.every(period).seconds.do(
            functools.partial(check_page, conf)
        )


def check_all_pages(page_confs):
    for conf in page_confs:
        check_page(conf)


def check_page(conf):
    content = fetch(conf)
    report = report_changes(conf, content)
    if report:
        logger.info("Sending notification for %r", conf["name"])
        notify(conf, report)

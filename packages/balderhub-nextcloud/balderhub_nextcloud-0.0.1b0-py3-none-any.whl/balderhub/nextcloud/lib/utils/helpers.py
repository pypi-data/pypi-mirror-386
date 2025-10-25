import logging
import time

from balderhub.nextcloud.lib.pages.web.base_page import BasePage

logger = logging.getLogger(__name__)


def dismiss_welcome_modal(base_page: BasePage, initial_wait_time: float = 3, timeout: float = 10) -> bool:
    """
    Helper funtion to dismiss the welcome modal when fist logged in.

    :return: True if the method has dismissed the welcome modal otherwise False.
    """

    time.sleep(initial_wait_time)  # TODO first there is the video
    # wait till the video modal is visible and then close it
    start_time = time.perf_counter()

    while not (base_page.modal_welcome.exists() and base_page.modal_welcome.is_visible()):
        time.sleep(.5)
        if time.perf_counter() - start_time > timeout:
            logger.info('no modal visible -> skip dismiss-welcome-modal')
            # no modal visible within the first 5 seconds -> break
            return False
    logger.info('dismiss welcome modal')

    base_page.modal_welcome.btn_close.click()
    base_page.modal_welcome.wait_to_be_removed_for(3)
    return True

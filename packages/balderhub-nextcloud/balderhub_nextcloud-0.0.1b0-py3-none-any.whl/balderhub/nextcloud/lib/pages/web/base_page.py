from typing import Union, List

import balder
from balderhub.html.lib.scenario_features.html_page import HtmlPage
from balderhub.html.lib.utils.selector import Selector
from balderhub.url.lib.utils import Url

from balderhub.nextcloud.lib.scenario_features import IsNextcloudServer
from balderhub.nextcloud.lib.utils.components.web import ModalVideo, ModalWelcome


class BasePage(HtmlPage):
    """
    base class for all web pages of the nextcloud web app
    """

    class Server(balder.VDevice):
        """
        remote serve vdevice
        """
        nextcloud = IsNextcloudServer()

    @property
    def applicable_on_url_schema(self) -> Union[Url, List[Url]]:
        raise NotImplementedError

    @property
    def modal_video(self) -> ModalVideo:
        """
        :return: selector to get the video modal
        """
        return ModalVideo.by_selector(
            self.driver, Selector.by_xpath(".//div[contains(@class, 'modal-wrapper') and .//video")
        )

    @property
    def modal_welcome(self) -> ModalWelcome:
        """
        :return: selector to get the welcome model
        """
        return ModalWelcome.by_selector(
            self.driver,
            Selector.by_xpath(".//div[contains(@class, 'modal-wrapper') "
                              "and .//h2[contains(text(), 'A collaboration platform that puts you in control')]]")
        )

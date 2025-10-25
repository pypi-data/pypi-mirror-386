from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector


class ModalWelcome(html.HtmlDivElement):
    """
    modal that shows the welcome box after first login
    """
    @property
    def btn_close(self) -> html.HtmlButtonElement:
        """
        :return: button to close modal
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath('.//div[contains(@class, "modal-container__content")]//button[@aria-label= "Close"]'),
            parent=self
        )

from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector


class ModalPickTemplate(html.HtmlDivElement):
    """
    modal that allows to pick a template - will be shown when creating a new file
    """
    @property
    def btn_blank(self):
        """
        :return: the button that needs to be clicked, when creating a blank file
        """
        return html.HtmlLabelElement.by_selector(
            self.driver, Selector.by_xpath('.//label[.//span[contains(text(), "Blank")]]'), parent=self
        )

    @property
    def btn_create(self):
        """
        :return: submit button to finally create the file
        """
        return html.HtmlButtonElement.by_selector(
            self.driver, Selector.by_xpath('.//input[@value="Create"]'), parent=self
        )

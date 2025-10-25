from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector
from .modal_pick_template import ModalPickTemplate

class ModalNewTextFile(html.HtmlDivElement):
    """
    modal to provide the name for the new file - will be shown directly when pressing the button to create a new file
    """

    @property
    def input_filename(self):
        """
        :return: returns the input element where the filename needs to be provided
        """
        return html.inputs.HtmlTextInput.by_selector(self.driver, Selector.by_css('.input-field__input'), parent=self)

    @property
    def btn_create(self):
        """
        :return: submit button to continue with the provided name
        """
        return html.HtmlButtonElement.by_selector(
            self.driver, Selector.by_xpath('.//button[.//span[contains(text(), "Create")]]'), parent=self
        )

    def click_on_create(self) -> ModalPickTemplate:
        """
        This method clicks on create and returns the following modal, where you can pick a template.
        :return:
        """
        self.btn_create.wait_to_be_clickable_for(3)
        self.btn_create.click()

        modal = ModalPickTemplate.by_selector(self.driver, Selector.by_xpath(
                ".//div[contains(@class, 'modal-wrapper') and .//h2[contains(text(), 'Pick a template for')]]"))
        modal.wait_to_be_clickable_for(3)
        return modal

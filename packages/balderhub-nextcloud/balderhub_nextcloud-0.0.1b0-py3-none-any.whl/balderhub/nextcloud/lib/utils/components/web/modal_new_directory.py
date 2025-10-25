from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector


class ModalNewDirectory(html.HtmlDivElement):
    """
    modal to provide the name for the new directory - will be shown directly when pressing the button to create a new
    directory
    """
    @property
    def input_filename(self):
        """
        :return: returns the input element where the directory name needs to be provided
        """
        return html.inputs.HtmlTextInput.by_selector(self.driver, Selector.by_css('.input-field__input'), parent=self)

    @property
    def btn_create(self):
        """
        :return: submit button to continue with the provided name
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath('.//button[.//span[contains(text(), "Create")]]'),
            parent=self
        )

    def click_on_create(self) -> None:
        """
        This method clicks on create.
        """
        self.btn_create.wait_to_be_clickable_for(3)
        self.btn_create.click()

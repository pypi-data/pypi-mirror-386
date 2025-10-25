from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector

from .modal_new_text_file import ModalNewTextFile
from .modal_new_directory import ModalNewDirectory


class MenuPlus(html.HtmlDivElement):
    """
    menu that will be opened after pressing on ``New`` button
    """

    @property
    def btn_new_text_file(self):
        """
        :return: returns the button for creating a new text file
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath(".//button[contains(@role, 'menuitem') and .//span[contains(text(), 'New text file')]]"),
            parent=self
        )

    @property
    def btn_new_directory(self):
        """
        :return: returns the button for creating a new directory
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath(".//button[contains(@role, 'menuitem') and .//span[contains(text(), 'New folder')]]"),
            parent=self
        )

    @property
    def btn_upload_file(self):
        """
        :return: returns the button for uploading a file
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath(".//button[contains(@role, 'menuitem') and .//span[contains(text(), 'Upload file')]]"),
            parent=self
        )

    def click_on_new_text_file(self):
        """
        This method clicks on the button to create a new text file and directly return the follow-up modal that will
        be shown when pressing the button.

        :return: the modal to provide the text file name
        """
        self.btn_new_text_file.wait_to_be_clickable_for(3).click()
        modal = ModalNewTextFile.by_selector(
            self.driver,
            Selector.by_xpath(".//div[contains(@class, 'modal-wrapper') and .//h2[contains(text(), 'New text file')]]")
        )
        modal.wait_to_be_clickable_for(3)
        return modal

    def click_on_new_directory(self):
        """
        This method clicks on the button to create a new directory and directly return the follow-up modal that will
        be shown when pressing the button.

        :return: the modal to provide the directory name
        """
        self.btn_new_directory.wait_to_be_clickable_for(3).click()
        modal = ModalNewDirectory.by_selector(
            self.driver,
            Selector.by_xpath(
                ".//div[contains(@class, 'modal-wrapper') and .//h2[contains(text(), 'Create new folder')]]"
            )
        )
        modal.wait_to_be_clickable_for(3)
        return modal

from abc import ABC, abstractmethod
from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector
from .modal_copy_or_move_to import ModalCopyOrMoveTo


class AbstractMenuTrigger(html.HtmlUlElement, ABC):
    """
    abstract conect menu that will be opened, when pressing the three dots within a file/directory row item
    """

    def _get_button_by_text(self, button_text: str):
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath(
                f".//button[contains(@class, 'action-button') and .//span[contains(text(), '{button_text}')]]"
            ),
            parent=self
        )

    @property
    def btn_moveorcopy(self):
        """
        :return: button for menu item ``Move or Copy``
        """
        return self._get_button_by_text('Move or copy')

    @property
    @abstractmethod
    def btn_delete(self) -> html.HtmlButtonElement:
        """
        :return: button for menu item ``Delete``
        """

    @property
    def btn_rename(self):
        """
        :return: button for menu item ``Rename``
        """
        return self._get_button_by_text('Rename')

    def click_on_moveorcopy(self) -> ModalCopyOrMoveTo:
        """
        This method clicks on the button ``Move or Copy` and returns the follow-up modal that will be opened after
        clicking on this button.`
        :return: the follow-up modal
        """
        self.btn_moveorcopy.wait_to_be_clickable_for(3).click()
        modal = ModalCopyOrMoveTo.by_selector(
            self.driver,
            Selector.by_xpath(
                ".//div[contains(@class, 'modal-wrapper') and .//h2[contains(text(), 'Choose destination')]]"
            )
        )
        modal.wait_to_be_clickable_for(3)
        return modal

    def click_on_delete(self) -> None:
        """
        This method clicks on the button ``Delete``.
        """
        self.btn_delete.wait_to_be_clickable_for(3).click()

    def click_on_rename(self) -> None:
        """
        This method clicks on the button ``Rename``.
        """
        self.btn_rename.wait_to_be_clickable_for(3).click()


class MenuContextForFile(AbstractMenuTrigger):
    """
    context menu class for files
    """
    @property
    def btn_delete(self):
        return self._get_button_by_text('Delete file')


class MenuContextForFolder(AbstractMenuTrigger):
    """
    context menu class for directories
    """
    @property
    def btn_delete(self):
        return self._get_button_by_text('Delete folder')

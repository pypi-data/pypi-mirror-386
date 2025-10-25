import time
from typing import Union, List

from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector
from balderhub.url.lib.utils import Url

from balderhub.nextcloud.lib.utils.components.web.menu_plus import MenuPlus
from balderhub.nextcloud.lib.utils.components.web import FilesListTable, FileRowItem

from .base_page import BasePage


class PageFiles(BasePage):
    """
    web app page for working with files
    """

    @property
    def applicable_on_url_schema(self) -> Union[Url, List[Url]]:
        return [
            Url(f'{self.Server.nextcloud.root_url.as_string()}/apps/files/files'),
            Url(f'{self.Server.nextcloud.root_url.as_string()}/apps/files/files/<int:change_no>?dir=<str:current_dir>')
        ]

    def open(self):
        """
        opens the web app page
        """
        self.driver.navigate_to(self.applicable_on_url_schema[0].as_string())
        self.wait_for_page()

    @property
    def table_files(self):
        """
        :return: returns the table object that holds all files of the current visible directory
        """
        return FilesListTable.by_selector(
            self.driver, Selector.by_xpath('.//table[contains(@class, "files-list__table")]')
        )

    @property
    def span_no_files(self):
        """
        :return: returns the span object that shows ``No files in here`` if the current selected directory is empty
        """
        return html.HtmlSpanElement.by_selector(
            self.driver, Selector.by_xpath('.//span[contains(text(), "No files in here")]')
        )

    @property
    def btn_menutoggle_new(self):
        """
        :return: returns the button object where it is possible to create/upload a new element
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath(".//button[contains(@class, 'action-item__menutoggle') and .//span[text()='New']]")
        )

    def open_plus_menu(self) -> MenuPlus:
        """
        This method opens the menu to create/upload a new file/directory
        :return:
        """
        self.btn_menutoggle_new.wait_to_be_clickable_for(3)
        self.btn_menutoggle_new.click()
        modal = MenuPlus.by_selector(
            self.driver,
            Selector.by_xpath('.//ul[contains(@id, "menu-") and .//li[contains(@class, "app-navigation-caption")]]')
        )
        modal.wait_to_be_clickable_for(3)
        return modal

    def get_all_visible_list_elements(self) -> list[FileRowItem]:
        """
        This method returns a list with all files/directory elements within the list. It returns a empty list if the
        ``No files in here`` is shown.
        :return: a list with all files/directories as :class:`FileRowItem`
        """
        start_time = time.perf_counter()
        while True: # todo use native wait method
            if self.span_no_files.is_visible() or self.table_files.is_visible():
                break
            if time.perf_counter() - start_time > 3:
                raise TimeoutError('no elements visible within 3 seconds')
        if self.span_no_files.is_visible():
            return []
        return self.table_files.get_child_elements()

    def focus_visible_list_element(self, name: str) -> FileRowItem:
        """
        This method returns a specific :class:`FileRowItem` with the provided name.

        :param name: the name the element should return for :meth:`FileRowItem.name`.
        :return: the row item with the requested name
        """
        # TODO what if list is really long?
        elements = self.get_all_visible_list_elements()
        filtered_elements = [elem for elem in elements if elem.full_name == name]
        if len(filtered_elements) == 0:
            raise ValueError(f'not able to find element with name "{name}"')
        if len(filtered_elements) > 1:
            raise ValueError(f'multiple elements with name "{name}"')
        return filtered_elements[0]

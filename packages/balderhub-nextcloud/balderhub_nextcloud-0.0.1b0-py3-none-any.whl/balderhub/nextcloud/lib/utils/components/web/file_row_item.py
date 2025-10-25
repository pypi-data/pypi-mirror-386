from typing import Union
from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector

from .menu_context import MenuContextForFile, MenuContextForFolder


class FileRowItem(html.HtmlDivElement):
    """
    single file/directory row item
    """

    @property
    def span_row_name(self):
        """
        :return: the span element that holds the file (without ext) or directory name
        """
        return html.HtmlSpanElement.by_selector(self.driver, Selector.by_css('.files-list__row-name-'), parent=self)

    @property
    def row_name(self):
        """
        :return: returns the file (without ext) or directory name
        """
        return self.span_row_name.text

    @property
    def span_row_name_ext(self):
        """
        :return: the span element that holds the file extension
        """
        return html.HtmlSpanElement.by_selector(self.driver, Selector.by_css('.files-list__row-name-ext'), parent=self)

    @property
    def row_name_ext(self):
        """
        :return: the file extension (with dot)
        """
        return self.span_row_name_ext.text

    @property
    def full_name(self):
        """
        :return: directory name or full file name (with ext)
        """
        return f"{self.row_name}{self.row_name_ext}"

    @property
    def is_file(self):
        """
        :return: True if this element is a file, False if it is a directory
        """
        return not html.HtmlSpanElement.by_selector(self.driver, Selector.by_css('.folder-icon'), parent=self).exists()

    @property
    def td_modified(self):
        """
        :return: table cell with the modified date
        """
        return html.HtmlTablecellElement.by_selector(
            self.driver, Selector.by_class('files-list__row-mtime'), parent=self
        )

    @property
    def btn_share(self):
        """
        :return: element button that opens the sharing tab
        """
        return html.HtmlButtonElement.by_selector(
            self.driver, Selector.by_xpath('.//button[@aria-label="Show sharing options"]'), parent=self
        )

    @property
    def btn_trigger_menu(self):
        """
        :return: button with the three dots to open context menu
        """
        return html.HtmlButtonElement.by_selector(
            self.driver, Selector.by_xpath('.//button[contains(@id, "trigger-menu-")]'), parent=self
        )

    @property
    def input_item_name(self):
        """
        :return: input field which will be available if the element should be renamed
        """
        return html.inputs.HtmlTextInput.by_selector(self.driver, Selector.by_xpath
            ('.//input[contains(@placeholder, "Folder name") or contains(@placeholder, "Filename")]'), parent=self)

    def open_context_menu(self) -> Union[MenuContextForFile, MenuContextForFolder]:
        """
        This method opens the context menu on the specific row and returns the context menu that will be opened with it.

        :return: the context menu
        """
        self.btn_trigger_menu.wait_to_be_clickable_for(3).click()

        if self.is_file:
            menu = MenuContextForFile.by_selector(
                self.driver,
                Selector.by_xpath('.//div[contains(@class, "v-popper__popper") and contains(@aria-hidden, "false") '
                                  'and .//ul[.//text()[contains(., "Delete file")]]]')
            )
        else:
            menu = MenuContextForFolder.by_selector(
                self.driver,
                Selector.by_xpath('.//div[contains(@class, "v-popper__popper") and contains(@aria-hidden, "false") '
                                  'and .//ul[.//text()[contains(., "Delete folder")]]]')
            )

        menu.wait_to_be_visible_for(3)
        return menu

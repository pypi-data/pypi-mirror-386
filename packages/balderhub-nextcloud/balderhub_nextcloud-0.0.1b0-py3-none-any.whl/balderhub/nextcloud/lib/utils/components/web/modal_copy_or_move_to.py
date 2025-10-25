from balderhub.gui.lib.utils.mixins import ListContainerMixin
from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector


class ModalCopyOrMoveTo(html.HtmlDivElement, ListContainerMixin):
    """
    modal to move or copy a file or a directory
    """

    class FilePickerRow(html.HtmlTablerowElement):
        """
        file/directory row within this modal
        """

        @property
        def td_row_name(self):
            """
            :return: the cell with the name of the row
            """
            return html.HtmlTablecellElement.by_selector(self.driver, Selector.by_class('row-name'), parent=self)

        @property
        def td_row_size(self):
            """
            :return: the cell with the file/directory size
            """
            return html.HtmlTablecellElement.by_selector(self.driver, Selector.by_class('row-size'), parent=self)

        @property
        def td_row_modified(self):
            """
            :return: the cell that holds the modified date
            """
            return html.HtmlTablecellElement.by_selector(self.driver, Selector.by_class('row-modified'), parent=self)

    def get_child_elements(self) -> list[FilePickerRow]:
        """
        :return: returns a list with all shown directories.
        """
        bridges = self.driver.find_bridges(Selector.by_xpath('.//tr[contains(@class,"file-picker__row")]'))
        return [self.FilePickerRow(bridge) for bridge in bridges]

    def get_file_picker_row_with_name(self, name: str) -> FilePickerRow:
        """
        This method returns the specific row that has the provided name.
        :param name: the name the directory should have
        :return: the specific list item
        """
        all_visible_rows = self.get_child_elements()
        filtered = [elem for elem in all_visible_rows if elem.td_row_name.text == name]
        if len(filtered) == 0:
            raise ValueError(f'did not find a row that matches the provided name `{name}`')
        if len(filtered) > 1:
            raise ValueError(f'found multiple rows with the name `{name}`')
        return filtered[0]

    @property
    def btn_copy(self):
        """
        :return: Submit button if the element should be copied
        """
        return html.HtmlButtonElement.by_selector(
            self.driver, Selector.by_xpath(".//button[.//span[contains(text(), 'Copy')]]"), parent=self
        )

    @property
    def btn_move(self):
        """
        :return: the move button if the element should be moved
        """
        return html.HtmlButtonElement.by_selector(
            self.driver, Selector.by_xpath(".//button[.//span[contains(text(), 'Move')]]"), parent=self
        )

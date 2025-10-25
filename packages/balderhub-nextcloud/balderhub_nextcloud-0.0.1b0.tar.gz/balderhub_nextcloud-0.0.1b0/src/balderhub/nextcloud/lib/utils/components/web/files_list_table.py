from typing import List

from balderhub.gui.lib.utils.mixins import ListContainerMixin
from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector

from .files_table_bulk_action import FilesTableBulkAction
from .file_row_item import FileRowItem


class FilesListTable(html.HtmlTableElement, ListContainerMixin):
    """
    inner table element with files/directories
    """

    @property
    def checkbox_selectall(self):
        """
        :return: returns the header checkbox that allows to select all elements of the table
        """
        return html.inputs.HtmlCheckboxInput.by_selector(
            self.driver,
            Selector.by_xpath('//thead//th[contains(@class, "files-list__column files-list__row-checkbox")]'),
            parent=self
        )

    @property
    def actions_batch(self):
        """
        :return: action menu to apply to selected items
        """
        return FilesTableBulkAction.by_selector(
            self.driver,
            Selector.by_xpath('//div[contains(@class, "files-list__column files-list__row-actions-batch")]')
        )

    def get_child_elements(self) -> List[FileRowItem]:
        """
        This method returns a list with all files/directory elements within the list.
        :return: a list with all files/directories as :class:`FileRowItem`
        """
        # TODO maybe we need to scroll
        all_bridges = self.bridge.find_bridges(Selector.by_class('files-list__row'))
        return [FileRowItem(bridge) for bridge in all_bridges]

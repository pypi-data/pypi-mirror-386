from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector


class FilesTableBulkAction(html.HtmlDivElement):
    """
    menu to change multiple items at once
    """

    @property
    def btn_add_to_favorites(self):
        """
        :return: button to add selected items to favorites
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath(".//button[.//span[text()='Add to favorites']]"),
            parent=self
        )

    @property
    def btn_manage_tags(self):
        """
        :return: button to modify the tags of the selected items
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath(".//button[.//span[text()='Manage tags']]"),
            parent=self
        )

    @property
    def btn_move_or_copy(self):
        """
        :return: button to move/copy the selected items
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath(".//button[.//span[text()='Move or copy']]"),
            parent=self
        )

    @property
    def btn_menutoggle(self):
        """
        :return: further button to open bulk context menu
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath(".//button[contains(@class, 'action-item__menutoggle')]"),
            parent=self
        )

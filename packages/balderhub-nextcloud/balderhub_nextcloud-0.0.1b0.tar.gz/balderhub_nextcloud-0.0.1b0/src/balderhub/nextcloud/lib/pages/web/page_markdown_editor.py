from typing import Union, List

from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector
from balderhub.url.lib.utils import Url

from .base_page import BasePage


class PageMarkdownEditor(BasePage):
    """
    page for editing or creating a markdown file
    """

    @property
    def applicable_on_url_schema(self) -> Union[Url, List[Url]]:
        return Url(f"{self.Server.nextcloud.root_url.as_string()}/apps/files/files/<int:index>"
                   f"?dir=<str:dir>&editing=false&openfile=true")

    @property
    def btn_save_document(self):
        """
        :return: returns the button to save the document
        """
        return html.HtmlButtonElement.by_selector(
            self.driver,
            Selector.by_xpath('//div[contains(@class, "viewer__file-wrapper")]//button[@aria-label="Save document"]')
        )

    @property
    def btn_close(self):
        """
        :return: returns the button to close the document
        """
        return html.HtmlButtonElement.by_selector(
            self.driver, Selector.by_xpath('//div[contains(@class, "modal-header")]//button[@aria-label="Close"]')
        )

    @property
    def editor(self):
        """
        :return: returns the input field that allows to edit the content of the document
        """
        # TODO it is a span and no input???
        return html.inputs.HtmlTextInput.by_selector(self.driver, Selector.by_css('.tiptap.ProseMirror-focused'))

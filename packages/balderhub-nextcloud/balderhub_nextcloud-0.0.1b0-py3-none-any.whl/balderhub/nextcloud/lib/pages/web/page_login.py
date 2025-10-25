from typing import Union, List

from balderhub.html.lib.utils import components as html
from balderhub.html.lib.utils.selector import Selector
from balderhub.url.lib.utils import Url

from .base_page import BasePage


class PageLogin(BasePage):
    """
    page where the user can log in
    """

    @property
    def applicable_on_url_schema(self) -> Union[Url, List[Url]]:
        return Url(f'{self.Server.nextcloud.root_url.as_string()}/login')

    def open(self):
        """
        opens the web app page
        """
        self.driver.navigate_to(self.applicable_on_url_schema.as_string())

    @property
    def input_username(self):
        """
        :return: returns the input field for the username
        """
        return html.inputs.HtmlTextInput.by_selector(self.driver, Selector.by_name('user'))

    @property
    def input_password(self):
        """
        :return: returns the inpu field for the password
        """
        return html.inputs.HtmlPasswordInput.by_selector(self.driver, Selector.by_name('password'))

    @property
    def btn_login(self):
        """
        :return: returns the button to submit the login form
        """
        return html.inputs.HtmlButtonInput.by_selector(self.driver, Selector.by_xpath('.//button[@type="submit"]'))

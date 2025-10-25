import balder
from balderhub.url.lib.utils import Url


class IsNextcloudServer(balder.Feature):
    """
    Base feature to mark a nextcloud server
    """

    @property
    def protocol(self) -> str:
        """
        :return: the protocol to connect with the nextcloud server
        """
        return 'http'

    @property
    def hostname(self) -> str:
        """
        :return: the hostname of the nextcloud server
        """
        return 'localhost'

    @property
    def port(self) -> int:
        """
        :return: the port of the nextcloud server
        """
        return 80

    @property
    def root_url(self) -> Url:
        """
        :return: the full root url
        """
        port_add_on = '' if self.port == 80 else f":{self.port}"
        return Url(f'{self.protocol}://{self.hostname}{port_add_on}')

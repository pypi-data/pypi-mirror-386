from typing import Union, List

import balderhub.html.lib.scenario_features

import balderhub.html.lib.utils.components as html
from balderhub.url.lib.utils import Url


class LoginPage(balderhub.html.lib.scenario_features.HtmlPage):
    """
    HTML Page for normal login pages as abstract base class - all abstract methods/properties needs to be defined in
    subclass
    """

    @property
    def url(self) -> Url:
        """
        :return: non-schema url the login page is located at
        """
        raise NotImplementedError

    @property
    def applicable_on_url_schema(self) -> Union[Url, List[Url]]:
        return self.url

    def open(self) -> None:
        """
        This method opens the login page.
        """
        self.driver.navigate_to(self.url)

    @property
    def input_username(self) -> html.inputs.HtmlTextInput:
        """
        :return: Html input field where the username needs to be filled
        """
        raise NotImplementedError

    @property
    def input_password(self) -> html.inputs.HtmlPasswordInput:
        """
        :return: Html input field where the password needs to be filled
        """
        raise NotImplementedError

    @property
    def btn_login(self) -> html.HtmlButtonElement:
        """
        :return: HTML button to submit the login form
        """
        raise NotImplementedError

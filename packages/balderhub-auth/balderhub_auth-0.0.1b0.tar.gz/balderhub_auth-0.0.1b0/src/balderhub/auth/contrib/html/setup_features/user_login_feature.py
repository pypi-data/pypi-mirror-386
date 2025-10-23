import balderhub.auth.lib.scenario_features.user_login_feature

from balderhub.auth.contrib.html.pages.login_page import LoginPage


class UserLoginFeature(balderhub.auth.lib.scenario_features.user_login_feature.UserLoginFeature):
    """
    Implementation of the user login feature for using the :class:`balderhub.contrib.html.pages.LoginPage` HTML pages
    """

    page = LoginPage()

    def insert_username(self, username: str) -> None:
        self.page.input_username.wait_to_be_clickable_for(1).type_text(username, clean_before=True)

    def insert_password(self, password: str) -> None:
        self.page.input_password.wait_to_be_clickable_for(1).type_text(password, clean_before=True)

    def submit_login(self) -> None:
        self.page.btn_login.wait_to_be_clickable_for(1).click()

    def is_already_logged_in(self):
        # TODO improve
        self.page.open()
        return not self.page.is_applicable()

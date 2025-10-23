import balder


class UserLoginFeature(balder.Feature):
    """
    This login feature can be assigned to devices that do provide a basic login handling.
    """

    def insert_username(self, username: str) -> None:
        """
        Inserts the username for login

        :param username: the username to insert
        """
        raise NotImplementedError

    def insert_password(self, password: str) -> None:
        """
        Inserts the password for login

        :param password: the password to insert
        """
        raise NotImplementedError

    def submit_login(self) -> None:
        """
        Executes the login
        """
        raise NotImplementedError

    def is_already_logged_in(self):
        """
        :return: returns True if someone is already logged in, otherwise False
        """
        raise NotImplementedError

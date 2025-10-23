from .base_role_feature import BaseRoleFeature


class UserRoleFeature(BaseRoleFeature):
    """
    config feature that provides a user/password authentification
    """
    @property
    def username(self) -> str:
        """
        :return: the valid username of this user role
        """
        raise NotImplementedError

    @property
    def password(self) -> str:
        """
        :return: the valid password for this user role
        """
        raise NotImplementedError

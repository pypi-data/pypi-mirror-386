from .base_role_feature import BaseRoleFeature


class TokenRoleFeature(BaseRoleFeature):
    """
    config feature that provides a basic token as authentication method
    """

    @property
    def token(self) -> str:
        """
        :return: returns the valid token to authenticate
        """
        raise NotImplementedError

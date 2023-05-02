class MissingEnvVarError(Exception):
    """ Exception raised when an environment variable is missing.
    """

    def __init__(self, env_var):
        self.env_var = env_var
        self.message = f'Missing Environment Variable: {self.env_var}'
        super().__init__(self.message)


class MisconfiguredConfFileError(Exception):
    """ Exception raised when the config file watchman.conf is missing.
    """

    def __init__(self):
        self.message = f"The file watchman.conf doesn't contain config details for Slack Watchman"
        super().__init__(self.message)


class MissingConfigVariable(Exception):
    """ Exception raised when config entry is missing.
    """

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.message = f'Missing variable in the config file: {self.config_entry}'
        super().__init__(self.message)


class SlackScopeError(Exception):
    """ Exception raised when the authed user doesn't have the required API scopes
    """

    def __init__(self, scope):
        self.scope = scope
        self.message = f'Slack API token is missing the required scope: {self.scope}'
        super().__init__(self.message)


class SlackAPIError(Exception):
    """ Exception raised for a generic Slack API error
    """

    def __init__(self, error_message):
        self.error_message = error_message
        self.message = f'Slack API error: {self.error_message}'
        super().__init__(self.message)


class SlackAPIRateLimit(Exception):
    """ Exception raised for a Slack rate limit warning
    """

    def __init__(self):
        self.message = f'Slack API rate limit reached - cooling off'
        super().__init__(self.message)

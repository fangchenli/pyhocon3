class ConfigException(Exception):

    def __init__(self, message, ex=None):
        super().__init__(message)
        self._exception = ex


class ConfigMissingException(ConfigException, KeyError):
    pass


class ConfigSubstitutionException(ConfigException):
    pass


class ConfigWrongTypeException(ConfigException):
    pass

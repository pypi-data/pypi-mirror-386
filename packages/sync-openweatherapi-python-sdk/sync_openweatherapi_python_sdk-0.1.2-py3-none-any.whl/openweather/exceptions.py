class OpenWeatherError(Exception):
    """ Base error for the SDK """

class AuthenticationError(OpenWeatherError):
    pass

class RateLimitError(OpenWeatherError):
    pass

class NotFoundError(OpenWeatherError):
    pass

class ServerError(OpenWeatherError):
    pass
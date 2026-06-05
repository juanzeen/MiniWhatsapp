class MiniWhatsappError(Exception):
    def __init__(self, message, status_code="error"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class DatabaseConnectionError(MiniWhatsappError):
    pass

class ValidationError(MiniWhatsappError):
    pass

class AuthenticationError(MiniWhatsappError):
    pass

class ResourceNotFoundError(MiniWhatsappError):
    pass

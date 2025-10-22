class DvNetException(Exception):
    pass


class DvNetRequestException(DvNetException):
    def __init__(self, message: str, request_body: str = "", status_code: int = 0):
        self.request_body = request_body
        self.status_code = status_code
        super().__init__(f"{message} (Status: {status_code}): {request_body}")


class DvNetInvalidRequestException(DvNetRequestException):
    pass


class DvNetServerException(DvNetRequestException):
    pass


class DvNetNetworkException(DvNetException):
    pass


class DvNetInvalidResponseDataException(DvNetException):
    pass


class DvNetInvalidWebhookException(DvNetException):
    pass


class DvNetUndefinedHostException(DvNetException):
    pass


class DvNetUndefinedXApiKeyException(DvNetException):
    pass

from __future__ import print_function

__all__ = ["HttpClient", "HttpMethod", "Request", "Response", "TwilioRestClient"]

from typing import Any, List, Optional

from com.google.common.collect import Range
from dev.coatl.helper.types import AnyStr
from java.io import InputStream
from java.lang import Enum, Object


class HttpClient(Object):
    def __init__(self):
        # type: () -> None
        super(HttpClient, self).__init__()

    def getLastRequest(self):
        # type: () -> Request
        pass

    def getLastResponse(self):
        # type: () -> Response
        pass

    def nmakeRequest(self, request):
        # type: (Request) -> Response
        raise NotImplementedError

    def reliableRequest(
        self,
        request,  # type: Request
        retryCodes=None,  # type: Optional[List[int]]
        retries=None,  # type: Optional[int]
        delayMillis=None,  # type: Optional[long]
    ):
        # type: (...) -> Response
        raise NotImplementedError


class HttpMethod(Enum):
    DELETE = "DELETE"
    GET = "GET"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    POST = "POST"
    PUT = "PUT"

    @staticmethod
    def forValue(value):
        # type: (AnyStr) -> HttpMethod
        pass

    @staticmethod
    def values():
        # type: () -> List[HttpMethod]
        pass


class Request(Object):
    def __init__(self, *args, **kwargs):
        # type: (*Any, **Any) -> None
        super(Request, self).__init__()
        print(args, kwargs)

    def addPostParam(self, name, value):
        # type: (AnyStr, AnyStr) -> None
        print(name, value)

    def addQueryDateRange(self, name, range):
        # type: (AnyStr, Range) -> None
        print(name, range)


class Response(Object):
    def __init__(self, *args, **kwargs):
        # type: (*Any, **Any) -> None
        super(Response, self).__init__()
        print(args, kwargs)

    def getContent(self):
        # type: () -> AnyStr
        pass

    def getStatusCode(self):
        # type: () -> int
        pass

    def getStream(self):
        # type: () -> InputStream
        pass


class TwilioRestClient(Object):

    class Builder(Object):
        def __init__(self, username, password):
            # type: (AnyStr, AnyStr) -> None
            super(TwilioRestClient.Builder, self).__init__()
            print(username, password)

        def accountSid(self, accountSid):
            # type: (AnyStr) -> TwilioRestClient.Builder
            print(accountSid)
            return self

        def build(self):
            # type: () -> TwilioRestClient
            return TwilioRestClient()

        def httpClient(self, httpClient):
            # type: (Object) -> TwilioRestClient.Builder
            print(httpClient)
            return self

        def region(self, region):
            # type: (AnyStr) -> TwilioRestClient.Builder
            print(region)
            return self

    HTTP_STATUS_CODE_CREATED = 201
    HTTP_STATUS_CODE_NO_CONTENT = 204
    HTTP_STATUS_CODE_OK = 200

    def getAccountSid(self):
        # type: () -> AnyStr
        pass

    def getHttpClient(self):
        # type: () -> HttpClient
        pass

    def getObjectMapper(self):
        # type: () -> Object
        pass

    def getRegion(self):
        # type: () -> AnyStr
        pass

    def request(self, request):
        # type: (Request) -> Response
        pass

from ..utils.dateutils import DateUtils
from ..pages import DefaultContentPage
from .handlerhttppage import HttpPageHandler


class DefaultUrlHandler(HttpPageHandler):
    """
    This handler works as HTML page handler, mostly
    """

    def __init__(self, url=None, contents=None, settings=None, request=None, url_builder=None):
        super().__init__(url, settings=settings, request=request, url_builder=url_builder)
        self.code = self.input2code(url)

    def get_page_url(self, url, crawler_name=None):
        #request = PageRequestObject(url)
        request = copy.copy(self.request)

        if not request:
            return

        request.url = url
        request.handler_type = HttpPageHandler
        request.crawler_name = crawler_name

        if self.url_builder:
            url = self.url_builder(url=url, request=request)
            return url


class DefaultChannelHandler(DefaultUrlHandler):
    pass

from django.middleware.gzip import GZipMiddleware


class PageGZipMiddleware(GZipMiddleware):
    """Gzip HTML/JSON only. Static files are pre-compressed (CSS/JS) or already compressed (images)."""

    def process_response(self, request, response):
        if request.path.startswith('/static/'):
            return response
        return super().process_response(request, response)

from django.middleware.gzip import GZipMiddleware

COMPRESSIBLE = ('text/', 'application/javascript', 'application/json', 'application/xml',
                'image/svg+xml', 'application/xhtml+xml')


class SmartGZipMiddleware(GZipMiddleware):
    """GZip only text-like 200 responses.

    Plain GZipMiddleware compresses *everything* with no Content-Encoding,
    including WhiteNoise's video responses, and corrupts Range/206 replies.
    This variant is safe to place in front of WhiteNoise so CSS/JS served as
    static files are compressed too.
    """

    def process_response(self, request, response):
        content_type = response.get('Content-Type', '')
        if (response.status_code != 200
                or response.has_header('Content-Range')
                or not content_type.startswith(COMPRESSIBLE)):
            return response
        return super().process_response(request, response)

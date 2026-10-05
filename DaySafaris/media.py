import os
import re

from django.http import FileResponse, Http404, HttpResponse, HttpResponseNotModified
from django.utils.http import http_date
from django.views.static import serve as django_serve

_RANGE = re.compile(r'bytes=(\d*)-(\d*)$')


def serve_media_with_range(request, path, document_root=None):
    """django.views.static.serve plus HTTP Range support.

    Safari/iOS will not play <video> unless the server answers Range requests
    with 206 Partial Content; the stock view always answers 200. Everything
    else (404s, directory traversal checks, 304s) is delegated to Django.
    """
    header = request.META.get('HTTP_RANGE')
    match = _RANGE.match(header.strip()) if header else None
    if not match or request.method != 'GET':
        return django_serve(request, path, document_root=document_root)

    full = os.path.normpath(os.path.join(str(document_root), path))
    if not full.startswith(os.path.normpath(str(document_root)) + os.sep) or not os.path.isfile(full):
        return django_serve(request, path, document_root=document_root)  # raises the proper 404

    size = os.path.getsize(full)
    start_s, end_s = match.groups()
    if start_s == '' and end_s == '':
        return django_serve(request, path, document_root=document_root)
    if start_s == '':                      # suffix range: last N bytes
        start, end = max(size - int(end_s), 0), size - 1
    else:
        start = int(start_s)
        end = min(int(end_s), size - 1) if end_s else size - 1
    if start > end or start >= size:
        response = HttpResponse(status=416)
        response['Content-Range'] = f'bytes */{size}'
        return response

    length = end - start + 1
    handle = open(full, 'rb')
    handle.seek(start)

    def chunks(chunk=64 * 1024, remaining=length):
        try:
            while remaining > 0:
                data = handle.read(min(chunk, remaining))
                if not data:
                    break
                remaining -= len(data)
                yield data
        finally:
            handle.close()

    from django.http import StreamingHttpResponse
    import mimetypes
    content_type = mimetypes.guess_type(full)[0] or 'application/octet-stream'
    response = StreamingHttpResponse(chunks(), status=206, content_type=content_type)
    response['Content-Length'] = str(length)
    response['Content-Range'] = f'bytes {start}-{end}/{size}'
    response['Accept-Ranges'] = 'bytes'
    response['Last-Modified'] = http_date(os.path.getmtime(full))
    return response

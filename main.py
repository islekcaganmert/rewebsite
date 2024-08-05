from flask import Flask, request, Response
import urllib.parse
import requests
import zlib
import gzip
from io import BytesIO

app = Flask(__name__)


@app.route('/<path:path>', methods=['GET', 'POST'])
@app.route('/', defaults={'path': '/'}, methods=['GET', 'POST'])
def index(path: str):
    domain = f"www.{request.host.removeprefix('re').split('.')[0].split('-')[0]}.com"
    url = f"https://{domain}/{path.removeprefix('/')}"
    if {i: request.args[i] for i in request.args}:
        url += '?'
        for i in request.args:
            url += f'{i}={urllib.parse.quote(request.args[i])}&'
        url = url.removesuffix('&')
    headers = {i[0]: i[1] for i in request.headers}
    headers.update({'Accept-Encoding': 'identity'})
    for i in ['Host', 'Upgrade-Insecure-Requests']:
        if i in headers:
            headers.pop(i)
    cookies = {i: request.cookies[i] for i in request.cookies}
    proxy = getattr(requests, request.method.lower())(url, headers=headers, data=request.get_data(), stream=True)
    headers = {i: proxy.headers[i] for i in proxy.headers}
    try:
        if headers.get('Content-Encoding') == 'deflate':
            content: str = zlib.decompress(proxy.content).decode()
        elif headers.get('Content-Encoding') == 'gzip':
            with gzip.GzipFile(fileobj=BytesIO(proxy.content)) as f:
                content: str = f.read().decode()
        else:
            content: str = headers.get('Content-Encoding')
    except zlib.error or gzip.error:
        content = proxy.content
    for i in ['Content-Encoding', 'Transfer-Encoding']:
        if i in headers:
            headers.pop(i)
    for i in headers:
        headers[i] = (
            headers[i]
            .replace(domain, request.host)
            .replace(domain.removeprefix('www.'), request.host)
            .replace(f"static.cdn{domain.removeprefix('www.')}", f"{request.host}/cdn")
        )
    if isinstance(content, str):
        content.replace(domain, request.host)
    return Response(
        response=proxy.content,
        status=proxy.status_code,
        headers=headers
    )


if __name__ == '__main__':
    app.run(debug=True)

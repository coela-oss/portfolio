"""Verify static redirect behavior without following a visitor to another origin."""
import concurrent.futures
import urllib.error
import urllib.parse
import urllib.request


def parse_rules(text):
    lines = text.splitlines()
    if not lines or len(lines) > 128:
        raise ValueError('Invalid redirect count')
    rules = []
    sources = set()
    for line in lines:
        fields = line.split()
        if len(fields) != 3 or len(line) > 4096:
            raise ValueError('Invalid redirect rule')
        source, target, status = fields
        if not source.startswith('/') or source.startswith('//') or any(c in source for c in '*:?\\') or '..' in source.split('/'):
            raise ValueError('Unsafe redirect source')
        url = urllib.parse.urlsplit(target)
        if target.startswith('/'):
            if target.startswith('//') or '..' in target.split('/'):
                raise ValueError('Unsafe local redirect')
        elif url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Unsafe redirect target')
        if status != '301' or source in sources or source == target:
            raise ValueError('Duplicate, cyclic or unsupported redirect')
        sources.add(source)
        rules.append((source, target))
    if any(target in sources for _, target in rules):
        raise ValueError('Redirect chain refused')
    return rules


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        return None


def verify_redirects(origin, text, observe=None):
    def read(source):
        opener = urllib.request.build_opener(NoRedirect)
        request = urllib.request.Request(origin + source, headers={'User-Agent': 'owner-site-release'})
        try:
            with opener.open(request, timeout=15) as response:
                return response.status, response.headers.get('Location')
        except urllib.error.HTTPError as error:
            with error:
                return error.code, error.headers.get('Location')
    observe = observe or read
    rules = parse_rules(text)
    def verify(rule):
        source, target = rule
        status, location = observe(source)
        if status != 301 or not location or urllib.parse.urljoin(origin, location) != urllib.parse.urljoin(origin, target):
            raise ValueError('Public redirect status or target differs')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(verify, rules))
    return len(rules)

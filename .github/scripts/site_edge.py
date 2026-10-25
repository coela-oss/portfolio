"""Python transport adapter to the public edge owner; no duplicate normalization."""
import json
import os
from pathlib import Path
from subprocess import run as edge_run, SubprocessError


def _edge(operation, data=b'', approved=None):
    pins = json.dumps(approved, separators=(',', ':'))
    if len(data) > 8 * 1024 * 1024 or len(pins) > 1024:
        raise ValueError('Edge adapter input exceeds budget')
    try:
        result = edge_run(['node', '--max-old-space-size=128', str(Path(__file__).with_suffix('.mjs')), operation, pins],
                          input=data, capture_output=True, timeout=10, check=True,
                          env={'PATH': os.environ.get('PATH', os.defpath)})
        if len(result.stdout) > 8 * 1024 * 1024:
            raise ValueError('Edge adapter output exceeds budget')
        return result.stdout
    except (SubprocessError, OSError) as error:
        raise ValueError('Public edge verification unavailable or rejected') from error


def edge_hashes(value):
    return json.loads(_edge('pins', approved=value))


def edge_script_digest(tag):
    return json.loads(_edge('digest', tag))


def origin_html(data, approved):
    return _edge('html', data, approved)

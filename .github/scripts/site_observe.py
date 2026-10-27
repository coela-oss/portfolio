"""Read a reviewed public release from hosted CI; never deploy or load CF keys."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.parse
from site_release import files, origin_html, edge_script_digest, read, select, unpack


def download(root, output):
    run_id = os.environ['SITE_RELEASE_RUN_ID']
    digest = os.environ['SITE_ARCHIVE_SHA256']
    if not re.fullmatch('[0-9]{1,16}', run_id) or not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('Invalid review identity')
    contract = read(root / '.github/site-release.json')
    owner = contract['repository']
    if os.environ.get('GITHUB_REPOSITORY', owner) != owner:
        raise ValueError('Foreign owner')
    metadata = subprocess.run(['gh', 'api', f'repos/{owner}/actions/runs/{run_id}'], check=True, capture_output=True, timeout=30)
    if len(metadata.stdout) > 1024 * 1024:
        raise ValueError('Run metadata exceeds observation budget')
    run = json.loads(metadata.stdout)
    site = select(root, contract, run['head_branch'])
    if run['event'] != 'push' or run['path'].split('@')[0] != '.github/workflows/release-site.yml' or not re.fullmatch('[a-f0-9]{40}', run['head_sha']):
        raise ValueError('Not an owned release run')
    output.mkdir(parents=True, exist_ok=False)
    subprocess.run(['gh', 'run', 'download', run_id, '--repo', owner, '--name', f"site-release-{run['head_sha']}-1", '--dir', str(output / 'input')], check=True, capture_output=True, timeout=60)
    archive = output / 'input/site.tgz'
    if archive.stat().st_size > 10 * 1024 * 1024:
        raise ValueError('Archive exceeds observation budget')
    candidate = unpack(archive, digest, output / 'verified')
    if candidate['source'] != run['head_sha'] or candidate['site'] != site:
        raise ValueError('Artifact target differs from current owner contract')
    (output / 'review.json').write_text(json.dumps({'source':run['head_sha'],'archive_sha256':digest,'run':run_id}) + '\n')


def observe(output):
    review = read(output / 'review.json')
    if hashlib.sha256((output / 'input/site.tgz').read_bytes()).hexdigest() != review['archive_sha256']:
        raise ValueError('Review archive changed')
    candidate = read(output / 'verified/candidate.json')
    if candidate['source'] != review['source'] or files(output / 'verified/assets') != candidate['files']:
        raise ValueError('Observation input changed')
    origin = candidate['site']['origin']
    pins = candidate['site'].get('edgeScriptHashes', {})
    results = output / 'results'
    results.mkdir(exist_ok=False)

    def one(item):
        name, expected = item
        path = name[:-10] if name.endswith('index.html') else name
        record = {'path':name,'expected_sha256':expected,'matched':False}
        try:
            with tempfile.TemporaryDirectory() as temporary:
                body_path = Path(temporary) / 'body'
                response = subprocess.run(['curl', '--silent', '--show-error', '--location', '--max-redirs', '5', '--proto-redir', '=https', '--connect-timeout', '5', '--max-time', '30', '--max-filesize', '8388608', '--dump-header', '-', '--output', str(body_path), '--write-out', '\n__OBSERVATION__%{http_code} %{url_effective}', origin + '/' + urllib.parse.quote(path)], capture_output=True, timeout=35)
                metadata = response.stdout.decode('utf8', errors='replace')
                header_text, status = metadata.rsplit('\n__OBSERVATION__', 1)
                code, final_url = status.split(' ', 1)
                record.update(exit_code=response.returncode,http_status=int(code))
                if urllib.parse.urlsplit(final_url).netloc != urllib.parse.urlsplit(origin).netloc:
                    record['error'] = 'unexpected_response_origin'
                    return record
                allowed = {'content-type','content-encoding','cache-control','etag','cf-ray','cf-cache-status','cf-mitigated','server'}
                record['headers'] = {key.lower():value.strip() for line in header_text.splitlines() if ':' in line for key,value in [line.split(':',1)] if key.lower() in allowed}
                data = body_path.read_bytes() if body_path.exists() else b''
                if len(data) > 8 * 1024 * 1024:
                    raise ValueError('Response too large')
            raw = hashlib.sha256(data).hexdigest()
            normalized = hashlib.sha256(origin_html(data, pins) if name.endswith('.html') else data).hexdigest()
            challenge = record['headers'].get('cf-mitigated') == 'challenge'
            record.update(raw_sha256=raw,normalized_sha256=normalized,bytes=len(data),matched=response.returncode == 0 and normalized == expected and not challenge and int(code) in ({200,404} if name == '404.html' else {200}))
            if not record['matched']:
                record['error'] = ('cloudflare_challenge' if challenge else
                                   'edge_http_forbidden' if int(code) == 403 and record['headers'].get('server') == 'cloudflare' else
                                   'asset_digest_mismatch')
                if name.endswith('.html'):
                    tags = [m.group() for m in re.finditer(rb'<script\b[^>]*>.*?</script>', data, re.S)]
                    record['script_digests'] = [edge_script_digest(tag) for tag in tags[-16:]]
                    (results / (hashlib.sha256(name.encode()).hexdigest() + '.html.txt')).write_bytes(data[:128 * 1024])
                    record['saved_body_truncated'] = len(data) > 128 * 1024
        except subprocess.TimeoutExpired:
            record['error'] = 'transport_timeout'
        except Exception as error:
            record.update(error='observation_failed',exception_type=type(error).__name__)
        return record

    expected = [(name, digest) for name, digest in candidate['files'].items() if name not in ['_redirects', '_headers']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        observed = list(pool.map(one, expected))
    report = {**review,'files':observed,'observed':len(observed),'matched':sum(r['matched'] for r in observed),'cloudflareCredentialsUsed':False,'deploymentAttempted':False}
    blocked = {'cloudflare_challenge', 'edge_http_forbidden'}
    failures = [row for row in observed if not row['matched']]
    report['state'] = ('verified' if not failures else 'public_observation_blocked' if all(row.get('error') in blocked for row in failures) else 'read_partial')
    report['blockedResponses'] = sum(row.get('error') in blocked for row in observed)
    (results / 'observations.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key:value for key,value in report.items() if key != 'files'}))
    return 0 if report['matched'] == len(expected) else 2


def summary(root, output):
    report = read(output / 'results/observations.json')
    text = f"Public observation: **{report['state']}**. Matched {report['matched']}/{report['observed']}; edge-blocked {report['blockedResponses']}. No deployment or Cloudflare credentials.\n"
    path = root / 'docs/operations/current-production-verification.json'
    if path.is_file():
        operator = read(path)
        if operator['source'] == report['source'] and operator['archiveSha256'] == report['archive_sha256'] and operator['verificationContext'] == 'local-public-read-only':
            text += f"\nSeparate operator evidence: {operator['publicAssetsVerified']} public assets and {operator['redirectsVerified']} redirects verified locally. See `docs/operations/current-production-verification.json`. This is explicitly separate from hosted CI verification.\n"
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
        stream.write(text)


if __name__ == '__main__':
    try:
        output = Path(sys.argv[2]).resolve()
        if sys.argv[1] == 'download':
            download(Path.cwd(), output)
            raise SystemExit(0)
        if sys.argv[1] == 'summary':
            summary(Path.cwd(), output)
            raise SystemExit(0)
        if sys.argv[1] != 'observe':
            raise ValueError('Unknown read-only action')
        raise SystemExit(observe(output))
    except Exception as error:
        print(json.dumps({'state':'observation_stopped','exception_type':type(error).__name__,'deploymentAttempted':False}))
        raise SystemExit(2)

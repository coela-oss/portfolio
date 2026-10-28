"""Owner-local static site tag admission, immutable packaging and deployment.

No central repository, preview Worker, DNS mutation or secret persistence.
"""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import urllib.error
import urllib.parse
from site_redirects import verify_redirects, parse_rules
from site_edge import edge_hashes, edge_script_digest, origin_html


def read(path):
    return json.loads(Path(path).read_text())


def owned(root, name):
    path = root / name
    if not re.fullmatch('[A-Za-z0-9._/-]+', name) or Path(name).is_absolute() or '..' in Path(name).parts or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes owner repository')
    return path


def select(root, contract, tag):
    if contract['schemaVersion'] != 1 or not re.fullmatch(r'[\w.-]+/[\w.-]+', contract['repository']):
        raise ValueError('Invalid owner contract')
    matches = [s for s in contract['sites'] if tag == f"site/{s['id']}/v{s['version']}"]
    if len(matches) != 1:
        raise ValueError('Tag must select exactly one site and its reviewed version')
    site = matches[0]
    edge_hashes(site.get('edgeScriptHashes', {}))
    if not isinstance(site.get('deploymentEnabled', True), bool):
        raise ValueError('Deployment readiness must be explicit boolean')
    if not re.fullmatch(r'site-production-[a-z0-9-]+', site['environment']):
        raise ValueError('Invalid production Environment')
    if not re.fullmatch(r'[a-z0-9-]+', site['id']) or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', site['version']):
        raise ValueError('Invalid site identity/version')
    if not re.fullmatch(r'[a-f0-9]{32}', site['account']) or not re.fullmatch(r'[a-z0-9-]+', site['worker']):
        raise ValueError('Invalid Cloudflare identity')
    if not re.fullmatch(r'[a-f0-9]{32}', site['zone']):
        raise ValueError('Invalid owned zone')
    if site['origin'] != 'https://' + site['domain'] or not re.fullmatch(r'[a-z0-9.-]+', site['domain']):
        raise ValueError('Invalid production origin')
    zone_name = site.get('zoneName', site['domain'])
    if not re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*', zone_name) or not (site['domain'] == zone_name or site['domain'].endswith('.' + zone_name)):
        raise ValueError('Site domain must belong to the explicit owned zone')
    install = owned(root, site.get('installDirectory', site['appDirectory']))
    if not owned(root, site['appDirectory']).resolve().is_relative_to(install.resolve()):
        raise ValueError('Install root must contain the selected application')
    for key in ['appDirectory', 'assetDirectory', 'siteConfig', 'documentDirectory']:
        owned(root, site[key])
    if read(owned(root, site['siteConfig']))['origin'] != site['origin']:
        raise ValueError('Site configuration origin differs from release target')
    return site


def selected_site(root, contract, environment):
    if environment.get('SITE_RELEASE_MODE') != 'main':
        return select(root, contract, environment['GITHUB_REF_NAME'])
    if len(contract['sites']) != 1:
        raise ValueError('Main release must select exactly one registered site')
    registered = contract['sites'][0]
    return select(root, contract, f"site/{registered['id']}/v{registered['version']}")


def request(url, token=None):
    headers = {'User-Agent': 'owner-site-release', 'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.url != url:
            raise ValueError('API redirect refused')
        data = response.read(10 * 1024 * 1024 + 1)
        if len(data) > 10 * 1024 * 1024:
            raise ValueError('Oversized metadata')
        return json.loads(data)


def admit(root, contract, environment):
    sha = environment['GITHUB_SHA']
    if environment['GITHUB_REPOSITORY'] != contract['repository'] or environment['GITHUB_REF_TYPE'] != 'tag' or not re.fullmatch('[a-f0-9]{40}', sha):
        raise ValueError('Owner/tag/source mismatch')
    event = read(environment['GITHUB_EVENT_PATH'])
    if event['repository']['full_name'] != contract['repository'] or event.get('deleted'):
        raise ValueError('Foreign or deleted tag')
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() != sha:
        raise ValueError('Checkout differs from event source')
    subprocess.run(['git', 'merge-base', '--is-ancestor', sha, 'origin/' + contract['defaultBranch']], cwd=root, check=True)
    runs = request(f"https://api.github.com/repos/{contract['repository']}/actions/runs?head_sha={sha}&per_page=100", environment['GH_TOKEN'])['workflow_runs']
    if not contract['requiredWorkflows']:
        raise ValueError('Source CI required')
    for workflow in contract['requiredWorkflows']:
        matches = [r for r in runs if r.get('path', '').split('@')[0] == '.github/workflows/' + workflow and r['event'] == 'push' and r['head_branch'] == contract['defaultBranch']]
        if not matches or matches[0]['status'] != 'completed' or matches[0]['conclusion'] != 'success':
            raise ValueError('Required source CI has not succeeded')


def admit_main(root, contract, environment):
    """Bind a completed main CI run to the current main commit before release."""
    sha = environment['SITE_RELEASE_SOURCE_SHA']
    event = read(environment['GITHUB_EVENT_PATH'])
    run = event.get('workflow_run', {})
    if (environment['GITHUB_REPOSITORY'] != contract['repository'] or
            environment.get('GITHUB_EVENT_NAME') != 'workflow_run' or
            not re.fullmatch('[a-f0-9]{40}', sha) or
            event.get('repository', {}).get('full_name') != contract['repository'] or
            run.get('head_repository', {}).get('full_name') != contract['repository'] or
            run.get('head_sha') != sha or run.get('head_branch') != contract['defaultBranch'] or
            run.get('event') != 'push' or run.get('status') != 'completed' or run.get('conclusion') != 'success' or
            run.get('run_attempt') != 1 or
            run.get('path', '').split('@')[0] != '.github/workflows/site.yml'):
        raise ValueError('Untrusted main CI event')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    ref = request(f"https://api.github.com/repos/{contract['repository']}/git/ref/heads/{contract['defaultBranch']}", environment['GH_TOKEN'])
    if head != sha or ref.get('object', {}).get('sha') != sha:
        raise ValueError('Main advanced or checkout differs')
    runs = request(f"https://api.github.com/repos/{contract['repository']}/actions/runs?head_sha={sha}&per_page=100", environment['GH_TOKEN'])['workflow_runs']
    if not contract['requiredWorkflows']:
        raise ValueError('Source CI required')
    for workflow in contract['requiredWorkflows']:
        matches = [r for r in runs if r.get('path', '').split('@')[0] == '.github/workflows/' + workflow and r.get('event') == 'push' and r.get('head_branch') == contract['defaultBranch']]
        if not matches or matches[0].get('status') != 'completed' or matches[0].get('conclusion') != 'success':
            raise ValueError('Required source CI has not succeeded')


def files(directory):
    result = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink in public output')
        if not path.is_file():
            continue
        if path.stat().st_size > 100 * 1024 * 1024 or len(result) >= 10000:
            raise ValueError('Public asset limits exceeded')
        result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not result or 'index.html' not in result:
        raise ValueError('Static homepage missing')
    return result


def build_worker(root, site):
    code = "import {documentWorker} from '@nuxtjp/localized-site/documents'; import {pathToFileURL} from 'node:url'; console.log(JSON.stringify(await documentWorker(pathToFileURL(process.argv[1]+'/'))))"
    result = subprocess.run(['node', '--input-type=module', '-e', code, str(owned(root, site['documentDirectory']))],
                            cwd=owned(root, site['appDirectory']), check=True, capture_output=True, text=True, timeout=120)
    if len(result.stdout.encode()) > 3 * 1024 * 1024:
        raise ValueError('Delivery entry exceeds byte budget')
    worker = json.loads(result.stdout)
    if set(worker) != {'source','origin','routes'} or worker['origin'] != site['origin'] or not isinstance(worker['source'], str) or len(worker['source'].encode()) > 1024 * 1024 or not isinstance(worker['routes'], list) or not 1 <= len(worker['routes']) <= 100 or len(set(worker['routes'])) != len(worker['routes']) or not all(isinstance(path, str) and re.fullmatch(r'/(?:[a-z0-9-]+/?)*', path) for path in worker['routes']):
        raise ValueError('Delivery entry selection differs from owned site')
    return worker


def pack(root, site, sha, output):
    if output.exists():
        raise ValueError('New artifact directory required')
    assets = owned(root, site['assetDirectory'])
    files(assets)  # Reject unsafe output before copying anything.
    if (assets / '_redirects').exists():
        parse_rules((assets / '_redirects').read_text())
    output.mkdir(parents=True)
    shutil.copytree(assets, output / 'assets')
    marker = {'site': site['id'], 'source_sha': sha, 'release_domain': site['domain'], 'purpose': 'production', 'version': site['version']}
    (output / 'assets/.well-known').mkdir(exist_ok=True)
    (output / 'assets/.well-known/release.json').write_text(json.dumps(marker) + '\n')
    receipt = {'site': site, 'source': sha, 'files': files(output / 'assets')}
    worker = build_worker(root, site)
    (output / 'worker.mjs').write_text(worker['source'])
    receipt['worker'] = {'sha256': hashlib.sha256((output / 'worker.mjs').read_bytes()).hexdigest(), 'routes': worker['routes']}
    (output / 'candidate.json').write_text(json.dumps(receipt, sort_keys=True) + '\n')
    with tarfile.open(output / 'site.tgz', 'w:gz') as archive:
        archive.add(output / 'candidate.json', arcname='candidate.json')
        archive.add(output / 'worker.mjs', arcname='worker.mjs')
        archive.add(output / 'assets', arcname='assets')
    digest = hashlib.sha256((output / 'site.tgz').read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(digest + '  site.tgz\n')
    return digest


def unpack(archive, expected, destination):
    if not re.fullmatch('[a-f0-9]{64}', expected) or hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError('Prepared archive digest mismatch')
    if destination.exists():
        raise ValueError('Fresh extraction directory required')
    with tarfile.open(archive) as data:
        names = set()
        total = 0
        for item in data:
            path = Path(item.name)
            total += item.size
            if total > 1024 * 1024 * 1024 or len(names) > 10003 or item.size > 100 * 1024 * 1024 or item.name in names or path.is_absolute() or '..' in path.parts or not (item.isfile() or item.isdir()) or not (item.name in ['candidate.json', 'worker.mjs'] or path.parts[0] == 'assets'):
                raise ValueError('Unsafe or duplicate archive entry')
            names.add(item.name)
        data.extractall(destination, filter='data')
    receipt = read(destination / 'candidate.json')
    if files(destination / 'assets') != receipt['files']:
        raise ValueError('Extracted public assets differ')
    entry = destination / 'worker.mjs'
    if not entry.is_file() or entry.is_symlink() or entry.stat().st_size > 1024 * 1024 or hashlib.sha256(entry.read_bytes()).hexdigest() != receipt['worker']['sha256']:
        raise ValueError('Extracted delivery entry differs')
    return receipt


def verify_assets(origin, expected, approved=None):
    approved = edge_hashes({} if approved is None else approved)
    def one(item):
        name, digest = item
        path = name[:-10] if name.endswith('index.html') else name
        for attempt in range(5):
            # Nuxt's .html assets redirect to canonical paths; generated 404
            # pages may legitimately retain 404 status. Admit only exact bytes.
            try:
                response = subprocess.run(['curl', '--silent', '--show-error', '--location', '--max-redirs', '5', '--proto-redir', '=https', '--connect-timeout', '5', '--max-time', '30', '--max-filesize', '8388608', origin + '/' + urllib.parse.quote(path)], capture_output=True, timeout=35)
            except subprocess.TimeoutExpired:
                response = None
            if response is not None and response.returncode == 0:
                content = response.stdout
                if hashlib.sha256(content).hexdigest() == digest:
                    return
                if name.endswith('.html') and hashlib.sha256(origin_html(content, approved)).hexdigest() == digest:
                    return
            if attempt < 4:
                time.sleep(3)
        raise ValueError('Production asset verification failed')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(one, expected.items()))


def deployment_tool(root, site):
    app = owned(root, site.get('installDirectory', site['appDirectory']))
    manifest = read(app / 'package.json')
    version = manifest.get('devDependencies', {}).get('wrangler', '')
    binary = app / 'node_modules/.bin/wrangler'
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version) or not (app / 'pnpm-lock.yaml').is_file() or not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError('Pinned Wrangler dependency, lockfile and installed executable are required')
    return binary


def verify_delivery(origin, receipt):
    def read(path, headers=None):
        req = urllib.request.Request(origin + path, headers={'User-Agent':'owner-site-release-readback', **(headers or {})})
        try:
            response = urllib.request.urlopen(req, timeout=20)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read(1024 * 1024 + 1)
            if len(body) > 1024 * 1024 or not response.url.startswith(origin + '/'):
                raise ValueError('Unexpected public delivery response')
            return response.status, response.headers, body
    status, robot_headers, robots = read('/robots.txt')
    if status != 200 or not robot_headers.get('Content-Type','').startswith('text/plain') or b'ai-train=yes' not in robots or b'Disallow: /' in robots:
        raise ValueError('Published AI permission policy is missing or overridden at the edge')
    def one(route):
        raw = '/raw' + ('/index' if route == '/' else route.rstrip('/')) + '.md'
        status, headers, body = read(route, {'Accept':'text/markdown'})
        if status != 200 or hashlib.sha256(body).hexdigest() != receipt['files'][raw.lstrip('/')] or not headers.get('Content-Type','').startswith('text/markdown') or 'accept' not in headers.get('Vary','').lower() or 'ai-train=yes' not in headers.get('Content-Signal',''):
            raise ValueError('Negotiated Markdown differs from prepared public bytes')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(one, receipt['worker']['routes']))


def deployment_config(site, receipt):
    # Existing custom domains are managed separately and checked before/after.
    # Omitting routes lets the deploy token avoid route-write permissions.
    return {'name': site['worker'], 'account_id': site['account'], 'compatibility_date': '2026-10-15',
            'workers_dev': False, 'preview_urls': False, 'main': './verified/worker.mjs',
            'assets': {'directory': './verified/assets', 'binding': 'ASSETS',
                       'run_worker_first': receipt['worker']['routes']}}


def deploy(root, contract, site, output, expected):
    receipt = unpack(output / 'site.tgz', expected, output / 'verified')
    is_main = os.environ.get('SITE_RELEASE_MODE') == 'main'
    source = os.environ['SITE_RELEASE_SOURCE_SHA'] if is_main else os.environ['GITHUB_SHA']
    if receipt['site'] != site or receipt['source'] != source:
        raise ValueError('Prepared artifact owner/source mismatch')
    # A configured Environment alone does not prove that review is enforced.
    environment = request(f"https://api.github.com/repos/{contract['repository']}/environments/{site['environment']}", os.environ['GH_TOKEN'])
    if not any(p['type'] == 'required_reviewers' and p.get('reviewers') for p in environment.get('protection_rules', [])):
        raise ValueError('Effective required reviewers missing; local-only release remains necessary')
    token = os.environ['CLOUDFLARE_API_TOKEN']
    prefix = f"https://api.cloudflare.com/client/v4/accounts/{site['account']}/workers"
    zone_url = f"https://api.cloudflare.com/client/v4/zones/{site['zone']}"
    zone = request(zone_url, token)
    if zone.get('success') is not True or zone['result']['name'] != site.get('zoneName', site['domain']) or zone['result']['account']['id'] != site['account'] or zone['result']['status'] != 'active':
        raise ValueError('Owned active zone mismatch')
    def dns_digest():
        records = []
        for page in range(1, 100):
            data = request(zone_url + f'/dns_records?per_page=100&page={page}', token)
            if data.get('success') is not True or not isinstance(data.get('result'), list):
                raise ValueError('DNS observation unavailable')
            records.extend(data['result'])
            if data.get('result_info', {}).get('total_pages', 100) <= page or len(data['result']) < 100:
                payload = json.dumps(sorted(records, key=lambda r:r['id']), sort_keys=True, separators=(',', ':'))
                return hashlib.sha256(payload.encode()).hexdigest()
        raise ValueError('DNS observation incomplete')
    original_dns = dns_digest()
    def domains():
        data = request(prefix + '/domains', token)
        if data.get('success') is not True or not isinstance(data.get('result'), list) or data.get('result_info', {}).get('total_pages', 1) > 1 or data.get('result_info', {}).get('total_count', 0) > len(data['result']):
            raise ValueError('Incomplete Worker domain observation')
        return sorted([{k: d.get(k) for k in ['id','hostname','service','environment']} for d in data['result']], key=lambda d:d['hostname'])
    before = domains()
    if not any(d['hostname'] == site['domain'] and d['service'] == site['worker'] and d['environment'] == 'production' for d in before):
        raise ValueError('Existing production binding missing; refuse creating a new deployment target')
    rollback = request(prefix + '/scripts/' + site['worker'] + '/deployments', token)
    if rollback.get('success') is not True or not rollback.get('result', {}).get('deployments'):
        raise ValueError('Rollback deployment metadata missing')
    versions = rollback['result']['deployments'][0]['versions']
    (output / 'rollback.json').write_text(json.dumps({'worker':site['worker'],'versions':versions}) + '\n')
    (output / 'before.json').write_text(json.dumps({'dns_sha256':original_dns,'custom_domains':before,'source':receipt['source']}) + '\n')
    config = deployment_config(site, receipt)
    (output / 'wrangler.json').write_text(json.dumps(config) + '\n')
    # Uses this repo's committed Wrangler dependency. No install/build receives the CF token.
    wrangler = owned(root, site.get('installDirectory', site['appDirectory'])) / 'node_modules/.bin/wrangler'
    current = request(site['origin'] + '/.well-known/release.json')
    if current.get('site') != site['id'] or current.get('purpose') != 'production':
        raise ValueError('Existing production is not this owned static site')
    already = current.get('source_sha') == receipt['source'] and current.get('version') == site['version']
    if not is_main and current.get('version') and not already and tuple(map(int, current['version'].split('.'))) >= tuple(map(int, site['version'].split('.'))):
        raise ValueError('Version already used or newer production exists; use explicit rollback procedure')
    if not already:
        if os.environ.get('GITHUB_EVENT_NAME') != ('workflow_run' if is_main else 'push') or os.environ.get('GITHUB_RUN_ATTEMPT') != '1':
            raise ValueError('Only initial tag push may deploy; later runs verify existing bytes only')
        if is_main:
            admit_main(root, contract, os.environ)
        # A fresh run is not evidence that an earlier deployment failed. Refuse
        # replay after a matching source/version; only verify those bytes above.
        wrangler = deployment_tool(root, site)
        (output / 'operation.json').write_text(json.dumps({'state':'deployment-starting; do not replay','site':site['id'],'source':receipt['source']}) + '\n')
        subprocess.run([str(wrangler), 'deploy', '--config', str(output / 'wrangler.json')], cwd=root, check=True)
    def readback_phase(phase):
        (output / 'operation.json').write_text(json.dumps({'state':'readback-pending; do not replay','phase':phase,'site':site['id'],'source':receipt['source'],'deployment_acknowledged':not already,'verify_only':already}) + '\n')
    def verify_provider_state(stage):
        readback_phase('bindings-and-dns')
        if before != domains():
            raise ValueError('Custom domain binding changed; do not replay deployment')
        if dns_digest() != original_dns:
            raise ValueError('DNS changed; do not replay deployment')
        exposure = request(prefix + '/scripts/' + site['worker'] + '/subdomain', token)
        if exposure.get('success') is not True or exposure['result'].get('enabled') is not False or exposure['result'].get('previews_enabled') is not False:
            raise ValueError('Unexpected workers.dev or preview exposure')
        # Provider preservation and public content are independent observations.
        # Keep the authenticated provider receipt even when edge challenges block CI.
        (output / 'provider-acceptance.json').write_text(json.dumps({
            'site':site['id'],'source':receipt['source'],'version':site['version'],
            'archive_sha256':expected,'dns_sha256':original_dns,'custom_domains':before,
            'dns_unchanged':True,'custom_domains_unchanged':True,
            'workers_dev_enabled':False,'preview_urls_enabled':False,
            'public_content_verified':False,'observation_stage':stage,'verify_only':already}) + '\n')
    verify_provider_state('before-public-readback')
    readback_phase('assets')
    public_files = {name: digest for name, digest in receipt['files'].items() if name not in ['_redirects', '_headers']}
    verify_assets(site['origin'], public_files, site.get('edgeScriptHashes', {}))
    verify_delivery(site['origin'], receipt)
    redirect_count = 0
    readback_phase('redirects')
    if '_redirects' in receipt['files']:
        redirect_count = verify_redirects(site['origin'], (output / 'verified/assets/_redirects').read_text())
    verify_provider_state('after-public-readback')
    (output / 'acceptance.json').write_text(json.dumps({'site':site['id'],'source':receipt['source'],'version':site['version'],
        'origin':site['origin'],'matched_assets':len(public_files),'matched_redirects':redirect_count,'archive_sha256':expected,'custom_domains_unchanged':True,
        'dns_unchanged':True,'workers_dev_enabled':False,'preview_urls_enabled':False,'verify_only':already,'markdown_routes_verified':len(receipt['worker']['routes']),'delivery_entry_sha256':receipt['worker']['sha256'],
        'edge_script_hashes':site.get('edgeScriptHashes', {})}) + '\n')
    (output / 'operation.json').write_text('{"state":"complete"}\n')


def main():
    root = Path.cwd()
    contract = read(root / '.github/site-release.json')
    mode = sys.argv[1]
    is_main = os.environ.get('SITE_RELEASE_MODE') == 'main'
    site = selected_site(root, contract, os.environ)
    if is_main:
        admit_main(root, contract, os.environ)
    if mode == 'plan':
        if not is_main:
            admit(root, contract, os.environ)
        for key, value in {'site':site['id'],'app':site['appDirectory'],'install':site.get('installDirectory', site['appDirectory']),'environment':site['environment'],'deploy-enabled':'true' if site.get('deploymentEnabled', True) else 'false'}.items():
            with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
                out.write(key + '=' + value + '\n')
    elif mode == 'pack':
        digest = pack(root, site, os.environ['SITE_RELEASE_SOURCE_SHA'] if is_main else os.environ['GITHUB_SHA'], Path(sys.argv[2]).resolve())
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            out.write('sha256=' + digest + '\n')
    elif mode == 'deploy':
        deploy(root, contract, site, Path(sys.argv[2]).resolve(), os.environ['EXPECTED_ARCHIVE_SHA256'])
    else:
        raise ValueError('Unknown release action')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Do not expose provider payloads, secrets or child output through exception text.
        print('Site release stopped; inspect job phase and retained receipts. Do not replay a deployment without read-back.', file=sys.stderr)
        sys.exit(1)

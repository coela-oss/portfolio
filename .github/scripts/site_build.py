"""Build exactly the selected owner contract site, never a shell-expanded input."""
import os
from pathlib import Path
import subprocess
import sys
from site_release import read, select

root = Path.cwd()
contract = read(root / '.github/site-release.json')
site = select(root, contract, os.environ['GITHUB_REF_NAME'])
if sys.argv[1:] != [site['id'], site['appDirectory']]:
    raise ValueError('Build selection differs from admitted contract')
app = root / site['appDirectory']
subprocess.run(['pnpm', 'install', '--frozen-lockfile', '--registry=https://registry.npmjs.org'], cwd=app, check=True)
if site['buildKind'] == 'organization':
    subprocess.run(['pnpm', 'validate:content'], cwd=app, check=True)
    subprocess.run(['pnpm', 'test'], cwd=app, check=True)
    subprocess.run(['pnpm', 'site', 'typecheck', site['id']], cwd=app, check=True)
    subprocess.run(['pnpm', 'site', 'build', site['id']], cwd=app, check=True)
else:
    scripts = read(app / 'package.json')['scripts']
    for script in ['validate:content', 'test']:
        if script in scripts:
            subprocess.run(['pnpm', script], cwd=app, check=True)
    subprocess.run(['pnpm', 'typecheck'], cwd=app, check=True)
    subprocess.run(['pnpm', 'exec', 'nuxt', 'generate'], cwd=app, check=True)

"""Credential-free observation preserves failures and excludes response cookies."""
import hashlib
import json
import os
from pathlib import Path
from subprocess import CompletedProcess
import tempfile
import unittest
from unittest.mock import patch
from site_release import pack
from site_observe import download, observe


class ObservationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'public').mkdir()
        (self.root / 'public/index.html').write_bytes(b'<html><body>Approved</body></html>')
        self.site = {'id':'example','version':'0.1.9','domain':'example.org','origin':'https://example.org','assetDirectory':'public'}
        self.output = self.root / 'observation'
        self.output.mkdir()
        digest = pack(self.root, self.site, 'a' * 40, self.output / 'input')
        from site_release import unpack
        unpack(self.output / 'input/site.tgz', digest, self.output / 'verified')
        (self.output / 'review.json').write_text(json.dumps({'source':'a' * 40,'archive_sha256':digest,'run':'123'}))

    def response(self, args, **kwargs):
        url = args[-1]
        name = url.removeprefix('https://example.org/') or 'index.html'
        data = (self.output / 'verified/assets' / name).read_bytes()
        Path(args[args.index('--output') + 1]).write_bytes(data)
        return CompletedProcess(args, 0, ('HTTP/2 200\r\nServer: cloudflare\r\nSet-Cookie: SECRET_FIXTURE\r\nETag: example\r\n\n__OBSERVATION__200 ' + url).encode())

    def test_exact_bytes_match_and_cookies_are_never_in_report(self):
        with patch('site_observe.subprocess.run', side_effect=self.response):
            self.assertEqual(observe(self.output), 0)
        report = (self.output / 'results/observations.json').read_text()
        self.assertNotIn('SECRET_FIXTURE', report)
        self.assertNotIn('set-cookie', report.lower())
        parsed = json.loads(report)
        self.assertEqual(parsed['matched'], 2)
        self.assertFalse(parsed['deploymentAttempted'])
        self.assertFalse(parsed['cloudflareCredentialsUsed'])

    def test_mismatched_public_html_is_recorded_without_success(self):
        def changed(args, **kwargs):
            result = self.response(args, **kwargs)
            if args[-1] == 'https://example.org/':
                Path(args[args.index('--output') + 1]).write_bytes(b'<html><body>Changed</body></html>')
            return result
        with patch('site_observe.subprocess.run', side_effect=changed):
            self.assertEqual(observe(self.output), 2)
        report = json.loads((self.output / 'results/observations.json').read_text())
        self.assertEqual(report['matched'], 1)
        bad = next(row for row in report['files'] if row['path'] == 'index.html')
        self.assertEqual(bad['error'], 'asset_digest_mismatch')
        self.assertEqual(len(list((self.output / 'results').glob('*.html.txt'))), 1)

    def test_changed_archive_stops_before_any_public_request(self):
        (self.output / 'input/site.tgz').write_bytes(b'not the reviewed archive')
        with patch('site_observe.subprocess.run') as run:
            with self.assertRaises(ValueError):
                observe(self.output)
            run.assert_not_called()

    def test_invalid_review_identifiers_stop_before_github_or_download(self):
        with patch.dict(os.environ, {'SITE_RELEASE_RUN_ID':'../123','SITE_ARCHIVE_SHA256':'b' * 64}), patch('site_observe.request') as request, patch('site_observe.subprocess.run') as run:
            with self.assertRaises(ValueError):
                download(self.root, self.root / 'new')
            request.assert_not_called()
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()

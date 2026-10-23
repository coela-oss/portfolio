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
from site_observe import download, observe, summary


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
        with patch.dict(os.environ, {'SITE_RELEASE_RUN_ID':'../123','SITE_ARCHIVE_SHA256':'b' * 64}), patch('site_observe.subprocess.run') as run:
            with self.assertRaises(ValueError):
                download(self.root, self.root / 'new')
            run.assert_not_called()

    def test_challenge_is_blocked_not_a_successful_content_check(self):
        def challenged(args, **kwargs):
            result = self.response(args, **kwargs)
            result.stdout = result.stdout.replace(b'HTTP/2 200', b'HTTP/2 403\r\nCf-Mitigated: challenge').replace(b'__OBSERVATION__200', b'__OBSERVATION__403')
            return result
        with patch('site_observe.subprocess.run', side_effect=challenged):
            self.assertEqual(observe(self.output), 2)
        report = json.loads((self.output / 'results/observations.json').read_text())
        self.assertEqual(report['state'], 'public_observation_blocked')
        self.assertEqual(report['blockedResponses'], 2)
        self.assertEqual(report['matched'], 0)
        self.assertTrue(all(row['error'] == 'cloudflare_challenge' for row in report['files']))

    def test_summary_labels_local_evidence_separately_and_excludes_stale_source(self):
        with patch('site_observe.subprocess.run', side_effect=self.response):
            observe(self.output)
        operator = self.root / 'docs/operations/current-production-verification.json'
        operator.parent.mkdir(parents=True)
        review = json.loads((self.output / 'review.json').read_text())
        evidence = {'source':review['source'],'archiveSha256':review['archive_sha256'],'verificationContext':'local-public-read-only','publicAssetsVerified':2,'redirectsVerified':1}
        operator.write_text(json.dumps(evidence))
        destination = self.root / 'summary.txt'
        with patch.dict(os.environ, {'GITHUB_STEP_SUMMARY':str(destination)}):
            summary(self.root, self.output)
        self.assertIn('Separate operator evidence', destination.read_text())
        self.assertIn('explicitly separate from hosted CI', destination.read_text())
        evidence['source'] = 'b' * 40
        operator.write_text(json.dumps(evidence))
        destination.write_text('')
        with patch.dict(os.environ, {'GITHUB_STEP_SUMMARY':str(destination)}):
            summary(self.root, self.output)
        self.assertNotIn('Separate operator evidence', destination.read_text())


if __name__ == '__main__':
    unittest.main()

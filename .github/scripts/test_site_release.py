import copy
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from site_release import select, pack, unpack, admit, deploy, verify_assets, deployment_tool
from subprocess import CompletedProcess


class SiteReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'site.json').write_text('{"origin":"https://example.org"}')
        self.site = {'id':'example','version':'0.1.0','account':'a'*32,'zone':'c'*32,'worker':'example-site',
            'environment':'site-production-example','origin':'https://example.org','domain':'example.org',
            'siteConfig':'site.json','appDirectory':'.','assetDirectory':'public','buildKind':'single'}
        self.contract = {'schemaVersion':1,'repository':'example/site','defaultBranch':'main',
                         'requiredWorkflows':['ci.yml'],'sites':[self.site]}
        self.env = {'GITHUB_SHA':'b'*40,'GITHUB_REPOSITORY':'example/site','GITHUB_REF_TYPE':'tag'}

    def test_exact_site_version_and_owned_origin(self):
        self.assertEqual(select(self.root,self.contract,'site/example/v0.1.0'),self.site)
        for tag in ['v0.1.0','site/other/v0.1.0','site/example/v0.2.0']:
            with self.assertRaises(ValueError): select(self.root,self.contract,tag)
        (self.root / 'site.json').write_text('{"origin":"https://other.example"}')
        with self.assertRaises(ValueError):select(self.root,self.contract,'site/example/v0.1.0')

    def test_subdomain_requires_explicit_parent_zone_on_a_label_boundary(self):
        site = self.contract['sites'][0]
        site.update(domain='product.example.org', origin='https://product.example.org', zoneName='example.org')
        (self.root/'site.json').write_text('{"origin":"https://product.example.org"}')
        self.assertEqual(select(self.root,self.contract,'site/example/v0.1.0'),site)
        for zone in ['ample.org', 'other.org', 'example.org/path', '.example.org', 'org.evil']:
            site['zoneName'] = zone
            with self.assertRaises(ValueError):select(self.root,self.contract,'site/example/v0.1.0')

    def test_shared_install_root_is_explicit_and_cannot_escape_the_owner(self):
        site = self.contract['sites'][0]
        site.update(appDirectory='products/example', installDirectory='.')
        self.assertEqual(select(self.root,self.contract,'site/example/v0.1.0'),site)
        for directory in ['../sibling', 'unrelated', './\nother=bad']:
            site['installDirectory'] = directory
            with self.assertRaises(ValueError):select(self.root,self.contract,'site/example/v0.1.0')

    def test_new_product_targets_remain_explicitly_disabled(self):
        self.contract['sites'][0]['deploymentEnabled'] = False
        self.assertFalse(select(self.root,self.contract,'site/example/v0.1.0')['deploymentEnabled'])
        self.contract['sites'][0]['deploymentEnabled'] = 'false'
        with self.assertRaises(ValueError):select(self.root,self.contract,'site/example/v0.1.0')

    def test_output_traversal_symlink_and_environment_output_injection_rejected(self):
        for key,value in [('assetDirectory','../public'),('appDirectory','./\nother=bad'),('environment','site-production-x\nother=bad')]:
            contract=copy.deepcopy(self.contract);contract['sites'][0][key]=value
            with self.assertRaises(ValueError):select(self.root,contract,'site/example/v0.1.0')
        (self.root/'public').mkdir();(self.root/'public/index.html').symlink_to(self.root/'site.json')
        with self.assertRaises(ValueError):pack(self.root,self.site,'b'*40,self.root/'archive')

    def prepare(self):
        (self.root/'public').mkdir();(self.root/'public/index.html').write_text('<h1>Approved</h1>')
        digest=pack(self.root,self.site,'b'*40,self.root/'archive')
        return self.root/'archive/site.tgz',digest

    def test_archive_binds_all_asset_bytes_to_immutable_source_and_target(self):
        archive,digest=self.prepare();receipt=unpack(archive,digest,self.root/'verified')
        self.assertEqual(receipt['source'],'b'*40);self.assertEqual(receipt['site'],self.site)
        self.assertIn('.well-known/release.json',receipt['files'])
        with self.assertRaises(ValueError):unpack(archive,'c'*64,self.root/'bad')
        with self.assertRaises(ValueError):unpack(archive,digest,self.root/'verified')

    def test_archive_links_and_traversal_rejected_before_extraction(self):
        for name in ['../outside','assets/../../outside','/outside']:
            archive=self.root/'bad.tgz'
            with tarfile.open(archive,'w:gz') as out:
                info=tarfile.TarInfo(name);info.size=1;out.addfile(info,io.BytesIO(b'x'))
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):unpack(archive,digest,self.root/'never-created')
            self.assertFalse((self.root/'never-created').exists())

    def test_source_admission_rejects_foreign_owner_before_git_or_network(self):
        with patch('site_release.subprocess.run') as run,patch('site_release.request') as request:
            with self.assertRaises(ValueError):admit(self.root,self.contract,{**self.env,'GITHUB_REPOSITORY':'fork/site'})
            run.assert_not_called();request.assert_not_called()

    def test_unprotected_environment_cannot_reach_cloudflare_or_deployment(self):
        _,digest=self.prepare()
        with patch.dict('os.environ',{**self.env,'GH_TOKEN':'synthetic-test-token'}),patch('site_release.request',return_value={'protection_rules':[]}) as request,patch('site_release.subprocess.run') as run:
            with self.assertRaises(ValueError):deploy(self.root,self.contract,self.site,self.root/'archive',digest)
            self.assertEqual(request.call_count,1);run.assert_not_called()

    def provider(self, already):
        def response(url, token=None):
            if '/environments/' in url:
                return {'protection_rules':[{'type':'required_reviewers','reviewers':[{'id':1}]}]}
            if url.endswith('/zones/'+'c'*32):
                return {'success':True,'result':{'name':'example.org','account':{'id':'a'*32},'status':'active'}}
            if '/dns_records?' in url:
                return {'success':True,'result':[],'result_info':{'total_pages':1}}
            if url.endswith('/domains'):
                return {'success':True,'result':[{'id':'domain','hostname':'example.org','service':'example-site','environment':'production'}]}
            if url.endswith('/deployments'):
                return {'success':True,'result':{'deployments':[{'versions':[{'version_id':'version','percentage':100}]}]}}
            if url.endswith('/subdomain'):
                return {'success':True,'result':{'enabled':False,'previews_enabled':False}}
            if url=='https://example.org/.well-known/release.json':
                return {'site':'example','purpose':'production','source_sha':'b'*40 if already else 'a'*40,**({'version':'0.1.0'} if already else {})}
            raise AssertionError('Unexpected API: '+url)
        return response

    def test_rerun_with_old_remote_marker_cannot_repeat_unknown_deployment(self):
        _,digest=self.prepare()
        env={**self.env,'GH_TOKEN':'synthetic-test-token','CLOUDFLARE_API_TOKEN':'synthetic-fixture-token','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ATTEMPT':'2'}
        with patch.dict('os.environ',env),patch('site_release.request',side_effect=self.provider(False)),patch('site_release.subprocess.run') as run:
            with self.assertRaises(ValueError):deploy(self.root,self.contract,self.site,self.root/'archive',digest)
            run.assert_not_called()

    def test_matching_production_is_verified_without_redeployment_on_manual_recovery(self):
        _,digest=self.prepare()
        env={**self.env,'GH_TOKEN':'synthetic-test-token','CLOUDFLARE_API_TOKEN':'synthetic-fixture-token','GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_RUN_ATTEMPT':'2'}
        with patch.dict('os.environ',env),patch('site_release.request',side_effect=self.provider(True)),patch('site_release.verify_assets') as verify,patch('site_release.subprocess.run') as run:
            deploy(self.root,self.contract,self.site,self.root/'archive',digest)
            verify.assert_called_once();run.assert_not_called()
        self.assertTrue(json.loads((self.root/'archive/acceptance.json').read_text())['verify_only'])

    def test_malformed_redirect_cannot_be_packaged_or_reach_a_deployment(self):
        (self.root/'public').mkdir()
        (self.root/'public/_redirects').write_text('/unsafe //other.example 301\n')
        with self.assertRaises(ValueError):
            pack(self.root,self.site,'b'*40,self.root/'archive')
        self.assertFalse((self.root/'archive').exists())

    def test_readback_failure_keeps_dns_baseline_and_phase_without_redeployment(self):
        _,digest=self.prepare()
        env={**self.env,'GH_TOKEN':'synthetic-test-token','CLOUDFLARE_API_TOKEN':'synthetic-fixture-token','GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_RUN_ATTEMPT':'2'}
        with patch.dict('os.environ',env),patch('site_release.request',side_effect=self.provider(True)),patch('site_release.verify_assets',side_effect=ValueError('fixture mismatch')),patch('site_release.subprocess.run') as run:
            with self.assertRaises(ValueError):deploy(self.root,self.contract,self.site,self.root/'archive',digest)
            run.assert_not_called()
        before=json.loads((self.root/'archive/before.json').read_text())
        self.assertRegex(before['dns_sha256'],r'^[a-f0-9]{64}$')
        self.assertEqual(before['custom_domains'][0]['service'],'example-site')
        operation=json.loads((self.root/'archive/operation.json').read_text())
        self.assertEqual(operation['phase'],'assets')
        self.assertTrue(operation['verify_only'])
        self.assertFalse(operation['deployment_acknowledged'])
        provider=json.loads((self.root/'archive/provider-acceptance.json').read_text())
        self.assertTrue(provider['dns_unchanged'])
        self.assertTrue(provider['custom_domains_unchanged'])
        self.assertFalse(provider['workers_dev_enabled'])
        self.assertFalse(provider['preview_urls_enabled'])
        self.assertFalse(provider['public_content_verified'])
        self.assertEqual(provider['dns_sha256'], before['dns_sha256'])
        self.assertEqual(provider['custom_domains'], before['custom_domains'])
        self.assertFalse((self.root/'archive/acceptance.json').exists())


    def test_provider_drift_or_unobserved_exposure_cannot_create_success_evidence(self):
        for failure in ['dns', 'binding', 'exposure', 'exposure-unobserved']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                output=Path(temporary)/'output'
                (self.root/'public').mkdir(exist_ok=True)
                (self.root/'public/index.html').write_text('<h1>Approved</h1>')
                digest=pack(self.root,self.site,'b'*40,output)
                counts={'dns':0,'binding':0}
                base=self.provider(True)
                def response(url,token=None):
                    result=base(url,token)
                    kind='dns' if '/dns_records?' in url else 'binding' if url.endswith('/domains') else None
                    if kind:
                        counts[kind]+=1
                        if failure==kind and counts[kind]==2:
                            result['result']=[{'id':'changed'}]
                    if url.endswith('/subdomain'):
                        if failure=='exposure':result['result']['enabled']=True
                        if failure=='exposure-unobserved':raise ValueError('fixture unobserved')
                    return result
                env={**self.env,'GH_TOKEN':'synthetic-test-token','CLOUDFLARE_API_TOKEN':'synthetic-fixture-token',
                     'GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_RUN_ATTEMPT':'2'}
                with patch.dict('os.environ',env),patch('site_release.request',side_effect=response),patch('site_release.verify_assets') as assets,patch('site_release.subprocess.run') as run:
                    with self.assertRaises(ValueError):deploy(self.root,self.contract,self.site,output,digest)
                    assets.assert_not_called();run.assert_not_called()
                self.assertFalse((output/'provider-acceptance.json').exists())
                self.assertFalse((output/'acceptance.json').exists())

    def test_redirect_control_file_is_artifact_bound_and_verified_as_behavior(self):
        (self.root/'public').mkdir()
        (self.root/'public/index.html').write_text('<h1>Approved</h1>')
        (self.root/'public/_redirects').write_text('/old /work 301\n')
        digest=pack(self.root,self.site,'b'*40,self.root/'archive')
        env={**self.env,'GH_TOKEN':'synthetic-test-token','CLOUDFLARE_API_TOKEN':'synthetic-fixture-token','GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_RUN_ATTEMPT':'2'}
        with patch.dict('os.environ',env),patch('site_release.request',side_effect=self.provider(True)),patch('site_release.verify_assets') as verify,patch('site_release.verify_redirects',return_value=1) as redirects,patch('site_release.subprocess.run') as run:
            deploy(self.root,self.contract,self.site,self.root/'archive',digest)
            self.assertNotIn('_redirects', verify.call_args.args[1])
            redirects.assert_called_once_with('https://example.org','/old /work 301\n')
            run.assert_not_called()
        receipt=json.loads((self.root/'archive/acceptance.json').read_text())
        self.assertEqual(receipt['matched_redirects'],1)
        self.assertEqual(receipt['matched_assets'],2)

    def test_deployment_tool_must_be_pinned_locked_and_executable(self):
        (self.root/'package.json').write_text('{"devDependencies":{"wrangler":"4.149.0"}}')
        with self.assertRaises(ValueError):deployment_tool(self.root,self.site)
        (self.root/'pnpm-lock.yaml').write_text('lockfileVersion: 9.0')
        binary=self.root/'node_modules/.bin/wrangler';binary.parent.mkdir(parents=True)
        binary.write_text('#!/bin/sh\nexit 0\n')
        with self.assertRaises(ValueError):deployment_tool(self.root,self.site)
        binary.chmod(0o700)
        self.assertEqual(deployment_tool(self.root,self.site),binary)
        (self.root/'package.json').write_text('{"devDependencies":{"wrangler":"latest"}}')
        with self.assertRaises(ValueError):deployment_tool(self.root,self.site)

    def test_missing_tool_stops_before_operation_record_or_subprocess(self):
        _,digest=self.prepare()
        (self.root/'package.json').write_text('{"devDependencies":{}}')
        env={**self.env,'GH_TOKEN':'synthetic-test-token','CLOUDFLARE_API_TOKEN':'synthetic-fixture-token','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ATTEMPT':'1'}
        with patch.dict('os.environ',env),patch('site_release.request',side_effect=self.provider(False)),patch('site_release.subprocess.run') as run:
            with self.assertRaises(ValueError):deploy(self.root,self.contract,self.site,self.root/'archive',digest)
            run.assert_not_called()
        self.assertFalse((self.root/'archive/operation.json').exists())

    def test_asset_readback_accepts_only_prepared_bytes_after_bounded_stale_reads(self):
        expected={'404.html':hashlib.sha256(b'approved fallback').hexdigest()}
        responses=[CompletedProcess([],0,b'stale page'),CompletedProcess([],0,b'approved fallback')]
        with patch('site_release.subprocess.run',side_effect=responses) as run,patch('site_release.time.sleep'):
            verify_assets('https://example.org',expected)
            self.assertEqual(run.call_count,2)
        with patch('site_release.subprocess.run',return_value=CompletedProcess([],0,b'wrong bytes')) as run,patch('site_release.time.sleep'):
            with self.assertRaises(ValueError):verify_assets('https://example.org',expected)
            self.assertEqual(run.call_count,5)


if __name__ == '__main__':
    # The same tests also validate the real owner contract after copying into a repo.
    contract_path = Path('.github/site-release.json')
    if contract_path.exists():
        contract = json.loads(contract_path.read_text())
        for site in contract['sites']:
            select(Path.cwd(), contract, f"site/{site['id']}/v{site['version']}")
    unittest.main()

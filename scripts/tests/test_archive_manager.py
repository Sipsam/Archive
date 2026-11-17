import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('manager',Path(__file__).parents[1]/'archive_manager.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.base=Path(self.tmp.name)
        self.root=self.base/'repo'; self.root.mkdir()
        self.g('init','-b','main'); self.g('config','user.name','Test'); self.g('config','user.email','test@localhost')
        (self.root/'Project').mkdir(); self.commit('Project/file.txt','base')
        self.first=m.oid(self.root,'HEAD')
        self.remote=self.base/'remote.git'; self.g('init','--bare',str(self.remote))
        self.g('remote','add','origin',str(self.remote)); self.g('push','origin','main'); self.g('fetch','origin')
    def tearDown(self): self.tmp.cleanup()
    def g(self,*args): return m.run(list(args),self.root)
    def commit(self,path,content):
        (self.root/path).write_text(content,encoding='utf-8'); self.g('add','.'); self.g('commit','-m','test')
        return m.oid(self.root,'HEAD')
    def state(self,name='main'): return next(r for r in m.inventory(self.root) if r['branch']==name)
    def test_equal_ahead_behind_diverged_and_unrelated(self):
        self.assertEqual(self.state()['state'],'UP_TO_DATE')
        second=self.commit('Project/file.txt','second'); self.assertEqual(self.state()['ahead'],1)
        self.g('update-ref','refs/remotes/origin/main',second); self.g('reset','--hard',self.first)
        self.assertEqual(self.state()['state'],'FAST_FORWARD')
        self.commit('Project/file.txt','different'); self.assertEqual(self.state()['state'],'DIVERGED')
        other=self.g('commit-tree',self.g('rev-parse','HEAD^{tree}'),'-m','unrelated')
        self.g('update-ref','refs/remotes/origin/main',other)
        self.assertIsNone(self.state()['mergeBase'])
    def test_remote_only_sync_rerun_and_local_only(self):
        self.g('push','origin','main:remote-only'); self.g('fetch','origin')
        self.assertEqual(self.state('remote-only')['state'],'REMOTE_ONLY')
        before=m.refs(self.root); m.sync(self.root,None,True); self.assertEqual(before,m.refs(self.root))
        m.sync(self.root,None,False); m.sync(self.root,None,False)
        self.assertEqual(self.state('remote-only')['state'],'UP_TO_DATE')
        self.g('branch','local-only'); self.assertEqual(self.state('local-only')['state'],'LOCAL_ONLY')
    def test_security_blocks_and_hides_value(self):
        fake='SG.'+'a'*22+'.'+'b'*43
        self.commit('Project/key.txt',fake)
        result=m.push(self.root,'main',True)
        self.assertEqual(result['state'],'SECURITY_BLOCKED'); self.assertNotIn(fake,str(result))
        self.assertEqual(m.live(self.root)['main'],self.first)
    def test_network_error_and_retry(self):
        self.commit('Project/file.txt','second'); self.g('remote','set-url','origin',str(self.base/'absent'))
        with self.assertRaises(m.Failure): m.push(self.root,'main',False)
        self.g('remote','set-url','origin',str(self.remote)); self.assertTrue(m.push(self.root,'main',False)['pushed'])
    def test_stale_remote_rejected(self):
        self.g('branch','old',self.first); self.g('push','origin','old')
        self.g('fetch','origin'); second=self.commit('Project/file.txt','second')
        self.g('push','origin',second+':refs/heads/old')
        with self.assertRaises(m.Failure): m.push(self.root,'old',True)
    def test_korean_extract_without_source_and_whatif(self):
        self.commit('Project/한글.txt','내용'); self.g('branch','Project/한글')
        before=m.refs(self.root); dest=self.base/'restored'
        m.extract(self.root,'Project','Project/한글',str(dest),True); self.assertFalse(dest.exists())
        m.extract(self.root,'Project','Project/한글',str(dest),False)
        self.assertEqual((dest/'Project/한글.txt').read_text(encoding='utf-8'),'내용')
        self.assertEqual(before,m.refs(self.root))
        with self.assertRaises(m.Failure): m.extract(self.root,'Project','main',str(dest),False)
    def test_backup_restore_preserves_objects(self):
        result=m.backup(self.root,str(self.base/'backup')); self.assertTrue(result['bundleVerified'])
        self.g('clone','--mirror',str(self.base/'backup/archive.bundle'),str(self.base/'restored.git'))
        self.assertEqual(m.oid(self.base/'restored.git','main'),self.first)
    def test_lfs_missing_and_snapshot_preserved(self):
        pointer='version https://git-lfs.github.com/spec/v1\noid sha256:'+'a'*64+'\nsize 10\n'
        self.commit('Project/model.bin',pointer); before=m.oid(self.root,'HEAD')
        result=m.validate(self.root); self.assertEqual(len(result['missingLfs']),1)
        self.assertEqual(before,m.oid(self.root,'HEAD'))
    def test_duplicate_add_and_dry_run(self):
        before=m.refs(self.root)
        with self.assertRaises(m.Failure): m.add(self.root,'Project',{'':str(self.base/'absent')},False)
        m.add(self.root,'New',{'':str(self.base/'absent')},True)
        self.assertEqual(before,m.refs(self.root))
    def test_add_stages_history_without_live_mutation(self):
        source=self.base/'source'; self.g('clone',str(self.root),str(source))
        before=m.refs(self.root)
        result=m.add(self.root,'New',{'':str(source)},False)
        try:
            self.assertEqual(result['state'],'REVIEW_REQUIRED'); self.assertEqual(before,m.refs(self.root))
            candidate=Path(result['candidate']); self.assertTrue(m.ancestor(candidate,self.first,m.oid(candidate,'New/main')))
        finally:
            import shutil
            import os, stat
            target=Path(result['candidate']).parent.resolve()
            self.assertEqual(target.parent,Path(tempfile.gettempdir()).resolve())
            self.assertTrue(target.name.startswith('archive-add-'))
            def retry(func,path,exc):
                os.chmod(path,stat.S_IWRITE); func(path)
            shutil.rmtree(target,onexc=retry)

    def test_known_lfs_and_new_missing(self):
        import json
        oid='a'*64
        self.commit('Project/known.bin','version https://git-lfs.github.com/spec/v1\noid sha256:'+oid+'\nsize 1\n')
        (self.root/'docs').mkdir()
        self.commit('docs/archive-lfs-known-missing.json',json.dumps({'oids':[oid]}))
        self.commit('Project/new.bin','version https://git-lfs.github.com/spec/v1\noid sha256:'+'b'*64+'\nsize 1\n')
        states={p['state'] for p in m.validate(self.root)['missingLfs']}
        self.assertEqual(states,{'KNOWN_MISSING','UNEXPECTED_MISSING'})

    def test_promote_stale_and_security(self):
        import json
        source=self.base/'source'; self.g('clone',str(self.root),str(source))
        result=m.add(self.root,'New',{'':str(source)},False); candidate=Path(result['candidate'])
        before=m.refs(self.root)
        self.assertEqual(m.promote(self.root,candidate,True)['state'],'REVIEW_REQUIRED')
        self.assertEqual(before,m.refs(self.root))
        self.g('branch','new-ref')
        with self.assertRaises(m.Failure):m.promote(self.root,candidate,False)
        self.g('branch','-d','new-ref')
        manifest_path=candidate.parent/'manifest.json'; manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        fake='SG.'+'a'*22+'.'+'b'*43
        (candidate/'New/key').write_text(fake,encoding='utf-8')
        m.run(['switch','main'],candidate);m.run(['add','.'],candidate);m.run(['commit','-m','test'],candidate)
        manifest['targets']['refs/heads/main']=m.oid(candidate,'main');manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
        with self.assertRaises(m.Failure):m.promote(self.root,candidate,True)
        self.assertEqual(before,m.refs(self.root))

    def test_add_promote_update_history(self):
        source=self.base/'source';self.g('clone',str(self.root),str(source))
        result=m.add(self.root,'New',{'':str(source)},False)
        candidate=Path(result['candidate'])
        promoted=m.promote(self.root,candidate,False)
        self.assertEqual(promoted['state'],'PROMOTED')
        self.assertEqual((self.root/'New/Project/file.txt').read_text(),'base')
        self.g('add','docs/archive-projects.json');self.g('commit','-m','register source')
        old=m.oid(self.root,'New/main')
        m.run(['config','user.name','Test'],source);m.run(['config','user.email','test@localhost'],source)
        (source/'Project/file.txt').write_text('new source',encoding='utf-8');m.run(['add','.'],source);m.run(['commit','-m','source change'],source)
        candidate2=Path(m.update(self.root,'New',False)['candidate'])
        self.assertTrue(m.ancestor(candidate2,old,m.oid(candidate2,'New/main')))
        m.promote(self.root,candidate2,False)
        self.assertEqual((self.root/'New/Project/file.txt').read_text(),'new source')
        self.assertEqual((self.root/'Project/file.txt').read_text(),'base')

    def test_source_unavailable_and_backup_excluded(self):
        self.assertEqual(m.update(self.root,'Project',True)['state'],'SOURCE_UNAVAILABLE')
        for branch in ['backup/x','Project/backup/old','security/fix']:
            self.assertTrue(m.excluded(branch));self.g('branch',branch)
            with self.assertRaises(m.Failure):m.push(self.root,branch,True)

    def test_security_cache_invalidated_by_commit(self):
        first=m.cached_security(self.root,self.first,True);self.assertTrue(first['clean'])
        fake='SG.'+'a'*22+'.'+'b'*43;new=self.commit('Project/key',fake)
        self.assertFalse(m.cached_security(self.root,new,False)['clean'])
        self.assertTrue(m.cached_security(self.root,self.first,False)['clean'])

    def test_push_protection_rejection_and_retry(self):
        hook=self.remote/'hooks/pre-receive'
        hook.write_text('#!/bin/sh\necho GH013 >&2\nexit 1\n',encoding='utf-8')
        self.commit('Project/file.txt','new')
        with self.assertRaises(m.Failure):m.push(self.root,'main',False)
        self.assertEqual(m.live(self.root)['main'],self.first)
        hook.unlink();self.assertTrue(m.push(self.root,'main',False)['pushed'])


    def test_powershell51_whatif_commands_preserve_state(self):
        import shutil
        shell=shutil.which('powershell')
        if not shell:self.skipTest('Windows PowerShell unavailable')
        wrapper=Path(__file__).parents[1]/'archive-manager.ps1'
        source=self.base/'source';self.g('clone',str(self.root),str(source))
        candidate=Path(m.add(self.root,'New',{'':str(source)},False)['candidate'])
        backup=m.backup(self.root,str(self.base/'saved'))
        self.commit('Project/file.txt','ahead')
        # Candidate is stale after this commit; regenerate so promote WhatIf verifies successfully.
        candidate=Path(m.add(self.root,'New',{'':str(source)},False)['candidate'])
        before=m.refs(self.root);remote=m.live(self.root)
        options=[('status',[]),('fetch',[]),('plan',[]),('sync',[]),('security',[]),('validate',[]),('push',['-Branch','main']),('backup',['-Destination',str(self.base/'never-backup')]),('restore',['-Bundle',str(self.base/'saved/archive.bundle'),'-Destination',str(self.base/'never-restore')]),('extract',['-Project','Project','-Branch','main','-Destination',str(self.base/'never-extract')]),('add',['-Project','Other','-SourceRepo',str(source)]),('promote',['-Candidate',str(candidate),'-Approve']),('update',['-Project','Project']),('verify-branches',[]),('push-safe',[])]
        for command,args in options:
            proc=subprocess.run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(wrapper.resolve()),command,'-Repository',str(self.root),'-WhatIf',*args],capture_output=True)
            self.assertEqual(proc.returncode,0,command)
        self.assertEqual(before,m.refs(self.root));self.assertEqual(remote,m.live(self.root))
        for name in ['never-backup','never-restore','never-extract']:self.assertFalse((self.base/name).exists())


if __name__=='__main__': unittest.main(verbosity=2)

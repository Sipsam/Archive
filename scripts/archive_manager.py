"""Conservative Archive administration. Python 3.9+; no external packages.
Git content and stderr never go to the console. Reports contain metadata only.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


class Failure(Exception):
    pass


def run(args, cwd, data=None, ok=(0,)):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1')
    p = subprocess.run(['git', '-c', 'core.quotepath=false', *args], cwd=cwd,
                       input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if p.returncode not in ok:
        raise Failure('Git operation failed: ' + args[0] + ' (exit ' + str(p.returncode) + '; raw output withheld)')
    return p.stdout.decode('utf-8', 'strict').strip()


def refs(root):
    out = run(['for-each-ref', '--format=%(refname) %(objectname)'], root)
    return dict(line.split(' ', 1) for line in out.splitlines())


def oid(root, ref):
    return run(['rev-parse', '--verify', ref + '^{commit}'], root)


def ancestor(root, a, b):
    p = subprocess.run(['git', 'merge-base', '--is-ancestor', a, b], cwd=root, capture_output=True)
    if p.returncode not in (0, 1):
        raise Failure('merge-base failed')
    return p.returncode == 0


def excluded(name):
    return name.startswith('security/') or 'backup' in name.split('/')


def inventory(root):
    rr = refs(root)
    local = {k[11:]: v for k, v in rr.items() if k.startswith('refs/heads/')}
    remote = {k[20:]: v for k, v in rr.items() if k.startswith('refs/remotes/origin/') and k != 'refs/remotes/origin/HEAD'}
    rows = []
    for name in sorted(local.keys() | remote.keys()):
        a, b = local.get(name), remote.get(name)
        ahead = behind = 0
        base = None
        if a and b:
            ahead, behind = map(int, run(['rev-list', '--left-right', '--count', a+'...'+b], root).split())
            base = run(['merge-base', a, b], root, ok=(0, 1)) or None
            state = 'UP_TO_DATE' if a == b else 'DIVERGED' if ahead and behind else 'LOCAL_AHEAD' if ahead else 'FAST_FORWARD'
        else:
            state = 'LOCAL_ONLY' if a else 'REMOTE_ONLY'
        rows.append(dict(project=name.split('/')[0] if '/' in name else '(root)', branch=name,
                         local=a, remote=b, ahead=ahead, behind=behind, mergeBase=base,
                         state=state, diverged=state=='DIVERGED', security='REQUIRED',
                         latest=run(['show','-s','--format=%H %cs', a or b], root),
                         risk='MANUAL_REVIEW' if state=='DIVERGED' or excluded(name) else state,
                         recommendation='review snapshots and security; never automatic merge' if state=='DIVERGED' else 'scan before push' if state in ('LOCAL_AHEAD','LOCAL_ONLY') else state))
    return rows


# Deliberately no matching text, value hashes or source lines in findings.
RULES = [
    ('SendGrid', rb'SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}'),
    ('GitHub token', rb'(?:gh[pousr]_[A-Za-z0-9]{30,255}|github_pat_[A-Za-z0-9_]{30,255})'),
    ('AWS access ID', rb'(?:AKIA|ASIA)[A-Z0-9]{16}'),
    ('Private key', rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    ('JWT', rb'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'),
    ('Credential assignment (review)', rb'''(?im)(?:password|passwd|secret|api[_-]?key|access[_-]?token|jwt[_-]?secret|aws_secret_access_key)\s*[=:]\s*["']?[^\s"'${}<>;]{8,}'''),
    ('Credential URL (review)', rb'[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/:]+:[^\s/@]{4,}@'),
]


_OBJECT_SCAN_CACHE = {}

def security(root, revisions=None):
    args = revisions or ['--all', '--reflog']
    listing = run(['rev-list', '--objects', *args], root)
    objects = dict((line.split(' ', 1)+[''])[:2] for line in listing.splitlines())
    proc = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    hits, pointers = [], []
    try:
        for obj, path in objects.items():
            if obj in _OBJECT_SCAN_CACHE:
                cached_hits,cached_pointers=_OBJECT_SCAN_CACHE[obj]
                hits.extend(dict(h,path=path) for h in cached_hits)
                pointers.extend(dict(p,path=path) for p in cached_pointers)
                continue
            hit_start,pointer_start=len(hits),len(pointers)
            proc.stdin.write((obj+'\n').encode()); proc.stdin.flush()
            header = proc.stdout.readline().split()
            if len(header) != 3:
                raise Failure('Missing Git object during security scan')
            size = int(header[2])
            content = proc.stdout.read(size)
            if len(content) != size or proc.stdout.read(1) != b'\n':
                raise Failure('Incomplete object read')
            # Scan commits, tags and blobs, including binary blobs; tree entries have no credential values.
            if header[1] not in (b'blob', b'commit', b'tag'):
                continue
            if content.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
                m = re.search(rb'oid sha256:([0-9a-f]{64})', content)
                if m:
                    pointers.append(dict(blob=obj, path=path, oid=m[1].decode()))
            for kind, pattern in RULES:
                for match in re.finditer(pattern, content):
                    hits.append(dict(type=kind, object=obj, objectType=header[1].decode(), path=path,
                                     line=content[:match.start()].count(b'\n')+1,
                                     severity='HIGH' if '(review)' not in kind else 'REVIEW',
                                     classification='candidate; validity and revocation unverified'))
            _OBJECT_SCAN_CACHE[obj]=([dict(h) for h in hits[hit_start:]],[dict(p) for p in pointers[pointer_start:]])
    finally:
        proc.stdin.close(); proc.stdout.close(); proc.wait()
    if proc.returncode:
        raise Failure('cat-file scan failed')
    if revisions is None:
        hit_objects={h['object'] for h in hits}
        affected=collections.defaultdict(list)
        for ref,commit in refs(root).items():
            reachable={line.split(' ',1)[0] for line in run(['rev-list','--objects',commit],root).splitlines()}
            for obj in hit_objects & reachable: affected[obj].append(ref)
        changes=collections.defaultdict(set)
        current=None
        for line in run(['log','--all','--reflog','--raw','--no-abbrev','--format=COMMIT:%H','-m'],root).splitlines():
            if line.startswith('COMMIT:'): current=line[7:]
            elif line.startswith(':') and not line.startswith('::'):
                fields=line.split('\t',1)[0].split()
                for obj in fields[2:4]:
                    if obj in hit_objects: changes[obj].add(current)
        for hit in hits:
            hit['affectedRefs']=affected[hit['object']]
            hit['changeCommits']=sorted(changes[hit['object']])
    return dict(scanner='archive-regex-v2 (HIGH blocks; broad REVIEW diagnostics do not; limited rules)',
                scope=args, objects=len(objects), findings=hits, lfsPointers=pointers,
                complete=True, clean=not any(h['severity']=='HIGH' for h in hits))


def clean(root):
    if run(['status', '--porcelain'], root):
        raise Failure('Clean working tree including untracked files required')


def backup(root, destination):
    dest = Path(destination).resolve()
    if dest == root or root in dest.parents:
        raise Failure('Backup must be outside the repository')
    dest.mkdir(parents=True, exist_ok=False)
    gitdir = Path(run(['rev-parse','--path-format=absolute','--git-common-dir'], root))
    shutil.copytree(gitdir, dest/'git-metadata')
    bundle = dest/'archive.bundle'
    run(['bundle','create',str(bundle),'--all'], root)
    run(['bundle','verify',str(bundle)], root)
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    (dest/'manifest.json').write_text(json.dumps(dict(refs=refs(root), sha256=digest),indent=2),encoding='utf-8')
    return dict(destination=str(dest), bundleVerified=True, sha256=digest,
                warning='Contains historical credentials. Protect backup access. Worktree changes not included.')


def live(root):
    text = run(['ls-remote','--heads','origin'], root)
    return {line.split('\t')[1][11:]: line.split('\t')[0] for line in text.splitlines()}


def selected(rows, branch):
    if branch:
        rows = [r for r in rows if r['branch']==branch]
        if not rows:
            raise Failure('Branch not found')
    return rows


def sync(root, branch, dry):
    rows = selected(inventory(root), branch)
    if dry:
        return rows
    clean(root)
    actual = live(root)
    checked = set(re.findall(r'^branch refs/heads/(.+)$', run(['worktree','list','--porcelain'], root), re.M))
    result = []
    saved = False
    for row in rows:
        name = row['branch']
        if excluded(name) or name in checked or row['state'] not in ('FAST_FORWARD','REMOTE_ONLY') or actual.get(name)!=row['remote']:
            result.append(dict(branch=name, action='HELD', reason='checked out, unsafe relation, or stale remote'))
            continue
        if not security(root,[row['remote']])['clean']:
            result.append(dict(branch=name,action='SECURITY_BLOCKED'));continue
        if not saved:
            backup(root,str(root.parent.parent/'Archive-backups'/('sync-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))))
            saved=True
        if live(root).get(name)!=row['remote']:raise Failure('Remote changed during sync')
        # Atomic compare-and-swap; never checkout, merge, delete or reset.
        run(['update-ref','refs/heads/'+name,row['remote'],row['local'] or '0'*40], root)
        result.append(dict(branch=name,action='FAST_FORWARD_OR_CREATE'))
    return result


def cached_security(root, commit, write=False):
    policy=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    common=Path(run(['rev-parse','--path-format=absolute','--git-common-dir'],root))
    folder=common/'archive-security-cache'; path=folder/(policy+'-'+commit+'.json')
    if path.exists():
        try:
            value=json.loads(path.read_text(encoding='utf-8'))
            if value.get('policy')==policy and value.get('commit')==commit:return value['scan']
        except (ValueError,OSError):pass
    scan=security(root,[commit])
    if write:
        folder.mkdir(exist_ok=True)
        path.write_text(json.dumps(dict(policy=policy,commit=commit,scan=scan)),encoding='utf-8')
    return scan


def push(root, branch, dry):
    if not branch:
        raise Failure('Push requires explicit -Branch; bulk push disabled')
    row = selected(inventory(root), branch)[0]
    if excluded(branch) or row['state'] not in ('LOCAL_AHEAD','LOCAL_ONLY'):
        raise Failure('Branch is not eligible for ordinary push')
    remote = live(root).get(branch)
    if remote != row['remote']:
        raise Failure('Remote changed; fetch and replan')
    scan = cached_security(root, row['local'], not dry)
    if not scan['clean']:
        return dict(branch=branch, state='SECURITY_BLOCKED', findings=scan['findings'], pushed=False)
    if dry:
        return dict(branch=branch, state='ELIGIBLE', pushed=False, whatIf=True)
    clean(root)
    recovery=backup(root,str(root.parent.parent/'Archive-backups'/('push-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))))
    if live(root).get(branch)!=remote or oid(root,'refs/heads/'+branch)!=row['local']:
        raise Failure('State changed during security scan')
    # Use the scanned immutable object, not a potentially moving local branch.
    run(['push','origin',row['local']+':refs/heads/'+branch], root)
    if live(root).get(branch)!=row['local']:
        raise Failure('Post-push verification failed')
    return dict(branch=branch,pushed=True,commit=row['local'],backup=recovery['destination'])


def extract(root, project, branch, destination, dry):
    if not project or '/' in project or '\\' in project or project in ('.','..'):
        raise Failure('Project must be an exact top-level directory')
    ref = 'refs/heads/'+branch
    commit = oid(root, ref)
    if not run(['ls-tree',commit,'--',project], root).startswith('040000 tree '):
        raise Failure('Project directory absent from this branch; inspect tree before choosing a path')
    dest = Path(destination).resolve()
    if dest.exists() or dest==root or root in dest.parents or dest in root.parents:
        raise Failure('Destination must be new and outside repository')
    if dry:
        return dict(commit=commit,project=project,destination=str(dest),whatIf=True)
    # git archive does not follow stored symlinks or run filters/hooks. Preserve a ZIP
    # and extract only regular files after checking traversal and Windows aliases.
    import zipfile
    with tempfile.TemporaryDirectory() as temp:
        zpath = str(Path(temp)/'snapshot.zip')
        run(['archive','--format=zip','--output='+zpath,commit,'--',project],root)
        with zipfile.ZipFile(zpath) as z:
            for info in z.infolist():
                parts = info.filename.replace('\\','/').split('/')
                if any(p in ('.','..') or ':' in p or p.endswith((' ','.')) or re.match(r'(?i)^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)',p) for p in parts if p):
                    raise Failure('Unsafe archive path')
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise Failure('Symlink extraction requires manual review')
            dest.mkdir(parents=True)
            z.extractall(dest)
    return dict(destination=str(dest),commit=commit,mode='file snapshot; no standalone history; LFS pointers remain pointers')


def add(root, project, sources, dry, updating=False):
    if not project or not re.fullmatch(r'[A-Za-z0-9_-]+',project):
        raise Failure('Use an ASCII project namespace')
    sources = {k:v for k,v in sources.items() if v}
    if not sources or ('' in sources and len(sources)>1):
        raise Failure('Choose SourceRepo OR frontend/backend repositories')
    if not updating and (run(['ls-tree','main','--',project],root) or any(k.startswith('refs/heads/'+project+'/') for k in refs(root))):
        raise Failure('Project already archived; updates require separate review')
    if dry:
        return dict(project=project,action='stage all source branches in isolated clone; review before import',whatIf=True)
    clean(root)
    base_refs=refs(root); remote_refs=live(root)
    # Deliver a recoverable candidate, without changing live Archive refs.
    stage = Path(tempfile.mkdtemp(prefix='archive-add-'))
    run(['clone','--no-hardlinks','--no-checkout',str(root),str(stage/'candidate')],root)
    candidate = stage/'candidate'
    run(['config','user.name','Archive Manager'],candidate)
    run(['config','user.email','archive-manager@localhost'],candidate)
    run(['switch','main'],candidate)
    for index,(segment,url) in enumerate(sources.items()):
        if url.startswith('-') or ('://' in url and not url.startswith('https://')) or re.search(r'https://[^/]*@',url):
            raise Failure('Only credential-free HTTPS or local repository paths accepted')
        remote = 'source'+str(index)
        run(['remote','add',remote,url],candidate)
        run(['fetch','--no-tags',remote],candidate)
        head = run(['ls-remote','--symref',remote,'HEAD'],candidate)
        match = re.search(r'ref: refs/heads/(.+)\tHEAD',head)
        if not match:
            raise Failure('Cannot determine source default branch')
        default = match[1]
        prefix = project+('/'+segment if segment else '')
        run(['subtree','pull' if updating else 'add','--prefix='+prefix,remote,default],candidate)
        # Each namespaced branch keeps the complete source history as parent,
        # and changes only its project prefix relative to integrated main.
    main = oid(candidate,'main')
    for index,(segment,url) in enumerate(sources.items()):
        remote = 'source'+str(index)
        prefix = project+('/'+segment if segment else '')
        for ref,commit in refs(candidate).items():
            if not ref.startswith('refs/remotes/'+remote+'/') or ref.endswith('/HEAD'):
                continue
            name = ref.split('/',3)[3]
            target = project+('/'+segment if segment else '')+'/'+name
            previous=base_refs.get('refs/heads/'+target) if updating else None
            run(['switch','--detach',previous or main],candidate)
            run(['merge','-s','ours','--allow-unrelated-histories','--no-edit',commit],candidate)
            run(['rm','-r','--ignore-unmatch','--',prefix],candidate)
            run(['read-tree','--prefix='+prefix+'/', '-u',commit],candidate)
            if run(['diff','--cached','--name-only'],candidate):
                run(['commit','-m','archive: project branch snapshot'],candidate)
            run(['branch',target,'HEAD'],candidate)
    targets={'refs/heads/main':oid(candidate,'main')}
    targets.update({k:v for k,v in refs(candidate).items() if k.startswith('refs/heads/'+project+'/')})
    scans=[security(candidate,[v]) for v in targets.values()]
    scan={'findings':[h for sc in scans for h in sc['findings']]}
    manifest=dict(project=project,sources=sources,baseRefs=base_refs,remoteRefs=remote_refs,targets=targets,updating=updating)
    (stage/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    run(['bundle','create',str(stage/'candidate.bundle'),'--all'],candidate)
    run(['bundle','verify',str(stage/'candidate.bundle')],candidate)
    return dict(candidate=str(candidate),bundle=str(stage/'candidate.bundle'),securityFindings=len(scan['findings']),
                state='REVIEW_REQUIRED',liveArchiveChanged=False)


def validate(root):
    fsck = subprocess.run(['git','fsck','--full'],cwd=root,capture_output=True)
    scan = security(root)
    common = Path(run(['rev-parse','--path-format=absolute','--git-common-dir'],root))
    missing = [p for p in scan['lfsPointers'] if not (common/'lfs/objects'/p['oid'][:2]/p['oid'][2:4]/p['oid']).is_file()]
    baseline=root/'docs/archive-lfs-known-missing.json'
    known=set(json.loads(baseline.read_text(encoding='utf-8'))['oids']) if baseline.exists() else set()
    for item in missing:item['state']='KNOWN_MISSING' if item['oid'] in known else 'UNEXPECTED_MISSING'
    rows = inventory(root)
    trees = []
    for row in rows:
        commit = row['local'] or row['remote']
        trees.append(dict(branch=row['branch'],rootTree=run(['rev-parse',commit+'^{tree}'],root),
                          projectPathPresent=bool(run(['ls-tree',commit,'--',row['project']],root)) if row['project']!='(root)' else None))
    return dict(objectsValid=fsck.returncode==0,fsckExit=fsck.returncode,
                danglingLines=sum('dangling ' in s for s in fsck.stdout.decode(errors='replace').splitlines()),
                mainDirectories=run(['ls-tree','-d','--name-only','main'],root).splitlines(),
                branches=rows,trees=trees,securityFindings=len(scan['findings']),missingLfs=missing,
                limitations='Pointer preservation is not LFS payload recovery. Deletion intent requires a reviewed baseline.')


def verify_branches(root, branch=None):
    result=[]
    for row in selected(inventory(root),branch):
        scan=security(root,[row['local'] or row['remote']])
        result.append(dict(branch=row['branch'],commit=row['local'] or row['remote'],state=row['state'],security='PASS' if scan['clean'] else 'SECURITY_BLOCKED',reviewFindings=sum(h['severity']=='REVIEW' for h in scan['findings']),excluded=excluded(row['branch'])))
    return result


def push_safe(root,dry,continue_on_error=False):
    result=[]
    for row in inventory(root):
        if excluded(row['branch']) or row['state']!='LOCAL_AHEAD':continue
        try:result.append(push(root,row['branch'],dry))
        except Failure as exc:
            result.append(dict(branch=row['branch'],state='FAILED',reason=str(exc)))
            if not continue_on_error:break
    return result


def promote(root, candidate_path, dry=True):
    if not candidate_path:raise Failure('Candidate path required')
    candidate=Path(candidate_path).resolve()
    manifest_path=candidate.parent/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    project=manifest['project']; targets=manifest['targets']; base=manifest['baseRefs']
    if refs(root)!=base or live(root)!=manifest['remoteRefs']:raise Failure('STALE_CANDIDATE: local or remote refs changed')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',project):raise Failure('Invalid namespace')
    for ref,commit in targets.items():
        if ref!='refs/heads/main' and not ref.startswith('refs/heads/'+project+'/'):raise Failure('Invalid target ref')
        run(['check-ref-format',ref],root)
        if oid(candidate,ref)!=commit:raise Failure('Candidate changed')
        if ref in base and not ancestor(candidate,base[ref],commit):raise Failure('Non fast-forward candidate')
        paths=run(['diff','--name-only',base.get(ref,base['refs/heads/main']),commit],candidate).splitlines()
        if any(not path.startswith(project+'/') for path in paths):raise Failure('Candidate changes outside project')
        if not security(candidate,[commit])['clean']:raise Failure('SECURITY_BLOCKED')
    if dry:return dict(state='REVIEW_REQUIRED',targets=targets,whatIf=True,requires='-Approve to apply; then push explicit branches')
    clean(root)
    checked=run(['branch','--show-current'],root)
    if checked!='main':raise Failure('Promote requires main checkout')
    active=run(['worktree','list','--porcelain'],root)
    for ref in targets:
        if ref!='refs/heads/main' and 'branch '+ref+'\n' in active+'\n':raise Failure('Target checked out in another worktree')
    saved=backup(root,str(root.parent.parent/'Archive-backups'/('promote-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))))
    for commit in targets.values():run(['fetch','--no-tags',str(candidate),commit],root)
    if refs(root)!=base or live(root)!=manifest['remoteRefs']:raise Failure('State changed before promotion')
    # Update the checked out main through Git so its index and files stay consistent.
    run(['merge','--ff-only',targets['refs/heads/main']],root)
    commands=['start']
    for ref,commit in targets.items():
        if ref!='refs/heads/main':commands.append('update '+ref+' '+commit+' '+base.get(ref,'0'*40))
    commands+=['prepare','commit']
    run(['update-ref','--stdin'],root,data=('\n'.join(commands)+'\n').encode())
    if any(oid(root,k)!=v for k,v in targets.items()):raise Failure('Post-promotion verification failed; backup retained')
    metadata=root/'docs/archive-projects.json'
    data=json.loads(metadata.read_text(encoding='utf-8')) if metadata.exists() else {}
    data[project]={'sources':manifest['sources']}
    metadata.parent.mkdir(exist_ok=True)
    metadata.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return dict(state='PROMOTED',targets=targets,backup=saved,metadataRequiresCommit=True,push='Commit metadata then push each explicit branch or push-safe')


def update(root,project,dry):
    metadata=root/'docs/archive-projects.json'
    data=json.loads(metadata.read_text(encoding='utf-8')) if metadata.exists() else {}
    if project not in data:return dict(project=project,state='SOURCE_UNAVAILABLE',reason='No registered source; Archive-only management remains available')
    sources=data[project]['sources']
    for url in sources.values():
        try:run(['ls-remote','--heads',url],root)
        except Failure:return dict(project=project,state='SOURCE_UNAVAILABLE')
    # Existing source commits are recognized by subtree history. Pull preserves ancestry.
    return add(root,project,sources,dry,updating=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['status','fetch','plan','sync','security','validate','push','backup','restore','add','extract','promote','update','verify-branches','push-safe'])
    for name in ['repository','branch','project','destination','bundle','frontend-repo','backend-repo','source-repo','report','candidate']:
        p.add_argument('--'+name)
    p.add_argument('--approve',action='store_true')
    p.add_argument('--continue-on-error',action='store_true')
    p.add_argument('--what-if',action='store_true')
    a=p.parse_args()
    root=Path(a.repository or '.').resolve()
    run(['rev-parse','--git-dir'],root)
    if a.branch:
        run(['check-ref-format','refs/heads/'+a.branch],root)
    c=a.command
    if c in ('status','plan'): result=inventory(root)
    elif c=='security': result=security(root)
    elif c=='validate': result=validate(root)
    elif c=='verify-branches': result=verify_branches(root,a.branch)
    elif c=='push-safe': result=push_safe(root,a.what_if,a.continue_on_error)
    elif c=='promote': result=promote(root,a.candidate,a.what_if or not a.approve)
    elif c=='update': result=update(root,a.project,a.what_if)
    elif c=='sync': result=sync(root,a.branch,a.what_if)
    elif c=='push': result=push(root,a.branch,a.what_if)
    elif c=='fetch':
        if not a.what_if: run(['fetch','--no-prune','--no-tags','origin'],root)
        result=dict(fetched=not a.what_if,prune=False)
    elif c=='backup':
        dest=a.destination or str(root.parent.parent/'Archive-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        result=dict(destination=dest,whatIf=True) if a.what_if else backup(root,dest)
    elif c=='restore':
        if not a.bundle or not a.destination: raise Failure('Restore requires Bundle and new Destination')
        dest=Path(a.destination).resolve()
        if dest.exists() or dest==root or root in dest.parents: raise Failure('Restore destination must be new and external')
        run(['bundle','verify',str(Path(a.bundle).resolve())],root)
        if not a.what_if: run(['clone','--mirror',str(Path(a.bundle).resolve()),str(dest)],root)
        result=dict(destination=str(dest),verified=True,whatIf=a.what_if,mode='bare mirror; remote-tracking refs preserved')
    elif c=='extract':
        if not a.branch or not a.destination: raise Failure('Extract requires Branch and Destination')
        result=extract(root,a.project,a.branch,a.destination,a.what_if)
    elif c=='add': result=add(root,a.project,{'frontend':a.frontend_repo,'backend':a.backend_repo,'':a.source_repo},a.what_if)
    output=json.dumps(result,ensure_ascii=False,indent=2)
    if a.report and not a.what_if:
        dest=Path(a.report).resolve()
        if dest.exists(): raise Failure('Report destination already exists')
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(output+'\n',encoding='utf-8')
        print(json.dumps(dict(report=str(dest),command=c),ensure_ascii=False))
    else: print(json.dumps(result,ensure_ascii=True,indent=2))
    if isinstance(result,dict) and (result.get('state')=='SECURITY_BLOCKED' or (c=='security' and not result['clean']) or (c=='validate' and (not result['objectsValid'] or any(x['state']=='UNEXPECTED_MISSING' for x in result['missingLfs'])))):
        return 2
    if isinstance(result,list) and any(r.get('state') in ('FAILED','SECURITY_BLOCKED') or r.get('security')=='SECURITY_BLOCKED' or r.get('action')=='SECURITY_BLOCKED' for r in result):return 2
    return 0


if __name__=='__main__':
    try: sys.exit(main())
    except (Failure,OSError,ValueError) as exc:
        # Never emit raw subprocess errors, source content or credential-bearing arguments.
        print('Archive manager stopped: '+str(exc) if isinstance(exc,Failure) else 'Archive manager stopped: local I/O or argument error',file=sys.stderr)
        sys.exit(1)

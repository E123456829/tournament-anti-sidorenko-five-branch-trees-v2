"""Build three reading views from one editable source graph.

Only the Python standard library, LuaLaTeX, BibTeX and latexmk are needed.
External references use the actual companion PDF's labels and anchors.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, sys, time

INPUT=re.compile(r'\\input\{([^{}]+)\}')
LABEL=re.compile(r'\\label\{([^{}]+)\}')

def active(source,root='main.tex'):
    result={}
    def visit(name):
        p=source/name
        if not p.suffix:p=p.with_suffix('.tex')
        rel=p.relative_to(source).as_posix()
        if rel in result:return
        text=p.read_text(encoding='utf8');result[rel]=text
        for child in INPUT.findall(text):visit(child)
    visit(root)
    return result

def own_labels(source,view):
    main=(source/'main.tex').read_text(encoding='utf8')
    if view=='article':
        body=main[main.index(r'\input{sec-introduction-five}'):main.index(r'\input{declarations}')]
        files=INPUT.findall(body)+['declarations']
    else:
        body=main[main.index(r'\appendix'):]
        files=INPUT.findall(body)
    labels=set()
    for f in files:
        for t in active(source,f).values():labels.update(LABEL.findall(t))
    return labels

def external_aux(original,dest,excluded):
    lines=['\\relax']
    for l in original.read_text(encoding='utf8').splitlines():
        m=re.match(r'\\newlabel\{([^{}]+)\}',l)
        if m and m[1] not in excluded:lines.append(l)
    dest.write_text('\n'.join(lines)+'\n',encoding='utf8')

def command():
    lua=shutil.which('lualatex')
    if not lua:raise RuntimeError('LuaLaTeX was not found on PATH')
    info=subprocess.run([lua,'--version'],capture_output=True,text=True,errors='replace')
    miktex='MiKTeX' in info.stdout+info.stderr
    lm=shutil.which('latexmk')
    if not lm:raise RuntimeError('latexmk was not found on PATH')
    prefix=[lm]
    if os.name=='nt' and miktex:
        script=Path(lua).parents[3]/'scripts/latexmk/latexmk.pl'
        perl=shutil.which('perl')
        gitperl=Path('C:/Program Files/Git/usr/bin/perl.exe')
        if gitperl.exists():perl=str(gitperl)
        if script.exists() and perl:prefix=[perl,str(script)]
    flags=['-norc','-lualatex','-bibtex','-recorder','-interaction=nonstopmode',
      '-halt-on-error','-file-line-error','-latexoption=-shell-restricted']
    if miktex:flags+=['-latexoption=-disable-installer','-e',"$bibtex = 'bibtex --miktex-disable-installer %O %S';"]
    if miktex and os.environ.get('Q45_LUA_FORMAT'):
        fmt=Path(os.environ['Q45_LUA_FORMAT'])
        if not fmt.is_file():raise RuntimeError('Configured existing LuaLaTeX format does not exist')
        flags+=['-latexoption=--fmt='+fmt.as_posix(),'-latexoption=--miktex-disable-maintenance','-latexoption=--miktex-disable-diagnose']
    return prefix+flags

def compile_job(folder,job):
    env=dict(os.environ);env['TEXMFCACHE']='.';env['max_print_line']='10000'
    if os.name=='nt' and Path('C:/Program Files/Git/usr/bin').exists():
        env['PATH']='C:/Program Files/Git/usr/bin;'+env.get('PATH','')
    cmd=command()+[job+'.tex'];start=time.time()
    print('Building',job,'in',folder.name,flush=True)
    p=subprocess.run(cmd,cwd=folder,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
    (folder/(job+'-build.txt')).write_text('$ '+' '.join(cmd)+'\n\n'+p.stdout+'\n'+p.stderr,encoding='utf8')
    if p.returncode:raise RuntimeError(job+' failed; see '+str(folder/(job+'-build.txt')))
    log=(folder/(job+'.log')).read_text(encoding='utf8',errors='replace')
    for pattern in [r'undefined on input line',r'multiply defined',r'Missing character:']:
        if re.search(pattern,log):raise RuntimeError(job+' has unresolved text/reference issues: '+pattern)
    return {'job':job,'seconds':round(time.time()-start,2),'command':cmd,
      'pdf_sha256':hashlib.sha256((folder/(job+'.pdf')).read_bytes()).hexdigest()}

def build(source,work,out,native=None):
    source=source.resolve();work=work.resolve();out=out.resolve()
    work.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    sourcefiles=active(source)
    for name in ['article.tex','supplement.tex','references.bib']:
        sourcefiles[name]=(source/name).read_text(encoding='utf8')
    graphics={}
    for text in sourcefiles.values():
        for rel in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}',text):
            asset=(source/rel).resolve()
            if not asset.is_relative_to(source) or not asset.is_file():
                raise RuntimeError('Missing or invalid graphic asset: '+rel)
            graphics[asset.relative_to(source).as_posix()]=asset.read_bytes()
    folders={}
    for view in ['complete','article','supplement']:
        p=work/view;p.mkdir(exist_ok=True);folders[view]=p
        for rel,text in sourcefiles.items():
            f=p/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text,encoding='utf8')
        for rel,data in graphics.items():
            f=p/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
        if (source/'fonts').is_dir():
            shutil.copytree(source/'fonts',p/'fonts',dirs_exist_ok=True)
    records=[]
    if native:
        native=native.resolve()
        for rel,text in active(source).items():
            if (native/rel).read_text(encoding='utf8')!=text:
                raise RuntimeError('Native full PDF is stale at '+rel)
        for f in (source/'fonts').glob('*'):
            if f.is_file() and (native/'fonts'/f.name).read_bytes()!=f.read_bytes():
                raise RuntimeError('Native font asset is stale at '+f.name)
        for rel,data in graphics.items():
            if (native/rel).read_bytes()!=data:
                raise RuntimeError('Native graphic asset is stale at '+rel)
        full=native
        shutil.copyfile(native/'main.pdf',folders['complete']/'main.pdf')
        shutil.copyfile(native/'main.aux',folders['complete']/'main.aux')
        log=native/'main.log'
        if not log.exists():log=native/'logs/main.log'
        shutil.copyfile(log,folders['complete']/'main.log')
        records.append({'job':'main','origin':'verified source-identical native full build',
          'origin_path':str(native),
          'pdf_sha256':hashlib.sha256((native/'main.pdf').read_bytes()).hexdigest()})
    else:
        records.append(compile_job(folders['complete'],'main'));full=folders['complete']
    art=folders['article'];sup=folders['supplement']
    external_aux(full/'main.aux',art/'article-external.aux',own_labels(source,'article'))
    records.append(compile_job(art,'article'))
    external_aux(art/'article.aux',sup/'supplement-external.aux',own_labels(source,'supplement'))
    records.append(compile_job(sup,'supplement'))
    external_aux(sup/'supplement.aux',art/'article-external.aux',own_labels(source,'article'))
    records.append(compile_job(art,'article'))
    # The article's content and named anchors are stable; now retain the
    # exact final back-reference labels in the supplementary source too.
    external_aux(art/'article.aux',sup/'supplement-external.aux',own_labels(source,'supplement'))
    records.append(compile_job(sup,'supplement'))
    for origin,name in [(art/'article.pdf','01_Article.pdf'),(sup/'supplement.pdf','02_Technical_Appendix.pdf'),
                         (full/'main.pdf','03_Complete_Manuscript.pdf')]:
        shutil.copyfile(origin,out/name)
    shutil.copyfile(art/'article-external.aux',source/'article-external.aux')
    shutil.copyfile(sup/'supplement-external.aux',source/'supplement-external.aux')
    report={'source_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in sourcefiles.items()},
      'graphic_asset_sha256':{k:hashlib.sha256(v).hexdigest()for k,v in graphics.items()},
      'font_asset_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in (source/'fonts').glob('*')if f.is_file()},
      'builds':records,'cross_references':'Companion-PDF labels and anchors come from actual final article/supplement aux files.',
      'outputs':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in out.glob('*.pdf')}}
    try:
        from pypdf import PdfReader
        for name,data in report['outputs'].items():data['pages']=len(PdfReader(out/name).pages)
    except ImportError:pass
    (work/'BUILD_VIEWS_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('Three reading views complete.',flush=True)
    return report

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8')
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--native-full',type=Path);a=ap.parse_args()
    build(a.source,a.work,a.out,a.native_full)

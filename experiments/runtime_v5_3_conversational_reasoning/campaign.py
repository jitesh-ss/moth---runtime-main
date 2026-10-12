"""Reproducible 5.3 qualification; raw output is not a promotion prerequisite."""
from pathlib import Path
import importlib,json,os,statistics,subprocess,sys,tempfile,time,resource,hashlib
ROOT=Path(__file__).resolve().parents[2]
EXPERIMENT=Path(__file__).resolve().parent
CANDIDATE=EXPERIMENT/'candidate'

def worker(version,artifact):
    name='moth_runtime_v'+version.replace('.','_')
    Model=getattr(importlib.import_module(name+'.artifact'),'ModelArtifact'+version.replace('.',''))
    compile_prompt=importlib.import_module(name+'.compile.hcf').compile_system_prompt
    load=importlib.import_module(name+'.energy.loader').load_hcf_field
    settle=importlib.import_module(name+'.energy.settlement').settle
    Store=importlib.import_module(name+'.persistence.objects').ObjectStore
    baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    model=Model.open(artifact)
    with tempfile.TemporaryDirectory() as tmp:
        field=load(compile_prompt(Store(tmp),model.energy_foundation,'Respond in detail.'),model.energy_foundation)
        for _ in range(100):settle(model.energy_foundation,(field,))
        times=[]
        for _ in range(1000):
            start=time.perf_counter_ns();settle(model.energy_foundation,(field,));times.append(time.perf_counter_ns()-start)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {'median_ns':statistics.median(times),'incremental_rss':peak-baseline,'baseline_rss':baseline,'peak_rss':peak}

def run():
    sys.path.insert(0,str(CANDIDATE))
    from moth_runtime_v5_3.build_artifact import build_artifact
    from moth_runtime_v5_3.runtime import Runtime53
    from experiments.runtime_v5_3_conversational_reasoning.legacy_panels import _surface_panel,_plan_panel
    env={**os.environ,'PYTHONPATH':os.pathsep.join([str(CANDIDATE),str(ROOT/'src'),str(ROOT)]),'PYTHONDONTWRITEBYTECODE':'1'}
    with tempfile.TemporaryDirectory(prefix='moth53-qualification-') as tmp:
        tmp=Path(tmp);builds=[build_artifact(tmp/f'a{i}') for i in range(3)]
        assert len({b['artifact_hash'] for b in builds})==1
        r=Runtime53.initialize(tmp/'store',tmp/'a0')
        surface=_surface_panel(r);skills=_plan_panel(r)
        chat_times=[]
        for _ in range(10):
            cid=r.create_conversation('')
            start=time.perf_counter_ns()
            result=r.turn(cid,'Take package A to room three.')
            chat_times.append(time.perf_counter_ns()-start)
            assert result['status']=='ANSWER'
            r.reexecute(cid,result['turn_id'])
        old=ROOT/'config/v5.2/model/model-5.2'
        samples={'5.2':[],'5.3':[]}
        for _ in range(5):
            for version,path in [('5.2',old),('5.3',tmp/'a0')]:
                process=subprocess.run([sys.executable,'-B','-m','experiments.runtime_v5_3_conversational_reasoning.campaign','worker',version,str(path)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
                samples[version].append(json.loads(process.stdout))
        median={v:{k:statistics.median(x[k] for x in rows) for k in rows[0]} for v,rows in samples.items()}
        performance={'samples':samples,'median':median,'time_ratio':median['5.3']['median_ns']/median['5.2']['median_ns'],
            'memory_ratio':median['5.3']['incremental_rss']/max(1,median['5.2']['incremental_rss'])}
        baseline=json.loads((EXPERIMENT/'fixtures/baseline-hashes.json').read_text())
        changed=[name for name,value in baseline.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=value]
        report={'artifact':builds[0],'three_identical_builds':True,'legacy_surface':surface,'legacy_skills':skills,'performance':performance,'protected_changes':changed,'chat_plan_turn_median_ns':statistics.median(chat_times)}
        (EXPERIMENT/'runs/qualification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        assert not changed,changed
        assert performance['time_ratio']<=1.1,performance
        assert performance['memory_ratio']<=1.1,performance
        return report

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':print(json.dumps(worker(sys.argv[2],Path(sys.argv[3]))))
    else:print(json.dumps(run(),sort_keys=True))

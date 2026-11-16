#!/usr/bin/env python3
"""Mine migration-log.csv files for recurring problems. Deterministic: no LLM, no network.
Usage: python3 -I mine_logs.py <csv-or-folder> [...] [--min-jobs 2] [--out clusters.json]"""
import csv, json, re, sys, os, hashlib
SKILL_HINTS = {
 "cendyn-page-builder": ["section","import","save","fill","create page","widget","gallery","verify","publish"],
 "cendyn-copy": ["copy","firecrawl","extract","verbatim","content.json","scrape","source site"],
 "cendyn-discovery": ["profile","probe","discovery","page-type","mapping","template page"],
 "image-prep": ["image","photo","20 mb","5500","dimension","file size","resize"],
 "migration-log": ["log","csv","row","column"],
}
STOP=set("the a an and or to of in on for was were is it be not by with at as from this that had has".split())
REDACT=[(re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),"<email>"),
        (re.compile(r"\b(?:\d[ -]?){13,16}\b"),"<card>"),
        (re.compile(r"\+?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b"),"<phone>")]
def redact(s):
    for rx,rep in REDACT: s=rx.sub(rep,s)
    return s
def toks(s):
    s=re.sub(r"https?://\S+"," ",s.lower()); s=re.sub(r"\b\d+\b"," ",s)
    return frozenset(t for t in re.findall(r"[a-z][a-z0-9_-]{2,}",s) if t not in STOP)
def jac(a,b): return len(a&b)/len(a|b) if a and b else 0.0
def guess(t):
    t=t.lower(); sc={k:sum(w in t for w in v) for k,v in SKILL_HINTS.items()}
    b=max(sc,key=sc.get); return b if sc[b] else "unknown"
def csvs(paths):
    for p in paths:
        if os.path.isdir(p):
            for r,ds,fs in os.walk(p):
                ds[:]=[d for d in ds if not d.startswith(("_","."))]  # skip _template etc.
                for f in fs:
                    if f.lower()=="migration-log.csv": yield os.path.join(r,f)
        elif p.lower().endswith(".csv"): yield p
def main(argv):
    mj,out,paths=2,None,[]; it=iter(argv)
    for a in it:
        if a=="--min-jobs": mj=int(next(it))
        elif a=="--out": out=next(it)
        else: paths.append(a)
    probs=[]; files=list(csvs(paths)); rows=0
    for f in files:
        site=os.path.basename(os.path.dirname(os.path.abspath(f))); seen=set()
        with open(f,encoding="utf-8-sig",newline="") as fh:
            for r in csv.DictReader(fh):
                rows+=1; p=(r.get("problems") or "").strip()
                if not p: continue
                # reference/read-only rows carry notes, not failures
                if re.search(r"read-only|reference",(r.get("result") or "")+" "+(r.get("job") or ""),re.I): continue
                jid=hashlib.sha1(f"{site}|{r.get('date')}|{r.get('job')}|{r.get('prompt')}".encode()).hexdigest()[:10]
                if (jid,p) in seen: continue
                seen.add((jid,p))
                probs.append({"site":site,"job_id":jid,"date":r.get("date",""),"job":r.get("job",""),
                              "text":redact(p),"result":redact((r.get("result") or "").strip()),"t":toks(p)})
    cl=[]
    for p in probs:
        for c in cl:
            if jac(p["t"],c["seed"])>=0.4: c["items"].append(p); break
        else: cl.append({"seed":p["t"],"items":[p]})
    res=[]
    for c in cl:
        jobs={i["job_id"] for i in c["items"]}
        if len(jobs)<mj: continue
        txt=" ".join(i["text"]+" "+i["job"] for i in c["items"])
        res.append({"suspected_skill":guess(txt),"distinct_jobs":len(jobs),
            "sites":sorted({i["site"] for i in c["items"]}),
            "first_seen":min(i["date"] for i in c["items"]),"last_seen":max(i["date"] for i in c["items"]),
            "evidence":[{k:i[k] for k in ("site","date","job","text","result")} for i in c["items"][:6]]})
    res.sort(key=lambda x:-x["distinct_jobs"])
    s=json.dumps({"files":len(files),"rows":rows,"problem_entries":len(probs),
                  "recurring_clusters":len(res),"min_jobs":mj,"clusters":res},indent=2,ensure_ascii=False)
    if out: open(out,"w",encoding="utf-8").write(s)
    print(s)
if __name__=="__main__": main(sys.argv[1:])

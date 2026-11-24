#!/usr/bin/env python3
"""Fetch a single community-data feed for central static caching; no third-party images."""
import datetime,json,urllib.request,pathlib,sys
base='https://api.openligadb.de/getmatchdata/pl/'
now=datetime.datetime.now(datetime.timezone.utc)
season=now.year if now.month>=7 else now.year-1
req=urllib.request.Request(base+str(season),headers={'User-Agent':'BetVaultHQ/1.0 (static sports information project; see site contact page)','Accept':'application/json'})
try:
 with urllib.request.urlopen(req,timeout=25) as res: raw=json.load(res)
 if not isinstance(raw,list) or not raw: raise ValueError('Unexpected feed format')
 # Preserve chronological order based on the original timestamps
 rows=[]
 for m in raw:
  dt=m.get('matchDateTimeUTC') or m.get('matchDateTime')
  if not dt:continue
  try:ts=datetime.datetime.fromisoformat(dt.replace('Z','+00:00'))
  except ValueError:continue
  if ts.tzinfo is None:ts=ts.replace(tzinfo=datetime.timezone.utc)
  if not now-datetime.timedelta(days=7)<=ts<=now+datetime.timedelta(days=14):continue
  home=(m.get('team1') or {}).get('teamName','TBC');away=(m.get('team2') or {}).get('teamName','TBC')
  results=m.get('matchResults') or [];final=next((x for x in results if x.get('resultTypeID')==2),None)
  score=f"{final.get('pointsTeam1')}–{final.get('pointsTeam2')}" if m.get('matchIsFinished') and final and all(type(final.get(p)) is int and final[p]>=0 for p in ('pointsTeam1','pointsTeam2')) else None
  local=ts.astimezone(__import__('zoneinfo').ZoneInfo('Europe/London')).strftime('%d %b %H:%M')
  rows.append((ts,{'kickoff_utc':ts.isoformat(),'kickoff_uk':local,'home':home,'away':away,'score':score,'status':'Finished' if m.get('matchIsFinished') else 'Scheduled / in progress'}))
 rows.sort(key=lambda x:x[0])
 output={'updated_utc':now.strftime('%Y-%m-%d %H:%M'),'source':'OpenLigaDB','license':'ODbL-1.0','competition':'Premier League','matches':[m for _,m in rows]}
 # Calculate standings from confirmed full-season results, not the fixture window.
 table={}; completed=[]
 for m in raw:
  h=(m.get('team1') or {}).get('teamName'); a=(m.get('team2') or {}).get('teamName')
  if not h or not a: continue
  for name in (h,a): table.setdefault(name,dict(team=name,played=0,won=0,drawn=0,lost=0,gf=0,ga=0,points=0,form=[]))
  if not m.get('matchIsFinished'): continue
  f=next((r for r in m.get('matchResults',[]) if r.get('resultTypeID')==2),None)
  if not f or not isinstance(f.get('pointsTeam1'),int) or not isinstance(f.get('pointsTeam2'),int): continue
  completed.append((m.get('matchDateTimeUTC') or m.get('matchDateTime') or '',h,a,f['pointsTeam1'],f['pointsTeam2']))
 for _,h,a,g1,g2 in sorted(completed):
  for name,gf,ga in ((h,g1,g2),(a,g2,g1)):
   r=table[name]; r['played']+=1; r['gf']+=gf; r['ga']+=ga
   result='W' if gf>ga else 'D' if gf==ga else 'L'
   r[{'W':'won','D':'drawn','L':'lost'}[result]]+=1; r['points']+= {'W':3,'D':1,'L':0}[result]; r['form']=(r['form']+[result])[-5:]
 for r in table.values(): r['gd']=r['gf']-r['ga']
 output['standings']=sorted(table.values(),key=lambda r:(-r['points'],-r['gd'],-r['gf'],r['team'])) if completed else []
 output['season']=season
 # An empty match window is valid during breaks; publish an empty snapshot with a current timestamp
 target=pathlib.Path('data/football.json')
 if target.exists():
  previous=json.loads(target.read_text())
  if {k:v for k,v in previous.items() if k!='updated_utc'}=={k:v for k,v in output.items() if k!='updated_utc'}:
   print('Football data unchanged')
   sys.exit(0)
 temporary=target.with_suffix('.tmp')
 temporary.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
 temporary.replace(target)
 print('Updated',len(output['matches']),'matches')
except Exception as e:
 print('Data update failed; previous file retained:',e,file=sys.stderr)
 sys.exit(1)

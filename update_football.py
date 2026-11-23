#!/usr/bin/env python3
"""Fetch a single community-data feed for central static caching; no third-party images."""
import datetime,json,urllib.request,pathlib,sys
base='https://api.openligadb.de/getmatchdata/pl/'
now=datetime.datetime.now(datetime.timezone.utc)
season=now.year if now.month>=7 else now.year-1
req=urllib.request.Request(base+str(season),headers={'User-Agent':'BetVaultHQ/1.0 (static sports information project; see site contact page)','Accept':'application/json'})
try:
 with urllib.request.urlopen(req,timeout=25) as res: raw=json.load(res)
 if not isinstance(raw,list): raise ValueError('Unexpected feed format')
 matches=[]
 for m in raw:
  dt=m.get('matchDateTimeUTC') or m.get('matchDateTime')
  if not dt:continue
  try: ts=datetime.datetime.fromisoformat(dt.replace('Z','+00:00'))
  except ValueError:continue
  if ts.tzinfo is None:ts=ts.replace(tzinfo=datetime.timezone.utc)
  # Only a rolling window, to keep pages small and relevant
  if not now-datetime.timedelta(days=3)<=ts<=now+datetime.timedelta(days=14):continue
  home=(m.get('team1') or {}).get('teamName','TBC')
  away=(m.get('team2') or {}).get('teamName','TBC')
  results=m.get('matchResults') or []
  final=next((x for x in results if x.get('resultTypeID')==2),None)
  if not final and m.get('matchIsFinished') and results: final=results[-1]
  score=f"{final.get('pointsTeam1')}–{final.get('pointsTeam2')}" if final else None
  local=ts.astimezone(__import__('zoneinfo').ZoneInfo('Europe/London')).strftime('%d %b %H:%M')
  matches.append({'kickoff_uk':local,'home':home,'away':away,'score':score,'status':'Finished' if m.get('matchIsFinished') else 'Scheduled / in progress'})
 matches.sort(key=lambda x:x['kickoff_uk']) # Display order corrected below from feed chronological ordering
 # Preserve chronological order based on the original timestamps
 rows=[]
 for m in raw:
  dt=m.get('matchDateTimeUTC') or m.get('matchDateTime')
  if not dt:continue
  try:ts=datetime.datetime.fromisoformat(dt.replace('Z','+00:00'))
  except ValueError:continue
  if ts.tzinfo is None:ts=ts.replace(tzinfo=datetime.timezone.utc)
  if not now-datetime.timedelta(days=3)<=ts<=now+datetime.timedelta(days=14):continue
  home=(m.get('team1') or {}).get('teamName','TBC');away=(m.get('team2') or {}).get('teamName','TBC')
  results=m.get('matchResults') or [];final=next((x for x in results if x.get('resultTypeID')==2),None)
  if not final and m.get('matchIsFinished') and results:final=results[-1]
  score=f"{final.get('pointsTeam1')}–{final.get('pointsTeam2')}" if final else None
  local=ts.astimezone(__import__('zoneinfo').ZoneInfo('Europe/London')).strftime('%d %b %H:%M')
  rows.append((ts,{'kickoff_uk':local,'home':home,'away':away,'score':score,'status':'Finished' if m.get('matchIsFinished') else 'Scheduled / in progress'}))
 rows.sort(key=lambda x:x[0])
 output={'updated_utc':now.strftime('%Y-%m-%d %H:%M'),'source':'OpenLigaDB','license':'ODbL-1.0','competition':'Premier League','matches':[m for _,m in rows]}
 # An empty match window is valid during breaks; publish an empty snapshot with a current timestamp
 pathlib.Path('data/football.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
 print('Updated',len(output['matches']),'matches')
except Exception as e:
 print('Data update failed; previous file retained:',e,file=sys.stderr)
 sys.exit(1)

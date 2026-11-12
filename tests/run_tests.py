#!/usr/bin/env python3
"""Automatische Tests für die Berechnungen im Trainingsbuch.
Start: python3 tests/run_tests.py   (braucht Python-Playwright mit Chromium)
Lädt index.html mit Testdaten und prüft die Formeln gegen Handrechnungen."""
import asyncio, json, math, os, sys, datetime as dt
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
today=dt.date.today(); D=lambda n:(today-dt.timedelta(days=n)).isoformat()
now=0
docs={
 "plans/push":{"name":"Push","kind":"kraft","order":1,"exercises":[{"name":"Kurzhantel-Bankdrücken","muscle":"Brust","reps":"5-8","sets":3}]},
 "plans/pull":{"name":"Pull","kind":"kraft","order":2,"exercises":[{"name":"Schrägbank-Curls","muscle":"Bizeps","reps":"8-12","sets":3}]},
 "plans/beine":{"name":"Beine","kind":"kraft","order":3,"exercises":[{"name":"Beinpresse","muscle":"Quadrizeps","reps":"5-8","sets":3}]},
 "logs/a":{"date":D(3),"planId":"push","planName":"Push","kind":"kraft","entries":[{"name":"Kurzhantel-Bankdrücken","muscle":"Brust","secondary":["Trizeps","Schultern"],"reps":"5-8","sets":[{"w":10,"r":10,"rir":6},{"w":24,"r":8,"rir":3},{"w":24,"r":8,"rir":3}]}]},
 "logs/b":{"date":D(2),"planId":"pull","planName":"Pull","kind":"kraft","entries":[{"name":"Schrägbank-Curls","muscle":"Bizeps","secondary":[],"reps":"8-12","sets":[{"w":14,"r":6,"rir":0},{"w":14,"r":6,"rir":0}]}]},
 "logs/c":{"date":D(1),"planId":"beine","planName":"Beine","kind":"kraft","rpe":7,"durationMin":60,"entries":[{"name":"Beinpresse","muscle":"Quadrizeps","secondary":["Gesäss"],"reps":"5-8","sets":[{"w":40,"r":9,"rir":5},{"w":85,"r":8,"rir":2},{"w":85,"r":8,"rir":1}]}]},
}
for i in range(14):
    docs[f"bodyweight/{D(i)}"]={"date":D(i),"kg":round(80-(13-i)*(-0.5/7)*-1,3)}  # -0.5 kg/Woche
for i in range(10):
    docs[f"garmin/{D(i)}"]={"date":D(i),"hrv":80,"rhr":50,"sleepH":8,"steps":0}
docs=json.loads(json.dumps(docs))
for k in docs: docs[k]["_u"]=1
CASES=[
 ("Aufwärmsatz erkannt (40 kg bei 85 kg Top)", "workSets(S.logs.find(l=>l.planId==='beine').entries[0]).length", 2),
 ("Sätze pro Muskel ohne Aufwärmen: Brust", "setsPerMuscle(daysAgo(6))['Brust']", 2),
 ("Mitbeteiligt zählt halb: Trizeps", "setsPerMuscle(daysAgo(6))['Trizeps']", 1),
 ("Rückschritt-Regel: Curls 14 kg × 6 bei 8–12", "progression({name:'Schrägbank-Curls',reps:'8-12'}).kind", "down"),
 ("Rückschritt-Gewicht: 12 kg", "progression({name:'Schrägbank-Curls',reps:'8-12'}).w", 12),
 ("Schnelle Steigerung bei 3 RIR: 24 → 28 kg", "progression({name:'Kurzhantel-Bankdrücken',reps:'5-8'}).w", 28),
 ("Session-RPE: 60 min × 7 → Belastung 12,2", "dayStrain(daysAgo(1)).strain", 12.2),
 ("HRV konstant → z = 0", "Math.round(hrvTrend(todayStr()).z*100)/100", 0),
 ("Gewichtstrend −0,5 kg/Woche", "Math.round(bwTrend().slope*100)/100", -0.5),
 ("TRIMP 60 min Ø 130 bpm (RHR 50, HRmax 191)", "Math.round(trimp(60,130))", round(60*((130-50)/(191-50))*0.64*math.exp(1.92*((130-50)/(191-50))))),
 ("Epley 100 kg × 10 = 133,3", "Math.round(e1rm(100,10)*10)/10", 133.3),
 ("Rotation: nächster Plan = am längsten nicht trainiert (Push)", "(()=>{const h=nextRow(); return /Push/.test(h);})()", True),
]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(); errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+os.path.join(ROOT,"index.html")); await pg.wait_for_timeout(500)
        await pg.evaluate("d=>LDB.importDocs(d)", docs); await pg.wait_for_timeout(500)
        fails=0
        for name,expr,exp in CASES:
            try: got=await pg.evaluate(expr)
            except Exception as e: got=f"FEHLER {e}"
            ok = got==exp or (isinstance(exp,float) and isinstance(got,(int,float)) and abs(got-exp)<0.06)
            fails+= not ok; print(("✓" if ok else "✗"), name, "" if ok else f"→ erwartet {exp}, erhalten {got}")
        if errs: print("JS-Fehler:",errs); fails+=1
        await b.close(); print(f"\n{len(CASES)-fails if not errs else len(CASES)-fails+1}/{len(CASES)} bestanden"); sys.exit(1 if fails else 0)
asyncio.run(main())

"""Bygger en testside som tegner ett rom med lysmotoren.

    python3 tools/lysmotor/lag_demo.py kabin tools/lysmotor/kabin_oppsett.js /tmp/kabin.html
    python3 tools/lysmotor/ta_bilde.py /tmp/kabin.html /tmp/kabin.png

Prototype. Lysmotoren er ikke koblet inn i appen ennå; dette er
verkstedet der utseendet prøves ut rom for rom før den erstatter
lyslagene i kartfanen.

Oppsettfila er JavaScript som returnerer lyskildene, grunnlyset og
eventuelle innervegger for rommet. Vegger er bakt inn i bakgrunnen, så
rom med innervegger må oppgi dem selv, ellers lekker lyset gjennom.
"""
import json, sys, os
SP = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(SP))
rom_id, oppsett_fil, ut_fil = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(os.path.join(REPO, "bestiary", "battlemaps.json"), encoding="utf-8"))
rom = [r for r in d["rooms"] if r["id"] == rom_id][0]
oppsett = open(oppsett_fil, encoding="utf-8").read()
motor = open(os.path.join(SP, "lysmotor.js"), encoding="utf-8").read()
mappe = "file://" + os.path.join(REPO, "web", "maps", rom["dir"])
side = """<!doctype html><html><head><meta charset="utf-8">
<style>body{margin:0;background:#111}canvas{display:block}</style></head><body>
<canvas id="ut"></canvas>
<script>%(motor)s</script>
<script>
const ROM = %(rom)s;
const BG = "%(mappe)s/%(bg)s", ATLAS = "%(mappe)s/%(atlas)s";
function last(src){return new Promise((ok,nei)=>{const i=new Image();i.onload=()=>ok(i);i.onerror=nei;i.src=src;});}

/* Hvor høy en gjenstand er, i rompiksler (16 per fot). Ting som
   ligger på gulvet eller står oppå andre ting kaster ingen egen
   skygge. */
function hoydeFor(it){
  const n=((it.name||"")+" "+it.sprite).toLowerCase();
  if((it.z||0)>=15) return 0;
  if(/dør|door|skilt|lab|sign|teppe|matte|rug|avis|papir|brev|flekk|blod|søl|oil|strø|straw|tau|rope|kjetting|chain|presenning|tarp|pall|pallet|lik |body|skinn|pelt|skrue|leider|ladder|hengelås/.test(n)) return 0;
  const solid=[[/oljefat|drum/,46],[/løs kasse|smallcrate/,30],[/sekk|sack/,20],
    [/verktøykasse|toolbox/,16],[/bøtte|bucket/,20]];
  for(const [re,h] of solid) if(re.test(n)) return h;
  if((it.z||0)<=6) return 0;
  const tabell=[[/bagasje/,64],[/våpenstativ|våpenskap|guns|arms/,80],[/statue/,72],
    [/orgel|organ/,84],[/maleri|paint/,56],[/vin|wine/,44],[/instrument/,48],
    [/urne|urns/,44],[/kiste|greenbox/,36],[/ballong|carboy/,40],[/plank|redwood/,22],[/skap|garderobe|wardrobe/,96],[/gulvlampe|floorlamp/,80],[/palme|palm/,64],
    [/lenestol|armchair/,46],[/stol|chair/,46],[/sofa|settee/,42],[/servant|sink/,44],
    [/askebeger|ashtray/,40],[/skrivebord|desk/,40],[/nattbord|nightstand/,36],
    [/dampkoffert|trunk/,34],[/seng|bed/,30],[/badekar|tub/,30],[/ovn|radiator/,30],
    [/salongbord|table/,26],[/koffert|suitcase/,24],[/toalett|toilet/,26],
    [/kurv|waste/,18],[/hatteske|hatbox/,18],[/kasse|crate/,48],[/fat|tønne|barrel/,48]];
  for(const [re,h] of tabell) if(re.test(n)) return h;
  return 28;
}

(async()=>{
  const S=4, W=ROM.widthPx, H=ROM.heightPx;
  const bg=await last(BG), atlas=await last(ATLAS);
  const scene=document.createElement("canvas"); scene.width=W*S; scene.height=H*S;
  const g=scene.getContext("2d"); g.imageSmoothingEnabled=false;
  g.drawImage(bg,0,0,W*S,H*S);
  const synlige=ROM.items.filter(i=>!i.hiddenByDefault).sort((a,b)=>(a.z||0)-(b.z||0));
  const hindre=[];
  synlige.forEach(it=>{
    const [fx,fy,fw,fh]=ROM.frames[it.sprite];
    g.save(); g.translate((it.x+fw/2)*S,(it.y+fh/2)*S); g.rotate((it.rotation||0)*Math.PI/180);
    g.drawImage(atlas,fx,fy,fw,fh,-fw/2*S,-fh/2*S,fw*S,fh*S); g.restore();
    const h=hoydeFor(it);
    // Spritene har en piksel kontur og fire piksler bakt skygge nede
    // til høyre; selve tingen er litt mindre enn bildet.
    if(h>0) hindre.push({poly:Lysmotor.hjorner(it.x+1,it.y+1,fw-5,fh-5,it.rotation||0),hoyde:h,navn:it.name});
  });
  const OPPSETT=(function(){ %(oppsett)s })();
  // Vegger er bakt inn i bakgrunnen, så motoren vet ikke om dem. Rom
  // som har innervegger oppgir dem selv.
  (OPPSETT.vegger||[]).forEach(v=>hindre.push({poly:Lysmotor.hjorner(v[0],v[1],v[2],v[3],0),hoyde:v[4]||160,navn:"vegg"}));
  const ut=document.getElementById("ut"); ut.width=W*S; ut.height=H*S;
  Lysmotor.render(ut,W,H,S,Object.assign({scene:scene,hindre:hindre},OPPSETT));
  document.title="FERDIG";
})().catch(e=>{document.title="FEIL "+e;});
</script></body></html>""" % {"motor": motor, "rom": json.dumps(rom), "mappe": mappe,
                               "bg": rom["bg"], "atlas": rom["atlas"], "oppsett": oppsett}
open(ut_fil, "w", encoding="utf-8").write(side)
print("side:", ut_fil)

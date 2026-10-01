# Builds the per-person immigration itinerary PDFs from the app data.
# Run from the repo root:  python3 docs/build.py   (needs playwright + chromium)
import asyncio,html,json,os
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E=html.escape
T={'ashik':dict(nm='Ashik',frm='Kochi, India',ain='Tokyo Haneda (HND)',ad='Thu 8 Oct 2026',at='04:55',dout='Tokyo Haneda (HND)',dd='Mon 19 Oct 2026',dt='08:50',nights='11 nights'),
   'binza':dict(nm='Binza',frm='Sydney, Australia',ain='Tokyo Haneda (HND)',ad='Wed 7 Oct 2026',at='20:35',dout='Tokyo Haneda (HND)',dd='Mon 19 Oct 2026',dt='08:30',nights='12 nights'),
   'ansar':dict(nm='Ansar',frm='Dubai, UAE',ain='Tokyo Narita (NRT)',ad='Wed 7 Oct 2026',at='17:35',dout='Tokyo Narita (NRT)',dd='Mon 19 Oct 2026',dt='22:30',nights='12 nights')}
STAYS=[dict(n='Mitsui Garden Hotel Jingugaien Tokyo Premier',ja='〒160-0013 東京都新宿区霞ヶ丘町11-3',en='11-3 Kasumigaoka-machi, Shinjuku-ku, Tokyo 160-0013',d='7 to 10 Oct',nights=3,tel='+81-3-5786-1531',c='#2F6FD6',city='Tokyo'),
       dict(n='Apartment Hotel 7key S Kyoto',ja='〒600-8443 京都府京都市下京区船鉾町404',en='404 Funeboko-cho, Shimogyo-ku, Kyoto 600-8443',d='10 to 15 Oct',nights=5,tel='see booking confirmation',c='#D6482F',city='Kyoto'),
       dict(n='Mitsui Garden Hotel Gotanda',ja='〒141-0022 東京都品川区東五反田2-2-6',en='2-2-6 Higashi-Gotanda, Shinagawa-ku, Tokyo 141-0022',d='15 to 19 Oct',nights=4,tel='+81-3-3441-3331',c='#2F6FD6',city='Tokyo')]
C={'Tokyo':'#2F6FD6','Kyoto':'#D6482F','Hiroshima':'#2E9E6B','Kyoto Pref.':'#1C9AA3','Nara & Osaka':'#E58A1F','Chiba':'#8A5BD6'}
DAYS=[('Wed 7 Oct','Tokyo','Tokyo','Arrival; hotel check-in in Shinjuku-ku',0),
('Thu 8 Oct','Tokyo','Tokyo','Asakusa: Senso-ji temple, Nakamise-dori; Shibuya: Shibuya Sky, Shibuya Crossing',0),
('Fri 9 Oct','Chiba','Urayasu','Tokyo DisneySea',0),
('Sat 10 Oct','Kyoto','Tokyo → Kyoto','Shinkansen to Kyoto; Arashiyama: Togetsukyo Bridge, Tenryu-ji, Bamboo Grove, Sagano scenic railway',1),
('Sun 11 Oct','Kyoto','Kyoto','Fushimi Inari Taisha, Kiyomizu-dera, Ninenzaka and Sannenzaka, Yasaka Shrine, Nishiki Market, Gion',1),
('Mon 12 Oct','Hiroshima','Day trip by car','Okunoshima (Rabbit Island), Takehara, Hiroshima Prefecture; alternative: Himeji Castle and Kobe',1),
('Tue 13 Oct','Kyoto Pref.','Day trip by car','Amanohashidate and the Ine funaya boat houses, northern Kyoto Prefecture',1),
('Wed 14 Oct','Nara & Osaka','Day trip by car','Nara Park and Todai-ji; Cup Noodles Museum, Ikeda; Osaka: Shinsaibashi and Dotonbori',1),
('Thu 15 Oct','Tokyo','Kyoto → Tokyo','Arashiyama Bamboo Grove; Shinkansen to Tokyo; Tokyo Skytree (alternative: Hakone, Kanagawa)',2),
('Fri 16 Oct','Tokyo','Tokyo','teamLab Planets, Toyosu; Nihonbashi; Shinjuku: Metropolitan Government Building, Omoide Yokocho',2),
('Sat 17 Oct','Tokyo','Tokyo','Ueno Park, Yanaka, Ameyoko; Ginza; Shinjuku',2),
('Sun 18 Oct','Tokyo','Tokyo','Ginza, Harajuku, Shibuya; packing',2),
('Mon 19 Oct','Tokyo','Departure','Haneda (two travellers, morning); Narita (one traveller, evening)',None)]
CSS="""
@page{size:A4;margin:0}*{box-sizing:border-box}body{margin:0;font-family:'Noto Sans','Noto Sans CJK JP','DejaVu Sans',sans-serif;color:#15181F;font-size:10pt;line-height:1.4;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:210mm;min-height:297mm;padding:14mm 14mm 12mm;position:relative;page-break-after:always}.page:last-child{page-break-after:auto}
.hero{background:linear-gradient(135deg,#15181F 0%,#2B3550 60%,#2F6FD6 100%);color:#fff;border-radius:14px;padding:16px 20px 14px;display:flex;justify-content:space-between;align-items:flex-end}
.hero h1{font-size:20pt;margin:0;line-height:1.1;letter-spacing:-.01em}.hero .k{font-size:9pt;opacity:.85;margin-top:5px}.hero .stamp{text-align:right;font-size:8.5pt;opacity:.9}.hero .stamp b{display:block;font-size:22pt;line-height:1}
h2{font-size:9pt;text-transform:uppercase;letter-spacing:.12em;color:#6B7280;margin:16px 0 7px;font-weight:700}
.trav{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:10px}.card{border:1px solid #E3E6EC;border-radius:12px;padding:10px 12px;background:#fff}.card.acc{border-left:5px solid var(--c)}
.lbl{font-size:7.5pt;text-transform:uppercase;letter-spacing:.08em;color:#6B7280;font-weight:700}.val{font-size:10.5pt;font-weight:600;margin-top:1px}.fill{display:block;border-bottom:1.2px solid #9AA3B2;height:16px;margin-top:4px}
.flt{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;margin-top:6px}.flt .big{font-size:15pt;font-weight:700;letter-spacing:-.01em;line-height:1}.flt .sm{font-size:8.5pt;color:#4B5563}.flt .arrow{font-size:16pt;color:#9AA3B2}
.pill{display:inline-block;font-size:7.5pt;font-weight:700;padding:2px 8px;border-radius:999px;color:#fff;background:var(--c);text-transform:uppercase;letter-spacing:.06em}
.stays{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}.stays .n{font-weight:700;font-size:10.5pt;margin:4px 0 2px;line-height:1.25}.stays .ja{font-size:9pt}.stays .en{font-size:8.5pt;color:#4B5563}.stays .tel{margin-top:6px;font-size:9.5pt;font-weight:600}.stays .dt{font-size:8.5pt;color:#4B5563}
.first{margin-top:8px;background:#FFF4D6;border-radius:10px;padding:8px 12px;font-size:9pt;border:1px solid #F3D98A}.first b{color:#7A4E00}
.with{display:grid;grid-template-columns:1fr 1fr;gap:10px}.with .card{padding:8px 12px}.with .n{font-weight:700}.with .sm{font-size:8.5pt;color:#4B5563}
.tl{position:relative;margin-top:4px}.tl:before{content:'';position:absolute;left:62px;top:6px;bottom:6px;width:2px;background:#E3E6EC}
.day{display:grid;grid-template-columns:52px 24px 1fr 150px;gap:0 8px;align-items:start;padding:7px 0;border-bottom:1px solid #F0F2F5}.day:last-child{border-bottom:0}
.day .d{font-weight:700;font-size:9pt;line-height:1.2;padding-top:2px}.day .d small{display:block;font-weight:500;color:#6B7280;font-size:7.5pt}
.day .dot{width:12px;height:12px;border-radius:50%;background:var(--c);margin:4px 0 0 4px;box-shadow:0 0 0 3px #fff,0 0 0 4px var(--c)}
.day .w{font-size:7.5pt;color:var(--c);font-weight:700;text-transform:uppercase;letter-spacing:.06em}.day .p{font-size:9.5pt;line-height:1.35}
.day .o{font-size:8.5pt;color:#4B5563;padding-top:2px}.day .o b{display:block;color:#15181F;font-size:8.5pt}
.foot{position:absolute;left:14mm;right:14mm;bottom:8mm;font-size:7.5pt;color:#6B7280;display:flex;justify-content:space-between}
.contact{display:grid;grid-template-columns:1fr 1fr 1.4fr;gap:10px}
"""
def page(k):
    t=T[k]; others=[v for kk,v in T.items() if kk!=k]
    stays=''.join(f"""<div class="card acc" style="--c:{s['c']}"><span class="pill">{s['city']} · {s['nights']} nights</span><div class="n">{E(s['n'])}</div><div class="ja" lang="ja">{s['ja']}</div><div class="en">{E(s['en'])}</div><div class="tel">{E(s['tel'])}</div><div class="dt">{s['d']} 2026</div></div>""" for s in STAYS)
    days=''
    for d,reg,where,places,si in DAYS:
        c=C[reg]; ov=STAYS[si]['n'] if si is not None else 'Departure'
        dd=d.split(' ',1)
        days+=f"""<div class="day" style="--c:{c}"><div class="d">{dd[1]}<small>{dd[0]}</small></div><div class="dot"></div><div><div class="w">{E(where) if where==reg else E(where)+' · '+E(reg)}</div><div class="p">{E(places)}</div></div><div class="o"><b>Overnight</b>{E(ov)}</div></div>"""
    return f"""<div class="page">
<div class="hero"><div><h1>Japan, 7 to 19 October 2026</h1><div class="k">Travel itinerary for immigration · tourism · three family members · all accommodation pre-booked, return flights held</div></div><div class="stamp"><b>{t['nights'].split()[0]}</b>nights</div></div>
<h2>Traveller</h2>
<div class="trav">
<div class="card"><div class="lbl">Name, as in passport</div><span class="fill"></span><div class="lbl" style="margin-top:8px">Passport number and nationality</div><span class="fill"></span><div class="lbl" style="margin-top:8px">Travelling from</div><div class="val">{E(t['frm'])}</div></div>
<div class="card"><div class="lbl">Arrival in Japan</div><div class="flt"><div><div class="big">{t['at']}</div><div class="sm">{t['ad']}</div></div><div class="arrow">→</div><div><div class="val" style="font-size:9.5pt">{E(t['ain'])}</div></div></div><div class="lbl" style="margin-top:10px">Flight number</div><span class="fill"></span></div>
<div class="card"><div class="lbl">Departure from Japan</div><div class="flt"><div><div class="big">{t['dt']}</div><div class="sm">{t['dd']}</div></div><div class="arrow">→</div><div><div class="val" style="font-size:9.5pt">{E(t['dout'])}</div></div></div><div class="lbl" style="margin-top:10px">Flight number</div><span class="fill"></span></div>
</div>
<h2>Travelling with</h2>
<div class="with">{''.join(f'<div class="card"><div class="n">{E(o["nm"])} <span class="sm">from {E(o["frm"])}</span></div><div class="sm">Arrives {E(o["ain"])}, {o["ad"]} {o["at"]} · departs {E(o["dout"])}, {o["dd"]} {o["dt"]}</div></div>' for o in others)}</div>
<h2>Accommodation, all pre-booked</h2>
<div class="stays">{stays}</div>
<div class="first"><b>First night for all three:</b> Mitsui Garden Hotel Jingugaien Tokyo Premier, 11-3 Kasumigaoka-machi, Shinjuku-ku, Tokyo 160-0013, Tel +81-3-5786-1531. Rental car (Nissan Rent a Car, Kyoto Station) 11 to 14 October for day trips from Kyoto; international driving permits held.</div>
<h2>Contact</h2>
<div class="contact"><div class="card"><div class="lbl">Mobile</div><span class="fill"></span></div><div class="card"><div class="lbl">Email</div><span class="fill"></span></div><div class="card"><div class="lbl">Home address</div><span class="fill"></span></div></div>
<div class="foot"><span>{E(t['nm'])} · Japan 2026</span><span>Page 1 of 2</span></div>
</div>
<div class="page">
<h2 style="margin-top:0">Day by day</h2>
<div class="tl">{days}</div>
<div class="foot"><span>Prepared from the family travel planner at ashikm22.github.io/japan-2026, updated 1 October 2026. Times and places may change on the day; accommodation and flights are fixed.</span><span>Page 2 of 2</span></div>
</div>"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page()
        for k in T:
            doc=f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{page(k)}</body></html>"
            path=os.path.join(ROOT,'docs',f'itinerary-{k}.html'); open(path,'w',encoding='utf8').write(doc)
            await pg.goto('file://'+path); await pg.wait_for_timeout(300)
            await pg.pdf(path=os.path.join(ROOT,'docs',f'itinerary-{k}.pdf'),format='A4',print_background=True,prefer_css_page_size=True)
            os.remove(path); print('built',k)
        await b.close()
asyncio.run(main())

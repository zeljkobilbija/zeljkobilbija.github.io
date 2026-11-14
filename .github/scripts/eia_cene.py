"""
Nedeljne prosečne cene goriva u SAD (EIA, U.S. Energy Information Administration, javni podaci)
→ interstate/cene.json za aplikaciju Interstate Info.

EIA objavljuje ponedeljkom (praznikom utorkom); GitHub Action ovo pokreće utorkom i sredom.
Oblasti: US, PADD podregioni (R1X New England, R1Y Central Atlantic, R1Z Lower Atlantic, R20 Midwest,
R30 Gulf Coast, R40 Rocky Mountain, R50 West Coast, R5XCA West Coast bez Kalifornije) i 9 država
(SCA, SCO, SFL, SMA, SMN, SNY, SOH, STX, SWA). Cene u $/gal: r regular, m midgrade, p premium, d dizel.

  pip install xlrd && python .github/scripts/eia_cene.py
"""
import json, os, sys, urllib.request
import xlrd

OBLASTI = ['NUS', 'R1X', 'R1Y', 'R1Z', 'R20', 'R30', 'R40', 'R50', 'R5XCA',
           'SCA', 'SCO', 'SFL', 'SMA', 'SMN', 'SNY', 'SOH', 'STX', 'SWA']
KOLONE = {'r': 'Regular All Formulations', 'm': 'Midgrade All Formulations',
          'p': 'Premium All Formulations', 'd': 'No 2 Diesel Retail Prices'}
CILJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'interstate', 'cene.json')


def oblast(kod):
    url = f'https://www.eia.gov/dnav/pet/xls/PET_PRI_GND_DCUS_{kod}_W.xls'
    zahtev = urllib.request.Request(url, headers={'User-Agent': 'InterstateInfo-cene/1.0'})
    with urllib.request.urlopen(zahtev, timeout=60) as r:
        knjiga = xlrd.open_workbook(file_contents=r.read())
    s = knjiga.sheet_by_name('Data 1')
    o, datum = {}, None
    for j in range(1, s.ncols):
        naslov = str(s.cell_value(2, j))
        for k, tekst in KOLONE.items():
            if tekst in naslov and k not in o:
                for i in range(s.nrows - 1, 2, -1):  # poslednja nedelja sa vrednošću
                    v = s.cell_value(i, j)
                    if v != '':
                        o[k] = round(float(v), 3)
                        d = xlrd.xldate_as_tuple(s.cell_value(i, 0), knjiga.datemode)[:3]
                        datum = max(datum or d, d)
                        break
    return o, datum


def main():
    rez = {'izvor': 'U.S. Energy Information Administration (EIA)', 'jedinica': 'USD/gal', 'oblasti': {}}
    najnoviji = None
    for kod in OBLASTI:
        try:
            o, d = oblast(kod)
        except Exception as e:  # jedna oblast koja ne radi ne sme da obori sve
            print(f'{kod}: greška {e}', file=sys.stderr)
            continue
        if o:
            rez['oblasti']['US' if kod == 'NUS' else kod] = o
            najnoviji = max(najnoviji or d, d)
    if len(rez['oblasti']) < 10:
        sys.exit(f'premalo oblasti ({len(rez["oblasti"])}), cene.json se ne menja')
    rez['nedelja'] = '%04d-%02d-%02d' % najnoviji
    os.makedirs(os.path.dirname(CILJ), exist_ok=True)
    with open(CILJ, 'w', encoding='utf-8') as f:
        json.dump(rez, f, separators=(',', ':'))
    print(f"cene.json: nedelja {rez['nedelja']}, oblasti {len(rez['oblasti'])}, US {rez['oblasti'].get('US')}")


if __name__ == '__main__':
    main()

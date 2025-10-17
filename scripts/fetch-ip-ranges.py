#!/usr/bin/env python3
import json, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

def fetch_bgpview(asn: int):
    url = f'https://api.bgpview.io/asn/{asn}/prefixes'
    req = Request(url, headers={'User-Agent':'Mozilla/5.0'})
    try:
        with urlopen(req, timeout=30) as r:
            data = json.load(r)
        v4 = [p['prefix'] for p in data.get('data',{}).get('ipv4_prefixes',[])]
        v6 = [p['prefix'] for p in data.get('data',{}).get('ipv6_prefixes',[])]
        return v4, v6
    except HTTPError as e:
        if e.code == 403:
            print(f'WARN: BGPView blocked ASN {asn} (HTTP {e.code})', file=sys.stderr)
        else:
            print(f'ERROR: BGPView ASN {asn} failed: {e}', file=sys.stderr)
        return [], []

def fetch_whois(asn: str):
    import subprocess
    try:
        cmd = ['whois', '-h', 'whois.radb.net', '--', '-i', 'origin', asn]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            v4, v6 = [], []
            for line in result.stdout.split('\n'):
                if line.startswith('route:'):
                    v4.append(line.split(':')[1].strip())
                elif line.startswith('route6:'):
                    v6.append(line.split(':')[1].strip())
            return v4, v6
    except Exception as e:
        print(f'ERROR: WHOIS ASN {asn} failed: {e}', file=sys.stderr)
    return [], []

def fetch_ipinfo(asn: int, token: str = None):
    if not token:
        return [], []
    url = f'https://ipinfo.io/AS{asn}?token={token}'
    req = Request(url, headers={'User-Agent':'Mozilla/5.0'})
    try:
        with urlopen(req, timeout=30) as r:
            data = json.load(r)
        v4, v6 = set(), set()
        for p in data.get('prefixes', []):
            nb = p.get('netblock') or p.get('prefix')
            if nb and '/' in nb:
                v4.add(nb)
        for p in data.get('prefixes6', []):
            nb = p.get('netblock') or p.get('prefix')
            if nb and '/' in nb:
                v6.add(nb)
        return list(v4), list(v6)
    except Exception as e:
        print(f'ERROR: IPInfo ASN {asn} failed: {e}', file=sys.stderr)
        return [], []

def fetch_all(asn: int, token: str = None):
    methods = [
        ('BGPView', lambda: fetch_bgpview(asn)),
        ('WHOIS RADB', lambda: fetch_whois(f'AS{asn}')),
    ]
    if token:
        methods.insert(0, ('IPInfo', lambda: fetch_ipinfo(asn, token)))
    
    all_v4, all_v6 = set(), set()
    for name, func in methods:
        try:
            v4, v6 = func()
            all_v4.update(v4)
            all_v6.update(v6)
            print(f'{name} ASN {asn}: {len(v4)} IPv4, {len(v6)} IPv6')
        except Exception as e:
            print(f'ERROR: {name} ASN {asn}: {e}', file=sys.stderr)
    
    return sorted(all_v4), sorted(all_v6)

# Telegram ASNs
telegram_asns = [62014, 44907, 211157]  # Telegram Messenger Inc, Telegram LLC, Telegram Messenger LLP
viber_asns = [58057]  # Viber Media S.à r.l.

root = Path('/home/guest/realistic-demo-pretamane/docs')
root.mkdir(parents=True, exist_ok=True)

# Fetch Telegram ranges
telegram_v4, telegram_v6 = set(), set()
for asn in telegram_asns:
    v4, v6 = fetch_all(asn)
    telegram_v4.update(v4)
    telegram_v6.update(v6)

# Fetch Viber ranges
viber_v4, viber_v6 = fetch_all(viber_asns[0])

# Write files
(root/'telegram-ipv4.txt').write_text('\n'.join(sorted(telegram_v4)) + '\n')
(root/'telegram-ipv6.txt').write_text('\n'.join(sorted(telegram_v6)) + '\n')
(root/'viber-ipv4.txt').write_text('\n'.join(sorted(viber_v4)) + '\n')
(root/'viber-ipv6.txt').write_text('\n'.join(sorted(viber_v6)) + '\n')

print(f'Telegram: {len(telegram_v4)} IPv4, {len(telegram_v6)} IPv6')
print(f'Viber: {len(viber_v4)} IPv4, {len(viber_v6)} IPv6')

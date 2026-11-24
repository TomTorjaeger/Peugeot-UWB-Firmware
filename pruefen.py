#!/usr/bin/env python3
"""Prueft die veroeffentlichte Firmware: Groesse, SHA-256, Version und ECDSA-Signatur gegen schluessel.txt.

    pip install cryptography
    python pruefen.py
"""
import hashlib
import json
import os
import re
import struct
import sys

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

HERE = os.path.dirname(os.path.abspath(__file__))
TRAILER = 88


def keys():
    out = {}
    with open(os.path.join(HERE, "schluessel.txt"), encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                name, kid, pub = line.split()
                pub = bytes.fromhex(pub)
                assert hashlib.sha256(pub).hexdigest()[:16] == kid, "Schluessel-ID passt nicht: " + name
                out[bytes.fromhex(kid)] = (name, pub)
    return out


def check(entry, known):
    path = os.path.join(HERE, entry["datei"])
    with open(path, "rb") as f:
        blob = f.read()
    if len(blob) != entry["groesse"]:
        return "Groesse falsch"
    if hashlib.sha256(blob).hexdigest() != entry["sha256"]:
        return "SHA-256 falsch"
    t = blob[-TRAILER:]
    if t[:8] != b"KEYLSIG1":
        return "nicht signiert"
    img_len, secver = struct.unpack_from("<II", t, 8)
    if img_len != len(blob) - TRAILER:
        return "Laenge im Anhang falsch"
    m = re.search(rb"#KEYLESS-FW:uwbfira-([0-9A-Za-z.\-]+)#", blob[:img_len])
    if not m or m.group(1).decode() != entry["version"]:
        return "Version in der Datei passt nicht"
    if t[16:24] not in known:
        return "unbekannter Schluessel " + t[16:24].hex()
    name, pub = known[t[16:24]]
    sig = encode_dss_signature(int.from_bytes(t[24:56], "big"), int.from_bytes(t[56:88], "big"))
    try:
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), pub).verify(
            sig, blob[:img_len] + t[:24], ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return "SIGNATUR FALSCH"
    return "ok (Schluessel %s, Sicherheitsstand %d)" % (name, secver)


def main():
    with open(os.path.join(HERE, "firmware.json"), encoding="utf-8") as f:
        idx = json.load(f)
    known = keys()
    bad = 0
    entries = [(k, idx.get(k)) for k in ("stabil", "beta")] + [("alt", v) for v in idx.get("versionen", [])]
    seen = set()
    for kanal, e in entries:
        if not e or e["datei"] in seen:
            continue
        seen.add(e["datei"])
        e = dict(e)
        e.setdefault("groesse", os.path.getsize(os.path.join(HERE, e["datei"])))
        res = check(e, known)
        bad += not res.startswith("ok")
        print("%-7s %-10s %s: %s" % (kanal, e["version"], e["datei"], res))
    if not seen:
        print("Noch keine Firmware veroeffentlicht.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

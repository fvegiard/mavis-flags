#!/usr/bin/env python3
"""
Mavis browser-flag manager — applies an audited keep/kill policy to
Chromium-based browser flags (Edge / Chrome) without touching anything else.

How it works:
  Chromium stores flags in "<User Data>/Local State" as
  browser.enabled_labs_experiments = ["flag-name@1", ...]
  where @1 = Enabled, @2 = Disabled. This script rewrites only that array.

Usage (on your Windows PC, all browsers CLOSED first):
  python mavis_flags.py                  -> applies policy to Edge
  python mavis_flags.py --chrome         -> also applies to Chrome
  python mavis_flags.py --list           -> just list current non-default flags
  python mavis_flags.py --user-data-dir "C:\\Path\\To\\User Data"

Safety:
  - Refuses to run while msedge.exe / chrome.exe are alive (they would
    overwrite Local State on exit).
  - Always backs up Local State to Local State.mavis-bak-<timestamp> first.
  - Only touches the enabled_labs_experiments array; everything else in the
    file is preserved byte-for-byte in meaning (json round-trip).
  - Python's json module preserves integer precision (unlike PowerShell's
    ConvertFrom-Json), so the rest of the file survives intact.
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys

# ---------------------------------------------------------------- policy ---
# Flags forced to Disabled (@2): conflicts, security/privacy risks,
# data-loss risks, silent perf costs. Everything else is left untouched.
KILL = [
    # -- real conflicts --
    "edge-studio-ntp",                 # fights edge-ntp-composer (keep Composer)
    "edge-onejs-ntp",                  # fights edge-ntp-composer (keep Composer)
    "edge-studio-ntp-component-extension",  # orphaned without studio-ntp
    # -- security / privacy --
    "unsafely-treat-insecure-origin-as-secure",
    "enable-unsafe-webgpu",
    "enable-isolated-web-app-dev-mode",     # allows UNVERIFIED isolated web apps
    "webtransport-developer-mode",          # skips certificate validation
    "edge-devtools-wdp-remote-debugging",   # remote debugging over LAN
    "edge-ad-selection-debug-token",        # may log browsing history
    # -- data-loss risk ("no data is migrated, use at your own peril") --
    "dom-storage-sqlite",
    "idb-sqlite-backing-store",
    # -- silent perf / disk costs --
    "enable-gpu-service-logging",       # logs every GL call
    "enable-network-logging-to-file",   # writes netlog.json nonstop
]

# Flags removed entirely (-> Default). Used for multi-choice flags where
# forcing Disabled could misbehave; removal restores the default choice.
RESET_TO_DEFAULT = [
    "edge-emulate-windows-sku",        # was emulating "Server" SKU
]

WHY = {
    "edge-studio-ntp": "conflict: 3 NTP architectures enabled, keeping Unified Composer",
    "edge-onejs-ntp": "conflict: 3 NTP architectures enabled, keeping Unified Composer",
    "edge-studio-ntp-component-extension": "orphaned without edge-studio-ntp",
    "unsafely-treat-insecure-origin-as-secure": "security: treats insecure origins as secure",
    "enable-unsafe-webgpu": "security: flag warns it can expose holes to websites",
    "enable-isolated-web-app-dev-mode": "security: allows unverified isolated web apps",
    "webtransport-developer-mode": "security: skips certificate validation",
    "edge-devtools-wdp-remote-debugging": "security: remote debugging over local network",
    "edge-ad-selection-debug-token": "privacy: ad auction debugging may log browsing history",
    "dom-storage-sqlite": "data-loss risk: no migration from existing storage",
    "idb-sqlite-backing-store": "data-loss risk: no migration from existing storage",
    "enable-gpu-service-logging": "perf: logs every GL driver call",
    "enable-network-logging-to-file": "perf/privacy: writes netlog.json continuously",
    "edge-emulate-windows-sku": "was emulating Windows Server SKU; back to default",
}


def find_targets(args):
    local_app = os.environ.get("LOCALAPPDATA", "")
    targets = []
    if args.user_data_dir:
        targets.append(("custom", args.user_data_dir))
    else:
        edge = os.path.join(local_app, "Microsoft", "Edge", "User Data")
        if os.path.isdir(edge):
            targets.append(("Edge", edge))
        if args.chrome:
            chrome = os.path.join(local_app, "Google", "Chrome", "User Data")
            if os.path.isdir(chrome):
                targets.append(("Chrome", chrome))
    return targets


def browsers_running():
    """Refuse to run while a Chromium browser could overwrite Local State."""
    if os.name != "nt":
        return []
    try:
        out = subprocess.run(["tasklist"], capture_output=True, text=True,
                             timeout=15).stdout.lower()
    except Exception:
        return []
    return [p for p in ("msedge.exe", "chrome.exe", "brave.exe", "opera.exe",
                        "vivaldi.exe", "arc.exe")
            if p in out]


def load_experiments(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    browser = data.setdefault("browser", {})
    exps = browser.get("enabled_labs_experiments", [])
    cur = {}
    for e in exps:
        name, sep, state = e.rpartition("@")
        if sep:
            cur[name] = state
        else:  # no suffix -> treat as enabled
            cur[e] = "1"
    return data, cur


def apply_policy(cur):
    changed = []
    for name in KILL:
        if cur.get(name) != "2":
            cur[name] = "2"
            changed.append(("DISABLED", name, WHY.get(name, "")))
    for name in RESET_TO_DEFAULT:
        if name in cur:
            del cur[name]
            changed.append(("RESET-TO-DEFAULT", name, WHY.get(name, "")))
    return changed


def process_target(label, user_data_dir, list_only=False):
    ls_path = os.path.join(user_data_dir, "Local State")
    if not os.path.isfile(ls_path):
        print(f"[{label}] no Local State found at {ls_path} - skipping")
        return 0
    data, cur = load_experiments(ls_path)

    if list_only:
        print(f"[{label}] {len(cur)} non-default flags:")
        for name in sorted(cur):
            state = {"1": "Enabled", "2": "Disabled"}.get(cur[name],
                                                          f"choice({cur[name]})")
            print(f"    [{state}] {name}")
        return 0

    changed = apply_policy(cur)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{ls_path}.mavis-bak-{stamp}"
    shutil.copy2(ls_path, backup)

    data["browser"]["enabled_labs_experiments"] = [
        f"{name}@{state}" for name, state in sorted(cur.items())
    ]
    # Compact JSON, like Chromium itself writes.
    with open(ls_path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)

    print(f"[{label}] backup -> {backup}")
    if changed:
        print(f"[{label}] {len(changed)} change(s):")
        for action, name, why in changed:
            print(f"    {action:16} {name}  ({why})")
    else:
        print(f"[{label}] already clean - nothing to change")
    return len(changed)


def main():
    ap = argparse.ArgumentParser(description="Mavis browser-flag manager")
    ap.add_argument("--chrome", action="store_true",
                    help="also apply to Chrome (default: Edge only)")
    ap.add_argument("--user-data-dir", default="",
                    help="custom Chromium user-data dir (for a 3rd browser)")
    ap.add_argument("--list", action="store_true",
                    help="only list current non-default flags, change nothing")
    ap.add_argument("--skip-process-check", action="store_true",
                    help="bypass the running-browser check (testing only)")
    args = ap.parse_args()

    if not args.skip_process_check and not args.list:
        running = browsers_running()
        if running:
            print("Close these browsers first (they would overwrite the "
                  f"changes on exit): {', '.join(running)}")
            sys.exit(1)

    targets = find_targets(args)
    if not targets:
        print("No browser user-data dir found. Pass --user-data-dir "
              "explicitly.")
        sys.exit(1)

    total = 0
    for label, d in targets:
        total += process_target(label, d, list_only=args.list)
    if not args.list:
        print(f"\nDone - {total} change(s). Relaunch the browser.")


if __name__ == "__main__":
    main()

# mavis-flags

One-shot manager for Chromium/Edge/Chrome experimental flags (`edge://flags`, `chrome://flags`).

## What it does

Reads your browser's `Local State` (`browser.enabled_labs_experiments`) and applies an audited policy:

- **Disables** conflicting / risky / costly flags — e.g. the three-way New Tab Page architecture fight (`edge-studio-ntp`, `edge-onejs-ntp` vs `edge-ntp-composer`), security red flags (`unsafely-treat-insecure-origin-as-secure`, `enable-unsafe-webgpu`, `enable-isolated-web-app-dev-mode`, …), data-loss risks (`dom-storage-sqlite`, `idb-sqlite-backing-store`), silent perf drains (`enable-gpu-service-logging`, `enable-network-logging-to-file`)
- **Resets** multi-choice flags to default (e.g. `edge-emulate-windows-sku`)
- **Leaves everything else untouched**

## Usage (Windows, all browsers closed first)

```powershell
python mavis-flags.py            # Edge
python mavis-flags.py --chrome   # also Chrome
python mavis-flags.py --list     # just list current non-default flags
```

Always backs up `Local State` first (`Local State.mavis-bak-<timestamp>`).
Idempotent — re-running changes nothing.

## The policy

Edit the `KILL` / `RESET_TO_DEFAULT` lists at the top of the script to make it yours. Each entry carries a `WHY` note explaining the reason.

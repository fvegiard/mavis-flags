# Flags audit — Edge 155.0.4283.33 (2026-10-02)

Source: full `edge://flags` dump (~110 non-default flags). Policy applied by `mavis-flags.py`.

## Keep: Unified Composer NTP

Three New Tab Page architectures were enabled simultaneously — they fight over the same surface:

| Flag | Verdict |
|---|---|
| `edge-ntp-composer` (Unified Composer) | **KEEP** — matches the Copilot / AI-search / omnibox stack |
| `edge-studio-ntp` | DISABLE — conflict |
| `edge-onejs-ntp` | DISABLE — conflict |
| `edge-studio-ntp-component-extension` | DISABLE — orphaned without studio-ntp |

## Disable: security / privacy red flags

| Flag | Why |
|---|---|
| `unsafely-treat-insecure-origin-as-secure` | treats insecure origins as secure |
| `enable-unsafe-webgpu` | flag warns it can expose security holes to websites |
| `enable-isolated-web-app-dev-mode` | allows **unverified** isolated web apps |
| `webtransport-developer-mode` | skips certificate validation for WebTransport |
| `edge-devtools-wdp-remote-debugging` | remote debugging over the local network |
| `edge-ad-selection-debug-token` | ad auction debugging may log browsing history |

## Disable: data-loss risk

| Flag | Why |
|---|---|
| `dom-storage-sqlite` | "no data is migrated from existing backing stores — use at your own peril" |
| `idb-sqlite-backing-store` | same — IndexedDB starts fresh |

## Disable: silent perf / disk costs

| Flag | Why |
|---|---|
| `enable-gpu-service-logging` | logs every GL driver call |
| `enable-network-logging-to-file` | writes `netlog.json` continuously |

## Reset to default

| Flag | Why |
|---|---|
| `edge-emulate-windows-sku` | was emulating the **Server** SKU — sites saw a Windows Server client |

## Deliberately kept

- **WASM trio** (`enable-webassembly-baseline` + `enable-webassembly-lazy-compilation` + `enable-webassembly-tiering`) — designed as a tiered-compilation stack, not a conflict.
- **GPU rasterization** + **zero-copy rasterizer** + **trees-in-viz** — compositor changes that compose by design.
- **WebNN stack** (`web-machine-learning-neural-network` + `experimental-web-machine-learning-neural-network` + `webnn-onnxruntime`) — enables ONNX Runtime inference on CPU/GPU/NPU via the WebNN API.
- **On-device Phi-mini APIs** (`edge-llm-prompt-api-for-phi-mini`, summarizer, writer, rewriter) + debug/perf flags.
- **ANGLE backend** left at Default (D3D11) — the most tested path on Windows/NVIDIA; OpenGL/Vulkan only as troubleshooting options.
- Everything else (~95 flags): UI, Copilot, DevTools, PWA, Cast — no conflicts, just surface area.

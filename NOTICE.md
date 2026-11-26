# NOTICE

The MIT license in [`LICENSE`](LICENSE) covers the plugin's source code **and the
two audio clips it embeds**, both of which the author created.

## Coin sound effects

| Sample key | Source recording | Origin |
| --- | --- | --- |
| `reward` | `cash-register-cha-ching` | author's own recording |
| `drop` | `原创金币掉落_短版` | author's own recording |

Both clips are trimmed, limited and downsampled to 22.05 kHz mono, then embedded
as base64 WAV payloads inside `client.js` (see `assets-src/process_samples.py`).
No third-party audio is redistributed with this repository or with a build of it.

> Earlier development builds embedded two clips downloaded from aigei.com. Those
> clips are no longer part of this repository, of the embedded payloads, or of
> any published artifact.

## Dependency

`@deepseek-ai/schemastery` (declared dependency, MIT) provides the configuration
schema used by the Host half. It is installed by the package manager and is not
vendored in this repository.

/**
 * Write the processed base64 payloads from assets-src into client.js.
 *
 * The plugin ships its coin sound embedded in the client bundle, because the
 * client module loader serves one file per package and the asset route only
 * serves images. This script is the reproducible form of that step.
 *
 * Run: node assets-src/embed_samples.mjs
 */
import { readFile, writeFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const clientPath = join(here, '..', 'client.js')

/** Sample key in COIN_SAMPLES mapped to its generated payload file. */
const payloads = {
  reward: join(here, 'coin-reward.b64'),
  drop: join(here, 'coin-drop.b64'),
}

let source = await readFile(clientPath, 'utf8')

for (const [key, file] of Object.entries(payloads)) {
  let payload
  try {
    payload = (await readFile(file, 'utf8')).trim()
  } catch {
    throw new Error(`missing ${file} — run assets-src/process_samples.py first`)
  }
  if (!/^[A-Za-z0-9+/=]+$/.test(payload) || payload.length < 1000) {
    throw new Error(`${file} does not look like a base64 WAV payload`)
  }
  const slot = new RegExp(`(\\b${key}: ')[A-Za-z0-9+/=]+(')`)
  if (!slot.test(source)) {
    throw new Error(`client.js has no "${key}" slot in COIN_SAMPLES`)
  }
  source = source.replace(slot, `$1${payload}$2`)
  console.log(`${key}: ${payload.length} base64 chars embedded`)
}

await writeFile(clientPath, source, 'utf8')
console.log(`client.js updated (${Buffer.byteLength(source)} bytes)`)

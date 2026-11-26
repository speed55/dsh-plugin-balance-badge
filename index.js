/**
 * Host half of the account balance badge.
 *
 * It declares the live preferences — the badge switch, the spend notice and its
 * threshold, and the balance refresh interval — and nothing else. The
 * `.volatile()` marker is what makes the fields editable from the browser: DSH
 * projects volatile fields into the Host settings document, so the Client half
 * reads and writes them through `ctx.configForms.get('balance-badge')` without a
 * restart. The values are persisted by DSH in the profile patch.
 *
 * The balance itself is never read here: the shipped account plugin owns the
 * credential and exposes it to the browser as `remote.account.getBalance`.
 */
import z from '@deepseek-ai/schemastery'

/** Live preferences projected to the browser. */
export const Config = z.object({
  /** Whether the sidebar footer shows the account balance. */
  showBalance: z.boolean().default(true).volatile(),
  /** Whether spending one threshold plays the frame-wide notice. */
  spendNotice: z.boolean().default(true).volatile(),
  /** Money spent between two notices, in the wallet's own currency. */
  noticeStep: z.number().default(5).min(0.01).max(1000).volatile(),
  /** How many coins and bills the rain drops, from sparse (0) to dense (100). */
  rainDensity: z.number().default(0).min(0).max(100).volatile(),
  /** Whether the notice also plays the coin sound. */
  soundNotice: z.boolean().default(true).volatile(),
  /** Which embedded coin recording the notice plays. */
  soundSample: z.union(['reward', 'drop']).default('reward').volatile(),
  /** Balance refresh interval in seconds while the page is visible; the client
   * backs off further while nothing changes or after a failed read. */
  refreshSeconds: z.number().default(60).min(15).max(600).volatile(),
})

/**
 * Nothing to mount: the Host owns configuration only.
 */
export function apply() {}

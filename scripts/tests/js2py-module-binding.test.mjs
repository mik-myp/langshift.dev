import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { spawnSync } from 'node:child_process'

test('L06 comparison: ESM imports are live bindings, not Python from bindings', () => {
  const directory = mkdtempSync(join(tmpdir(), 'js2py-esm-'))
  try {
    writeFileSync(join(directory, 'settings.mjs'), `
export let budget = 20;
export function updateBudget(value) { budget = value; }
`)
    writeFileSync(join(directory, 'probe.mjs'), `
import { budget, updateBudget } from './settings.mjs';
console.log(budget);
updateBudget(40);
console.log(budget);
try { budget = 7; } catch (error) { console.log(error.name); }
`)
    const result = spawnSync(process.execPath, ['probe.mjs'], { cwd: directory, encoding: 'utf8', timeout: 5000 })
    assert.equal(result.status, 0, result.stderr)
    assert.equal(result.stdout, '20\n40\nTypeError\n')
    assert.equal(Math.ceil(2.1), 3)
  } finally {
    rmSync(directory, { recursive: true, force: true })
  }
})

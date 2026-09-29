import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import vm from 'node:vm'
import ts from 'typescript'

const source = ts.createSourceFile(
  'python-editor.tsx',
  readFileSync(new URL('../../components/python-editor.tsx', import.meta.url), 'utf8'),
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TSX,
)
let initializer
function visit(node) {
  if (ts.isVariableDeclaration(node) && node.name.getText(source) === 'runJavascriptCode') {
    initializer = node.initializer.getText(source)
  }
  ts.forEachChild(node, visit)
}
visit(source)
assert.ok(initializer, 'Test the actual editor handler, not a copied implementation')
const javascript = ts.transpileModule(`globalThis.run = ${initializer}`, {
  compilerOptions: { target: ts.ScriptTarget.ES2022 },
}).outputText

function run(code, canRun = true) {
  const originalLog = () => {}
  const state = { output: undefined, error: undefined }
  const context = {
    javascriptCode: code,
    canRun,
    console: { log: originalLog },
    setOutput: (value) => { state.output = value },
    setError: (value) => { state.error = value },
    t: { editor: { executionError: 'Execution failed' } },
  }
  vm.createContext(context)
  vm.runInContext(javascript, context)
  context.run()
  assert.equal(context.console.log, originalLog, 'console.log must always be restored')
  return state
}

test('captures synchronous output and restores console', () => {
  assert.deepEqual(run('console.log("ok")'), { output: 'ok', error: '' })
})
test('restores console after a thrown error', () => {
  assert.equal(run('throw new Error("lesson failure")').error, 'lesson failure')
})
test('display-only snippets cannot execute', () => {
  assert.deepEqual(run('throw new Error("must not run")', false), { output: undefined, error: undefined })
})
test('an empty JavaScript side is not evaluated as TypeScript', () => {
  assert.deepEqual(run(''), { output: undefined, error: undefined })
})

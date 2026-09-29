import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'
import { test } from 'node:test'
import ts from 'typescript'
import { highlight } from 'codehike/code'

const source = readFileSync(new URL('../../components/code-client.tsx', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
}).outputText

function renderInitialCodeClient(codeblock, highlighted) {
  const exported = {}
  const jsx = (type, props) => ({ type, props })
  const mocks = {
    'react/jsx-runtime': { jsx, jsxs: jsx },
    react: { useState: () => [false, () => {}] },
    'codehike/code': { Pre: 'codehike-pre' },
    './annotations/callout': { callout: {} },
    'lucide-react': { Check: 'check-icon', Copy: 'copy-icon' },
  }
  vm.runInNewContext(compiled, {
    exports: exported,
    require: name => {
      assert.ok(name in mocks, `Unexpected component import: ${name}`)
      return mocks[name]
    },
  })
  return exported.CodeClient({ codeblock, highlighted })
}

function findPre(node) {
  if (!node || typeof node !== 'object') return undefined
  if (node.type === 'codehike-pre') return node
  const children = node.props?.children
  for (const child of Array.isArray(children) ? children : [children]) {
    const match = findPre(child)
    if (match) return match
  }
}

for (const [lang, value] of [['text', 'Hello!\nPython'], ['python', 'print("Hello!")']]) {
  test(`${lang} blocks keep the theme foreground instead of inheriting page text`, async () => {
    const codeblock = { value, lang, meta: '' }
    const highlighted = await highlight(codeblock, 'github-dark')
    const pre = findPre(renderInitialCodeClient(codeblock, highlighted))
    assert.ok(pre, 'the actual CodeClient must render a Pre component')
    assert.equal(pre.props.style.color, highlighted.style.color)
    assert.equal(pre.props.style.color.toLowerCase(), '#c9d1d9')
    assert.strictEqual(pre.props.code, highlighted, 'preserve language-specific token colors')
  })
}

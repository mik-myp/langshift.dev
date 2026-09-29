import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'

const lessonDirectory = new URL('../../content/docs/js2py/', import.meta.url)

test('L07: actual three-locale JSON comparison and explicit non-finite difference', () => {
  const expected = '{\n  "title": "学习",\n  "done": false\n}\n学习\n'
  const sources = ['', '.zh-cn', '.zh-tw'].map(locale => {
    const text = readFileSync(new URL(`module-07-data-automation${locale}.mdx`, lessonDirectory), 'utf8')
    const source = text.match(/```javascript case=json-text-comparison\n([\s\S]*?)```/)?.[1]
    assert.ok(source, `Missing actual comparison in ${locale || 'en'}`)
    const result = spawnSync(process.execPath, ['--input-type=module', '-e', source], {
      encoding: 'utf8', timeout: 5000,
    })
    assert.equal(result.status, 0, result.stderr)
    assert.equal(result.stderr, '')
    assert.equal(result.stdout, expected)
    return source
  })
  assert.equal(sources[0], sources[1])
  assert.equal(sources[0], sources[2])
  assert.equal(JSON.stringify(NaN), 'null')
  assert.equal(JSON.stringify(Infinity), 'null')
  assert.equal(JSON.parse('{"title":"first","title":"second"}').title, 'second')
})

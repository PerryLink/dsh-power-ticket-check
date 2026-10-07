import { readFile, readdir } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { loadRuleset } from '../src/shared/ruleset.ts'
import { parseMaterial } from '../src/parse.ts'
import { runCheck } from '../src/check.ts'
import { buildView } from '../src/view.ts'
import { findForbiddenWording } from '../src/shared/wording.ts'
import { addDays, diffDays, parseWallClock } from '../src/shared/datetime.ts'
import { parseYaml } from '../src/shared/yaml.ts'
import { Config as ConfigSchema } from '../src/config.ts'
import { inject, name as pluginName, resolvePackageFile, TOOL_NAME } from '../src/index.ts'
import type { Report } from '../src/shared/report.ts'
import type { CheckOptions } from '../src/check.ts'

const here = dirname(fileURLToPath(import.meta.url))
const packageRoot = resolve(here, '..')
const rulesPath = join(packageRoot, 'rules', 'power-ticket-check.yaml')
const fixturesRoot = join(here, 'fixtures')
const CHECKED_AT = '2026-10-06T00:00:00.000Z'

interface CaseFile {
  ruleId: string
  configure?: Record<string, Record<string, unknown>>
  pairs: { name: string; material: string; expect: { ruleId: string; count: number } }[]
}

async function loadPack() {
  return loadRuleset(await readFile(rulesPath, 'utf8'))
}

function runOptions(overrides: Partial<CheckOptions> = {}): CheckOptions {
  return { plugin: pluginName, checkedAt: CHECKED_AT, disabledRules: [], onlyRules: [], ...overrides }
}

function withConfiguration(ruleset: Awaited<ReturnType<typeof loadPack>>, configure: CaseFile['configure']) {
  if (configure === undefined) return ruleset
  return {
    ...ruleset,
    rules: ruleset.rules.map((rule) =>
      configure[rule.id] === undefined ? rule : { ...rule, params: { ...rule.params, ...configure[rule.id] } },
    ),
  }
}

async function runFixture(materialText: string, target: string, configure?: CaseFile['configure']): Promise<Report> {
  const ruleset = withConfiguration(await loadPack(), configure)
  const kinds = configure?.['PT-002']?.ticketKinds
  return runCheck(
    parseMaterial(materialText, target),
    ruleset,
    runOptions(Array.isArray(kinds) ? { ticketKinds: kinds as string[] } : {}),
  )
}

function issuesOf(report: Report, ruleId: string) {
  return report.issues.filter((issue) => issue.ruleId === ruleId)
}

async function ruleDirectories(): Promise<string[]> {
  const entries = await readdir(fixturesRoot, { withFileTypes: true })
  return entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort()
}

async function readCases(directory: string): Promise<CaseFile> {
  return JSON.parse(await readFile(join(fixturesRoot, directory, 'cases.json'), 'utf8')) as CaseFile
}

const GOOD = {
  工作票编号: 'DL-2026-0001',
  工作票种类: '第一种工作票',
  许可时间: '2026-03-15 08:30',
  签发时间: '2026-03-14 16:00',
  终结时间: '2026-03-15 17:00',
}

describe('rule pack', () => {
  it('declares a citable basis for every rule', async () => {
    const ruleset = await loadPack()
    expect(ruleset.plugin).toBe(pluginName)
    expect(ruleset.rules.length).toBeGreaterThanOrEqual(5)
    for (const rule of ruleset.rules) {
      expect(rule.basis.document, `${rule.id} document`).not.toBe('')
      expect(rule.basis.clause, `${rule.id} clause`).not.toBe('')
      expect(rule.basis.excerpt.length, `${rule.id} excerpt`).toBeGreaterThanOrEqual(8)
      expect(rule.basis.source, `${rule.id} source`).toMatch(/^https?:\/\//)
      expect(['direct', 'derived-from-principle', 'institutional-configuration']).toContain(rule.basis.kind)
    }
  })

  it('never lets a principle-derived or locally configured check be an error', async () => {
    const ruleset = await loadPack()
    for (const rule of ruleset.rules) {
      if (rule.basis.kind === 'derived-from-principle') expect(rule.severity, rule.id).not.toBe('error')
      if (rule.basis.kind === 'institutional-configuration') expect(rule.severity, rule.id).toBe('info')
    }
  })

  it('cites real clauses, and records the standard effect tier that fixes the severities', async () => {
    const ruleset = await loadPack()
    for (const rule of ruleset.rules) {
      expect(rule.basis.excerpt, rule.id).not.toContain('本次未取得')
      expect(rule.basis.excerpt.length, rule.id).toBeGreaterThan(20)
    }
    const source = await readFile(rulesPath, 'utf8')
    expect(source).toContain('本标准的第5章和7.3.4为推荐性，其余为强制性')
    const mech = ruleset.rules.find((rule) => rule.id === 'PT-006')
    expect(mech?.basis.number).toBe('GB 26860—2011')
    expect(mech?.basis.clause).toBe('6.1.1')
  })

  it('never blocks a workflow on a chapter-5 clause, which the standard makes recommendatory', async () => {
    const ruleset = await loadPack()
    // The standard's foreword makes chapter 5 and 7.3.4 recommendatory and everything else
    // mandatory, so a chapter-5 rule may inform or warn but must never be an error.
    for (const rule of ruleset.rules) {
      if (!rule.basis.clause.startsWith('5.')) continue
      expect(rule.severity, `${rule.id} rests on a recommendatory chapter-5 clause`).not.toBe('error')
    }
    const errors = ruleset.rules.filter((rule) => rule.severity === 'error')
    expect(errors.map((rule) => rule.id)).toEqual(['PT-006'])
    const mech = ruleset.rules.find((rule) => rule.id === 'PT-006')
    expect(mech?.basis.clause).toBe('6.1.1')
  })

  it('tells the reader how to escalate PT-007 without touching code', async () => {
    const ruleset = await loadPack()
    const permit = ruleset.rules.find((rule) => rule.id === 'PT-007')
    expect(permit?.severity).toBe('warn')
    expect(permit?.note).toContain('把本条 severity 改为 error')
    expect(permit?.note).toContain('改严重级不需要改代码')
    expect(permit?.note).toContain('唯一使用 error 级的是 PT-006')
  })

  it('never adopts the three unsupported claims', async () => {
    const source = await readFile(rulesPath, 'utf8')
    expect(source).toContain('无任何此类时限')
    expect(source).toContain('未规定任何时长或次数上限')
    expect(source).toContain('「事故应急抢修单」是错误名称')
    const kinds = (await loadPack()).rules.find((rule) => rule.id === 'PT-002')
    expect(kinds?.note).toContain('紧急抢修单')
    expect(kinds?.note).toContain('不是「事故应急抢修单」')
  })

  it('states that the appendix governing ticket layout is informative', async () => {
    const ruleset = await loadPack()
    const fields = ruleset.rules.find((rule) => rule.id === 'PT-001')
    expect(fields?.basis.excerpt).toContain('可包含')
    expect(fields?.note).toContain('资料性附录')
    expect(fields?.severity).toBe('info')
  })

  it('ships every locally-owned list and threshold unconfigured', async () => {
    const ruleset = await loadPack()
    expect(ruleset.rules.find((rule) => rule.id === 'PT-001')?.params.requiredFields).toEqual([])
    expect(ruleset.rules.find((rule) => rule.id === 'PT-002')?.params.ticketKinds).toEqual([])
    expect(ruleset.rules.find((rule) => rule.id === 'PT-003')?.params.minMinutesBeforeWork).toBe(0)
    expect(ruleset.rules.find((rule) => rule.id === 'PT-003')?.params.maxDurationHours).toBe(0)
    expect(ruleset.rules.find((rule) => rule.id === 'PT-005')?.params.exclusiveRolePairs).toEqual([])
  })

  it('never claims to judge the adequacy of safety measures', async () => {
    const source = await readFile(rulesPath, 'utf8')
    expect(source).toContain('**不判断安全措施是否充分**')
    expect(source).toContain('**不判断该用哪一种票**')
  })

  it('refuses a rule pack that overstates a principle-derived check', () => {
    const overstated = [
      'plugin: probe',
      'version: "0"',
      'rules:',
      '  - id: X-001',
      '    title: probe',
      '    severity: error',
      '    basis:',
      '      document: 《X》',
      '      number: X〔2020〕1号',
      '      clause: 第一条',
      '      excerpt: 这是一个足够长的逐字摘录示例。',
      '      kind: derived-from-principle',
      '      source: https://example.invalid/x',
    ].join('\n')
    expect(() => loadRuleset(overstated)).toThrow(/strongest permitted severity/)
  })
})

describe('paired fixtures', () => {
  it('has both a compliant and a violating sample for every rule', async () => {
    const ruleset = await loadPack()
    const covered = new Set<string>()
    for (const directory of await ruleDirectories()) {
      const cases = await readCases(directory)
      expect(cases.pairs.filter((pair) => pair.expect.count === 0).length, `${directory} compliant sample`).toBeGreaterThanOrEqual(1)
      expect(cases.pairs.filter((pair) => pair.expect.count > 0).length, `${directory} violating sample`).toBeGreaterThanOrEqual(1)
      for (const pair of cases.pairs) {
        const material = await readFile(join(fixturesRoot, directory, pair.material), 'utf8')
        const report = await runFixture(material, pair.material, cases.configure)
        const matched = issuesOf(report, cases.ruleId)
        expect(
          matched.length,
          `${directory}/${pair.name} expected ${pair.expect.count} × ${cases.ruleId}, got ${matched.map((issue) => issue.found).join(' | ')}`,
        ).toBe(pair.expect.count)
        covered.add(cases.ruleId)
      }
    }
    for (const rule of ruleset.rules) expect(covered.has(rule.id), `covered ${rule.id}`).toBe(true)
  })

  it('gives every issue a citable basis and a stable id', async () => {
    for (const directory of await ruleDirectories()) {
      const cases = await readCases(directory)
      for (const pair of cases.pairs) {
        const material = await readFile(join(fixturesRoot, directory, pair.material), 'utf8')
        const report = await runFixture(material, pair.material, cases.configure)
        for (const issue of report.issues) {
          expect(issue.basis).toContain('「')
          expect(issue.id).toMatch(/^dsh-power-ticket-check\.PT-\d{3}\.[0-9a-f]{8}$/)
          expect(issue.found).not.toBe('')
          expect(issue.expected).not.toBe('')
        }
      }
    }
  })
})

describe('chronology', () => {
  it('flags a permit that precedes issue on the same day', async () => {
    const ruleset = await loadPack()
    const material = JSON.stringify({ 签发时间: '2026-03-15 10:00', 许可时间: '2026-03-15 08:00' })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    const issue = issuesOf(report, 'PT-003')[0]
    expect(issue?.found).toContain('早于签发时间')
    expect(issue?.locator.column).toBe('许可时间')
  })

  it('compares across days as one continuous timeline', async () => {
    const ruleset = await loadPack()
    const material = JSON.stringify({ 签发时间: '2026-03-15 10:00', 许可时间: '2026-03-14 08:00' })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    const issue = issuesOf(report, 'PT-003')[0]
    expect(issue?.found).toContain('早于签发时间')
    // A whole day earlier must not be reported as a small negative interval.
    expect(issue?.found).toContain('2026-03-14')
  })

  it('applies a configured minimum interval only when one is set', async () => {
    const ruleset = withConfiguration(await loadPack(), { 'PT-003': { minMinutesBeforeWork: 120 } })
    const material = JSON.stringify({ 签发时间: '2026-03-15 08:00', 许可时间: '2026-03-15 08:30' })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    const issue = issuesOf(report, 'PT-003')[0]
    expect(issue?.found).toContain('30 分钟')
    expect(issue?.found).toContain('120 分钟')
  })

  it('reports an unreadable time rather than silently skipping the order check', async () => {
    const ruleset = await loadPack()
    const material = JSON.stringify({ 签发时间: '二〇二六年三月十五日', 许可时间: '2026-03-15 08:00' })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    const issue = issuesOf(report, 'PT-003')[0]
    expect(issue?.found).toContain('无法解析为日期时间')
    expect(issue?.locator.column).toBe('签发时间')
  })

  it('skips the order check when a time is simply absent', async () => {
    const ruleset = await loadPack()
    const report = runCheck(parseMaterial(JSON.stringify({ 许可时间: '2026-03-15 08:00' }), 'inline'), ruleset, runOptions())
    expect(issuesOf(report, 'PT-003')).toHaveLength(0)
    expect(report.skipped.find((entry) => entry.rule === 'PT-003')?.reason).toContain('缺少签发时间')
  })

  it('flags a work duration beyond the configured ceiling', async () => {
    const ruleset = withConfiguration(await loadPack(), { 'PT-003': { maxDurationHours: 8 } })
    const material = JSON.stringify({ 签发时间: '2026-03-14 16:00', 许可时间: '2026-03-15 08:00', 终结时间: '2026-03-15 20:00' })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    expect(issuesOf(report, 'PT-003')[0]?.found).toContain('超过本机构配置的 8 小时')
  })
})

describe('role separation', () => {
  it('matches role columns with a suffix such as 签名', () => {
    const input = parseMaterial(JSON.stringify({ 工作负责人签名: '李工', 工作许可人: '王工' }), 'inline')
    expect(input.roles.map((role) => role.role)).toContain('工作负责人签名')
    expect(input.roles.find((role) => role.role === '工作许可人')?.person).toBe('王工')
  })

  it('ignores a role pair when one side is blank', async () => {
    const ruleset = withConfiguration(await loadPack(), { 'PT-005': { exclusiveRolePairs: ['工作票签发人|工作负责人'] } })
    const material = JSON.stringify({ 工作票签发人: '张工' })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    expect(issuesOf(report, 'PT-005')).toHaveLength(0)
  })
})

describe('skipped reporting', () => {
  it('admits that the field list is not configured', async () => {
    const report = await runFixture(JSON.stringify(GOOD), 'inline')
    expect(report.skipped.find((entry) => entry.rule === 'PT-001')?.reason).toContain('未配置 requiredFields')
  })

  it('admits that the ticket-kind list is not configured', async () => {
    const report = await runFixture(JSON.stringify(GOOD), 'inline')
    expect(report.skipped.find((entry) => entry.rule === 'PT-002')?.reason).toContain('ticketKinds')
  })

  it('warns when the ticket does not say which kind it is', () => {
    const input = parseMaterial(JSON.stringify({ 工作票编号: 'DL-1' }), 'inline')
    expect(input.warnings.join(' ')).toContain('未写明工作票种类')
  })

  it('names disabled rules exactly once and appends the configured note', async () => {
    const ruleset = await loadPack()
    const input = parseMaterial(JSON.stringify(GOOD), 'inline')
    const report = runCheck(input, ruleset, runOptions({ disabledRules: ['PT-004'], skipNotes: '本机构工作票细则' }))
    const entries = report.skipped.filter((item) => item.rule === 'PT-004')
    expect(entries).toHaveLength(1)
    expect(entries[0]?.reason).toContain('禁用')
    expect(entries[0]?.reason).toContain('本机构工作票细则')
  })
})

describe('report rendering', () => {
  it('never uses adjudicating wording and always carries the disclaimer', async () => {
    const material = await readFile(join(fixturesRoot, 'PT-003', 'PT-003-unsafe.json'), 'utf8')
    const report = await runFixture(material, 'PT-003-unsafe.json')
    const view = buildView(report)
    expect(findForbiddenWording(view.markdown)).toEqual([])
    expect(view.markdown).toContain('免责声明')
    expect(view.markdown).toContain('未执行的检查')
    expect(JSON.parse(view.reportJson)).toMatchObject({ plugin: pluginName, summary: report.summary })
  })
})

describe('plugin contract', () => {
  it('declares a static inject array covering every service apply touches', () => {
    expect(Array.isArray(inject)).toBe(true)
    expect(inject).toContain('tools')
  })

  it('exposes a Schemastery Config with serializable defaults', () => {
    const resolved = ConfigSchema(null)
    expect(resolved.rulesFile).toBe('rules/power-ticket-check.yaml')
    expect(resolved.disabledRules).toEqual([])
    expect(resolved.timeoutMs).toBeGreaterThan(0)
  })

  it('resolves the packaged rule pack and rejects a missing one', () => {
    expect(resolvePackageFile('rules/power-ticket-check.yaml')).toBe(rulesPath)
    expect(() => resolvePackageFile('rules/does-not-exist.yaml')).toThrow(/未找到/)
  })

  it('names the tool after the package family convention', () => {
    expect(TOOL_NAME).toBe('power_ticket_check')
  })
})

describe('material reader', () => {
  it('rejects empty material instead of reporting an empty result', () => {
    expect(() => parseMaterial('   ', 'inline')).toThrow(/材料为空/)
  })

  it('rejects material with no readable field at all', () => {
    expect(() => parseMaterial(JSON.stringify({ nested: { a: 1 } }), 'inline')).toThrow(/没有任何可读字段/)
  })
})

describe('shared kit', () => {
  it('parses wall-clock timestamps and rejects impossible dates', () => {
    expect(parseWallClock('2026-03-15 08:30')).toEqual({ date: '2026-03-15', time: '08:30', hasTime: true, minutes: 510 })
    expect(parseWallClock('2026-02-30')).toBeUndefined()
  })

  it('does calendar arithmetic', () => {
    expect(addDays('2026-03-31', 1)).toBe('2026-04-01')
    expect(diffDays('2026-03-01', '2026-03-06')).toBe(5)
  })

  it('reads the supported YAML subset and rejects the rest', () => {
    expect(parseYaml('a: 1\nb:\n  - x\n')).toEqual({ a: 1, b: ['x'] })
    expect(() => parseYaml('a: 1\na: 2\n')).toThrow(/duplicate/)
  })
})

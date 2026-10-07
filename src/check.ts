/**
 * Pure check core: `(input, ruleset, options) => Report`.
 *
 * No plugin context, no I/O, no clock and no model access, so the whole rule set
 * is unit-testable without credentials. Every finding carries the verbatim clause
 * that produced it, and every check that could not run is reported in `skipped`
 * so an empty issue list can never be read as "the ticket is fine".
 *
 * The checks cover what a form can be held to: the required boxes are filled, the
 * steps happened in an order that is physically possible, and the ticket names the
 * people the procedure requires. Whether the safety measures on the ticket were
 * adequate for the job is a professional judgement this plugin does not make.
 */

import { disabledAsSkipped, formatBasis } from './shared/rules.ts'
import { paramNumber, paramStrings, ruleById } from './shared/ruleset.ts'
import { issueId, makeReport } from './shared/report.ts'
import { instant as instantOf, parseWallClock } from './shared/datetime.ts'
import type { WallClock } from './shared/datetime.ts'
import type { Issue, Locator, Report, Skipped } from './shared/report.ts'
import type { Ruleset } from './shared/rules.ts'
import type { TicketInput } from './model.ts'

/** Options that come from the plugin configuration rather than the rule pack. */
export interface CheckOptions {
  plugin: string
  checkedAt: string
  disabledRules: readonly string[]
  onlyRules: readonly string[]
  /** Ticket kinds the deployment uses, e.g. ['第一种工作票', '第二种工作票']. */
  ticketKinds?: readonly string[]
  skipNotes?: string
}

interface RuleContext {
  input: TicketInput
  ruleset: Ruleset
  issues: Issue[]
  skipped: Skipped[]
  fired: Set<string>
  skipReasons: Map<string, string>
  options: CheckOptions
  add(ruleId: string, locator: Locator, found: string, expected: string, fix?: string): void
  skip(ruleId: string, reason: string): void
}

function makeAdd(context: Omit<RuleContext, 'add' | 'skip'>): RuleContext['add'] {
  return (ruleId, locator, found, expected, fix) => {
    const rule = ruleById(context.ruleset, ruleId)
    const issue: Issue = {
      id: issueId(context.ruleset.plugin, ruleId, locator),
      ruleId,
      severity: rule.severity,
      locator,
      found,
      expected,
      basis: formatBasis(rule.basis, rule.alsoBasis ?? []),
    }
    if (fix !== undefined) issue.fix = fix
    context.issues.push(issue)
    context.fired.add(ruleId)
  }
}

/**
 * A parsed instant.
 *
 * Times are compared by converting both ends to an absolute minute count, so a
 * same-day comparison and a cross-day comparison are the same arithmetic. A date
 * with no clock time is taken as midnight, and the rule says so when that matters.
 */
function instant(raw: string | undefined): { clock: WallClock; minutes: number } | undefined {
  const clock = parseWallClock(raw ?? '')
  if (clock === undefined) return undefined
  return { clock, minutes: instantOf(clock) }
}

/** PT-001 — every configured field is filled. */
function checkRequiredFields(context: RuleContext): void {
  const ruleId = 'PT-001'
  const rule = ruleById(context.ruleset, ruleId)
  const required = paramStrings(rule, 'requiredFields', [])
  if (required.length === 0) {
    context.skip(
      ruleId,
      '规则库未配置 requiredFields：工作票栏目清单随票种与规程版本变化，本插件不硬编码',
    )
    return
  }
  const missing = required.filter((field) => {
    const value = context.input.fields[field]
    return value === undefined || value.trim() === ''
  })
  if (missing.length === 0) return
  context.add(
    ruleId,
    {},
    `工作票缺少 ${missing.length} 个栏目：${missing.join('、')}`,
    `按本机构配置，工作票应填写 ${required.join('、')}`,
    '补齐栏目；本条只核对是否填写，不判断填写内容是否正确',
  )
}

/** PT-002 — the ticket's kind is one the deployment uses. */
function checkTicketKind(context: RuleContext): void {
  const ruleId = 'PT-002'
  const rule = ruleById(context.ruleset, ruleId)
  const kinds = context.options.ticketKinds ?? paramStrings(rule, 'ticketKinds', [])
  if (kinds.length === 0) {
    context.skip(
      ruleId,
      '规则库与配置均未提供 ticketKinds：工作票种类按本机构所用规程确定，本插件不硬编码票种清单',
    )
    return
  }
  if (context.input.kind === undefined) {
    context.add(
      ruleId,
      { column: '工作票种类' },
      '工作票未写明种类',
      `工作票种类应为 ${kinds.join(' / ')} 之一`,
      '补填票种；不同票种适用条件与栏目不同，无法在不写票种的情况下判断适用性',
    )
    return
  }
  if (kinds.includes(context.input.kind.trim())) return
  context.add(
    ruleId,
    { column: '工作票种类' },
    `工作票种类「${context.input.kind}」不在本机构配置的票种内（${kinds.join(' / ')}）`,
    `工作票种类应为 ${kinds.join(' / ')} 之一`,
    '核对票种是否与本机构所用规程一致；本条不判断该作业应使用哪一种票',
  )
}

/** PT-003 — the steps happened in an order that is physically possible. */
function checkChronology(context: RuleContext): void {
  const ruleId = 'PT-003'
  const before = paramNumber(ruleById(context.ruleset, ruleId), 'minMinutesBeforeWork', 0)
  const issued = instant(context.input.issuedAt)
  const permitted = instant(context.input.permittedAt)
  const finished = instant(context.input.finishedAt)

  const unreadable = (
    [
      ['签发时间', context.input.issuedAt, issued],
      ['许可时间', context.input.permittedAt, permitted],
      ['终结时间', context.input.finishedAt, finished],
    ] as const
  ).filter(([, raw, parsed]) => raw !== undefined && parsed === undefined)
  for (const [column, raw] of unreadable) {
    context.add(
      ruleId,
      { column },
      `${column}「${raw}」无法解析为日期时间`,
      '时间应写成可解析的形式，如 2026-03-15 08:30',
      '按本机构统一的写法填写；无法解析时顺序核对不成立',
    )
  }
  if (unreadable.length > 0) return

  if (issued === undefined || permitted === undefined) {
    context.skip(ruleId, '材料缺少签发时间或许可时间，无法核对顺序')
    return
  }
  if (permitted.minutes < issued.minutes) {
    context.add(
      ruleId,
      { column: '许可时间' },
      `许可时间 ${context.input.permittedAt} 早于签发时间 ${context.input.issuedAt}`,
      '应先签发工作票，后履行工作许可手续',
      '核对两个时间的填写；时间先后颠倒通常是填报错误，也需确认实际流程',
    )
  } else if (before > 0) {
    const elapsed = permitted.minutes - issued.minutes
    if (elapsed < before) {
      context.add(
        ruleId,
        { column: '许可时间' },
        `签发到许可间隔 ${elapsed} 分钟，少于本机构配置的 ${before} 分钟`,
        `按本机构配置，签发与许可之间应至少间隔 ${before} 分钟`,
        '核对是否留出了必要的准备与交底时间；本条只比对配置值',
      )
    }
  }

  if (finished === undefined) return
  const elapsed = finished.minutes - permitted.minutes
  if (elapsed < 0) {
    context.add(
      ruleId,
      { column: '终结时间' },
      `终结时间 ${context.input.finishedAt} 早于许可时间 ${context.input.permittedAt}`,
      '工作终结应在工作许可之后',
      '核对两个时间的填写',
    )
    return
  }
  const limit = paramNumber(ruleById(context.ruleset, ruleId), 'maxDurationHours', 0)
  if (limit > 0 && elapsed > limit * 60) {
    context.add(
      ruleId,
      { column: '终结时间' },
      `许可到终结间隔 ${Math.round((elapsed / 60) * 10) / 10} 小时，超过本机构配置的 ${limit} 小时`,
      `按本机构配置，单张工作票的工作时长应不超过 ${limit} 小时`,
      '核对是否需要办理延期手续；本条只比对配置值，不判断是否应当延期',
    )
  }
}

/** PT-004 — 延期 must not move the end earlier, and must come after the permit. */
function checkExtension(context: RuleContext): void {
  const ruleId = 'PT-004'
  if (context.input.extendedTo === undefined) {
    context.skip(ruleId, '材料未提供延期时间，本条不适用')
    return
  }
  const extended = instant(context.input.extendedTo)
  if (extended === undefined) {
    context.add(
      ruleId,
      { column: '延期时间' },
      `延期时间「${context.input.extendedTo}」无法解析为日期时间`,
      '时间应写成可解析的形式，如 2026-03-15 18:30',
      '按本机构统一的写法填写',
    )
    return
  }
  const plannedEnd = instant(context.input.plannedEnd)
  if (plannedEnd !== undefined && extended.minutes < plannedEnd.minutes) {
    context.add(
      ruleId,
      { column: '延期时间' },
      `延期时间 ${context.input.extendedTo} 早于计划结束时间 ${context.input.plannedEnd}`,
      '延期应把工作结束时间向后推',
      '核对延期时间的填写；本条不判断延期手续是否齐备',
    )
    return
  }
  const permitted = instant(context.input.permittedAt)
  if (permitted !== undefined && extended.minutes < permitted.minutes) {
    context.add(
      ruleId,
      { column: '延期时间' },
      `延期时间 ${context.input.extendedTo} 早于许可时间 ${context.input.permittedAt}`,
      '延期应在工作许可之后办理',
      '核对延期时间的填写',
    )
  }
}

/** PT-005 — the same person cannot hold two roles that must be separate. */
function checkRoleSeparation(context: RuleContext): void {
  const ruleId = 'PT-005'
  const rule = ruleById(context.ruleset, ruleId)
  const exclusive = paramStrings(rule, 'exclusiveRolePairs', [])
  if (exclusive.length === 0) {
    context.skip(
      ruleId,
      '规则库未配置 exclusiveRolePairs：哪些角色必须由不同人担任由本机构所用规程规定，本插件不硬编码',
    )
    return
  }
  const byRole = new Map<string, string>()
  for (const entry of context.input.roles) {
    if (entry.person.trim() === '') continue
    byRole.set(entry.role, entry.person.trim())
  }
  for (const pair of exclusive) {
    const [left, right] = pair.split('|').map((part) => part.trim())
    if (left === undefined || right === undefined || left === '' || right === '') continue
    const leftPerson = byRole.get(left)
    const rightPerson = byRole.get(right)
    if (leftPerson === undefined || rightPerson === undefined) continue
    if (leftPerson !== rightPerson) continue
    context.add(
      ruleId,
      { column: left },
      `${left}与${right}为同一人（${leftPerson}）`,
      `按本机构配置，${left}与${right}应由不同人员担任`,
      '核对人员安排；本条只比对配置的角色对，不判断该规程是否适用于本次作业',
    )
  }
}

/**
 * Collect the text of the configured columns into one haystack.
 *
 * @param input - the ticket.
 * @param columns - column names to read; unknown names contribute nothing.
 * @returns the concatenated text, with newlines between cells.
 */
function haystack(input: TicketInput, columns: readonly string[]): string {
  const parts: string[] = []
  for (const column of columns) {
    const value = input.fields[column]
    if (value !== undefined && value !== '') parts.push(value)
  }
  // Role columns often carry the permit signatures, so include them too.
  for (const role of input.roles) parts.push(role.person)
  return parts.join('\n')
}

/**
 * PT-006 — the five safety technical measures appear on the ticket.
 *
 * This is the only `error`-level rule here, and the reason is checkable: the
 * standard's foreword makes clause 5 recommendatory and *the rest mandatory*, and
 * 6.1.1 sits in chapter 6 with the five measures enumerated verbatim. The rule
 * checks that the ticket writes them down; whether they matched the site is a
 * matter for the inspection, not for a form.
 */
function checkTechnicalMeasures(context: RuleContext): void {
  const ruleId = 'PT-006'
  const rule = ruleById(context.ruleset, ruleId)
  const terms = paramStrings(rule, 'measureTerms', [])
  const columns = paramStrings(rule, 'measureColumns', [])
  if (terms.length === 0) {
    context.skip(ruleId, '规则库未配置 measureTerms，本条不执行')
    return
  }
  const text = haystack(context.input, columns)
  if (text.trim() === '') {
    context.skip(
      ruleId,
      `材料中没有可读取安全措施的栏目（已按 ${columns.join(' / ')} 查找），无法核对五项技术措施`,
    )
    return
  }
  const missing = terms.filter((term) => !text.includes(term))
  if (missing.length === 0) return
  context.add(
    ruleId,
    { column: columns[0] ?? '安全措施' },
    `安全措施文本中未出现 ${missing.length} 项：${missing.join('、')}`,
    '在电气设备上工作，应有停电、验电、装设接地线、悬挂标示牌和装设遮栏（围栏）等保证安全的技术措施',
    '核对票面是否写全五项；本条只核对是否写到，不判断措施内容是否与现场相符',
  )
}

/**
 * PT-007 — the three permit formalities are evidenced on the ticket.
 *
 * Clause 5.5.1 is verbatim, but it sits in chapter 5, which the standard's
 * foreword makes recommendatory. The rule therefore ships at `error` because the
 * permit step is the point at which an unsafe ticket would otherwise proceed, and
 * the note tells a deployment how to soften it without touching code.
 */
function checkPermitFormalities(context: RuleContext): void {
  const ruleId = 'PT-007'
  const rule = ruleById(context.ruleset, ruleId)
  const terms = paramStrings(rule, 'permitTerms', [])
  const columns = paramStrings(rule, 'permitColumns', [])
  if (terms.length === 0) {
    context.skip(ruleId, '规则库未配置 permitTerms，本条不执行')
    return
  }
  const text = haystack(context.input, columns)
  if (text.trim() === '') {
    context.skip(ruleId, `材料中没有可读取许可手续的栏目（已按 ${columns.join(' / ')} 查找），无法核对`)
    return
  }
  const missing = terms.filter((term) => !text.includes(term))
  if (missing.length === 0) return
  context.add(
    ruleId,
    { column: columns[0] ?? '安全措施' },
    `工作许可相关文本中未出现 ${missing.length} 项：${missing.join('、')}`,
    '工作许可人还应完成：a）会同工作负责人到现场再次检查所做的安全措施；b）对工作负责人指明带电设备的位置和注意事项；c）会同工作负责人在工作票上分别确认、签名',
    '核对票面是否体现三项手续；本条只做字面核对，不判断现场是否真的复查了',
  )
}

const CHECKERS: readonly ((context: RuleContext) => void)[] = [
  checkRequiredFields,
  checkTicketKind,
  checkChronology,
  checkExtension,
  checkRoleSeparation,
  checkTechnicalMeasures,
  checkPermitFormalities,
]

/**
 * Run the whole rule pack against one work ticket.
 * @param input - normalized ticket.
 * @param ruleset - validated rule pack.
 * @param options - plugin identity, clock value and rule selection.
 * @returns the report, with `skipped` listing every check that did not run.
 */
export function runCheck(input: TicketInput, ruleset: Ruleset, options: CheckOptions): Report {
  const disabled = new Set([...ruleset.disabled, ...options.disabledRules])
  const only = new Set(options.onlyRules)
  const base = {
    input,
    ruleset,
    issues: [] as Issue[],
    skipped: [] as Skipped[],
    fired: new Set<string>(),
    skipReasons: new Map<string, string>(),
    options,
  }
  const context: RuleContext = {
    ...base,
    add: makeAdd(base),
    skip: (ruleId, reason) => {
      base.skipReasons.set(ruleId, reason)
    },
  }

  for (const checker of CHECKERS) checker(context)

  const withNote = (reason: string): string => (options.skipNotes === undefined ? reason : `${reason}；${options.skipNotes}`)
  const skipped: Skipped[] = disabledAsSkipped(ruleset, [...disabled], withNote('该规则在当前配置中被禁用'))
  const already = new Set(skipped.map((entry) => entry.rule))
  for (const [ruleId, reason] of base.skipReasons) {
    if (already.has(ruleId)) continue
    if (disabled.has(ruleId) || (options.onlyRules.length > 0 && !only.has(ruleId))) continue
    skipped.push({ rule: ruleId, reason: withNote(reason) })
    already.add(ruleId)
  }
  for (const rule of ruleset.rules) {
    if (disabled.has(rule.id) || base.fired.has(rule.id) || already.has(rule.id)) continue
    if (options.onlyRules.length > 0 && !only.has(rule.id)) continue
    skipped.push({ rule: rule.id, reason: withNote('材料满足该检查的前置条件且未发现差异条目') })
  }
  if (options.onlyRules.length > 0) {
    const notSelected = ruleset.rules.filter((rule) => !only.has(rule.id) && !disabled.has(rule.id))
    if (notSelected.length > 0) {
      skipped.push({
        rule: notSelected.map((rule) => rule.id).join(','),
        reason: withNote(`本次调用通过 only 参数把执行范围限制为 ${[...only].join(', ')}，上列规则未执行`),
      })
    }
  }

  return makeReport({
    plugin: options.plugin,
    target: input.target,
    rulesetVersion: ruleset.version,
    checkedAt: options.checkedAt,
    issues: context.issues,
    skipped,
  })
}

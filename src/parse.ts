/**
 * Reader for the power work ticket.
 *
 * The material is JSON or YAML: one flat mapping of the ticket's own column names
 * to their values. Known columns are recognised; everything is kept in `fields`
 * so a finding can name the column it read and an unknown template still works.
 */

import { YamlSubsetError, parseYaml } from './shared/yaml.ts'
import { ROLE_COLUMNS } from './model.ts'
import type { TicketInput, TicketRole } from './model.ts'

/** Raised when the material cannot be read at all. */
export class MaterialError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'MaterialError'
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function text(value: unknown): string | undefined {
  if (value === undefined || value === null) return undefined
  if (typeof value === 'string') return value.trim() === '' ? undefined : value.trim()
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return undefined
}

/** Find the first present value among a set of candidate column names. */
function pick(fields: Record<string, string>, names: readonly string[]): string | undefined {
  for (const name of names) {
    const value = fields[name]
    if (value !== undefined && value !== '') return value
  }
  return undefined
}

/**
 * Parse material into the normalized input contract.
 * @param source - JSON or YAML text.
 * @param target - description of where the material came from.
 * @returns the normalized input.
 */
export function parseMaterial(source: string, target: string): TicketInput {
  const trimmed = source.trim()
  if (trimmed === '') throw new MaterialError('材料为空')
  let document: unknown
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      document = JSON.parse(trimmed)
    } catch (error) {
      throw new MaterialError(`JSON 无法解析：${error instanceof Error ? error.message : String(error)}`)
    }
  } else {
    try {
      document = parseYaml(trimmed)
    } catch (error) {
      if (error instanceof YamlSubsetError) throw new MaterialError(`YAML 无法解析：${error.message}`)
      throw error
    }
  }
  if (!isRecord(document)) throw new MaterialError('材料根节点必须是映射（一张工作票）')

  const fields: Record<string, string> = {}
  for (const [key, value] of Object.entries(document)) {
    if (value === undefined || value === null) continue
    if (isRecord(value) || Array.isArray(value)) continue
    const rendered = text(value)
    if (rendered !== undefined) fields[key] = rendered
  }
  if (Object.keys(fields).length === 0) {
    throw new MaterialError('材料中没有任何可读字段，无法执行检查')
  }

  const warnings: string[] = []
  const input: TicketInput = { target, roles: [], fields, warnings }

  const number = pick(fields, ['工作票编号', '编号', 'number'])
  if (number !== undefined) input.number = number
  const kind = pick(fields, ['工作票种类', '票种', '种类', 'kind', 'type'])
  if (kind !== undefined) input.kind = kind
  const location = pick(fields, ['工作地点', '地点', 'location'])
  if (location !== undefined) input.location = location
  const task = pick(fields, ['工作任务', '工作内容', '任务', 'task'])
  if (task !== undefined) input.task = task

  const plannedStart = pick(fields, ['计划开始时间', '计划工作时间起', '计划工作开始时间'])
  if (plannedStart !== undefined) input.plannedStart = plannedStart
  const plannedEnd = pick(fields, ['计划结束时间', '计划工作时间止', '计划工作结束时间'])
  if (plannedEnd !== undefined) input.plannedEnd = plannedEnd
  const issuedAt = pick(fields, ['签发时间', '工作票签发时间'])
  if (issuedAt !== undefined) input.issuedAt = issuedAt
  const permittedAt = pick(fields, ['许可时间', '许可开始工作时间', '开工时间'])
  if (permittedAt !== undefined) input.permittedAt = permittedAt
  const finishedAt = pick(fields, ['终结时间', '工作终结时间', '完工时间'])
  if (finishedAt !== undefined) input.finishedAt = finishedAt
  const extendedTo = pick(fields, ['延期时间', '延期至', '延期后结束时间'])
  if (extendedTo !== undefined) input.extendedTo = extendedTo

  // Role names may also appear with a suffix such as `签名`, so match by prefix.
  for (const column of ROLE_COLUMNS) {
    const exact = fields[column]
    if (exact !== undefined && exact !== '') {
      input.roles.push({ role: column, person: exact })
      continue
    }
    for (const [key, value] of Object.entries(fields)) {
      if (key !== column && !key.startsWith(column)) continue
      input.roles.push({ role: key, person: value })
    }
  }

  if (input.kind === undefined) {
    warnings.push('材料未写明工作票种类（kind），按种类判断适用性的检查将无法执行')
  }
  if (input.roles.length === 0) {
    warnings.push('材料中没有可识别的人员角色列，人员相关检查将无法执行')
  }

  return input
}

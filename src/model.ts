/**
 * Input contract for the power work-ticket checker.
 *
 * The material is one 工作票: its identifying fields, the personnel named on it,
 * and the times of the issuing / permitting / completion steps. The checker
 * verifies completeness and the order of those steps — it never decides whether
 * the safety measures written on the ticket were adequate, which is the
 * issuer's and the permitter's professional responsibility.
 */

/** One named role on the ticket. */
export interface TicketRole {
  /** The column the name was read from, e.g. `工作负责人`. */
  role: string
  /** The person named. */
  person: string
}

/** The whole normalized input. */
export interface TicketInput {
  target: string
  /** 工作票编号. */
  number?: string
  /** 工作票种类, as written on the ticket. */
  kind?: string
  /** 工作地点. */
  location?: string
  /** 工作任务. */
  task?: string
  /** 计划工作时间, as written. */
  plannedStart?: string
  plannedEnd?: string
  /** 签发时间, as written. */
  issuedAt?: string
  /** 许可（开工）时间, as written. */
  permittedAt?: string
  /** 工作终结时间, as written. */
  finishedAt?: string
  /** 延期时间, as written. */
  extendedTo?: string
  /** Every named role found, in column order. */
  roles: TicketRole[]
  /** Values keyed by the ticket's own column names. */
  fields: Record<string, string>
  warnings: string[]
}

/** Columns recognised as a named role, in priority order. */
export const ROLE_COLUMNS = [
  '工作票签发人',
  '工作负责人',
  '工作许可人',
  '专责监护人',
  '工作班成员',
  '值班负责人',
  '调度许可人',
] as const

/** Columns recognised as the safety measures written on the ticket. */
export const MEASURE_COLUMNS = [
  '安全措施',
  '应装设接地线',
  '应设遮栏',
  '应挂标示牌',
  '停电范围',
  '安全注意事项',
] as const

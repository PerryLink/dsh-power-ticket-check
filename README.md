# dsh-power-ticket-check — Power work-ticket completeness and issue-permit-termination order check

[English](README.md) · [简体中文](README-zh.md) · [Español](README-es.md) · [Português](README-pt.md) · [हिन्दी](README-hi.md)

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-power-ticket-check` reads one **电力工作票** as a flat mapping of the ticket's own column names to their values, together with the roles named on it, and checks that ticket for what a form can be held to: that every column in your configured `requiredFields` is filled, that the 工作票种类 is one your deployment lists, that 签发时间 → 许可时间 → 终结时间 form a sequence that is physically possible, that a 延期时间 pushes the end forward and does not precede the permit, that roles you configured as exclusive are held by different people, and that the safety-measure and permit text carries the five 安全技术措施 terms and the three 许可手续 terms the pack looks for. Checks that could not run are listed in `skipped` with their reason rather than passing silently.

## Install

```sh
dsh plugin --profile <name> add dsh-power-ticket-check
dsh --profile <name> --dump-config | grep 'dsh-power-ticket-check'
```

## What it looks like

![Terminal demo of dsh-power-ticket-check: real output over its PT-003 fixture](https://raw.githubusercontent.com/PerryLink/dsh-power-ticket-check/main/docs/assets/dsh-power-ticket-check-hero.png)

![Animated terminal demo of dsh-power-ticket-check](https://raw.githubusercontent.com/PerryLink/dsh-power-ticket-check/main/docs/assets/dsh-power-ticket-check-demo.gif)

Real output from this plugin over its own `PT-003` test fixture — not a mock-up. The rule pack ships no invented quotations, so a finding names both the clause it applied and the fact that the clause text was not obtained.

## What it answers

| You ask | What it answers |
|---|---|
| Out of the box it passes every ticket I run through it — why? | Because `PT-001` reports itself in `skipped`, not as a pass. Its `requiredFields` list ships empty, so the rule cannot run; fill it with the columns your own form requires. Even when configured, `PT-001` checks that a column is filled, not that the value in it is correct, and it sits at `info`. |
| The ticket is a 电气第一种工作票 but the 工作性质 mentions 带电作业 — is that a contradiction it reports? | No. `PT-002` reports only two things: that the 工作票种类 is missing, or that it is not among the kinds your deployment lists. Its `ticketKinds` list ships empty and the rule then reports itself in `skipped`, exactly as `PT-005` does when its `exclusiveRolePairs` list is empty; the plugin does not decide which kind of ticket a job needs. Once you fill those lists, configure `PT-005` with the pair 工作许可人 and 工作负责人 to have the same person in both columns reported. Neither rule judges anyone's qualification or whether holding two roles was approved. |
| The 许可时间 is written earlier than the 签发时间, and one time column will not parse. | `PT-003` reports both: 许可时间 earlier than 签发时间, 终结时间 earlier than 许可时间, and any unreadable column as 无法解析为日期时间, expecting a form such as `2026-03-15 08:30`. Both ends are converted to an absolute minute count, so a ticket spanning midnight compares correctly. If 签发时间 or 许可时间 cannot be read at all, the rule reports itself in `skipped`, because the order check cannot be established. It never checks whether the work actually followed the ticket, and an optional interval or duration limit is yours to configure. |
| The 延期时间 is earlier than the 计划结束时间, so the extension shortens the job rather than lengthening it. | `PT-004` reports it, and also reports a 延期时间 earlier than the 许可时间. The standard sets no ceiling on how long or how often a ticket may be extended, so the rule carries no quantitative limit and does not check whether the extension formalities were completed. |
| The 安全措施 column is filled in but mentions only 停电 and 验电. | `PT-006` reports the three missing terms one by one. It is the only rule here at `error`, because its clause 6.1.1 sits in the mandatory chapter, and it checks that the five measures are written on the ticket, not that they match the site or were carried out. If no readable measure column is found it reports itself in `skipped`. |
| Nothing on the ticket shows that the 工作许可人 went to the site again with the 工作负责人. | `PT-007` reports which of the three permit-formality terms are absent from the text it reads, that text being the `permitColumns` plus the names in the role columns. It reads wording only: it cannot tell whether the site re-check really happened, and an institution that wants this to block can raise the rule's severity in the pack without a code change. |

## Standards it follows

| Document | Number | Cited by rules |
|---|---|---|
| 《电力安全工作规程 发电厂和变电站电气部分》 | GB 26860—2011 | PT-001, PT-002, PT-003, PT-004, PT-005, PT-006, PT-007 |

**Boundary:** this plugin checks one **电力工作票** for what a form can be held to — that the required
boxes are filled, that 签发 / 许可 / 终结 happened in an order that is physically possible, that 延期
moves the end forward, and that roles you require to be separate are held by different people. It does
**not** judge whether the safety measures written on the ticket were adequate, **does not** say which
kind of ticket a job needs, and **does not** verify that anyone's qualification is real.

> ### ⚠️ Three things this plugin refuses to do, and the effect tier that fixes its severities
>
> **1. It respects the standard's own effect tier.** GB 26860—2011's foreword says, verbatim,
> 「本标准的第5章和7.3.4为推荐性，其余为强制性」 — **the work-ticket regime sits in the *recommendatory*
> chapter 5.** So every rule resting on chapter 5 ships at `warn` or `info` and **nothing there can block a
> workflow**. `PT-006` (the five safety technical measures, clause 6.1.1) is the **only** `error`, because
> chapter 6 is mandatory. `PT-007` (the permit formalities, clause 5.5.1) is a `warn`; its note explains that
> an institution which wants those formalities to block can raise it by editing the rule pack, with no code
> change. A test asserts both directions: no chapter-5 rule is an `error`, and `PT-006` is the sole one.
>
> **2. It does not adopt three claims that have no basis in the standards.** After reading GB 26860—2011
> and GB 26859—2011 in full: there is **no** "第一种工作票应工作前一日送达" deadline anywhere; 5.3.12 and
> 5.4.10 say only 「延期应办理手续」 with **no ceiling on duration or count**; and the statutory name is
> **紧急抢修单** (5.2.4), not "事故应急抢修单". A test asserts the pack records all three.
>
> **3. It does not treat the ticket layout as mandatory.** 5.1.2 says the ticket "**可**包含" those items,
> and appendices A–D are marked **资料性附录** (informative) in the standard's contents. So `PT-001` ships
> with an **empty** field list for you to fill from your own form, and reports at `info`.
>
> Two more lists are yours: `PT-002`'s ticket kinds and `PT-005`'s exclusive role pairs. Both ship empty.
> The plugin never judges whether the safety measures written on a ticket were adequate, which ticket
> kind a job needs, or whether anyone's qualification is real — the standard sets out roles' **duties**
> (5.4.1–5.4.5) and **no qualification conditions**.

## Compatibility

| Surface | Status |
|---|---|
| Harness | Peer range `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verified to accept both `0.2.0-rc.2` and `0.2.1-rc.2`. `engines.dsh` is declared as `>=0.2.1-0 <0.3.0` and is enforced by the host since 0.2.1 |
| Node | `^22.19.0 || >=24.0.0` |
| Platforms | All (plain ESM; no native code, no network, no model call) |
| Tool mode | Works in `native` and `ptc`; for a month of tickets use `ptc` |

## What it does

Registers the `power_ticket_check` tool. It reads one ticket as a flat mapping of the ticket's own column
names to their values, applies a versioned rule pack, and returns a report.

| Rule | Check | Severity | Basis kind |
|---|---|---|---|
| `PT-001` | every configured column is filled (off by default, informative layout) | info | local |
| `PT-002` | the ticket kind is one you use, and matches the work's nature | warn | direct |
| `PT-003` | 签发 → 许可 → 终结 is a possible order; optional interval and duration limits | warn | principle |
| `PT-004` | 延期 moves the end forward and follows the permit | warn | direct |
| `PT-005` | roles you require to be separate are held by different people (off by default) | warn | direct |
| `PT-006` | the five safety technical measures are written on the ticket | error | direct |
| `PT-007` | the permit formalities (site re-check, live parts pointed out, both signatures) | warn | direct |

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `rulesFile` | string | `rules/power-ticket-check.yaml` | Rule-pack path, relative to the package root |
| `disabledRules` | string[] | `[]` | Rule ids to stop running; each appears in `skipped` |
| `onlyRules` | string[] | `[]` | Run only these rule ids; empty runs every rule |
| `skipNotes` | string | `""` | Note appended to every `skipped` reason |
| `timeoutMs` | number | `120000` | Cooperative tool timeout budget |

Rule-level parameters worth knowing:

- `PT-001` `requiredFields` — the columns that must be filled, using the same names the material uses.
- `PT-002` `ticketKinds` — your ticket kinds, e.g. `[第一种工作票, 第二种工作票, 带电作业票]`. It can
  also be passed per call.
- `PT-003` `minMinutesBeforeWork` — the least interval you require between 签发 and 许可. `0` disables
  the interval comparison.
- `PT-003` `maxDurationHours` — the longest a single ticket may run. `0` disables the duration check.
- `PT-005` `exclusiveRolePairs` — pairs that must not be the same person, written
  `['工作票签发人|工作许可人']`.

## Material format

The tool accepts JSON or YAML. One ticket is one flat mapping:

```yaml
工作票编号: DL-2026-0001
工作票种类: 第一种工作票
工作地点: 35kV 某某变电站
工作任务: 10kV 某某线 01 号杆更换隔离开关
计划开始时间: 2026-03-15 08:00
计划结束时间: 2026-03-15 18:00
签发时间: 2026-03-14 16:00
许可时间: 2026-03-15 08:30
终结时间: 2026-03-15 17:00
工作票签发人: 张工
工作负责人: 李工
工作许可人: 王工
```

Times are accepted as `2026-03-15 08:30` or as a bare date, in which case midnight is assumed and the
report says so when that matters. Role columns may carry a suffix — `工作负责人签名` is recognised as the
工作负责人 role — so a form exported with its signature boxes still maps cleanly.

The chronology check compares both ends on **one continuous timeline**, so a permit that falls on an
earlier day is reported as an earlier instant, not as a small negative same-day interval.

## Rule sources

Rule data lives in `rules/power-ticket-check.yaml`. Every rule carries a document, a document number, a
clause in the source's own numbering, a verbatim excerpt and the URL the excerpt was read from. The
loader enforces that an excerpt is a real quotation of at least eight characters, and that a check
resting on a general principle or a local policy can never be declared `error`.

The clauses quoted come from **GB 26860—2011《电力安全工作规程 发电厂和变电站电气部分》** — 5.1.2, 5.2.1–5.2.4,
5.3.7, 5.3.12, 5.5.1, 5.7.5 and 6.1.1 — with the standard's foreword providing the effect tier that
fixes each rule's severity. The clause text was obtained from a full-text scan transcription and
cross-checked verbatim against a second independent site.

Current standards in this family, all verified against the standards platform:

| Standard | In force | Note |
|---|---|---|
| GB 26860—2011 发电厂和变电站电气部分 | 2012-06-01 | mandatory, except chapters 5 and 7.3.4; a revision is "being approved" |
| GB 26859—2011 电力线路部分 | 2012-06-01 | the line-side counterpart |
| DL/T 408—2023 发电厂和变电站电气部分 | 2024-06-28 | replaces **DL 408—1991**, runs **alongside** GB 26860 — not a replacement for it |
| DL/T 409—2023 电力线路部分 | 2024-06-28 | |
| DL/T 560—2022 高压试验室部分 | 2022-11-13 | replaces DL 560—1995 |

**DL/T 408—2023's clause text could not be obtained, so this pack cites none of it.** Its identity and
chapter structure were verified, and DL/T 408—2023 renames 紧急抢修单 to 故障紧急抢修单 and adds 带电作业票 and
双签发 — which is why `PT-002` accepts both names rather than picking one.

The full clause-verification report, including the sources that were checked and rejected, is in
`rules/evidence/clause-verification.md`.

## Troubleshooting

- **`PT-001`, `PT-002` or `PT-005` report themselves as skipped.** Their lists are empty. Fill in the
  ones your enterprise's rules require.
- **`PT-003` reports nothing about order.** 签发时间 and 许可时间 are not both present; the rule says so
  in `skipped`. If a time is present but unreadable, the rule reports *that* instead of skipping, so an
  unparseable cell never hides the check.
- **`PT-003` fires on a duration that is normal for us.** `maxDurationHours` is `0` by default; if you set
  it, it applies to every ticket the tool sees. Leave it at `0` if your tickets legitimately run long.
- **`PT-005` misses a case I know about.** Add the role pair. The plugin compares only the pairs you list,
  because which roles must be separate depends on the ticket kind and your implementing rules.
- **The plugin installs but the tool never appears.** Check that `main` resolves to `lib/index.mjs` and
  that `pnpm run build` produced it; a wrong `main` makes the loader skip the entry silently.
- **`dsh plugin add` refuses the package as incompatible.** The peer range covers `0.1.x` and `0.2.x`;
  if your runtime sits outside it, grant an explicit exemption:
  `dsh plugin --profile <name> allow-version dsh-power-ticket-check@0.1.0 --dsh-version <runtime> --accept-risk`
- **`check` reports `manifest-peers` as failed.** The static checker compares against a hard-coded peer
  range that predates the 0.2 line. The runtime enforces peer compatibility at install time, so the
  declared range is the correct one; this is a known upstream issue in `dsh-plugin-dev`.

## Development

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit
pnpm test            # vitest, paired fixtures per rule
pnpm run build       # tsdown -> lib/index.mjs + lib/index.d.mts
node ../scripts/sync-shared.mjs dsh-power-ticket-check   # refresh src/shared from ../_shared
```

## PerryLink DSH Plugin Family

This project is part of the DeepSeek Harness plugin family from [PerryLink](https://github.com/PerryLink). The roster stays collapsed below so every README keeps a short first screen; expand it to see every row and its status.

<details>
<summary>Expand all plugins</summary>

| Plugin | Status |
|---|---|
| **[dsh-aqua-input-check](https://github.com/PerryLink/dsh-aqua-input-check)** |  |
| **[dsh-archive-check](https://github.com/PerryLink/dsh-archive-check)** |  |
| **[dsh-auto-review](https://github.com/PerryLink/dsh-auto-review)** |  |
| **[dsh-autotier](https://github.com/PerryLink/dsh-autotier)** |  |
| **[dsh-bid-ca-precheck](https://github.com/PerryLink/dsh-bid-ca-precheck)** |  |
| **[dsh-bid-qual-check](https://github.com/PerryLink/dsh-bid-qual-check)** |  |
| **[dsh-cert-mcp](https://github.com/PerryLink/dsh-cert-mcp)** |  |
| **[dsh-checkpoint-rewind](https://github.com/PerryLink/dsh-checkpoint-rewind)** |  |
| **[dsh-click](https://github.com/PerryLink/dsh-click)** |  |
| **[dsh-composer-history](https://github.com/PerryLink/dsh-composer-history)** |  |
| **[dsh-contract-stance](https://github.com/PerryLink/dsh-contract-stance)** |  |
| **[dsh-customs-doc-check](https://github.com/PerryLink/dsh-customs-doc-check)** |  |
| **[dsh-data-quality](https://github.com/PerryLink/dsh-data-quality)** |  |
| **[dsh-demurrage-ledger](https://github.com/PerryLink/dsh-demurrage-ledger)** |  |
| **[dsh-doublecheck](https://github.com/PerryLink/dsh-doublecheck)** |  |
| **[dsh-drill-script-check](https://github.com/PerryLink/dsh-drill-script-check)** |  |
| **[dsh-eia-guide-check](https://github.com/PerryLink/dsh-eia-guide-check)** |  |
| **[dsh-emergency-plan](https://github.com/PerryLink/dsh-emergency-plan)** |  |
| **[dsh-essay-rubric-check](https://github.com/PerryLink/dsh-essay-rubric-check)** |  |
| **[dsh-evidence-check](https://github.com/PerryLink/dsh-evidence-check)** |  |
| **[dsh-export-ctl-check](https://github.com/PerryLink/dsh-export-ctl-check)** |  |
| **[dsh-fast](https://github.com/PerryLink/dsh-fast)** |  |
| **[dsh-fmea-table-check](https://github.com/PerryLink/dsh-fmea-table-check)** |  |
| **[dsh-forecast-penalty](https://github.com/PerryLink/dsh-forecast-penalty)** |  |
| **[dsh-fund-research](https://github.com/PerryLink/dsh-fund-research)** |  |
| **[dsh-github](https://github.com/PerryLink/dsh-github)** |  |
| **[dsh-gongwen-flow-check](https://github.com/PerryLink/dsh-gongwen-flow-check)** |  |
| **[dsh-gongwen-word-check](https://github.com/PerryLink/dsh-gongwen-word-check)** |  |
| **[dsh-guard-plan-qc](https://github.com/PerryLink/dsh-guard-plan-qc)** |  |
| **[dsh-hazchem-check](https://github.com/PerryLink/dsh-hazchem-check)** |  |
| **[dsh-hazplan-check](https://github.com/PerryLink/dsh-hazplan-check)** |  |
| **[dsh-hidden-risk-map](https://github.com/PerryLink/dsh-hidden-risk-map)** |  |
| **[dsh-hs-classify](https://github.com/PerryLink/dsh-hs-classify)** |  |
| **[dsh-icd-rule-check](https://github.com/PerryLink/dsh-icd-rule-check)** |  |
| **[dsh-industry-research](https://github.com/PerryLink/dsh-industry-research)** |  |
| **[dsh-lawcite-adapter](https://github.com/PerryLink/dsh-lawcite-adapter)** |  |
| **[dsh-laya](https://github.com/PerryLink/dsh-laya)** |  |
| **[dsh-lc-doc-check](https://github.com/PerryLink/dsh-lc-doc-check)** |  |
| **[dsh-learning-gap-check](https://github.com/PerryLink/dsh-learning-gap-check)** |  |
| **[dsh-library](https://github.com/PerryLink/dsh-library)** |  |
| **[dsh-local-ai](https://github.com/PerryLink/dsh-local-ai)** |  |
| **[dsh-lsp-actions](https://github.com/PerryLink/dsh-lsp-actions)** |  |
| **[dsh-mask](https://github.com/PerryLink/dsh-mask)** |  |
| **[dsh-mcp-panel](https://github.com/PerryLink/dsh-mcp-panel)** |  |
| **[dsh-medrec-qc](https://github.com/PerryLink/dsh-medrec-qc)** |  |
| **[dsh-memento](https://github.com/PerryLink/dsh-memento)** |  |
| **[dsh-nsfc-form-check](https://github.com/PerryLink/dsh-nsfc-form-check)** |  |
| **[dsh-nurse-record-check](https://github.com/PerryLink/dsh-nurse-record-check)** |  |
| **[dsh-observe](https://github.com/PerryLink/dsh-observe)** |  |
| **[dsh-origin-rvc-check](https://github.com/PerryLink/dsh-origin-rvc-check)** |  |
| **[dsh-ota-review-check](https://github.com/PerryLink/dsh-ota-review-check)** |  |
| **[dsh-output-styles](https://github.com/PerryLink/dsh-output-styles)** |  |
| **[dsh-paper-doc-adapter](https://github.com/PerryLink/dsh-paper-doc-adapter)** |  |
| **[dsh-permission-rules](https://github.com/PerryLink/dsh-permission-rules)** |  |
| **[dsh-permit-report-check](https://github.com/PerryLink/dsh-permit-report-check)** |  |
| **[dsh-pipeline-check](https://github.com/PerryLink/dsh-pipeline-check)** |  |
| **[dsh-pleading-draft](https://github.com/PerryLink/dsh-pleading-draft)** |  |
| **[dsh-plugin-doctor](https://github.com/PerryLink/dsh-plugin-doctor)** |  |
| **[dsh-plugin-guide](https://github.com/PerryLink/dsh-plugin-guide)** |  |
| **[dsh-plugin-kit](https://github.com/PerryLink/dsh-plugin-kit)** |  |
| **[dsh-plugin-upgrade](https://github.com/PerryLink/dsh-plugin-upgrade)** |  |
| **[dsh-policy-brief-draft](https://github.com/PerryLink/dsh-policy-brief-draft)** |  |
| **[dsh-power-loss-split](https://github.com/PerryLink/dsh-power-loss-split)** |  |
| **[dsh-power-ticket-check](https://github.com/PerryLink/dsh-power-ticket-check)** |  |
| **[dsh-ppap-check](https://github.com/PerryLink/dsh-ppap-check)** |  |
| **[dsh-protest-deadline](https://github.com/PerryLink/dsh-protest-deadline)** |  |
| **[dsh-railway-window](https://github.com/PerryLink/dsh-railway-window)** |  |
| **[dsh-repair-order-qc](https://github.com/PerryLink/dsh-repair-order-qc)** |  |
| **[dsh-research-report](https://github.com/PerryLink/dsh-research-report)** |  |
| **[dsh-review-reply-check](https://github.com/PerryLink/dsh-review-reply-check)** |  |
| **[dsh-rulefile-check](https://github.com/PerryLink/dsh-rulefile-check)** |  |
| **[dsh-safety-brief-check](https://github.com/PerryLink/dsh-safety-brief-check)** |  |
| **[dsh-score](https://github.com/PerryLink/dsh-score)** |  |
| **[dsh-session-sync](https://github.com/PerryLink/dsh-session-sync)** |  |
| **[dsh-site-log-check](https://github.com/PerryLink/dsh-site-log-check)** |  |
| **[dsh-skill-pack-security](https://github.com/PerryLink/dsh-skill-pack-security)** |  |
| **[dsh-soe-decision-check](https://github.com/PerryLink/dsh-soe-decision-check)** |  |
| **[dsh-soilwater-check](https://github.com/PerryLink/dsh-soilwater-check)** |  |
| **[dsh-sop-sync-check](https://github.com/PerryLink/dsh-sop-sync-check)** |  |
| **[dsh-spc-gbt-adapter](https://github.com/PerryLink/dsh-spc-gbt-adapter)** |  |
| **[dsh-talk](https://github.com/PerryLink/dsh-talk)** |  |
| **[dsh-tender-extract](https://github.com/PerryLink/dsh-tender-extract)** |  |
| **[dsh-tender-matrix](https://github.com/PerryLink/dsh-tender-matrix)** |  |
| **[dsh-test-drive](https://github.com/PerryLink/dsh-test-drive)** |  |
| **[dsh-ticktick](https://github.com/PerryLink/dsh-ticktick)** |  |
| **[dsh-translate](https://github.com/PerryLink/dsh-translate)** |  |
| **[dsh-warranty-calc](https://github.com/PerryLink/dsh-warranty-calc)** |  |
| **[dsh-budget](https://github.com/PerryLink/dsh-budget)** | 🧊 FROZEN — see the repo README |
| **[dsh-claude-move](https://github.com/PerryLink/dsh-claude-move)** | 🧊 FROZEN — see the repo README |
| **[dsh-defend](https://github.com/PerryLink/dsh-defend)** | 🧊 FROZEN — see the repo README |
| **[dsh-draw](https://github.com/PerryLink/dsh-draw)** | 🧊 FROZEN — see the repo README |
| **[dsh-reach](https://github.com/PerryLink/dsh-reach)** | 🧊 FROZEN — see the repo README |
| **[dsh-background-agents](https://github.com/PerryLink/dsh-background-agents)** | 🚫 RETIRED — see the repo README |
| **[dsh-session-pin](https://github.com/PerryLink/dsh-session-pin)** | 🚫 RETIRED — see the repo README |
| **[dsh-team-rooms](https://github.com/PerryLink/dsh-team-rooms)** | 🚫 RETIRED — see the repo README |

</details>

## License

[Apache License 2.0](LICENSE) © 2026 dsh-power-ticket-check contributors.

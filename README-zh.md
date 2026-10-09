# dsh-power-ticket-check — 电力工作票要素齐备性与签发许可终结顺序核对

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-power-ticket-check` 读取一份 **电力工作票**——以票面栏目名为键、栏目取值为值的平铺映射，外加票上列出的人员角色——按一张票面能被要求到的范围核对：本机构配置的 `requiredFields` 各栏是否都已填写、工作票种类是否在本机构列出的票种之内、签发时间 → 许可时间 → 终结时间 的顺序是否物理上成立、延期时间是否把结束时间向后推且不早于许可时间、本机构配置为须分设的角色是否由不同人员担任，以及安全措施与许可文本中是否出现规则库要求核对的安全技术措施五项与许可手续三项关键词。未能执行的检查逐条列在 `skipped` 并写明原因，而不是静默通过。

## 实际输出长什么样

![Terminal demo of dsh-power-ticket-check: real output over its PT-003 fixture](https://raw.githubusercontent.com/PerryLink/dsh-power-ticket-check/main/docs/assets/dsh-power-ticket-check-demo.png)

本插件对自己 `PT-003` 测试夹具的**真实输出**，不是示意图。规则库不伪造引文，因此每条发现都会同时写明所引条款，以及该条款原文本次未取得。

## 它回答什么问题

| 你会问 | 它怎么答 |
|---|---|
| 出厂状态下，随便一份工作票都能通过，为什么？ | 因为 `PT-001` 是以 `skipped` 自报，不是判定通过。它的 `requiredFields` 清单出厂为空，本条无法执行；请按本机构票面把必填栏目填进去。即便配置好后，`PT-001` 也只核对栏目是否填写，不判断填写内容是否正确，且严重级为 `info`。 |
| 票种填的是电气第一种工作票，工作性质却写着带电作业，这种矛盾会报出吗？ | 不会。`PT-002` 只报两种情况：工作票种类没有填写，或所填种类不在本机构列出的票种之内。它的 `ticketKinds` 清单出厂为空，此时本条以 `skipped` 自报——`PT-005` 在 `exclusiveRolePairs` 清单为空时也是如此；本插件不判断该作业应当使用哪一种票。把清单填上以后，可把 `PT-005` 的角色对配成工作许可人与工作负责人，同一人同时出现在这两栏时即会报出。两条规则都不判断人员资格，也不判断兼职是否经批准。 |
| 许可时间写得比签发时间还早，另有一个时间栏的格式读不出来。 | `PT-003` 两种情况都会报：许可时间早于签发时间、终结时间早于许可时间，以及读不出来的栏目报为无法解析为日期时间，提示应按本机构统一写法填写，如 `2026-03-15 08:30`。它把两端都换算为绝对分钟数比较，跨天填写也算得准。若签发时间或许可时间完全读不出来，本条改为以 `skipped` 自报，因为顺序核对不成立。它不判断实际作业是否按票执行；可选的间隔与时长上限由使用方自行配置。 |
| 延期时间早于计划结束时间，等于把工期改短了。 | `PT-004` 会报出，延期时间早于许可时间也一并报出。标准未规定延期可以延长多久、可以办几次，因此本条不带任何量化上限，也不判断延期手续是否齐备。 |
| 安全措施栏写了内容，但只提到停电和验电。 | `PT-006` 会逐项报出缺少的三项。本条是本库唯一使用 `error` 级的规则，因为其依据 6.1.1 落在强制性章节；它只核对票面是否写到这五项，不判断措施内容是否与现场相符、是否执行到位。若找不到可读取的安全措施栏目，本条以 `skipped` 自报。 |
| 票面上看不出工作许可人曾会同工作负责人再到现场复查。 | `PT-007` 会报出它所读取的文本中缺少三项许可手续里的哪几项，读取范围是 `permitColumns` 这些栏目加上各角色栏的人名。它只做字面核对：现场是否真的复查过，它无从判断；若本机构要求这类问题阻断流程，可在规则库中直接提高本条严重级，不必改代码。 |

## 依据的标准

| 文件 | 文号 | 引用它的规则 |
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

| 项目 | 状态 |
|---|---|
| Harness | 对等版本范围 `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` —— 已实测同时接受 `0.2.0-rc.2` 与 `0.2.1-alpha.1`。**刻意不声明 `engines.dsh`**：它没有任何读取者，也无法拒装任何宿主 |
| Node | `^22.19.0 || >=24.0.0` |
| 平台 | 全平台（纯 ESM；无原生代码、无联网、不调用模型） |
| 工具模式 | `native` / `ptc` / `both` 均可；批量校验整个目录时建议 `ptc`，schema 成本只付一次 |

## What it does

规则表、字段说明与行为细节见 [README.md](README.md#what-it-does)（英文主版本）。本插件只列出材料与所引条款之间的字面差异，并对无法执行的检查在 `skipped` 中逐项说明。

## Install

```sh
dsh plugin --profile <name> add dsh-power-ticket-check
dsh --profile <name> --dump-config | grep 'dsh-power-ticket-check'
```

## Configuration

全部可调参数都在 `src/config.ts` 的 Schemastery schema 中，只改 `cordis.yml` 即可生效，无需改代码；逐条阈值在 `rules/` 下的规则库文件里。

| 键 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `rulesFile` | string | `rules/power-ticket-check.yaml` | 规则库文件路径，相对插件包根目录 |
| `disabledRules` | string[] | `[]` | 要停用的规则 id 列表；每条都会出现在 `skipped` 中 |
| `onlyRules` | string[] | `[]` | 只执行这些规则 id；留空表示执行全部规则 |
| `skipNotes` | string | `""` | 附加到每条 `skipped` 说明后的备注 |
| `timeoutMs` | number | `120000` | 工具协作式超时预算（毫秒） |

## Material format

支持 JSON 与 YAML。完整字段示例见 [README.md](README.md#material-format)（英文主版本）。字段在读取层是可选的，由检查引擎校验，因此部分导出的材料会产生"缺项"类差异，而不是让程序崩溃。

## Rule sources

规则数据与代码分离，每条规则都带文件名、文号、按原文自身编号体系的条款号、逐字摘录与来源地址。加载期强制：摘录必须是真实引文且不少于八个字符；依据仅为原则性条款（`kind: derived-from-principle`，严重级上限 `warn`）或本机构配置（`kind: institutional-configuration`，上限 `info`）的检查不得标为 `error`。夸大依据的规则库会在加载期失败，而不会产出一份看起来很有底气的报告。

核验中确认的边界与"刻意没有作出的结论"见 [README.md](README.md#rule-sources)（英文主版本）与随包的 `rules/evidence/` 目录。

## Troubleshooting

- **插件装上了但工具不出现**：确认 `main` 指向 `lib/index.mjs` 且 `pnpm run build` 已生成该文件；`main` 写错会让加载器静默跳过该条目。
- **`dsh plugin add` 报版本不兼容**：peer 范围覆盖 `0.1.x` 与 `0.2.x`；若运行时在其之外，可显式豁免：`dsh plugin --profile <name> allow-version <包名@版本> --dsh-version <runtime> --accept-risk`
- **某条规则没有执行**：查看 `skipped` 数组，其中写明了规则 id 与原因。
- **`check` 报 `manifest-peers` 失败**：静态检查器比对的是一份早于 0.2 世代的硬编码 peer 范围；安装期的 peer 校验以运行时为准。这是 `dsh-plugin-dev` 的已知上游问题。
- **时间看起来偏移**：全部计算都是对输入字符串做墙上时钟运算，不做时区换算。

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-power-ticket-check
```

第 4 项把 `../_shared` 的共享件同步进 `src/shared/`；每次改动共享件后都要重跑。

## License

[Apache License 2.0](LICENSE) © 2026 dsh-power-ticket-check contributors.

# dsh-power-ticket-check — Verificação da completude do permiso de trabalho elétrico e da ordem de emissão, autorização e encerramento

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-power-ticket-check` lê um **电力工作票** como um mapa plano dos nomes das colunas do próprio formulário para os respetivos valores, em conjunto com os papéis nele indicados, e verifica o que se pode exigir a um formulário: que todas as colunas do seu `requiredFields` configurado estejam preenchidas, que o 工作票种类 conste dos que a sua implantação declara, que 签发时间 → 许可时间 → 终结时间 formem uma sequência fisicamente possível, que um 延期时间 empurre o fim para a frente e não seja anterior à autorização, que os papéis configurados como exclusivos sejam desempenhados por pessoas diferentes, e que o texto das medidas de segurança e da autorização contenha os cinco termos de 安全技术措施 e os três de 许可手续 que o pacote procura. As verificações que não puderam ser executadas são listadas em `skipped` com o respetivo motivo, em vez de passarem em silêncio.

## Como é a saída

![Terminal demo of dsh-power-ticket-check: real output over its PT-003 fixture](https://raw.githubusercontent.com/PerryLink/dsh-power-ticket-check/main/docs/assets/dsh-power-ticket-check-demo.png)

Saída real deste plugin sobre o seu próprio fixture de teste `PT-003` — não é uma simulação. O pacote de regras não inventa citações, por isso cada achado nomeia a cláusula aplicada e avisa que o seu texto não foi obtido.

## O que ele responde

| Você pergunta | O que ele responde |
|---|---|
| Tal como vem, aprova todos os permís que lhe passo, por quê? | Porque `PT-001` declara-se a si mesma em `skipped`, e não como aprovada. A sua lista `requiredFields` vem vazia, pelo que a regra não pode ser executada; preencha-a com as colunas que o seu próprio formulário exige. Mesmo configurada, `PT-001` verifica que a coluna está preenchida, não que o valor esteja correto, e o seu nível é `info`. |
| O permís é um 电气第一种工作票 mas a 工作性质 menciona 带电作业 — isso é reportado como contradição? | Não. `PT-002` reporta apenas duas coisas: que falte o 工作票种类, ou que não conste dos tipos que a sua implantação declara. A sua lista `ticketKinds` vem vazia e a regra declara-se então em `skipped`, tal como `PT-005` quando a sua lista `exclusiveRolePairs` está vazia; o plugin não decide de que tipo de permís uma tarefa precisa. Depois de preencher essas listas, configure `PT-005` com o par 工作许可人 e 工作负责人 para que a mesma pessoa nas duas colunas seja reportada. Nenhuma das regras julga a habilitação de alguém nem se foi autorizado acumular dois papéis. |
| O 许可时间 está escrito antes do 签发时间, e além disso uma coluna de tempo não é analisável. | `PT-003` reporta ambas as coisas: o 许可时间 anterior ao 签发时间, o 终结时间 anterior ao 许可时间, e qualquer coluna ilegível como 无法解析为日期时间, esperando uma forma como `2026-03-15 08:30`. Ambos os extremos são convertidos num total absoluto de minutos, pelo que um permís que atravessa a meia-noite é comparado corretamente. Se o 签发时间 ou o 许可时间 não puderem ser lidos de todo, a regra declara-se em `skipped`, porque a verificação da ordem não pode ser estabelecida. Nunca verifica se o trabalho seguiu realmente o permís, e o limite opcional de intervalo ou de duração é você quem o configura. |
| O 延期时间 é anterior ao 计划结束时间, pelo que a prorrogação encurta o trabalho em vez de o prolongar. | `PT-004` reporta-o, e reporta também um 延期时间 anterior ao 许可时间. A norma não fixa qualquer limite a quanto nem a quantas vezes um permís pode ser prorrogado, pelo que a regra não tem limite quantitativo nem verifica se as formalidades da prorrogação foram cumpridas. |
| A coluna 安全措施 está preenchida, mas menciona apenas 停电 e 验电. | `PT-006` reporta os três termos em falta, um por um. É a única regra aqui com nível `error`, porque a sua cláusula 6.1.1 está no capítulo obrigatório, e verifica que as cinco medidas estão escritas no permís, não que correspondam ao local ou tenham sido executadas. Se não encontrar nenhuma coluna de medidas legível, declara-se em `skipped`. |
| Nada no permís mostra que o 工作许可人 tenha voltado ao local com o 工作负责人. | `PT-007` reporta quais dos três termos das formalidades de autorização faltam no texto que lê, e esse texto são as `permitColumns` mais os nomes das colunas de papel. Lê apenas a redação: não pode saber se a revisão do local aconteceu de facto, e uma instituição que queira que isto bloqueie pode subir o nível da regra no pacote sem tocar no código. |

## Normas que segue

| Documento | Número | Regras que o citam |
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

| Superfície | Estado |
|---|---|
| Harness | Faixa de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificada para aceitar tanto `0.2.0-rc.2` quanto `0.2.1-alpha.1`. **`engines.dsh` não é declarado**: não tem leitor e não pode recusar nenhum host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sem código nativo, sem rede, sem chamada ao modelo) |
| Modo de ferramenta | Funciona em `native`, `ptc` e `both`; para um diretório inteiro use `ptc` |

## What it does

A tabela de regras, os campos e o comportamento detalhado estão em [README.md](README.md#what-it-does) (versão principal em inglês). O plugin apenas lista divergências literais frente às cláusulas citadas e indica em `skipped` cada verificação que não pôde ser executada.

## Install

```sh
dsh plugin --profile <name> add dsh-power-ticket-check
dsh --profile <name> --dump-config | grep 'dsh-power-ticket-check'
```

## Configuration

Todos os parâmetros ajustáveis ficam no esquema Schemastery de `src/config.ts`, portanto mudam pelo `cordis.yml` sem editar código; os limites por regra ficam no pacote de regras sob `rules/`.

| Chave | Tipo | Padrão | Descrição |
|---|---|---|---|
| `rulesFile` | string | `rules/power-ticket-check.yaml` | Caminho do pacote de regras, relativo à raiz do pacote |
| `disabledRules` | string[] | `[]` | Ids de regras a desativar; cada uma aparece em `skipped` |
| `onlyRules` | string[] | `[]` | Executar apenas estas regras; vazio executa todas |
| `skipNotes` | string | `""` | Nota acrescentada a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Orçamento de tempo limite cooperativo da ferramenta |

## Material format

Aceita JSON ou YAML. O exemplo completo de campos está em [README.md](README.md#material-format) (versão principal em inglês). Os campos são opcionais na camada de leitura e validados pelo motor, de modo que uma exportação parcial gera achados sobre o que falta em vez de falhar.

## Rule sources

Os dados das regras ficam separados do código: cada regra traz documento, número, cláusula na numeração própria da fonte, trecho literal e URL de origem. O carregador impõe que o trecho seja citação real de pelo menos oito caracteres e que uma verificação baseada apenas em princípio geral (`kind: derived-from-principle`, teto `warn`) ou em política local (`kind: institutional-configuration`, teto `info`) nunca seja declarada `error`.

Os limites verificados e as conclusões deliberadamente **não** afirmadas estão em [README.md](README.md#rule-sources) (versão principal em inglês) e em `rules/evidence/`.

## Troubleshooting

- **O plugin instala mas a ferramenta não aparece**: confirme que `main` resolve para `lib/index.mjs` e que `pnpm run build` o gerou.
- **`dsh plugin add` recusa o pacote**: a faixa de peers cobre `0.1.x` e `0.2.x`; fora dela, conceda isenção explícita com `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Uma regra não executou**: leia o arranjo `skipped`.
- **`check` informa `manifest-peers` como falha**: problema conhecido do `dsh-plugin-dev`; o runtime aplica a compatibilidade na instalação.
- **Os horários parecem deslocados**: toda a aritmética é de hora local sobre as cadeias fornecidas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-power-ticket-check
```

O último comando copia o kit compartilhado de `../_shared` para `src/shared/`; execute-o novamente após cada alteração compartilhada.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-power-ticket-check contributors.

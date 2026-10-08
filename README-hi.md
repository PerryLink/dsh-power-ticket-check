# dsh-power-ticket-check — विद्युत कार्य-अनुज्ञप्ति की पूर्णता तथा निर्गमन, अनुमति और समापन के क्रम की जाँच

`dsh-power-ticket-check` एक **电力工作票** को उसके अपने कॉलम नामों से मानों तक के सपाट मैपिंग के रूप में पढ़ता है — साथ में उस पर अंकित भूमिकाएँ — और उस अनुज्ञप्ति की वह जाँच करता है जो एक फ़ॉर्म से अपेक्षित की जा सकती है: आपके कॉन्फ़िगर किए गए `requiredFields` के हर कॉलम में मान भरा हो, 工作票种类 आपकी संस्था द्वारा सूचीबद्ध किस्मों में से हो, 签发时间 → 许可时间 → 终结时间 का क्रम भौतिक रूप से संभव हो, 延期时间 अंत को आगे बढ़ाए और अनुमति से पहले न हो, जिन भूमिकाओं को आपने अलग-अलग रखने के लिए कॉन्फ़िगर किया है वे अलग-अलग व्यक्तियों के हों, तथा सुरक्षा-उपाय और अनुमति के पाठ में नियम-पैक द्वारा खोजे जाने वाले 安全技术措施 के पाँच और 许可手续 के तीन शब्द मौजूद हों। जो जाँचें चल नहीं सकीं, वे चुपचाप पास होने के बजाय कारण के साथ `skipped` में दर्ज होती हैं।

## यह किन सवालों का जवाब देता है

| आपका सवाल | इसका जवाब |
|---|---|
| जैसा यह आता है, मेरी हर अनुज्ञप्ति इसमें पास हो जाती है — क्यों? | क्योंकि `PT-001` स्वयं को पास के रूप में नहीं, `skipped` में दर्ज करता है। उसकी `requiredFields` सूची खाली आती है, इसलिए यह नियम चल ही नहीं सकता; उसमें अपने फ़ॉर्म के अनिवार्य कॉलम भरें। कॉन्फ़िगर होने पर भी `PT-001` यह देखता है कि कॉलम भरा है, यह नहीं कि उसमें लिखा मान सही है, और उसका स्तर `info` है। |
| अनुज्ञप्ति 电气第一种工作票 है पर 工作性质 में 带电作业 लिखा है — क्या यह विरोधाभास दर्ज होता है? | नहीं। `PT-002` केवल दो बातें दर्ज करता है: कि 工作票种类 ही नहीं लिखा, या वह आपकी संस्था द्वारा सूचीबद्ध किस्मों में नहीं है। उसकी `ticketKinds` सूची खाली आती है और तब यह नियम स्वयं को `skipped` में दर्ज करता है — ठीक वैसे ही जैसे `PT-005` अपनी `exclusiveRolePairs` सूची खाली होने पर करता है; किस काम के लिए कौन-सी अनुज्ञप्ति चाहिए, यह प्लगइन तय नहीं करता। इन सूचियों को भरने के बाद `PT-005` में 工作许可人 और 工作负责人 का युग्म कॉन्फ़िगर करें, ताकि दोनों कॉलमों में एक ही व्यक्ति दर्ज हो। कोई भी नियम किसी की योग्यता या दो भूमिकाएँ रखने की अनुमति की जाँच नहीं करता। |
| 许可时间 签发时间 से पहले लिखा है, और एक समय-कॉलम पढ़ा भी नहीं जा सकता। | `PT-003` दोनों दर्ज करता है: 许可时间 का 签发时间 से पहले होना, 终结时间 का 许可时间 से पहले होना, और किसी भी अपठनीय कॉलम को 无法解析为日期时间 के रूप में, `2026-03-15 08:30` जैसी लेखन-शैली की अपेक्षा के साथ। दोनों सिरों को पूर्ण मिनट-गणना में बदला जाता है, इसलिए आधी रात पार करने वाली अनुज्ञप्ति भी ठीक तुलना में आती है। यदि 签发时间 या 许可时间 बिल्कुल पढ़ा ही न जा सके, तो यह नियम स्वयं को `skipped` में दर्ज करता है, क्योंकि क्रम की जाँच तब सिद्ध नहीं होती। यह कभी नहीं देखता कि काम वास्तव में अनुज्ञप्ति के अनुसार हुआ; वैकल्पिक अंतराल या अवधि-सीमा आप स्वयं कॉन्फ़िगर करते हैं। |
| 延期时间 计划结束时间 से पहले है, यानी मंज़ूरी काम को बढ़ाने के बजाय घटा रही है। | `PT-004` इसे दर्ज करता है, और 许可时间 से पहले के 延期时间 को भी दर्ज करता है। मानक में यह तय नहीं है कि मंज़ूरी कितनी लंबी या कितनी बार हो सकती है, इसलिए इस नियम में कोई मात्रात्मक सीमा नहीं है और यह नहीं देखता कि मंज़ूरी की औपचारिकताएँ पूरी हुईं या नहीं। |
| 安全措施 कॉलम भरा है, पर उसमें केवल 停电 और 验电 का उल्लेख है। | `PT-006` छूटे हुए तीन शब्द एक-एक करके दर्ज करता है। यहाँ यह अकेला `error` स्तर का नियम है, क्योंकि उसका खंड 6.1.1 अनिवार्य अध्याय में है, और यह देखता है कि पाँचों उपाय अनुज्ञप्ति पर लिखे हैं, यह नहीं कि वे साइट से मेल खाते हैं या पूरे किए गए। यदि कोई पठनीय उपाय-कॉलम न मिले, तो यह स्वयं को `skipped` में दर्ज करता है। |
| अनुज्ञप्ति से यह नहीं दिखता कि 工作许可人 工作负责人 के साथ दोबारा साइट पर गया। | `PT-007` उन तीन अनुमति-औपचारिकता शब्दों में से जो उसके पढ़े गए पाठ में नहीं हैं, उन्हें दर्ज करता है — और वह पाठ `permitColumns` तथा भूमिका-कॉलमों के नामों से बनता है। यह केवल शब्दों की जाँच है: साइट पर दोबारा निरीक्षण वास्तव में हुआ या नहीं, यह बता नहीं सकता; और यदि आपकी संस्था चाहे कि यह प्रक्रिया रोके, तो कोड बदले बिना नियम-पैक में इसका स्तर बढ़ाया जा सकता है। |

## यह किन मानकों पर आधारित है

| दस्तावेज़ | संख्यांक | इन्हें उद्धृत करने वाले नियम |
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

| सतह | स्थिति |
|---|---|
| Harness | peer रेंज `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — `0.2.0-rc.2` और `0.2.1-alpha.1` दोनों को स्वीकार करने के लिए सत्यापित। **`engines.dsh` जानबूझकर घोषित नहीं**: इसका कोई पाठक नहीं और यह किसी होस्ट को अस्वीकार नहीं कर सकता |
| Node | `^22.19.0 || >=24.0.0` |
| प्लेटफ़ॉर्म | सभी (शुद्ध ESM; कोई नेटिव कोड नहीं, कोई नेटवर्क नहीं, कोई मॉडल कॉल नहीं) |
| टूल मोड | `native`, `ptc` और `both` में काम करता है; पूरे फ़ोल्डर के लिए `ptc` चुनें |

## What it does

नियम-सूची, फ़ील्ड और विस्तृत व्यवहार [README.md](README.md#what-it-does) (अंग्रेज़ी मुख्य संस्करण) में हैं। यह प्लगइन केवल उद्धृत धाराओं के सामने शाब्दिक अंतर सूचीबद्ध करता है और हर न चल पाई जाँच को `skipped` में बताता है।

## Install

```sh
dsh plugin --profile <name> add dsh-power-ticket-check
dsh --profile <name> --dump-config | grep 'dsh-power-ticket-check'
```

## Configuration

सभी समायोज्य पैरामीटर `src/config.ts` की Schemastery स्कीमा में हैं, इसलिए कोड बदले बिना `cordis.yml` से बदले जा सकते हैं; प्रति-नियम सीमाएँ `rules/` के नियम-पैक में हैं।

| कुंजी | प्रकार | डिफ़ॉल्ट | विवरण |
|---|---|---|---|
| `rulesFile` | string | `rules/power-ticket-check.yaml` | नियम-पैक का पथ, पैकेज रूट के सापेक्ष |
| `disabledRules` | string[] | `[]` | बंद करने वाले नियम id; प्रत्येक `skipped` में दिखता है |
| `onlyRules` | string[] | `[]` | केवल ये नियम चलाएँ; खाली होने पर सभी नियम चलते हैं |
| `skipNotes` | string | `""` | हर `skipped` कारण के आगे जोड़ी जाने वाली टिप्पणी |
| `timeoutMs` | number | `120000` | उपकरण का सहकारी समय-सीमा बजट |

## Material format

JSON या YAML स्वीकार्य है। पूरा फ़ील्ड उदाहरण [README.md](README.md#material-format) (अंग्रेज़ी मुख्य संस्करण) में है। पढ़ने की परत में फ़ील्ड वैकल्पिक हैं और जाँच इंजन उन्हें सत्यापित करता है, इसलिए आंशिक निर्यात पर क्रैश के बजाय "अनुपस्थित" श्रेणी के निष्कर्ष मिलते हैं।

## Rule sources

नियम-डेटा कोड से अलग है: प्रत्येक नियम में दस्तावेज़, संख्या, स्रोत की अपनी क्रमांकन-प्रणाली के अनुसार धारा, शब्दशः उद्धरण और स्रोत URL होता है। लोडर लागू करता है कि उद्धरण कम से कम आठ अक्षरों का वास्तविक उद्धरण हो, और जिस जाँच का आधार केवल सामान्य सिद्धांत (`kind: derived-from-principle`, अधिकतम `warn`) या स्थानीय नीति (`kind: institutional-configuration`, अधिकतम `info`) हो, उसे कभी `error` घोषित न किया जाए।

सत्यापित सीमाएँ और जान-बूझकर **न** कहे गए निष्कर्ष [README.md](README.md#rule-sources) (अंग्रेज़ी मुख्य संस्करण) और `rules/evidence/` में हैं।

## Troubleshooting

- **प्लगइन इंस्टॉल हो गया पर टूल दिखता नहीं**: जाँचें कि `main` `lib/index.mjs` पर जाता है और `pnpm run build` ने उसे बनाया है।
- **`dsh plugin add` असंगत बताकर मना करता है**: peer range `0.1.x` और `0.2.x` दोनों को कवर करती है; बाहर होने पर स्पष्ट छूट दें: `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`।
- **कोई नियम नहीं चला**: `skipped` सरणी देखें।
- **`check` में `manifest-peers` विफल दिखता है**: यह `dsh-plugin-dev` की ज्ञात अपस्ट्रीम समस्या है; रनटाइम इंस्टॉल के समय अनुकूलता लागू करता है।
- **समय खिसका हुआ लगता है**: सारी गणना दिए गए स्ट्रिंग पर वॉल-क्लॉक है।

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-power-ticket-check
```

अंतिम कमांड `../_shared` का साझा किट `src/shared/` में कॉपी करता है; हर साझा बदलाव के बाद इसे दोबारा चलाएँ।

## License

[Apache License 2.0](LICENSE) © 2026 dsh-power-ticket-check contributors.

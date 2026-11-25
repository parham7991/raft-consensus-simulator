# ۰۵ — ماژول‌های هستهٔ موتور

این سند ماژول‌های پوشش‌داده‌شده در فاز ۲ را شرح می‌دهد: مسئولیت هرکدام، امضای عمومی و ناوردایی‌هایی (invariants) که همه‌ی تست‌ها بر آن‌ها تکیه دارند. تغییر معماری = اول آپدیت این سند، بعد کد.

## نمودار وابستگی

```
cluster ──► network ──► (هیچ ماژول داخلی دیگری)
   │            ▲
   └──► node ───┘   (Node از Network فقط از طریق Cluster استفاده می‌کند)
state_machine و messages مستقل‌اند (messages فقط داده است)
```

## `raft/core/messages.py` — پیام‌های RPC *(تسک ۲٫۳)*

فقط dataclass؛ هیچ منطقی در این فایل نیست. فیلدها دقیقاً طبق مقاله‌ی Raft (§5.1–5.4):

| پیام | فیلدها |
|---|---|
| `RequestVote` | `term, candidate_id, last_log_index, last_log_term` |
| `VoteResponse` | `term, vote_granted` |
| `AppendEntries` | `term, leader_id, prev_log_index, prev_log_term, entries, leader_commit` |
| `AppendResponse` | `term, success, match_index` |

**ناوردایی:** هیچ RPCای بدون `term` وجود ندارد؛ گیرنده پیام با `term` کمتر از `current_term` خود را نادیده می‌گیرد.

## `raft/core/network.py` — شبکه‌ی صریح

| عضو | امضا | توضیح |
|---|---|---|
| `Envelope` | dataclass: `from_id, to_id, payload, sent_at, deliver_at` | پوشه‌ی پیام در حال پرواز |
| `Network.send` | `(from_id, to_id, payload, now, rng) -> Envelope` | `deliver_at = now + U(5, 20)ms` |
| `Network.deliver_due` | `(now) -> list[Envelope]` | به‌ترتیب `deliver_at`؛ قبل از سررسید چیزی تحویل نمی‌شود |
| `Network.set_link` | `(i, j, up: bool)` | **متقارن**: افت روی جفت `{i, j}` اعمال می‌شود |
| `Network.pending` | `() -> int` | تعداد پیام‌های در حال پرواز |
| `network.stats` | `{sent, delivered, dropped}` | — |

**ناوردایی‌ها:**

1. هر پیام ارسال‌شده دقیقاً یک‌بار حسابداری می‌شود: `sent == delivered + dropped`.
2. لینک پایین ⇒ drop قطعی (نه تأخیر) + رویداد `dropped`.
3. گرهٔ مقصد از کار افتاده ⇒ drop قطعی (از طریق `is_reachable` که توسط `Cluster` تزریق می‌شود).
4. ترتیب تحویل فقط با `deliver_at` است، نه ترتیب `send`.

## `raft/core/node.py` — گرهٔ Raft *(تسک ۲٫۳ تکمیل می‌شود)*

مرز حالت — این مهم‌ترین قرارداد فاز ۲ است:

| مانا (persisted) | فرار (volatile) |
|---|---|
| `current_term` | `commit_index` |
| `voted_for` | `last_applied` |
| `log` (هر entry: `{term, command}`) | نقش (`Role.FOLLOWER/CANDIDATE/LEADER`) و تایمرها |

**ناوردایی‌ها:**

1. `current_term` اکیداً غیرنزولی است؛ هرگز کم نمی‌شود.
2. ایندکس لاگ از **۱** شروع می‌شود؛ ایندکس ۰ sentinel با `term=0` است.
3. kill/restart: persisted دست‌نخورده می‌ماند؛ volatileها صفر می‌شوند؛ نقش `follower` می‌شود.
4. نقش اولیه `follower` است.

## `raft/core/cluster.py` — هماهنگ‌کننده

| عضو | امضا | توضیح |
|---|---|---|
| `Cluster.__init__` | `(n=5, seed=42, on_event=None)` | پیش‌فرض ۵ گره، اکثریت ۳ |
| `cluster.now` | `float` (ms) | از ۰؛ فقط با `tick` جلو می‌رود — **ساعت شبیه‌سازی، نه ساعت واقعی** |
| `Cluster.tick` | `(dt_ms)` | زمان را جلو می‌برد، گره‌های زنده را tick می‌زند، بعد پیام‌های سررسیدشده را تحویل می‌دهد |
| `Cluster.kill / restart` | `(node_id)` | گره را از مدار خارج/وارد می‌کند؛ رویداد `down`/`up` |
| `Cluster.set_link` | `(i, j, up)` | پروکسی به Network (متقارن) |
| `Cluster.on_event` | `(cb)` | ثبت listener؛ همه‌ی رویدادها (`sent/delivered/dropped/down/up/link_down/link_up`) به همهٔ listenerها می‌رسند |
| `Cluster.majority` | `() -> int` | `⌊n/2⌋ + 1` |
| `Cluster.alive_nodes` | `() -> list` | گره‌های غیر kill‌شده |

**ناوردایی‌ها:**

1. هیچ RPCای ناپدید نمی‌شود: `sent == delivered + dropped` (تست `test_headless_tick_loses_no_message_accounting`).
2. گرهٔ kill‌شده tick نمی‌خورد و پیام دریافتی‌اش drop می‌شود (با رویداد).
3. همه‌چیز با `seed` بازتولیدپذیر است؛ هیچ تستی به ساعت واقعی وصل نیست.

## قرارداد رویدادها (برای فاز ۶/۷ — پل WS و UI)

`cb(event: dict)` با کلید مشترک `type`. انواع فاز ۲: `sent`, `delivered`, `dropped`, `down`, `up`, `link_up`, `link_down`. از فاز ۳ به بعد: `election`, `vote`, `append`, `commit`. ترتیب رویدادها، ترتیب رخدادشان در tick است.

## چیزهایی که عمداً در فاز ۲ نیست

انتخابات واقعی (فاز ۳)، `AppendEntries`/commit (فاز ۴)، پارتیشن/heal سناریوها (فاز ۵)، `StateMachine` اعمال روی committed entries (در ۲٫۳ تعریف، اعمال واقعی در ۴)، پل WebSocket (فاز ۶).

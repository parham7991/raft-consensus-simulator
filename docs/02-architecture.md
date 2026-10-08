# ۰۲ — معماری سیستم

## انتخاب فناوری

| لایه | فناوری | دلیل |
|---|---|---|
| موتور شبیه‌سازی | **Python 3.11+ / asyncio** | زبان مجازِ صورت پروژه؛ مدل هم‌روندی طبیعی برای گره‌های مستقل |
| پل ارتباطی | **WebSocket** (کتابخانهٔ سبک `websockets`) | استریم رویدادها به UI با تأخیر نزدیک به صفر |
| لایهٔ نمایش | **Vanilla JS + SVG + CSS** | بدون build step؛ باز شدن مستقیم روی GitHub Pages و هر مرورگری |
| تست | **pytest** | تست واحد ماژول‌ها + تست یکپارچهٔ سناریوها |

> شبیه‌ساز آموزشی است، نه Raft تولیدی: دیسک واقعی، snapshot و membership change در نسخهٔ ۱ نیستند (خارج از دامنه — ثبت در Issueهای آینده).

## دیاگرام کلان

```
┌──────────────────────────── مرورگر ────────────────────────────┐
│  web/index.html + ui.js + style.css                            │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ SVG topology│  │ per-node logs│  │ event stream & controls │  │
│  └─────▲──────┘  └──────▲───────┘  └───────────▲─────────────┘  │
│        └───────────────┴──── state store ──────┘               │
└──────────────────────────────┬─────────────────────────────────┘
                     WebSocket │  (رویدادها: election, vote, append,
                               │   commit, drop, down, up …)
┌──────────────────────────────▼─────────────────────────────────┐
│  raft/api/server.py  —  حلقهٔ asyncio + انتشار رویداد           │
├────────────────────────────────────────────────────────────────┤
│  raft/core/cluster.py — زمان شبیه‌سازی، صف پیام با تأخیر، لینک‌ها│
│  raft/core/network.py — تأخیر تصادفی، drop بر اساس پارتیشن     │
│  raft/core/node.py    — ماشین حالت Raft (Follower/Cand/Leader) │
│  raft/core/state_machine.py — اعمال دستورها پس از commit       │
└────────────────────────────────────────────────────────────────┘
```

## اصول طراحی موتور

1. **زمان شبیه‌سازی (Simulated Clock):** همهٔ تایمرها روی `cluster.now` کار می‌کنند، نه ساعت واقعی. UI یک ضریب سرعت دارد؛ تست‌ها time را deterministically جلو می‌برند.
2. **Network به‌عنوان شهروند درجه‌یک:** هر پیام `(from, to, sent_at, deliver_at)` در صف است؛ لینک پایین = drop + رویداد `dropped` برای نمایش.
3. **جدایی persisted/volatile state:** `currentTerm, votedFor, log` ماندگار؛ `commitIndex, nextIndex…` فرار. kill/restart دقیقاً همین مرز را شبیه‌سازی می‌کند.
4. **رویدادمحور برای UI:** موتور هیچ DOMای نمی‌شناسد؛ فقط رویداد منتشر می‌کند. این یعنی همان موتور، هم در تست headless و هم در مرورگر اجرا می‌شود.

## ماژول‌ها (امضای پیشنهادی)

```python
class RaftNode:      # id, state, current_term, voted_for, log[], commit_index
    def tick(dt)            # پیش‌روی تایمرها
    def receive(msg)        # پردازش RequestVote / AppendEntries / پاسخ‌ها
    def submit(cmd) -> int  # فقط روی Leader

class Cluster:       # nodes[], links{}, messages[], now
    def tick(dt)
    def kill(i) / restart(i)
    def set_link(i, j, up: bool)
    def on_event(cb)
```

## تست

- **واحد:** انتخابات تک‌رهبره، رد رأی با لاگ قدیمی، truncate صحیح، monotonic بودن term.
- **سناریو:** kill-leader، partition-majority/minority، heal، restart-catch-up — هرکدام assertion روی commitIndex و برابری لاگ‌ها.
- **E2E:** اجرای سرور + اتصال کلاینت WebSocket + دریافت رویداد elected/committed (فاز ۴).

➡️ [03-roadmap.md](03-roadmap.md) · [01-raft-theory.md](01-raft-theory.md)

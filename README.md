<div align="center">

# 🛶 شبیه‌ساز تعاملی اجماع Raft
### Raft Consensus Simulator

**پروژهٔ درس اصول سیستم‌عامل — پاییز ۱۴۰۵**

[![Docs](https://img.shields.io/badge/📚_Docs-GitHub_Pages-1D76DB?style=for-the-badge)](https://parham7991.github.io/raft-consensus-simulator/)
[![License](https://img.shields.io/badge/License-MIT-E4B33C?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-0E8A16?style=for-the-badge)](https://www.python.org)
[![Status](https://img.shields.io/badge/Phase-0_%7C_Docs_%26_Roadmap-5319E7?style=for-the-badge)](docs/03-roadmap.md)

*یک شبیه‌ساز آموزشی و تعاملی برای الگوریتم اجماع Raft — با موتور پایتون و رابط وب زنده*

</div>

---

## 🎯 پروژه چیست؟

این مخزن، پروژهٔ شمارهٔ **۱۹** درس اصول سیستم‌عامل است: **شبیه‌سازی الگوریتم اجماع و توافق توزیع‌شده (Raft)**.
هدف، ساخت ابزاری است که رفتار واقعی یک خوشهٔ Raft را **به‌صورت زنده و قابل‌لمس** نشان دهد:

- 🗳️ **انتخاب رهبر (Leader Election)** با تایمرهای تصادفی و split vote
- 📜 **تکرار لاگ (Log Replication)** با مدیریت تضاد و truncate
- 💥 **تحمل خطا**: سقوط رهبر، پارتیشن شبکه، بازگشت رهبر قدیمی
- 🎛️ **کنترل تعاملی**: kill/restart گره‌ها، قطع لینک‌ها با کلیک، تزریق فرمان کلاینت
- 📊 **مشاهدهٔ زندهٔ لاگ هر گره** با رنگ‌بندی بر اساس Term

> 🐍 زبان مجاز طبق صورت پروژه: **Python** — موتور شبیه‌سازی با `asyncio` نوشته می‌شود و لایهٔ نمایش، یک رابط وب سبک (بدون فریم‌ورک سنگین) است تا «بهترین UI/UX ممکن» را برای دموی کلاسی فراهم کند.

## 🗺️ نقشهٔ راه — مرحله به مرحله

| مرحله | عنوان | وضعیت |
|---|---|---|
| ۰ | داکیومنت، معماری و راه‌اندازی مخزن | ✅ انجام شد |
| ۱ | هستهٔ انتخاب رهبر (Election) | 🔵 در جریان |
| ۲ | تکرار لاگ (Log Replication) | ⬜ بعدی |
| ۳ | تحمل خطا: Crash و Partition | ⬜ در صف |
| ۴ | رابط وب تعاملی + WebSocket | ⬜ در صف |
| ۵ | گزارش نهایی و ارائه | ⬜ پایانی |


جزئیات کامل هر فاز، معیار پذیرش (Definition of Done) و مدیریت ریسک در
📄 [docs/03-roadmap.md](docs/03-roadmap.md) — و نسخهٔ زندهٔ آن به‌صورت **Milestone و Issue** روی همین مخزن تعریف شده است.

## 📚 داکیومنت‌ها

| سند | محتوا |
|---|---|
| [docs/01-raft-theory.md](docs/01-raft-theory.md) | شرح کامل الگوریتم Raft به فارسی: Termها، نقش‌ها، انتخابات، تکرار لاگ، اثبات ایمنی |
| [docs/02-architecture.md](docs/02-architecture.md) | معماری سیستم: موتور asyncio، پل WebSocket، لایهٔ نمایش SVG |
| [docs/03-roadmap.md](docs/03-roadmap.md) | مراحل، معیار پذیرش و مدیریت ریسک |
| [docs/04-team.md](docs/04-team.md) | اعضای تیم، تقسیم کار و سیاست بازبینی |
| 🌐 [سایت داکیومنت](https://parham7991.github.io/raft-consensus-simulator/) | نسخهٔ وب زیبای همین داکیومنت‌ها (GitHub Pages) |

## 🏗️ ساختار مخزن

```
raft-consensus-simulator/
├── README.md                  # همین فایل
├── LICENSE                    # MIT
├── CONTRIBUTING.md            # قواعد مشارکت و جریان کاری
├── .github/
│   ├── ISSUE_TEMPLATE/        # قالب گزارش باگ و درخواست ویژگی
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── index.html             # سایت داکیومنت (GitHub Pages)
│   ├── 01-raft-theory.md
│   ├── 02-architecture.md
│   ├── 03-roadmap.md
│   └── 04-team.md
├── raft/                      # ← فاز ۱ به بعد: موتور شبیه‌سازی (Python)
│   ├── core/                  #    node.py, cluster.py, network.py
│   └── api/                   #    سرور WebSocket
├── web/                       # ← فاز ۴: رابط وب تعاملی
└── tests/                     # تست‌های واحد و سناریو (pytest)
```

## 🚀 اجرا (پس از پایان فاز ۱)

```bash
git clone https://github.com/parham7991/raft-consensus-simulator.git
cd raft-consensus-simulator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m raft.api.server          # موتور + WebSocket روی :8000
# سپس web/index.html را در مرورگر باز کنید
```

فعلاً (فاز ۰) فقط داکیومنت‌ها موجود است؛ سایت داکیومنت روی GitHub Pages فعال است.

## 👥 تیم

| عضو | گیت‌هاب | تلگرام | نقش پیشنهادی |
|---|---|---|---|
| پرهام خان‌محمدی | [@parham7991](https://github.com/parham7991) | [@Parham_7991](https://t.me/Parham_7991) | موتور Raft، تست‌ها، معماری |
| علی عرب‌محمدی | [@Alivrab](https://github.com/Alivrab) | [@c4llmeali](https://t.me/c4llmeali) | رابط وب، UI/UX، داکیومنت |

> هر Pull Request باید توسط عضو دیگر تیم **بازبینی و تأیید** شود — جزئیات در [CONTRIBUTING.md](CONTRIBUTING.md).

## 📖 منابع

1. Diego Ongaro & John Ousterhout, *"In Search of an Understandable Consensus Algorithm"*, USENIX ATC 2014 — [theraftpaper.com](https://raft.github.io/raft.pdf)
2. [The Secret Lives of Data — Raft animated intro](http://thesecretlivesofdata.com/raft/)
3. [raft.github.io — منابع رسمی](https://raft.github.io)

## 📜 مجوز

MIT © ۲۰۲۶ پرهام خان‌محمدی و علی عرب‌محمدی — متن کامل در [LICENSE](LICENSE).

---
<div align="center"> ساخته‌شده با ❤️ برای درس اصول سیستم‌عامل </div>

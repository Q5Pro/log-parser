# 📋 log-parser

Nginx/Apache log dosyalarını ayrıştırır, istatistik üretir ve filtreli çıktı verir.

## Kurulum
```bash
go build -o log-parser .
```
## Kullanım
```bash
log-parser --stats access.log
log-parser --filter 404 access.log
log-parser --top-ips 10 access.log
```
## Lisans
MIT

---

> Made in [discord.gg/codeshare](https://discord.gg/codeshare) · [astra-dev.com.tr](https://astra-dev.com.tr)


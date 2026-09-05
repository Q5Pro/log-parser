"""
log-analyzer — Log dosyalarını analiz eder: hata sayıları, IP adresleri,
saat bazlı dağılım ve en sık tekrarlanan mesajlar.

Kullanım:
    python analyze.py access.log
    python analyze.py app.log --level ERROR
    python analyze.py *.log --top 20 --json
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LEVEL_COLORS = {
    "DEBUG": "\033[36m", "INFO": "\033[32m", "WARNING": "\033[33m",
    "ERROR": "\033[91m", "CRITICAL": "\033[95m",
}
RESET = "\033[0m"

IP_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
LEVEL_RE = re.compile(r"\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b")
HOUR_RE = re.compile(r"\b(\d{2}):\d{2}:\d{2}\b")


def analyze_file(path: str, level_filter: str = None) -> dict:
    lines = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Hata: '{path}' bulunamadı.", file=sys.stderr)
        return {}

    level_counts = Counter()
    ip_counts = Counter()
    hour_counts = Counter()
    messages = []

    for line in lines:
        # Seviye filtresi
        level_match = LEVEL_RE.search(line)
        level = level_match.group(1) if level_match else "OTHER"
        if level_filter and level != level_filter:
            continue

        level_counts[level] += 1

        for ip in IP_RE.findall(line):
            ip_counts[ip] += 1

        hour_match = HOUR_RE.search(line)
        if hour_match:
            hour_counts[int(hour_match.group(1))] += 1

        messages.append(line.strip())

    return {
        "file": path,
        "total_lines": len(lines),
        "matched_lines": len(messages),
        "level_counts": dict(level_counts),
        "top_ips": ip_counts.most_common(10),
        "hour_distribution": dict(sorted(hour_counts.items())),
        "top_messages": Counter(messages).most_common(5),
    }


def print_report(data: dict, top_n: int):
    if not data:
        return
    print(f"\n{'='*55}")
    print(f"  📋 {data['file']}")
    print(f"  Toplam: {data['total_lines']} satır | Eşleşen: {data['matched_lines']} satır")
    print(f"{'='*55}")

    if data["level_counts"]:
        print("\n📊 Seviye Dağılımı:")
        for level in LOG_LEVELS + ["OTHER"]:
            count = data["level_counts"].get(level, 0)
            if count:
                color = LEVEL_COLORS.get(level, "")
                bar = "█" * min(count, 30)
                print(f"  {color}{level:<10}{RESET} {bar} {count}")

    if data["hour_distribution"]:
        print("\n🕐 Saatlik Aktivite:")
        max_count = max(data["hour_distribution"].values(), default=1)
        for hour, count in sorted(data["hour_distribution"].items()):
            bar_len = int(count / max_count * 20)
            bar = "█" * bar_len
            print(f"  {hour:02d}:00  {bar} {count}")

    if data["top_ips"]:
        print(f"\n🌐 En Aktif IP'ler (üst {min(top_n, len(data['top_ips']))}):")
        for ip, count in data["top_ips"][:top_n]:
            print(f"  {ip:<18} {count}")

    if data["top_messages"]:
        print(f"\n💬 En Sık Mesajlar:")
        for msg, count in data["top_messages"]:
            truncated = msg[:70] + "..." if len(msg) > 70 else msg
            print(f"  ({count:>4}x) {truncated}")


def main():
    parser = argparse.ArgumentParser(description="Log dosyası analiz aracı")
    parser.add_argument("files", nargs="+", help="Log dosyası/dosyaları")
    parser.add_argument("--level", choices=LOG_LEVELS, help="Sadece bu seviyeyi filtrele")
    parser.add_argument("--top", type=int, default=10, help="Üst N sonuç")
    parser.add_argument("--json", action="store_true", help="JSON formatında çıktı")
    args = parser.parse_args()

    results = []
    for f in args.files:
        data = analyze_file(f, args.level)
        if data:
            results.append(data)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for data in results:
            print_report(data, args.top)


if __name__ == "__main__":
    main()

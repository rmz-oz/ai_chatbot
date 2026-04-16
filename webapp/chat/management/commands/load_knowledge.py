"""
Load knowledge entries from /app/data/*.txt into LightRAG.
Each entry is inserted individually (# Title\nContent format).

Usage:
    python manage.py load_knowledge
    python manage.py load_knowledge --file data/acu_ortak.txt
    python manage.py load_knowledge --limit 50
"""

import os
import re
from django.core.management.base import BaseCommand
from chat.llm import insert_text


def _split_entries(text: str) -> list[str]:
    parts = re.split(r'(?=^# )', text, flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip()]


class Command(BaseCommand):
    help = "Load knowledge entries from data/ into LightRAG (one entry at a time)"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Specific file to load")
        parser.add_argument("--limit", type=int, default=0, help="Max entries to load (0=all)")

    def handle(self, *args, **options):
        data_dir = "/app/data"
        specific = options.get("file")
        limit = options.get("limit", 0)

        if specific:
            files = [specific] if os.path.exists(specific) else []
        else:
            files = sorted([
                os.path.join(data_dir, f)
                for f in os.listdir(data_dir)
                if f.endswith(".txt")
            ]) if os.path.isdir(data_dir) else []

        if not files:
            self.stdout.write(self.style.WARNING("data/ klasöründe .txt dosyası bulunamadı."))
            return

        total_inserted = 0
        for path in files:
            self.stdout.write(f"Dosya: {path}")
            with open(path, encoding="utf-8") as f:
                text = f.read()

            entries = _split_entries(text)
            self.stdout.write(f"  {len(entries)} entry bulundu")

            for i, entry in enumerate(entries):
                if limit and total_inserted >= limit:
                    self.stdout.write(self.style.WARNING(f"Limit {limit} ulaşıldı, durduruluyor."))
                    return
                try:
                    insert_text(entry)
                    total_inserted += 1
                    if total_inserted % 10 == 0:
                        self.stdout.write(f"  [{total_inserted}] {entry[:60].splitlines()[0]}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  HATA entry {i}: {e}"))
                    continue

            self.stdout.write(self.style.SUCCESS(f"  OK: {path}"))

        self.stdout.write(self.style.SUCCESS(f"Toplam {total_inserted} entry yüklendi."))

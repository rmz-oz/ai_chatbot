"""
Load text files from /app/data/ into LightRAG.

Usage:
    python manage.py load_knowledge
    python manage.py load_knowledge --file data/acu.txt
"""

import os
from django.core.management.base import BaseCommand
from chat.llm import insert_text


class Command(BaseCommand):
    help = "Load .txt files from data/ directory into LightRAG"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Specific file to load")

    def handle(self, *args, **options):
        data_dir = "/app/data"
        specific = options.get("file")

        if specific:
            files = [specific] if os.path.exists(specific) else []
        else:
            files = [
                os.path.join(data_dir, f)
                for f in os.listdir(data_dir)
                if f.endswith(".txt")
            ] if os.path.isdir(data_dir) else []

        if not files:
            self.stdout.write(self.style.WARNING("data/ klasöründe .txt dosyası bulunamadı."))
            self.stdout.write("data/ klasörüne .txt dosyası ekleyin ve tekrar çalıştırın.")
            return

        for path in files:
            self.stdout.write(f"Yükleniyor: {path}")
            with open(path, encoding="utf-8") as f:
                text = f.read()
            insert_text(text)
            self.stdout.write(self.style.SUCCESS(f"  OK: {path}"))

        self.stdout.write(self.style.SUCCESS("Tüm dosyalar LightRAG'a yüklendi."))

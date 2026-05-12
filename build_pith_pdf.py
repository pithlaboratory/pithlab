import subprocess

md_file = "pith-master-plan.md"
pdf_file = "pith-master-plan.pdf"

cmd = [
    "pandoc", md_file, "-o", pdf_file,
    "--pdf-engine=xelatex",
    "-V", "mainfont=DejaVu Sans",
    "-V", "monofont=DejaVu Sans Mono",
    "-V", "geometry:margin=1in"
]

print("🔨 Сборка PDF (без стилей)...")
subprocess.run(cmd, check=True)
print(f"✅ Готово: {pdf_file}")

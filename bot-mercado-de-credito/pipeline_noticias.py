import subprocess
import sys

scripts = [
    "extrator_link.py",
    "classifica_llm.py",
    "enviar_noticia.py"
]

for script in scripts:
    print(f"\n{'=' * 60}")
    print(f"Executando: {script}")
    print(f"{'=' * 60}\n")

    subprocess.run(
        [sys.executable, script],
        check=True
    )

print("\nPipeline finalizado com sucesso.")
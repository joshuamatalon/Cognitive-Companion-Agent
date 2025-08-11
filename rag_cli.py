# rag_cli.py
from datetime import datetime
from rag_chain import answer
import os

os.makedirs("history", exist_ok=True)

q = input("Ask CCA (persistent): ")
resp, used = answer(q, k=5)

ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
with open(f"history/{ts}.txt", "w", encoding="utf-8") as f:
    f.write(f"Q: {q}\n\nA:\n{resp}\n\nUSED: {used}\n")

print("\n— Answer —\n", resp)
print("\nMemories used:", used)

# seed_vec.py
from vec_memory import upsert_note, search

seed = [
    "Josh prefers deep work from 9am to 11am.",
    "Josh is building a Cognitive Companion Agent using LangChain and Chroma.",
    "Josh’s 18–24 month goal is to earn equity at an early-stage AI startup.",
    "Josh lives with parents and can relocate for AI proximity.",
    "Josh aims to ship one public artifact per week.",
]

for s in seed:
    upsert_note(s, {"type": "fact", "source": "seed"})

print("Search test:")
print(search("When should Josh do deep work?", k=3))

from src.server import search_papers, download_paper
import json

print("Testing search_papers (Arxiv)...")
results = search_papers("arxiv", "LLM Agents", limit=1)
print(json.dumps(results, indent=2))

print("\nTesting search_papers (IEEE)...")
results_ieee = search_papers("ieee", "LLM Agents", limit=1)
print(json.dumps(results_ieee, indent=2))

print("\nTesting search_papers (IEEE Open Access)...")
results_ieee_oa = search_papers("ieee", "LLM Agents", limit=1, open_access_only=True)
print(json.dumps(results_ieee_oa, indent=2))

# Note: Download testing might fail if we pick a locked paper, but we can check the return string.

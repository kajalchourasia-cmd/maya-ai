"""Build the frozen fictional Stage 4 extraction benchmark inventory."""
from __future__ import annotations
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evals/stage4_document_provider_benchmark.jsonl"
def main():
 rows=[]
 with (ROOT/"data/synthetic/document_inventory.csv").open(encoding="utf-8",newline="") as f:
  for item in csv.DictReader(f):
   rows.append({"case_id":"stage4-provider-"+item["document_id"].lower(),"dataset_version":"stage4-fictional-extraction-benchmark-v1","document_id":item["document_id"],"input_class":"fictional_exact_hash_document","expected_extraction":f"data/synthetic/{item['expected_extraction_json']}","expected_graph":f"data/synthetic/{item['typed_graph_truth']}","required_metrics":["exact_quote_fidelity","field_accuracy","schema_compliance","unsupported_field_rate","conflict_preservation","latency_ms","cost_usd","failure_or_timeout"],"production_eligible":False})
 OUT.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows),encoding="utf-8")
 print(f"stage4 provider benchmark fixtures: {len(rows)}/{len(rows)} frozen")
 return 0
if __name__=="__main__": raise SystemExit(main())
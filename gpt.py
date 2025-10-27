# gpt.py — goal-agnostic planning & insights

import os, json
from datetime import date
from typing import List, Dict, Optional
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PLAN_SYSTEM = """You are an expert goal planner. Produce a concise, practical plan of 6–8 SMALL, ACTIONABLE steps for ANY goal.
Do NOT use labels like 'Milestone 1' or generic headings. Each step MUST be atomic and start with a verb.
Return JSON with fields: title, detail (how to do it), metric (measurable), duration_min (int), why (motivation), due_offset_days (int, optional)."""

PLAN_USER_TMPL = """Goal: {title}
Deadline (optional): {deadline}

Constraints:
- Steps must be concrete, small, and completable within 20–90 minutes.
- Prefer daily/near-daily cadence.
- If a deadline is provided, spread steps logically before it.
- Keep language general enough for any domain, but precise.
Output JSON list only (no markdown)."""

SUMMARY_SYSTEM = """You analyze progress. Write a motivational, specific weekly summary that highlights:
- What went well (tied to steps/metrics)
- Risks / blockers
- 3 specific focus items for next week"""

QUOTE_SYSTEM = "Return a very short, non-cheesy motivational line under 12 words."

def _safe_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return []

def generate_plan(title: str, deadline_iso: Optional[str]) -> List[Dict]:
    prompt = PLAN_USER_TMPL.format(title=title, deadline=deadline_iso or "None")
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content": PLAN_SYSTEM},
            {"role":"user", "content": prompt}
        ],
        temperature=0.3
    )
    raw = resp.choices[0].message.content.strip()
    items = _safe_json(raw)
    # Normalize and compute due_date from due_offset_days if present
    out = []
    for i, s in enumerate(items, start=1):
        out.append({
            "order_index": i,
            "title": (s.get("title") or "").strip(),
            "detail": (s.get("detail") or "").strip(),
            "metric": (s.get("metric") or "").strip(),
            "duration_min": int(s.get("duration_min")) if s.get("duration_min") else None,
            "why": (s.get("why") or "").strip(),
            # leave due_date empty; user can set in UI. If you prefer auto, you can compute from due_offset_days here.
            "due_date": None,
            "done": 0
        })
    return [s for s in out if s["title"]]

def weekly_summary(steps: List[Dict], checkins: List[Dict]) -> str:
    # compact, goal-agnostic context
    steps_txt = json.dumps([{k: s.get(k) for k in ("title","metric","done","due_date")} for s in steps], ensure_ascii=False)
    checks_txt = json.dumps(checkins, ensure_ascii=False)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content": SUMMARY_SYSTEM},
            {"role":"user", "content": f"Steps: {steps_txt}\nCheck-ins: {checks_txt}"}
        ],
        temperature=0.3
    )
    return resp.choices[0].message.content.strip()

def short_quote() -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":QUOTE_SYSTEM},{"role":"user","content":"One line."}],
        temperature=0.7
    )
    return resp.choices[0].message.content.strip()

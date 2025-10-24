from santai_mcp_client.models import Decision, Tool
from typing import List, Dict, Any, Optional
import json
from santai_mcp_client.llm_endpoint import call_llm
import re


class Selector:
    def __init__(
        self,
        base_endpoint: str,
        api_key: str,
        model: Optional[str] = None,
    ) -> None:
        self.base_endpoint = base_endpoint
        self.api_key = api_key
        self.model = model

    def choose_tool(self, context: str, query: str, tools: List[Tool]) -> Decision:
        processed_tools = self._process_tools(tools)
        decision = self._build_system_prompt(context, query, processed_tools)

        return decision

    # ---------------------------
    # PRIVATE HELPERS
    # ---------------------------

    def _process_tools(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        out = []
        for t in tools:
            sch = t.input_schema or {}
            out.append(
                {
                    "name": t.name,
                    "description": (t.description or "")[:400],
                    "required": list((sch.get("required") or [])),
                    "properties": list((sch.get("properties") or {}).keys()),
                    "schema": sch,
                }
            )
        return out

    def _build_system_prompt(
        self, context: str, query: str, tools: List[Dict[str, Any]]
    ) -> Decision:
        system = (
            "You are a strict MCP tool router.\n"
            "Your job is to decide whether to call one of the available tools based on:\n"
            "  1. The CONTEXT of the prior conversation\n"
            "  2. The CURRENT user query\n"
            "  3. The AVAILABLE MCP tools and their schemas\n\n"
            "Follow these rules STRICTLY:\n"
            "  - You may select AT MOST ONE tool.\n"
            "  - If a tool is clearly applicable, select it and provide valid arguments.\n"
            "  - If NO tool makes sense for the current query, DO NOT select one.\n"
            "  - If no tool is applicable, return an empty tool call like this: "
            '{"tool":"","arguments":{}}.\n'
            "  - NEVER guess tool arguments. Only use information present in the query or context.\n"
            "  - Use tool property names EXACTLY as defined in the schemas.\n"
            '  - Return ONLY JSON in this exact format: {"tool":"<name>","arguments":{...}}.\n'
        )

        user = (
            f"Context:\n{context or ''}\n\n"
            f"User query:\n{query or ''}\n\n"
            f"Tools (full schema):\n{tools}\n\n"
        )

        print("Calling LLM Endpoint...")
        raw = call_llm(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            base_endpoint=self.base_endpoint,
            api_key=self.api_key,
        )

        print("Parsing output of LLM endpoint...")
        print("[router][raw]:", raw)
        parsed = self._parse_json(raw)
        if not parsed:
            return Decision("", "")

        print("[router][parsed]:", parsed)
        name = (parsed.get("tool") or "").strip()
        args = parsed.get("arguments") or {}

        by_name = {t["name"]: t for t in tools}
        if name not in by_name:
            lower = {t["name"].lower(): t for t in tools}
            t_obj = lower.get(name.lower())
            if not t_obj:
                return Decision("", "")
        else:
            t_obj = by_name[name]

        coerced_args = self._coerce_arguments(args, t_obj.get("schema", {}))

        decision = Decision(t_obj, coerced_args)
        return decision

    def _coerce_arguments(
        self, args: Dict[str, Any], schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        def _primary_type(t):
            # Accept "number" or ["number","null"] etc.
            if isinstance(t, list):
                for cand in t:
                    if cand != "null":
                        return cand
                return t[0] if t else None
            return t

        def _safe_int(v):
            if v is None:
                return None
            if isinstance(v, str) and not v.strip():
                return None
            try:
                return int(v)
            except (TypeError, ValueError):
                return v

        def _safe_float(v):
            if v is None:
                return None
            if isinstance(v, str) and not v.strip():
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return v

        props = (schema or {}).get("properties") or {}
        out = dict(args or {})

        for k, p in props.items():
            if k not in out:
                continue

            v = out[k]
            t = _primary_type(p.get("type"))

            # Skip coercion for explicit null
            if v is None:
                continue

            try:
                if t == "integer":
                    out[k] = _safe_int(v)

                elif t == "number":
                    out[k] = _safe_float(v)

                elif t == "boolean":
                    if isinstance(v, bool):
                        continue
                    s = str(v).strip().lower()
                    if s in {"true", "1", "yes", "y", "on"}:
                        out[k] = True
                    elif s in {"false", "0", "no", "n", "off"}:
                        out[k] = False
                    # else: leave as-is

                elif t == "array":
                    if isinstance(v, list):
                        continue
                    if isinstance(v, str):
                        out[k] = [x.strip() for x in v.split(",") if x.strip()]
                    else:
                        out[k] = [v]

                # strings/objects: leave as-is

            except Exception as e:
                # one-time lightweight debug to pinpoint the offender
                # (remove after it stabilizes)
                print(f"[coerce] key={k!r}, type={t!r}, value={v!r} -> error: {e}")

        return out

    def _parse_json(self, s: str) -> Optional[Dict[str, Any]]:
        s = s.strip()
        if s.startswith("```"):
            s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.S)
        try:
            return json.loads(s)
        except Exception:
            start = s.find("{")
            if start == -1:
                return None
            depth = 0
            for i, ch in enumerate(s[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(s[start : i + 1])
                        except Exception:
                            return None
            return None

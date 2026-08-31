import os
import json
import re
import time
from typing import Dict, Any, List, Tuple

from app.config import settings
from app.prompts.system_prompt import SYSTEM_PROMPT, format_rag_prompt

class AIService:
    """
    Tier 2 AI Reasoning Provider:
    Integrates Google Gemini API with automatic model failover (3.6 -> 3.7 -> flash-latest)
    to guarantee continuous high availability.
    """

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.gemini_models_cascade = [
            settings.GEMINI_MODEL or "gemini-3.5-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3.6-flash",
            "gemini-3.7-flash"
        ]

    def generate_grounded_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], int, int, float]:
        """
        Executes LLM completion with prompt grounding and model cascade fallback.
        Returns: (parsed_response_dict, prompt_tokens, completion_tokens, latency_ms)
        """
        start_time = time.time()
        user_prompt = format_rag_prompt(query, context_chunks)
        gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

        # 1. Try Google Gemini API with model cascade
        if gemini_key:
            for model_candidate in self.gemini_models_cascade:
                try:
                    print(f"[AIService] Attempting Gemini API ({model_candidate}) for query: '{query[:45]}'...")
                    res, pt, ct = self._call_gemini(user_prompt, gemini_key, model_candidate)
                    latency_ms = (time.time() - start_time) * 1000
                    print(f"[AIService] SUCCESS with {model_candidate} in {latency_ms:.1f}ms! (Tokens: {pt} in, {ct} out)")
                    return res, pt, ct, latency_ms
                except Exception as e:
                    print(f"[AIService] Model {model_candidate} error: {e}. Trying next cascade model...")

        # 2. Try OpenAI API
        openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            try:
                print(f"[AIService] Calling OpenAI API ({settings.OPENAI_MODEL})...")
                res, pt, ct = self._call_openai(user_prompt, openai_key)
                latency_ms = (time.time() - start_time) * 1000
                return res, pt, ct, latency_ms
            except Exception as e:
                print(f"[AIService] OpenAI API error: {e}. Attempting offline synthesizer...")

        # 3. Offline Grounded Synthesizer
        print(f"[AIService] Warning: Using offline synthesizer.")
        res = self._offline_synthesizer(query, context_chunks)
        latency_ms = (time.time() - start_time) * 1000
        return res, 0, 0, latency_ms

    def _call_gemini(self, user_prompt: str, api_key: str, model_name: str) -> Tuple[Dict[str, Any], int, int]:
        """Calls Google Gemini API using google.genai Client."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=settings.TEMPERATURE,
            max_output_tokens=3000,
            response_mime_type="application/json"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=config
        )
        raw_text = response.text or "{}"

        prompt_tokens = len(user_prompt.split()) + len(SYSTEM_PROMPT.split())
        completion_tokens = len(raw_text.split())

        parsed = self._clean_json(raw_text)
        return parsed, prompt_tokens, completion_tokens

    def _call_openai(self, user_prompt: str, api_key: str) -> Tuple[Dict[str, Any], int, int]:
        """Calls OpenAI Chat Completion API."""
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_OUTPUT_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        raw_text = response.choices[0].message.content or "{}"
        prompt_tokens = response.usage.prompt_tokens if response.usage else len(user_prompt.split())
        completion_tokens = response.usage.completion_tokens if response.usage else len(raw_text.split())

        parsed = self._clean_json(raw_text)
        return parsed, prompt_tokens, completion_tokens

    def _offline_synthesizer(self, query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesizes an offline grounded response when API keys are not supplied."""
        from app.services.deterministic_service import deterministic_service

        # Check if query matches explicit escalation patterns
        for esc_pat in deterministic_service.escalation_patterns:
            if re.search(esc_pat, query, re.IGNORECASE):
                return {
                    "answer": "He transferido tu solicitud a uno de nuestros asesores humanos para brindarte atención personalizada.",
                    "confidence": 0.3,
                    "sources": [],
                    "escalate_to_human": True,
                    "escalation_reason": "EXPLICIT_ESCALATION_INTENT"
                }

        if not context_chunks:
            return {
                "answer": "He transferido tu consulta a nuestro equipo de admisiones humanas para brindarte atención personalizada.",
                "confidence": 0.3,
                "sources": [],
                "escalate_to_human": True,
                "escalation_reason": "NO_CONTEXT_AVAILABLE"
            }

        top_chunk = context_chunks[0]
        sources = [f"{top_chunk.get('filename', '')}#{top_chunk.get('section', '')}"]

        answer = f"**Información de Global Language Academy:**\n\n{top_chunk.get('text', '').strip()}"
        return {
            "answer": answer,
            "confidence": 0.88,
            "sources": sources,
            "escalate_to_human": False,
            "escalation_reason": None
        }

    def _clean_json(self, raw_text: str) -> Dict[str, Any]:
        """Cleans and extracts JSON object from raw response with relaxed control char parsing."""
        try:
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

            data = json.loads(cleaned, strict=False)
            return {
                "answer": data.get("answer", "Thank you for reaching out. How can I assist you further?"),
                "confidence": float(data.get("confidence", 0.95)),
                "sources": data.get("sources", []),
                "escalate_to_human": bool(data.get("escalate_to_human", False)),
                "escalation_reason": data.get("escalation_reason", None)
            }
        except Exception as e:
            print(f"[AIService] JSON parse error: {e}, Raw text: {raw_text[:200]}")
            answer_match = re.search(r'"answer"\s*:\s*"([^"]+)"', raw_text, re.DOTALL)
            answer = answer_match.group(1) if answer_match else raw_text.strip()
            return {
                "answer": answer,
                "confidence": 0.85,
                "sources": [],
                "escalate_to_human": False,
                "escalation_reason": None
            }

ai_service = AIService()

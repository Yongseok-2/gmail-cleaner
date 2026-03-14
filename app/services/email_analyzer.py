import json
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.settings import settings

ALLOWED_CATEGORIES = {
    "work_action",
    "finance_billing",
    "account_security",
    "shopping_delivery",
    "newsletter_promo",
    "social_community",
    "personal",
    "other",
}


class EmailAnalyzer:
    async def analyze_email(self, email: dict[str, Any]) -> dict[str, Any]:
        rule_result = self._analyze_with_rules(email)
        if not self._is_ambiguous(rule_result):
            return rule_result

        gemini_result = await self._analyze_with_gemini(email, rule_result)
        if gemini_result is not None:
            return gemini_result

        rule_result["review_required"] = True
        return rule_result

    def _analyze_with_rules(self, email: dict[str, Any]) -> dict[str, Any]:
        subject = (email.get("subject") or "").strip()
        snippet = (email.get("snippet") or "").strip()
        from_email = (email.get("from_email") or "").strip().lower()
        text = f"{subject} {snippet}".lower()

        category, confidence = self._classify_category(text=text, from_email=from_email)
        urgency_score = self._score_urgency(text=text)
        keywords = self._extract_keywords(text=text)
        summary = self._build_summary(subject=subject, snippet=snippet)

        return {
            "gmail_message_id": email.get("gmail_message_id"),
            "sender_email": email.get("from_email", ""),
            "category": category,
            "urgency_score": urgency_score,
            "summary": summary,
            "keywords": keywords,
            "confidence_score": confidence,
            "analysis_source": "rules",
            "review_required": confidence < settings.analysis_confidence_threshold,
            "draft_reply_context": self._build_draft_context(category=category, summary=summary),
            "analyzed_at": datetime.now(UTC),
        }

    def _is_ambiguous(self, result: dict[str, Any]) -> bool:
        return bool(
            result["confidence_score"] < settings.analysis_confidence_threshold
            or result["category"] == "other"
        )

    async def _analyze_with_gemini(
        self, email: dict[str, Any], fallback: dict[str, Any]
    ) -> dict[str, Any] | None:
        if not settings.gemini_api_key:
            return None

        prompt = self._build_gemini_prompt(email, fallback)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=settings.gemini_timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError:
            return None

        data = response.json()
        parsed = self._parse_gemini_json(data)
        if parsed is None:
            return None

        category = parsed.get("category", fallback["category"])
        if category not in ALLOWED_CATEGORIES:
            category = "other"

        urgency_score = int(parsed.get("urgency_score", fallback["urgency_score"]))
        confidence_score = float(parsed.get("confidence_score", fallback["confidence_score"]))
        summary = str(parsed.get("summary", fallback["summary"]))[:240]
        keywords = parsed.get("keywords", fallback["keywords"])
        if not isinstance(keywords, list):
            keywords = fallback["keywords"]

        return {
            "gmail_message_id": fallback["gmail_message_id"],
            "sender_email": fallback["sender_email"],
            "category": category,
            "urgency_score": max(0, min(100, urgency_score)),
            "summary": summary,
            "keywords": [str(item)[:50] for item in keywords[:12]],
            "confidence_score": max(0.0, min(1.0, confidence_score)),
            "analysis_source": "gemini_flash_lite",
            "review_required": confidence_score < settings.analysis_confidence_threshold,
            "draft_reply_context": self._build_draft_context(category=category, summary=summary),
            "analyzed_at": datetime.now(UTC),
        }

    def _parse_gemini_json(self, response_json: dict[str, Any]) -> dict[str, Any] | None:
        try:
            candidates = response_json.get("candidates", [])
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return None
            text = parts[0].get("text", "")
            return json.loads(text)
        except (ValueError, KeyError, TypeError):
            return None

    def _build_gemini_prompt(self, email: dict[str, Any], fallback: dict[str, Any]) -> str:
        return (
            "You are classifying a Gmail message for inbox triage.\n"
            "Return JSON only with fields: category, urgency_score, summary, keywords, confidence_score.\n"
            f"Allowed category values: {sorted(ALLOWED_CATEGORIES)}\n"
            "urgency_score must be integer 0..100. confidence_score must be float 0..1.\n"
            "If uncertain, use category 'other' and lower confidence_score.\n\n"
            f"from_email: {email.get('from_email', '')}\n"
            f"subject: {email.get('subject', '')}\n"
            f"snippet: {email.get('snippet', '')}\n"
            f"rule_based_hint: category={fallback['category']}, confidence={fallback['confidence_score']}\n"
        )

    def _classify_category(self, text: str, from_email: str) -> tuple[str, float]:
        if any(word in text for word in ["invoice", "receipt", "billing", "payment"]):
            return ("finance_billing", 0.86)
        if any(word in text for word in ["meeting", "schedule", "calendar", "action required"]):
            return ("work_action", 0.83)
        if any(word in text for word in ["security", "verify", "password", "login alert"]):
            return ("account_security", 0.86)
        if any(word in text for word in ["shipping", "delivered", "order", "tracking"]):
            return ("shopping_delivery", 0.82)
        if any(word in text for word in ["sale", "discount", "promotion", "unsubscribe"]):
            return ("newsletter_promo", 0.8)
        if any(word in from_email for word in ["linkedin", "facebook", "x.com", "discord"]):
            return ("social_community", 0.77)
        if any(word in text for word in ["mom", "dad", "family", "friend"]):
            return ("personal", 0.74)
        return ("other", 0.45)

    def _score_urgency(self, text: str) -> int:
        score = 20
        if any(word in text for word in ["urgent", "asap", "immediately", "today"]):
            score += 35
        if any(word in text for word in ["deadline", "overdue", "final notice"]):
            score += 30
        if any(word in text for word in ["action required", "important"]):
            score += 15
        return min(score, 100)

    def _extract_keywords(self, text: str) -> list[str]:
        candidate_words = [
            "invoice",
            "payment",
            "meeting",
            "deadline",
            "urgent",
            "promotion",
            "receipt",
            "shipping",
            "security",
            "verification",
            "refund",
            "tracking",
        ]
        return [word for word in candidate_words if word in text]

    def _build_summary(self, subject: str, snippet: str) -> str:
        if subject and snippet:
            return f"{subject} - {snippet[:120]}"
        if subject:
            return subject[:160]
        return snippet[:160]

    def _build_draft_context(self, category: str, summary: str) -> str:
        return f"category={category}; summary={summary}"


email_analyzer = EmailAnalyzer()

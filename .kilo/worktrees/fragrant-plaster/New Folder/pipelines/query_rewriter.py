# pipelines/query_rewriter.py
"""
Advanced Query Rewriting for Better Retrieval
- Spell correction
- Query reformulation
- LLM-based rewriting
- Template-based expansion
"""

import os
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from pipelines._logging import setup_logger

log = setup_logger("query_rewriter")


@dataclass
class RewrittenQuery:
    """Rewritten query result"""

    original: str
    rewritten: str
    method: str
    confidence: float


class SpellCorrector:
    """Persian spell correction"""

    # Common misspellings in legal Persian
    CORRECTIONS = {
        "قانن": "قانون",
        "مقرات": "مقررات",
        "دادگا": "دادگاه",
        "قراداد": "قرارداد",
        "محکوم": "محکوم",
    }

    @staticmethod
    def correct(query: str) -> str:
        """Apply spell corrections"""
        corrected = query
        for wrong, right in SpellCorrector.CORRECTIONS.items():
            corrected = corrected.replace(wrong, right)
        return corrected


class QueryReformulator:
    """Reformulate queries for better matching"""

    # Question patterns to statement conversion
    QUESTION_PATTERNS = [
        (r"چه (.+) است\??", r"\1"),
        (r"چگونه (.+)\??", r"نحوه \1"),
        (r"چرا (.+)\??", r"دلیل \1"),
        (r"کجا (.+)\??", r"مکان \1"),
        (r"چه زمانی (.+)\??", r"زمان \1"),
    ]

    @staticmethod
    def reformulate(query: str) -> List[str]:
        """Generate reformulations"""
        reformulations = [query]

        # Convert questions to statements
        for pattern, replacement in QueryReformulator.QUESTION_PATTERNS:
            match = re.search(pattern, query)
            if match:
                reformulated = re.sub(pattern, replacement, query)
                reformulations.append(reformulated)

        # Remove question marks
        if "؟" in query or "?" in query:
            reformulations.append(query.replace("؟", "").replace("?", "").strip())

        return list(set(reformulations))


class LLMQueryRewriter:
    """LLM-based query rewriting"""

    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        if OpenAI is None:
            raise ImportError("OpenAI not installed")

        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        log.info(f"LLM rewriter initialized: {model}")

    def rewrite(self, query: str) -> str:
        """Rewrite query using LLM"""

        prompt = f"""شما یک متخصص جستجوی اسناد حقوقی هستید. 
سوال کاربر را به یک query بهینه برای جستجو در پایگاه داده حقوقی تبدیل کنید.

قوانین:
- کلمات کلیدی مهم را حفظ کنید
- اصطلاحات حقوقی دقیق استفاده کنید
- سوال را به عبارت جستجو تبدیل کنید
- فقط query بهینه شده را برگردانید (بدون توضیح)

سوال کاربر: {query}

Query بهینه شده:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal search expert."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=100,
            )

            rewritten = response.choices[0].message.content.strip()
            return rewritten

        except Exception as e:
            log.error(f"LLM rewriting error: {e}")
            return query


class TemplateExpander:
    """Template-based query expansion"""

    TEMPLATES = {
        "definition": ["تعریف {term}", "{term} چیست", "مفهوم {term}"],
        "procedure": ["نحوه {action}", "روش {action}", "مراحل {action}"],
        "law": ["قانون {topic}", "مقررات {topic}", "ماده {topic}"],
    }

    @staticmethod
    def expand(query: str) -> List[str]:
        """Expand query using templates"""
        expansions = [query]

        # Detect query type and apply templates
        if any(word in query for word in ["چیست", "تعریف", "مفهوم"]):
            # Extract term
            term = query.replace("چیست", "").replace("تعریف", "").replace("مفهوم", "").strip()
            for template in TemplateExpander.TEMPLATES["definition"]:
                expansions.append(template.format(term=term))

        elif any(word in query for word in ["نحوه", "چگونه", "روش"]):
            action = query.replace("نحوه", "").replace("چگونه", "").replace("روش", "").strip()
            for template in TemplateExpander.TEMPLATES["procedure"]:
                expansions.append(template.format(action=action))

        return list(set(expansions))[:5]  # Limit to 5


class AdvancedQueryRewriter:
    """Comprehensive query rewriting system"""

    def __init__(self, use_llm: bool = False, api_key: str = None):
        self.spell_corrector = SpellCorrector()
        self.reformulator = QueryReformulator()
        self.template_expander = TemplateExpander()

        self.llm_rewriter = None
        if use_llm:
            try:
                self.llm_rewriter = LLMQueryRewriter(api_key=api_key)
            except Exception as e:
                log.warning(f"LLM rewriter not available: {e}")

    def rewrite(self, query: str, max_variants: int = 5) -> List[RewrittenQuery]:
        """Generate multiple query variants"""

        variants = []

        # 1. Original (with spell correction)
        corrected = self.spell_corrector.correct(query)
        variants.append(
            RewrittenQuery(
                original=query,
                rewritten=corrected,
                method="spell_correction",
                confidence=1.0 if corrected != query else 0.9,
            )
        )

        # 2. Reformulations
        reformulations = self.reformulator.reformulate(corrected)
        for ref in reformulations[:2]:
            if ref != corrected:
                variants.append(
                    RewrittenQuery(
                        original=query, rewritten=ref, method="reformulation", confidence=0.8
                    )
                )

        # 3. Template expansions
        expansions = self.template_expander.expand(corrected)
        for exp in expansions[:2]:
            if exp not in [v.rewritten for v in variants]:
                variants.append(
                    RewrittenQuery(
                        original=query, rewritten=exp, method="template_expansion", confidence=0.7
                    )
                )

        # 4. LLM rewriting
        if self.llm_rewriter:
            llm_rewritten = self.llm_rewriter.rewrite(query)
            if llm_rewritten not in [v.rewritten for v in variants]:
                variants.append(
                    RewrittenQuery(
                        original=query, rewritten=llm_rewritten, method="llm", confidence=0.9
                    )
                )

        # Limit and sort by confidence
        variants = sorted(variants, key=lambda x: x.confidence, reverse=True)[:max_variants]

        return variants


def main():
    """Test query rewriting"""
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--use_llm", action="store_true")
    ap.add_argument("--api_key", default=None)
    args = ap.parse_args()

    rewriter = AdvancedQueryRewriter(use_llm=args.use_llm, api_key=args.api_key)

    variants = rewriter.rewrite(args.query)

    print(f"\n📝 Original Query: {args.query}")
    print(f"\n🔄 Rewritten Variants ({len(variants)}):\n")

    for i, variant in enumerate(variants, 1):
        print(f"{i}. [{variant.method}] (confidence: {variant.confidence:.2f})")
        print(f"   {variant.rewritten}\n")


if __name__ == "__main__":
    main()

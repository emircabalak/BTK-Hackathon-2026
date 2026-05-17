"""Pydantic data models shared across agents."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Review(BaseModel):
    author: str
    rating: int
    text: str
    date: str | None = None
    verified_purchase: bool = False


class Seller(BaseModel):
    seller_id: str
    name: str
    rating: float = 0.0
    total_sales: int = 0
    response_style: str = "normal"  # short note inferred from past public replies


class Product(BaseModel):
    product_id: str
    title: str
    price: float
    currency: str = "TL"
    marketplace: Literal["trendyol", "hepsiburada", "n11", "seed"] = "trendyol"
    url: str = ""
    image_url: str = ""
    description: str = ""
    category: str = ""  # e.g. "kulaklik", "olta", "klavye"
    tags: list[str] = Field(default_factory=list)
    rating: float = 0.0
    review_count: int = 0
    seller: Seller
    reviews: list[Review] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


# --- Negotiation primitives ---

Speaker = Literal["negotiator", "seller", "system"]
Intent = Literal["open", "counter", "accept", "refuse", "walk_away"]


class Turn(BaseModel):
    speaker: Speaker
    message: str
    intent: Intent
    offered_price: float | None = None
    internal_thought: str | None = None
    extras: list[str] = Field(default_factory=list)


class NegotiationContext(BaseModel):
    """All the levers Negotiator has when crafting a turn."""

    product: Product
    budget_max: float | None = None
    competitor_avg_price: float | None = None
    user_persona: str | None = None
    leverage_points: list[str] = Field(default_factory=list)
    target_discount_pct: float = 15.0
    walk_away_discount_pct: float = 5.0
    max_turns: int = 6


class SellerPersona(BaseModel):
    personality: Literal["comert", "normal", "siki"] = "normal"
    max_discount_pct: float = 15.0
    cost_basis_pct: float = 0.7  # estimated cost as fraction of list price
    style_note: str = ""

    @property
    def floor_price(self) -> float:
        # Convenience: caller passes list_price externally
        return 0.0  # placeholder — actual floor computed in agent


class NegotiationOutcome(BaseModel):
    status: Literal["agreement", "walk_away", "no_movement", "max_turns"]
    original_price: float
    final_price: float
    savings_tl: float
    savings_pct: float
    extras: list[str] = Field(default_factory=list)
    turn_count: int
    transcript: list[Turn]
    summary: str = ""


# --- Pipeline outputs (Scout / Critic / Verifier / Decider) ---


class ParsedQuery(BaseModel):
    """What Scout extracts from the user's natural-language query."""

    category: str = ""  # primary category match (e.g. "kulaklik")
    budget_max: float | None = None
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    persona: str = ""


class ScoutOutput(BaseModel):
    parsed: ParsedQuery
    candidates: list[Product] = Field(default_factory=list)
    log: list[str] = Field(default_factory=list)


class TopicSentiment(BaseModel):
    topic: str
    score: float  # -1..1
    sample: str = ""


class CriticReport(BaseModel):
    product_id: str
    fake_ratio: float  # 0..1
    real_sentiment: float  # 0..1 average from reviews flagged "real"
    topics: list[TopicSentiment] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    representative_quote: str = ""
    confidence: float = 0.5  # how sure Critic is about its analysis


class VerifierReport(BaseModel):
    product_id: str
    brand_consistency: float  # 0..100
    spec_consistency: float  # 0..100
    seller_score: float  # 0..100
    overall_authenticity: float  # 0..100
    flags: list[str] = Field(default_factory=list)


class TrustBreakdown(BaseModel):
    fake_ratio_contribution: float
    authenticity_contribution: float
    sentiment_contribution: float
    seller_contribution: float


class FinalCard(BaseModel):
    """The end-of-pipeline decision card shown to the user."""

    winner: Product
    trust_score: float  # 0..100
    trust_breakdown: TrustBreakdown
    negotiation: NegotiationOutcome | None = None
    headline: str
    explanation: str
    alternatives: list[Product] = Field(default_factory=list)
    buy_link: str = ""


class PipelineResult(BaseModel):
    """Everything the orchestrator produces in one run."""

    query: str
    scout: ScoutOutput
    critic: dict[str, CriticReport] = Field(default_factory=dict)
    verifier: dict[str, VerifierReport] = Field(default_factory=dict)
    negotiation: NegotiationOutcome | None = None
    final: FinalCard | None = None

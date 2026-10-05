from pydantic import BaseModel


class Summary(BaseModel):
    total_products_detected: int
    our_products_count: int
    competitor_products_count: int
    our_share_percent: float
    competitor_share_percent: float


class OurProductDetail(BaseModel):
    product: str
    matched_as: str | None
    confidence: float | None
    note: str | None = None


class CompetitorProduct(BaseModel):
    product: str


class MenuAnalysisResponse(BaseModel):
    summary: Summary
    our_products: list[OurProductDetail]
    competitor_products: list[CompetitorProduct]
"""Portfolio schemas."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    currency: Literal["USD", "INR"] = "USD"


class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    currency: Optional[Literal["USD", "INR"]] = None


class PortfolioResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: str
    currency: str
    created_at: str


class HoldingCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Za-z0-9.^-]+$")
    quantity: float = Field(..., gt=0)
    buy_price: float = Field(..., gt=0)
    buy_currency: Literal["USD", "INR"] = "USD"
    buy_date: Optional[str] = None


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    buy_price: Optional[float] = Field(None, gt=0)
    buy_currency: Optional[Literal["USD", "INR"]] = None
    buy_date: Optional[str] = None


class HoldingResponse(BaseModel):
    id: int
    portfolio_id: int
    ticker: str
    display_name: str
    exchange: str
    quantity: float
    buy_price: float
    buy_currency: str
    buy_date: str
    created_at: str

    @property
    def invested_value(self) -> float:
        return self.quantity * self.buy_price


class AnalysisRequest(BaseModel):
    portfolio_id: int = Field(..., gt=0)
    alpha: float = Field(0.6, ge=0.0, le=1.0)
    portfolio_value: float = Field(100000, ge=1000)
    use_llm: bool = True


class AnalysisResponse(BaseModel):
    tickers: List[str]
    display_names: Dict[str, str]
    opt_result: Dict[str, Any]
    baseline: Dict[str, Any]
    final_weights: Dict[str, float]
    weight_changes: Dict[str, Dict[str, float]]
    sentiment_scores: Dict[str, float]
    risk_report: Dict[str, Any]
    health_score: Dict[str, Any]
    selected_cap: float
    adaptive_candidates: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    frontier: Dict[str, List[float]]


class HistoryResponse(BaseModel):
    id: int
    portfolio_id: int
    run_date: str
    alpha_used: Optional[float]
    sharpe_ratio: Optional[float]
    expected_return: Optional[float]
    volatility: Optional[float]
    tickers: List[str]
    opt_result: Dict[str, Any]
    sentiment_scores: Dict[str, float]
    recommendations: List[Dict[str, Any]]
    risk_report: Dict[str, Any]


class BenchmarkResponse(BaseModel):
    dates: List[str]
    portfolio: List[float]
    spy: List[float]


class SharpeTrendResponse(BaseModel):
    date: str
    sharpe_ratio: Optional[float]
    expected_return: Optional[float]
    volatility: Optional[float]
from pydantic import BaseModel, Field, model_validator
from typing import Dict, Any, Optional, Literal

class SequenceLengthConfig(BaseModel):
    """시퀀스 길이 범위 설정"""
    min: int = Field(..., ge=1, description="최소 시퀀스 길이")
    max: int = Field(..., ge=1, description="최대 시퀀스 길이")

    class Config:
        validate_assignment = True

    def __post_init__(self):
        if self.min > self.max:
            raise ValueError("min must be <= max")

class AutoModelSelector(BaseModel):
    """hf 모델 설정"""
    name: str = Field(..., description="모델 카드 이름")

class ByokEmbedderConfig(BaseModel):
    """BYOK 임베더 설정"""
    provider: str = Field(..., description="API 제공자 (e.g., 'openai', 'cohere', 'google')")
    name: str = Field(..., description="Litellm 모델 이름 (e.g., 'text-embedding-3-large')")

class ProbeConfig(BaseModel):
    """프로브 생성 설정"""
    mask_ratio: float = Field(default=0.15, description="Masking 비율")
    sequence_length: SequenceLengthConfig = Field(default=SequenceLengthConfig(min=4, max=16), description="시퀀스 길이 범위. min부터 max까지 순차적으로 평가.")
    samples_per_length: int = Field(default=10, description="각 시퀀스 길이에 대해 평가할 샘플 개수. Stratified CSAT 모드에서 사용.")

class ModelsConfig(BaseModel):
    merger: Optional[AutoModelSelector] = Field(default=None, description="merger_mode용 모델 설정")
    base_embedder: Optional[AutoModelSelector] = Field(default=None, description="기본 임베더 설정")
    native_embedder: Optional[AutoModelSelector] = Field(default=None, description="native_mode용 임베더 설정")
    byok_embedder: Optional[ByokEmbedderConfig] = Field(default=None, description="BYOK mode용 임베더 설정")

class DatasetConfig(BaseModel):
    """데이터셋 설정"""
    path: str = Field(default="enzoescipy/finesse-benchmark-database", description="HF 데이터셋 경로")
    split: str = Field(default="train")
    num_samples: int = Field(default=10000)

class OutputConfig(BaseModel):
    format: str = Field(default="json")
    sign: bool = Field(default=True)

class BenchmarkConfig(BaseModel):
    mode: Literal["merger_mode", "native_mode", "byok_mode"] = Field(default="merger_mode", description="merger_mode, native_mode 또는 byok_mode")
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    probe_config: ProbeConfig = Field(default_factory=ProbeConfig)
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    advanced: Dict[str, Any] = Field(default_factory=dict, description="고급 옵션 (batch_size, device 등)")
    seed: Optional[int] = Field(default=42, description="Random seed for reproducibility")

    @model_validator(mode='after')
    def validate_mode_config(self) -> 'BenchmarkConfig':
        if self.mode == "merger_mode":
            if self.models.merger is None:
                raise ValueError("merger_mode requires 'models.merger' configuration.")
            if self.models.base_embedder is None:
                raise ValueError("merger_mode requires 'models.base_embedder' configuration.")
        elif self.mode == "native_mode":
            if self.models.native_embedder is None:
                raise ValueError("native_mode requires 'models.native_embedder' configuration.")
        elif self.mode == "byok_mode":
            if self.models.byok_embedder is None:
                raise ValueError("byok_mode requires 'models.byok_embedder' configuration.")
        return self

    class Config:
        json_schema_extra = {"example": {
            "mode": "byok_mode",
            "models": {
                "byok_embedder": {
                    "provider": "openai",
                    "name": "text-embedding-3-small"
                }
            },
            "probe_config": {
                "mask_ratio": 0.15,
                "sequence_length": {"min": 5, "max": 16},
                "samples_per_length": 1,
            },
            "dataset": {
                "path": "enzoescipy/finesse-benchmark-database",
                "num_samples": 5
            },
            # ... 기타 필드
        }}
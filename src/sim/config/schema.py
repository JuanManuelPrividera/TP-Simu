from pydantic import BaseModel, Field, model_validator


class DistributionConfig(BaseModel):
    distribution: str
    mean: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    rate: float | None = None
    values: list[float] | None = None
    weights: list[float] | None = None


class FailureConfig(BaseModel):
    mtbf: float = Field(gt=0)
    repair_time: DistributionConfig


class StageConfig(BaseModel):
    machines: int = Field(ge=1)
    processing_time: DistributionConfig
    setup_time: float = Field(ge=0.0)
    energy_rate: float = Field(ge=0.0)
    operating_windows: list[list[float]] = Field(default_factory=lambda: [[0, 24]])
    failure: FailureConfig
    materials: list[int] = Field(default_factory=list)
    defect_probability: float | None = None
    defect_threshold: float | None = None


class DispatchConfig(BaseModel):
    threshold: int = Field(ge=1)


class StagesConfig(BaseModel):
    printing: StageConfig
    binding: StageConfig
    qa: StageConfig
    packaging: StageConfig
    dispatch: DispatchConfig


class MaterialConfig(BaseModel):
    index: int = Field(ge=0, le=4)
    name: str
    initial_stock: float = Field(gt=0)
    reorder_point: float = Field(ge=0)
    replenishment_quantity: float = Field(gt=0)
    consumption_per_lot: float = Field(gt=0)
    lead_time: DistributionConfig


class MaintenanceDurationsConfig(BaseModel):
    printing: float = Field(gt=0)
    binding: float = Field(gt=0)
    qa: float = Field(gt=0)
    packaging: float = Field(gt=0)


class MaintenanceConfig(BaseModel):
    frequency: float = Field(ge=0)  # 0 = disabled
    durations: MaintenanceDurationsConfig


class SequencingConfig(BaseModel):
    policy: str = "FIFO"

    @model_validator(mode="after")
    def validate_policy(self) -> "SequencingConfig":
        valid = {"FIFO", "PRIORITY", "BOOK_TYPE"}
        if self.policy not in valid:
            raise ValueError(f"policy must be one of {valid}, got {self.policy!r}")
        return self


class OrderConfig(BaseModel):
    page_count: DistributionConfig
    units: DistributionConfig
    book_types: list[str] = Field(min_length=1)
    priority_range: list[int] = Field(min_length=2, max_length=2)


class ArrivalConfig(BaseModel):
    distribution: str = "exponential"
    rate: float = Field(gt=0)


class LotsConfig(BaseModel):
    books_per_lot: int = Field(ge=1)


class SimulationConfig(BaseModel):
    orders: int = Field(ge=1)
    seed: int = 42


class OutputConfig(BaseModel):
    event_log: bool = False
    format: str = "json"


class SimConfig(BaseModel):
    simulation: SimulationConfig
    arrival: ArrivalConfig
    order: OrderConfig
    lots: LotsConfig
    stages: StagesConfig
    materials: list[MaterialConfig] = Field(min_length=5, max_length=5)
    maintenance: MaintenanceConfig
    sequencing: SequencingConfig = Field(default_factory=SequencingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @model_validator(mode="after")
    def validate_materials_indexed(self) -> "SimConfig":
        indices = sorted(m.index for m in self.materials)
        if indices != list(range(5)):
            raise ValueError("materials must have indices 0..4 exactly once each")
        return self

from pydantic import BaseModel, Field


class ArtifactSchema(BaseModel):
    """Standard output schema for worker agents producing artifacts."""

    summary: str = Field(
        description="A concise summary of the action performed and key findings."
    )
    artifacts: dict[str, str] = Field(
        default_factory=dict,
        description="A dictionary mapping file paths to their descriptions (e.g., {'output/chart.png': 'Sales trend chart'}).",
    )

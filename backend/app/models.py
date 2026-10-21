from pydantic import BaseModel, Field, HttpUrl


class RunConfig(BaseModel):
    target_url: str
    browser: str = "chrome"
    suite_path: str
    cases_path: str
    screenshot_dir: str = "artifacts/screenshots"
    output_dir: str = "artifacts/reports"
    timeout_seconds: int = Field(default=10, ge=1, le=300)


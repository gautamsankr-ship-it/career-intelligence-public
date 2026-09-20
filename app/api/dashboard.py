"""Small FastAPI surface showing grouped synthetic resolution."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI(title="Synthetic Application Resolution Portfolio")


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return "<h1>Synthetic application resolution</h1>"


@app.get("/action-required", response_class=HTMLResponse)
def action_required() -> str:
    return """
    <main>
      <h1>Action required</h1>
      <p>Review the synthetic answer group before resolving it.</p>
    </main>
    """

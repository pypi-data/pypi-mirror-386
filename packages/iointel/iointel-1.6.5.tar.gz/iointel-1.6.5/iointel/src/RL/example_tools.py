from iointel import register_tool
from typing import Dict, Any
from datetime import datetime
import random


@register_tool
def get_current_datetime() -> str:
    """Get the current datetime."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@register_tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    print(f"add: {a} + {b}", flush=True)
    return a + b


@register_tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    print(f"subtract: {a} - {b}", flush=True)
    return a - b


@register_tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    print(f"multiply: {a} * {b}", flush=True)
    return a * b


@register_tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    print(f"divide: {a} / {b}", flush=True)
    return a / b


@register_tool
def square_root(x: float) -> float:
    """Get the square root of a number."""
    print(f"square_root: {x}", flush=True)
    return x**0.5


@register_tool
def get_weather(city: str) -> Dict[str, Any]:
    """Get weather information for a city: available cities are New York, London, Tokyo, or Paris."""
    # Mock weather data
    weather_data = {
        "New York": {"temp": round(72 + random.random(), 2), "condition": "Sunny"},
        "London": {"temp": round(65 + random.random(), 2), "condition": "Rainy"},
        "Tokyo": {"temp": round(55 + random.random(), 2), "condition": "Cloudy"},
        "Paris": {"temp": round(70 + random.random(), 2), "condition": "Clear"},
    }
    return weather_data.get(city, {"temp": 0, "condition": "Unknown"})


@register_tool
def gradio_dynamic_ui(components: list[dict], title: str = "Generated UI") -> dict:
    """
    Return a UI spec for dynamic rendering in the main Gradio app.

    components: REQUIRED. List of dicts, each describing a UI component.
      Each dict can have:
        - type: "textbox" or "slider"
        - label: string
        - value: string or number
        - min, max, step: numbers (for sliders)

    Example usage:
        gradio_dynamic_ui(
            components=[
                {"type": "textbox", "label": "Your name", "value": ""},
                {"type": "slider", "label": "Age", "min": 0, "max": 100, "value": 25}
            ],
            title="Personal Information Survey"
        )

    Example JSON:
        {
          "components": [
            {"type": "textbox", "label": "Your name", "value": ""},
            {"type": "slider", "label": "Age", "min": 0, "max": 100, "value": 25}
          ],
          "title": "Personal Information Survey"
        }
    """
    return {"ui": components, "title": title}

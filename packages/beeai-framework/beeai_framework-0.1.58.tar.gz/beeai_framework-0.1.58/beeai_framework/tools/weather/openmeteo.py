# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from datetime import UTC, date, datetime
from typing import Any, Literal
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field, field_validator

from beeai_framework.context import RunContext
from beeai_framework.emitter.emitter import Emitter
from beeai_framework.logger import Logger
from beeai_framework.tools import JSONToolOutput
from beeai_framework.tools.errors import ToolInputValidationError
from beeai_framework.tools.tool import Tool
from beeai_framework.tools.types import ToolRunOptions

logger = Logger(__name__)


class OpenMeteoToolInput(BaseModel):
    location_name: str = Field(description="The name of the location to retrieve weather information.")
    country: str | None = Field(description="Country name.", default=None)
    start_date: date | None = Field(
        description="Start date for the weather forecast in the format YYYY-MM-DD (UTC)", default=None
    )
    end_date: date | None = Field(
        description="End date for the weather forecast in the format YYYY-MM-DD (UTC)", default=None
    )
    temperature_unit: Literal["celsius", "fahrenheit"] = Field(
        description="The unit to express temperature", default="celsius"
    )

    @classmethod
    @field_validator("temperature_unit", mode="before")
    def _to_lower(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.lower()
        else:
            return value


class OpenMeteoTool(Tool[OpenMeteoToolInput, ToolRunOptions, JSONToolOutput[dict[str, Any]]]):
    name = "OpenMeteoTool"
    description = "Retrieve current, past, or future weather forecasts for a location."
    input_schema = OpenMeteoToolInput

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        super().__init__(options)

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "weather", "openmeteo"],
            creator=self,
        )

    async def _geocode(self, input: OpenMeteoToolInput) -> dict[str, str]:
        params = {"format": "json", "count": 1}
        if input.location_name:
            params["name"] = input.location_name
        if input.country:
            params["country"] = input.country

        encoded_params = urlencode(params, doseq=True)

        async with httpx.AsyncClient(proxy=os.environ.get("BEEAI_OPEN_METEO_TOOL_PROXY")) as client:
            response = await client.get(
                f"https://geocoding-api.open-meteo.com/v1/search?{encoded_params}",
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )

            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                raise ToolInputValidationError(f"Location '{input.location_name}' was not found.")
            geocode: dict[str, str] = results[0]
            return geocode

    async def get_params(self, input: OpenMeteoToolInput) -> dict[str, Any]:
        params = {
            "current": ",".join(
                [
                    "temperature_2m",
                    "rain",
                    "relative_humidity_2m",
                    "wind_speed_10m",
                ]
            ),
            "daily": ",".join(["temperature_2m_max", "temperature_2m_min", "rain_sum"]),
            "timezone": "UTC",
        }

        geocode = await self._geocode(input)
        params["latitude"] = geocode.get("latitude", "")
        params["longitude"] = geocode.get("longitude", "")
        current_date = datetime.now(tz=UTC).date()
        params["start_date"] = str(input.start_date or current_date)
        params["end_date"] = str(input.end_date or current_date)
        params["temperature_unit"] = input.temperature_unit
        return params

    async def _run(
        self, input: OpenMeteoToolInput, options: ToolRunOptions | None, context: RunContext
    ) -> JSONToolOutput[dict[str, Any]]:
        params = urlencode(await self.get_params(input), doseq=True)
        logger.debug(f"Using OpenMeteo URL: https://api.open-meteo.com/v1/forecast?{params}")

        async with httpx.AsyncClient(proxy=os.environ.get("BEEAI_OPEN_METEO_TOOL_PROXY")) as client:
            response = await client.get(
                f"https://api.open-meteo.com/v1/forecast?{params}",
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            response.raise_for_status()
            return JSONToolOutput(response.json())

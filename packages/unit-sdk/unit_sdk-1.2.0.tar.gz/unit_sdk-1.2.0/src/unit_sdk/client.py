# Copyright 2025 PageKey Solutions, LLC

import json
import sys

import requests

from pydantic import BaseModel


class UnitStore(BaseModel):
    name: str
    path: str

class UnitMetadata(BaseModel):
    inputs: dict[str, str]
    stores: dict[str, UnitStore]

class ProcessInputFormatException(Exception):
    def __init__(self, raw_metadata: str):
        message = f"Invalid Unit metadata format: {raw_metadata}"
        super().__init__(message)

class StoreRoleNotFoundException(Exception):
    def __init__(self, role: str):
        message = f"Store Role not found: {role}"
        super().__init__(message)

class UnitClient:
    def __init__(self):
        raw_metadata = sys.stdin.read()
        try:
            self._metadata = UnitMetadata(**json.loads(raw_metadata))
        except json.JSONDecodeError:
            raise ProcessInputFormatException(raw_metadata)

    def get_input(self, key: str) -> str:
        return self._metadata.inputs.get(key, "")

    def get_store_by_role(self, role: str) -> UnitStore:
        if role in self._metadata.stores:
            return self._metadata.stores.get(role)
        else:
            raise StoreRoleNotFoundException(role)

    def run_process(self, app: str, process: str, inputs: dict[str, str]):
        token = self._metadata.inputs["__token__"]
        response = requests.post(
            f"http://host.containers.internal:8000/api/apps/{app}/run/{process}",
            headers={
                "Cookie": f"unit_token={token}",
            },
            files={"_": (None, "")},
            timeout=60,
        )
        return response.content

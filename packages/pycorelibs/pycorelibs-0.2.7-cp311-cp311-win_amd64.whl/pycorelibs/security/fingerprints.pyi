from pycorelibs.system.gpu.inspector import GPUInfo as GPUInfo
from pycorelibs.system.inspector import SystemInfo as SystemInfo
from typing import Any
from uuid import uuid4 as uuid4

def generate_hardware_fingerprint(isGPU: bool = False, salt: str | None = None) -> dict[str, Any]: ...

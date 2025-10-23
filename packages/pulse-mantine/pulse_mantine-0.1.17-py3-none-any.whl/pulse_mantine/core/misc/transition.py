from typing import Any

import pulse as ps


@ps.react_component("Transition", "@mantine/core")
def Transition(*children: ps.Child, key: str | None = None, **props: Any): ...

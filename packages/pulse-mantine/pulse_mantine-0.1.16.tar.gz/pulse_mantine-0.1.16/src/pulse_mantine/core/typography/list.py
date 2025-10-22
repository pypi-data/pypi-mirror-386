from typing import Any

import pulse as ps


@ps.react_component("List", "@mantine/core")
def List(*children: ps.Child, key: str | None = None, **props: Any): ...


@ps.react_component("List", "@mantine/core", prop="Item")
def ListItem(*children: ps.Child, key: str | None = None, **props: Any): ...

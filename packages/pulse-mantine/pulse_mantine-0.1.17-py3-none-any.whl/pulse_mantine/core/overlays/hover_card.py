from typing import Any

import pulse as ps


@ps.react_component("HoverCard", "@mantine/core")
def HoverCard(*children: ps.Child, key: str | None = None, **props: Any): ...


@ps.react_component("HoverCard", "@mantine/core", prop="Target")
def HoverCardTarget(*children: ps.Child, key: str | None = None, **props: Any): ...


@ps.react_component("HoverCard", "@mantine/core", prop="Dropdown")
def HoverCardDropdown(*children: ps.Child, key: str | None = None, **props: Any): ...


@ps.react_component("HoverCard", "@mantine/core", prop="Group")
def HoverCardGroup(*children: ps.Child, key: str | None = None, **props: Any): ...

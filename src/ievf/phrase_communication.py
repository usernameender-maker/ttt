"""Deterministic phrase-template communication for navigation and travel.

This module is intentionally explicit and small. It supports a compact catalog of
basic navigation phrases, order phrases, and travel instructions, and resolves
those phrases to structured intent without guessing in ambiguous situations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("text must be a string")
    return re.sub(r"\s+", " ", value.strip()).casefold()


@dataclass(frozen=True)
class PhraseTemplate:
    """A phrase template with optional named slots and a stage label."""

    identifier: str
    language: str
    text: str
    slots: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    stage: str = "basic"

    def _pattern(self) -> str:
        pattern = re.escape(_normalize_text(self.text))
        for slot in self.slots:
            pattern = pattern.replace(re.escape(f"{{{slot}}}"), rf"(?P<{slot}>.+?)")
        return pattern

    def match(self, text: str) -> dict[str, str] | None:
        normalized = _normalize_text(text)
        pattern = self._pattern()
        compiled = re.compile(rf"^\s*{pattern}\s*$", re.IGNORECASE)
        match = compiled.fullmatch(normalized)
        if match is None:
            return None
        return {slot: match.group(slot).strip() for slot in self.slots}

    def alias_match(self, text: str) -> bool:
        normalized = _normalize_text(text)
        return any(normalized == _normalize_text(alias) for alias in self.aliases)


@dataclass
class PhraseCatalog:
    """Catalog of phrase templates that can be resolved deterministically."""

    templates: list[PhraseTemplate] = field(default_factory=list)

    def add_template(self, template: PhraseTemplate) -> None:
        self.templates.append(template)

    def determine(self, text: str, language: str) -> dict[str, object]:
        normalized = _normalize_text(text)
        matches: list[tuple[PhraseTemplate, dict[str, str]]] = []
        for template in self.templates:
            if template.language != language:
                continue
            if template.alias_match(normalized):
                matches.append((template, {}))
                continue
            values = template.match(normalized)
            if values is not None:
                matches.append((template, values))
        if not matches:
            raise ValueError(f"No template matched text in language '{language}': {text!r}")
        if len(matches) > 1:
            choices = ", ".join(match[0].identifier for match in matches)
            raise ValueError(f"Ambiguous phrase match in language '{language}': {choices}")
        template, values = matches[0]
        return {
            "template_id": template.identifier,
            "language": language,
            "stage": template.stage,
            "slots": values,
        }

    @classmethod
    def from_templates(cls, templates: Iterable[PhraseTemplate]) -> "PhraseCatalog":
        catalog = cls()
        for template in templates:
            catalog.add_template(template)
        return catalog


def build_navigation_catalog() -> PhraseCatalog:
    """Create a compact, multi-stage navigation phrase catalog."""
    return PhraseCatalog.from_templates(
        [
            PhraseTemplate("basic_move_forward", "en", "move forward", stage="basic"),
            PhraseTemplate("basic_move_back", "en", "move back", stage="basic"),
            PhraseTemplate("basic_turn_left", "en", "turn left", stage="basic"),
            PhraseTemplate("basic_turn_right", "en", "turn right", stage="basic"),
            PhraseTemplate("basic_stop", "en", "stop", stage="basic"),
            PhraseTemplate("basic_wait", "en", "wait", stage="basic"),
            PhraseTemplate("travel_to_place", "en", "travel to {destination}", ("destination",), stage="travel"),
            PhraseTemplate("travel_route", "en", "route to {destination}", ("destination",), stage="travel"),
            PhraseTemplate("travel_heading", "en", "head toward {direction}", ("direction",), stage="travel"),
            PhraseTemplate("travel_waypoint", "en", "go to waypoint {waypoint}", ("waypoint",), stage="travel"),
            PhraseTemplate("order_hold", "en", "hold position", stage="order"),
            PhraseTemplate("order_follow", "en", "follow {path}", ("path",), stage="order"),
            PhraseTemplate("order_scan", "en", "scan {sector}", ("sector",), stage="order"),
            PhraseTemplate("order_maintain", "en", "maintain heading {heading}", ("heading",), stage="order"),
            PhraseTemplate("space_sector", "en", "move to sector {sector}", ("sector",), stage="space"),
            PhraseTemplate("space_orbit", "en", "orbit {target}", ("target",), stage="space"),
            PhraseTemplate("space_land", "en", "land on {location}", ("location",), stage="space"),
            PhraseTemplate("space_depart", "en", "launch from {origin}", ("origin",), stage="space"),
            PhraseTemplate("basic_move_forward_es", "es", "avanza", stage="basic"),
            PhraseTemplate("basic_move_back_es", "es", "retrocede", stage="basic"),
            PhraseTemplate("basic_turn_left_es", "es", "gira a la izquierda", stage="basic"),
            PhraseTemplate("basic_turn_right_es", "es", "gira a la derecha", stage="basic"),
            PhraseTemplate("basic_stop_es", "es", "detente", stage="basic"),
            PhraseTemplate("travel_to_place_es", "es", "viaja hacia {destination}", ("destination",), stage="travel"),
            PhraseTemplate("order_hold_es", "es", "mantener posicion", stage="order"),
            PhraseTemplate("space_sector_es", "es", "muevete al sector {sector}", ("sector",), stage="space"),
        ]
    )


def determine_phrase(text: str, language: str, catalog: PhraseCatalog | None = None) -> dict[str, object]:
    """Determine the intended phrase from a structured communication catalog."""
    if catalog is None:
        catalog = build_navigation_catalog()
    return catalog.determine(text, language)


__all__ = [
    "PhraseCatalog",
    "PhraseTemplate",
    "build_navigation_catalog",
    "determine_phrase",
]

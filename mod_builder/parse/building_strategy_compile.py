from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml


SOURCE_FILE_ORDER = [
    "resource.yaml",
    "industry.yaml",
    "trade.yaml",
    "research.yaml",
    "unity.yaml",
    "military.yaml",
    "wilderness.yaml",
]

ALLOWED_PROJECTIONS = {"designation", "zone"}

ALLOWED_STRATEGIES = {
    "efficiency",
    "always",
    "job_only",
    "job_low_priority",
    "district_capacity",
    "job_bookend",
}


@dataclass(frozen=True)
class Priority:
    before: str | None = None
    after: str | None = None


@dataclass(frozen=True)
class ConstructionSubcase:
    trigger: str
    strategy_override: str | None = None


@dataclass(frozen=True)
class ConstructionRow:
    building: str
    projection: str
    context: str
    strategy: str
    include_default: bool
    subcases: tuple[ConstructionSubcase, ...]
    priority: Priority
    source_order: int


@dataclass(frozen=True)
class DestructionRow:
    building: str
    triggers: tuple[str, ...]
    remove_series: bool
    source_order: int


@dataclass(frozen=True)
class DesignationSubcase:
    trigger: str
    job_provider_districts: str | tuple[str, ...]


@dataclass(frozen=True)
class DesignationContext:
    name: str
    job_provider_districts: str | tuple[str, ...]
    subcases: tuple[DesignationSubcase, ...]


class NoAliasSafeDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


def _iter_source_files(buildings_dir: Path) -> list[Path]:
    file_map = {
        path.name: path
        for path in buildings_dir.glob("*.yaml")
        if path.name != "designation_contexts.yaml"
    }
    ordered_files = [file_map[name] for name in SOURCE_FILE_ORDER if name in file_map]
    remaining_files = sorted(path for name, path in file_map.items() if name not in SOURCE_FILE_ORDER)
    return ordered_files + remaining_files


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, Dumper=NoAliasSafeDumper, allow_unicode=True, sort_keys=False)


def _copy_required_string_list(value: Any, key: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise ValueError(f"'{key}' must be a non-empty list of strings.")
    return list(value)


def _copy_optional_string_list(value: Any, key: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"'{key}' must be a list of strings.")
    return list(value)


def _parse_contexts(value: Any) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list) and value and all(isinstance(item, str) and item for item in value):
        if len(set(value)) != len(value):
            raise ValueError("'context' must not contain duplicate values.")
        return list(value)
    raise ValueError("'context' must be a non-empty string or list of strings.")


def _parse_priority(value: Any) -> Priority:
    if value is None:
        return Priority()
    if not isinstance(value, dict):
        raise ValueError("'priority' must be a mapping.")
    before = value.get("before")
    after = value.get("after")
    if before is not None and not isinstance(before, str):
        raise ValueError("'priority.before' must be a string.")
    if after is not None and not isinstance(after, str):
        raise ValueError("'priority.after' must be a string.")
    return Priority(before=before, after=after)


def _parse_building_ref(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Building refs must be strings in the strategy model: {value!r}")
    return value


def _parse_strategy(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("'strategy' must be a non-empty string.")
    if value not in ALLOWED_STRATEGIES:
        raise ValueError(f"Unknown building construction strategy '{value}'.")
    return value


def _parse_subcase_trigger(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Subcase trigger must be a non-empty scripted trigger name.")
    return value


def _parse_construction_subcases(value: Any) -> tuple[ConstructionSubcase, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not value:
        raise ValueError("'subcases' must be a non-empty list of mappings.")

    result: list[ConstructionSubcase] = []
    seen: set[str] = set()
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError("'subcases' entries must be mappings.")
        trigger = _parse_subcase_trigger(entry.get("trigger"))
        if trigger in seen:
            raise ValueError(f"Duplicate construction subcase trigger '{trigger}'.")
        seen.add(trigger)
        strategy_override = entry.get("strategy_override")
        result.append(
            ConstructionSubcase(
                trigger=trigger,
                strategy_override=(
                    _parse_strategy(strategy_override)
                    if strategy_override is not None
                    else None
                ),
            )
        )
    return tuple(result)


def _parse_include_default(value: Any, subcases: tuple[ConstructionSubcase, ...]) -> bool:
    if value is None:
        return True
    if not isinstance(value, bool):
        raise ValueError("'include_default' must be a boolean.")
    if not value and not subcases:
        raise ValueError("'include_default: false' requires at least one subcase.")
    return value


def _parse_job_provider_districts(value: Any, key: str) -> str | tuple[str, ...]:
    if value is None or value == "any":
        return "any"
    return tuple(_copy_required_string_list(value, key))


def load_designation_contexts(buildings_dir: Path) -> dict[str, DesignationContext]:
    path = buildings_dir / "designation_contexts.yaml"
    if not path.exists():
        return {}

    raw_data = _load_yaml(path) or {}
    if not isinstance(raw_data, dict) or not isinstance(raw_data.get("designation_contexts"), dict):
        raise ValueError(f"{path} must contain a 'designation_contexts' mapping.")

    result: dict[str, DesignationContext] = {}
    for name, raw_context in raw_data["designation_contexts"].items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"{path} contains an invalid designation context name: {name!r}")
        if raw_context is None:
            raw_context = {}
        if not isinstance(raw_context, dict):
            raise ValueError(f"{path} designation context '{name}' must be a mapping.")

        job_provider_districts = _parse_job_provider_districts(
            raw_context.get("job_provider_districts"),
            f"designation_contexts.{name}.job_provider_districts",
        )
        raw_subcases = raw_context.get("subcases") or {}
        if not isinstance(raw_subcases, dict):
            raise ValueError(f"{path} designation context '{name}' subcases must be a mapping.")

        subcases: list[DesignationSubcase] = []
        for trigger, raw_subcase in raw_subcases.items():
            trigger = _parse_subcase_trigger(trigger)
            if raw_subcase is None:
                raw_subcase = {}
            if not isinstance(raw_subcase, dict):
                raise ValueError(f"{path} subcase '{trigger}' must be a mapping.")
            subcases.append(
                DesignationSubcase(
                    trigger=trigger,
                    job_provider_districts=(
                        _parse_job_provider_districts(
                            raw_subcase["job_provider_districts"],
                            f"designation_contexts.{name}.subcases.{trigger}.job_provider_districts",
                        )
                        if "job_provider_districts" in raw_subcase
                        else job_provider_districts
                    ),
                )
            )

        result[name] = DesignationContext(
            name=name,
            job_provider_districts=job_provider_districts,
            subcases=tuple(subcases),
        )
    return result


def _parse_destruction_entries(value: Any) -> list[tuple[tuple[str, ...], bool]]:
    if value is None:
        return []

    entries: list[Any]
    if isinstance(value, list):
        entries = value
    elif isinstance(value, dict):
        # Temporary tolerance for existing grouped data while it is migrated.
        entries = [value]
    else:
        raise ValueError("'destruction' must be a list of mappings.")

    parsed: list[tuple[tuple[str, ...], bool]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("'destruction' entries must be mappings.")
        raw_triggers = entry.get("triggers", entry.get("any_triggers"))
        triggers = tuple(_copy_required_string_list(raw_triggers, "destruction.triggers"))
        remove_series = entry.get("remove_series", True)
        if not isinstance(remove_series, bool):
            raise ValueError("'destruction.remove_series' must be a boolean.")
        parsed.append((triggers, remove_series))
    return parsed


def _emit_grouped_context_rows(
    raw_data: list[Any],
    *,
    path: Path,
    source_counter: list[int],
    construction_rows: list[ConstructionRow],
    destruction_rows: list[DestructionRow],
) -> None:
    for context_index, context in enumerate(raw_data):
        if not isinstance(context, dict):
            raise ValueError(f"{path} context #{context_index} must be a mapping.")

        designations = _copy_optional_string_list(context.get("designations"), "designations")
        zone_types = _copy_optional_string_list(context.get("zone_types"), "zone_types")
        if not designations and not zone_types:
            raise ValueError(
                f"{path} context #{context_index} must define at least one of 'designations' or 'zone_types'."
            )

        groups = context.get("groups")
        if not isinstance(groups, list) or not groups:
            raise ValueError(f"{path} context #{context_index} must define a non-empty 'groups' list.")

        for group_index, group in enumerate(groups):
            if not isinstance(group, dict):
                raise ValueError(f"{path} context #{context_index} group #{group_index} must be a mapping.")

            strategy = _parse_strategy(group.get("strategy"))
            subcases = _parse_construction_subcases(group.get("subcases"))
            include_default = _parse_include_default(group.get("include_default"), subcases)
            if subcases and not designations:
                raise ValueError(
                    f"{path} context #{context_index} group #{group_index} defines subcases "
                    "without a designation projection."
                )
            buildings = group.get("buildings")
            if not isinstance(buildings, list) or not buildings:
                raise ValueError(f"{path} context #{context_index} group #{group_index} must define buildings.")

            destruction_entries = _parse_destruction_entries(group.get("destruction"))

            for building_ref in buildings:
                building = _parse_building_ref(building_ref)
                for designation in designations:
                    construction_rows.append(
                        ConstructionRow(
                            building=building,
                            projection="designation",
                            context=designation,
                            strategy=strategy,
                            include_default=include_default,
                            subcases=subcases,
                            priority=Priority(),
                            source_order=source_counter[0],
                        )
                    )
                    source_counter[0] += 1

                for zone_type in zone_types:
                    construction_rows.append(
                        ConstructionRow(
                            building=building,
                            projection="zone",
                            context=zone_type,
                            strategy=strategy,
                            include_default=True,
                            subcases=(),
                            priority=Priority(),
                            source_order=source_counter[0],
                        )
                    )
                    source_counter[0] += 1

                for triggers, remove_series in destruction_entries:
                    destruction_rows.append(
                        DestructionRow(
                            building=building,
                            triggers=triggers,
                            remove_series=remove_series,
                            source_order=source_counter[0],
                        )
                    )
                    source_counter[0] += 1


def _emit_building_overlay_rows(
    raw_data: dict[str, Any],
    *,
    path: Path,
    source_counter: list[int],
    construction_rows: list[ConstructionRow],
    destruction_rows: list[DestructionRow],
) -> None:
    buildings = raw_data.get("buildings")
    if not isinstance(buildings, dict):
        raise ValueError(f"{path} building-centered configs must contain a 'buildings' mapping.")

    for building, config in buildings.items():
        if not isinstance(building, str):
            raise ValueError(f"{path} contains a non-string building id: {building!r}")
        if not isinstance(config, dict):
            raise ValueError(f"{path} entry '{building}' must be a mapping.")

        for index, item in enumerate(config.get("construction") or []):
            if not isinstance(item, dict):
                raise ValueError(f"{path} entry '{building}' construction #{index} must be a mapping.")
            projection = item.get("projection")
            if projection not in ALLOWED_PROJECTIONS:
                raise ValueError(f"{path} entry '{building}' has invalid projection '{projection}'.")
            contexts = _parse_contexts(item.get("context"))
            subcases = _parse_construction_subcases(item.get("subcases"))
            include_default = _parse_include_default(item.get("include_default"), subcases)
            if projection == "zone" and subcases:
                raise ValueError(f"{path} entry '{building}' uses designation subcases in a zone projection.")
            strategy = _parse_strategy(item.get("strategy"))
            priority = _parse_priority(item.get("priority"))
            for context in contexts:
                construction_rows.append(
                    ConstructionRow(
                        building=building,
                        projection=projection,
                        context=context,
                        strategy=strategy,
                        include_default=include_default,
                        subcases=subcases,
                        priority=priority,
                        source_order=source_counter[0],
                    )
                )
                source_counter[0] += 1

        for triggers, remove_series in _parse_destruction_entries(config.get("destruction")):
            destruction_rows.append(
                DestructionRow(
                    building=building,
                    triggers=triggers,
                    remove_series=remove_series,
                    source_order=source_counter[0],
                )
            )
            source_counter[0] += 1


def load_strategy_rows(buildings_dir: Path) -> tuple[list[ConstructionRow], list[DestructionRow]]:
    construction_rows: list[ConstructionRow] = []
    destruction_rows: list[DestructionRow] = []
    source_counter = [0]

    for path in _iter_source_files(buildings_dir):
        raw_data = _load_yaml(path)
        if raw_data is None:
            continue
        if isinstance(raw_data, list):
            _emit_grouped_context_rows(
                raw_data,
                path=path,
                source_counter=source_counter,
                construction_rows=construction_rows,
                destruction_rows=destruction_rows,
            )
        elif isinstance(raw_data, dict):
            _emit_building_overlay_rows(
                raw_data,
                path=path,
                source_counter=source_counter,
                construction_rows=construction_rows,
                destruction_rows=destruction_rows,
            )
        else:
            raise ValueError(f"{path} must contain grouped contexts or a building overlay mapping.")

    _validate_duplicate_construction_rows(construction_rows)
    return construction_rows, destruction_rows


def load_manual_destruction_rows(path: Path, source_order_start: int) -> list[DestructionRow]:
    if not path.exists():
        return []

    raw_data = _load_yaml(path) or {}
    if not isinstance(raw_data, dict):
        raise ValueError(f"{path} must contain a mapping.")
    entries = raw_data.get("manual_building_destruction")
    if not isinstance(entries, list):
        raise ValueError(f"{path} must contain a 'manual_building_destruction' list.")

    rows: list[DestructionRow] = []
    source_order = source_order_start
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"{path} entry #{index} must be a mapping.")
        buildings = _copy_required_string_list(entry.get("buildings"), "buildings")
        triggers = tuple(_copy_required_string_list(entry.get("triggers"), "triggers"))
        remove_series = entry.get("remove_series", True)
        if not isinstance(remove_series, bool):
            raise ValueError(f"{path} entry #{index} 'remove_series' must be a boolean.")

        for building in buildings:
            rows.append(
                DestructionRow(
                    building=building,
                    triggers=triggers,
                    remove_series=remove_series,
                    source_order=source_order,
                )
            )
            source_order += 1
    return rows


def _validate_duplicate_construction_rows(rows: list[ConstructionRow]) -> None:
    seen: set[tuple[str, str, str]] = set()
    bookends: dict[tuple[str, str, str | None], list[str]] = defaultdict(list)
    for row in rows:
        key = (row.building, row.projection, row.context)
        if key in seen:
            raise ValueError(
                "Duplicate construction row for "
                f"{row.building} in {row.projection}:{row.context}."
            )
        seen.add(key)

        effective_strategies: list[tuple[str | None, str]] = []
        if row.include_default:
            effective_strategies.append((None, row.strategy))
        effective_strategies.extend(
            (subcase.trigger, subcase.strategy_override or row.strategy)
            for subcase in row.subcases
        )
        for subcase, strategy in effective_strategies:
            if strategy == "job_bookend":
                bookends[(row.projection, row.context, subcase)].append(row.building)

    for (projection, context, subcase), buildings in bookends.items():
        if len(buildings) > 1:
            raise ValueError(
                "Only one job_bookend building is allowed in a projection context "
                f"'{projection}:{context}:{subcase or 'default'}': {', '.join(buildings)}."
            )


def _sort_bucket(rows: list[ConstructionRow]) -> tuple[list[ConstructionRow], list[str]]:
    warnings: list[str] = []
    by_building = {row.building: row for row in rows}
    outgoing: dict[str, set[str]] = {row.building: set() for row in rows}
    incoming_count: dict[str, int] = {row.building: 0 for row in rows}

    for row in rows:
        if row.priority.after:
            if row.priority.after not in by_building:
                warnings.append(
                    f"Ignored priority.after for {row.building}: "
                    f"{row.priority.after} is not in the same bucket."
                )
            elif row.building not in outgoing[row.priority.after]:
                outgoing[row.priority.after].add(row.building)
                incoming_count[row.building] += 1
        if row.priority.before:
            if row.priority.before not in by_building:
                warnings.append(
                    f"Ignored priority.before for {row.building}: "
                    f"{row.priority.before} is not in the same bucket."
                )
            elif row.priority.before not in outgoing[row.building]:
                outgoing[row.building].add(row.priority.before)
                incoming_count[row.priority.before] += 1

    available = sorted(
        [row for row in rows if incoming_count[row.building] == 0],
        key=lambda row: row.source_order,
    )
    result: list[ConstructionRow] = []

    while available:
        row = available.pop(0)
        result.append(row)
        for next_building in sorted(outgoing[row.building], key=lambda item: by_building[item].source_order):
            incoming_count[next_building] -= 1
            if incoming_count[next_building] == 0:
                available.append(by_building[next_building])
                available.sort(key=lambda item: item.source_order)

    if len(result) != len(rows):
        cycle_buildings = [building for building, count in incoming_count.items() if count > 0]
        raise ValueError(f"Priority cycle in construction bucket: {', '.join(cycle_buildings)}")

    return result, warnings


def _build_strategy_buckets(rows: list[ConstructionRow]) -> tuple[list[dict[str, Any]], list[str]]:
    strategy_map: dict[str, list[ConstructionRow]] = defaultdict(list)
    for row in sorted(rows, key=lambda item: item.source_order):
        strategy_map[row.strategy].append(row)

    strategy_buckets: list[dict[str, Any]] = []
    warnings: list[str] = []
    for strategy, bucket_rows in sorted(
        strategy_map.items(),
        key=lambda item: min(row.source_order for row in item[1]),
    ):
        sorted_rows, bucket_warnings = _sort_bucket(bucket_rows)
        warnings.extend(bucket_warnings)
        strategy_buckets.append(
            {
                "strategy": strategy,
                "buildings": [row.building for row in sorted_rows],
            }
        )
    return strategy_buckets, warnings


def _serialize_job_provider_districts(value: str | tuple[str, ...]) -> str | list[str]:
    return value if value == "any" else list(value)


def _build_designation_branches(
    context: str,
    context_rows: list[ConstructionRow],
    context_config: DesignationContext,
) -> tuple[list[dict[str, Any]], list[str]]:
    configured_triggers = [subcase.trigger for subcase in context_config.subcases]
    configured_trigger_set = set(configured_triggers)
    for row in context_rows:
        for subcase in row.subcases:
            if subcase.trigger not in configured_trigger_set:
                raise ValueError(
                    f"Construction row {row.building} references undeclared subcase "
                    f"'{subcase.trigger}' in designation context '{context}'."
                )

    branches: list[dict[str, Any]] = []
    default_rows = [row for row in context_rows if row.include_default]
    default_buckets, warnings = _build_strategy_buckets(default_rows)
    branches.append(
        {
            "name": "default",
            "trigger": None,
            "exclude_triggers": configured_triggers,
            "job_provider_districts": _serialize_job_provider_districts(
                context_config.job_provider_districts
            ),
            "strategy_buckets": default_buckets,
        }
    )

    excluded: list[str] = []
    for subcase in context_config.subcases:
        branch_rows: list[ConstructionRow] = []
        for row in context_rows:
            construction_subcase = next(
                (item for item in row.subcases if item.trigger == subcase.trigger),
                None,
            )
            if construction_subcase is not None:
                branch_rows.append(
                    replace(
                        row,
                        strategy=construction_subcase.strategy_override or row.strategy,
                    )
                )
        branch_buckets, branch_warnings = _build_strategy_buckets(branch_rows)
        warnings.extend(branch_warnings)
        branches.append(
            {
                "name": subcase.trigger,
                "trigger": subcase.trigger,
                "exclude_triggers": list(excluded),
                "job_provider_districts": _serialize_job_provider_districts(
                    subcase.job_provider_districts
                ),
                "strategy_buckets": branch_buckets,
            }
        )
        excluded.append(subcase.trigger)
    return branches, warnings


def _build_construction_projection(
    rows: list[ConstructionRow],
    projection: str,
    designation_context_configs: dict[str, DesignationContext] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    context_map: dict[str, list[ConstructionRow]] = defaultdict(list)
    for row in rows:
        if row.projection == projection:
            context_map[row.context].append(row)

    contexts: list[dict[str, Any]] = []
    warnings: list[str] = []

    for context, context_rows in context_map.items():
        if projection == "designation":
            context_config = (designation_context_configs or {}).get(
                context,
                DesignationContext(context, "any", ()),
            )
            branches, branch_warnings = _build_designation_branches(
                context,
                context_rows,
                context_config,
            )
            warnings.extend(branch_warnings)
            contexts.append(
                {
                    "context": context,
                    "job_provider_districts": _serialize_job_provider_districts(
                        context_config.job_provider_districts
                    ),
                    "branches": branches,
                    "_sort_key": min(row.source_order for row in context_rows),
                }
            )
        else:
            invalid_subcase_rows = [row for row in context_rows if row.subcases]
            if invalid_subcase_rows:
                raise ValueError(
                    f"Subcase is only supported for designation construction; "
                    f"found it in zone context '{context}'."
                )
            strategy_buckets, bucket_warnings = _build_strategy_buckets(context_rows)
            warnings.extend(bucket_warnings)
            contexts.append(
                {
                    "context": context,
                    "strategy_buckets": strategy_buckets,
                    "_sort_key": min(row.source_order for row in context_rows),
                }
            )

    contexts.sort(key=lambda item: item["_sort_key"])
    for item in contexts:
        item.pop("_sort_key", None)
        item["types"] = [item["context"]]
    if projection == "zone":
        contexts = _merge_equivalent_zone_contexts(contexts)
    return contexts, warnings


def _strategy_buckets_key(strategy_buckets: list[dict[str, Any]]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (bucket["strategy"], tuple(bucket.get("buildings") or []))
        for bucket in strategy_buckets
    )


def _merge_equivalent_zone_contexts(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    index_by_key: dict[tuple[tuple[str, tuple[str, ...]], ...], int] = {}

    for context in contexts:
        key = _strategy_buckets_key(context["strategy_buckets"])
        existing_index = index_by_key.get(key)
        if existing_index is None:
            index_by_key[key] = len(merged)
            merged.append(context)
            continue

        existing = merged[existing_index]
        existing["types"].extend(context["types"])

    return merged


def _load_building_metadata(generated_configs_dir: Path) -> dict[str, dict[str, Any]]:
    path = generated_configs_dir / "building_conditions.yaml"
    if not path.exists():
        return {}
    data = _load_yaml(path) or {}
    result: dict[str, dict[str, Any]] = {}
    for item in data.get("bca_buildings") or []:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            result[item["name"]] = item
    return result


def _build_destruction_projection(
    rows: list[DestructionRow],
    *,
    building_metadata: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    grouped: dict[tuple[str, str | None], list[DestructionRow]] = defaultdict(list)
    warnings: list[str] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        expanded_buildings = [row.building]
        if row.remove_series:
            expanded_buildings.extend(building_metadata.get(row.building, {}).get("upgrade_chain") or [])

        for building in expanded_buildings:
            category = building_metadata.get(building, {}).get("category")
            if category is None:
                warnings.append(f"No category metadata found for demolition building {building}.")
            for trigger in row.triggers:
                dedupe_key = (building, trigger)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                grouped[(trigger, category)].append(
                    DestructionRow(
                        building=building,
                        triggers=(trigger,),
                        remove_series=False,
                        source_order=row.source_order,
                    )
                )

    result: list[dict[str, Any]] = []
    for (trigger, category), grouped_rows in grouped.items():
        sorted_rows = sorted(grouped_rows, key=lambda item: item.source_order)
        item: dict[str, Any] = {
            "trigger": [trigger],
        }
        if category:
            item["category_filter"] = [category]
        item["building"] = [row.building for row in sorted_rows]
        item["_sort_key"] = min(row.source_order for row in sorted_rows)
        result.append(item)

    result.sort(key=lambda item: item["_sort_key"])
    for item in result:
        item.pop("_sort_key", None)
    return result, warnings


def _build_normalized_debug(
    construction_rows: list[ConstructionRow],
    destruction_rows: list[DestructionRow],
) -> dict[str, Any]:
    buildings: dict[str, dict[str, Any]] = {}

    for row in sorted(construction_rows, key=lambda item: item.source_order):
        entry = buildings.setdefault(row.building, {})
        construction = entry.setdefault("construction", [])
        row_data: dict[str, Any] = {
            "projection": row.projection,
            "context": row.context,
            "strategy": row.strategy,
            "source_order": row.source_order,
        }
        if not row.include_default:
            row_data["include_default"] = False
        if row.subcases:
            row_data["subcases"] = []
            for subcase in row.subcases:
                subcase_data: dict[str, Any] = {"trigger": subcase.trigger}
                if subcase.strategy_override:
                    subcase_data["strategy_override"] = subcase.strategy_override
                row_data["subcases"].append(subcase_data)
        if row.priority.before or row.priority.after:
            row_data["priority"] = {}
            if row.priority.before:
                row_data["priority"]["before"] = row.priority.before
            if row.priority.after:
                row_data["priority"]["after"] = row.priority.after
        construction.append(row_data)

    for row in sorted(destruction_rows, key=lambda item: item.source_order):
        entry = buildings.setdefault(row.building, {})
        destruction = entry.setdefault("destruction", [])
        row_data: dict[str, Any] = {
            "triggers": list(row.triggers),
            "source_order": row.source_order,
        }
        if row.remove_series:
            row_data["remove_series"] = True
        destruction.append(row_data)

    return {"building_strategy_model": {"buildings": buildings}}


def compile_building_strategies(
    buildings_dir: Path | None = None,
    generated_configs_dir: Path | None = None,
) -> dict[str, Any]:
    base_dir = Path(__file__).resolve().parent.parent
    buildings_dir = buildings_dir or (base_dir / "configs" / "buildings")
    generated_configs_dir = generated_configs_dir or (base_dir / "templates" / "generated_configs")

    construction_rows, destruction_rows = load_strategy_rows(buildings_dir)
    next_source_order = max(
        (row.source_order for row in construction_rows + destruction_rows),
        default=-1,
    ) + 1
    destruction_rows.extend(
        load_manual_destruction_rows(
            base_dir / "configs" / "manual_building_destruction.yaml",
            next_source_order,
        )
    )
    designation_context_configs = load_designation_contexts(buildings_dir)
    building_metadata = _load_building_metadata(generated_configs_dir)

    designation_contexts, designation_warnings = _build_construction_projection(
        construction_rows,
        "designation",
        designation_context_configs,
    )
    zone_contexts, zone_warnings = _build_construction_projection(construction_rows, "zone")
    destruction_list, destruction_warnings = _build_destruction_projection(
        destruction_rows,
        building_metadata=building_metadata,
    )
    warnings = designation_warnings + zone_warnings + destruction_warnings

    outputs = {
        "designation_building_strategies.yaml": {
            "building_strategy_designation_contexts": designation_contexts,
        },
        "zone_building_strategies.yaml": {
            "building_strategy_zone_contexts": zone_contexts,
        },
        "destruction_building_strategies.yaml": {
            "building_strategy_destruction_contexts": destruction_list,
        },
        "normalized_building_strategy_model.yaml": _build_normalized_debug(construction_rows, destruction_rows),
    }
    if warnings:
        outputs["building_strategy_compile_warnings.yaml"] = {"building_strategy_compile_warnings": warnings}
    else:
        warning_path = generated_configs_dir / "building_strategy_compile_warnings.yaml"
        if warning_path.exists():
            warning_path.unlink()

    for filename, data in outputs.items():
        _dump_yaml(generated_configs_dir / filename, data)

    return {key: value for data in outputs.values() for key, value in data.items()}


if __name__ == "__main__":
    compile_building_strategies()

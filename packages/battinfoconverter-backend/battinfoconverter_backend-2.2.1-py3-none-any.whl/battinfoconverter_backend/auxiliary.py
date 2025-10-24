import inspect
import re
import traceback
from decimal import Decimal
from typing import Any, Optional
import pandas as pd

DEBUG_STATUS = False

def add_to_structure(
    jsonld: dict,
    path: list[str],
    value: Any,
    unit: str,
    data_container: "json_convert.ExcelContainer",
    metadata: str | None = None,
) -> None:
    """
    Adds a value to a JSON-LD structure at a specified path, incorporating units and other contextual information.

        This function processes a path to traverse or modify the JSON-LD structure and handles special cases like 
        measured properties, ontology links, and unique identifiers. It uses data from the provided ExcelContainer 
        to resolve unit mappings and context connectors.

        Args:
            jsonld (dict): The JSON-LD structure to modify.
            path (list[str]): A list of strings representing the hierarchical path in the JSON-LD where the value should be added.
            value (any): The value to be inserted at the specified path.
            unit (str): The unit associated with the value. If 'No Unit', the value is treated as unitless.
            data_container (ExcelContainer): An instance of the ExcelContainer dataclass (from son_convert module) containing supporting data
                                            for unit mappings, connectors, and unique identifiers.
            metadata (str | None): Optional metadata label from the schema sheet, used to align repeated connector entries.
        Returns:
            None: This function modifies the JSON-LD structure in place.

        Raises:
            ValueError: If the value is invalid, a required unit is missing, or an error occurs during path processing.
            RuntimeError: If any unexpected error arises while processing the value and path.
    """
    from .json_convert import get_information_value

    # ------------------------------------------------------------------ #
    # helper functions                                                   #
    # ------------------------------------------------------------------ #
    MULTI_CONNECTORS = {
        "hasConstituent",
        "hasAdditive",
        "hasSolute",
        "hasSolvent",
    }

    def _merge_type(node: dict[str, Any], new_type: str) -> None:
        """Ensure the ``@type`` entry on ``node`` includes ``new_type``.

        Args:
            node (dict[str, Any]): The JSON-LD node whose ``@type`` should be updated.
            new_type (str): The type value to merge into the node.

        Returns:
            None: This helper mutates ``node`` in place.
        """

        if "@type" not in node:
            node["@type"] = new_type
        else:
            existing_type = node["@type"]
            if isinstance(existing_type, list):
                if new_type not in existing_type:
                    existing_type.append(new_type)
            elif existing_type != new_type:
                node["@type"] = [existing_type, new_type]

    def _add_or_extend_list(
        node: dict[str, Any], key: str, entry: dict[str, Any]
    ) -> None:
        """Add ``entry`` to ``node[key]`` while normalizing the holder to a list.

        Args:
            node (dict[str, Any]): The parent node whose key should hold the entry.
            key (str): The key on ``node`` where the entry should be inserted.
            entry (dict[str, Any]): The dictionary representing the new list item.

        Returns:
            None: This helper mutates ``node`` in place.
        """

        current_value = node.get(key)
        if current_value in (None, {}):
            node[key] = entry
        elif isinstance(current_value, list):
            current_value.append(entry)
        else:
            node[key] = [current_value, entry]

    def _extract_type(segment: str) -> str:
        """Return the type payload when ``segment`` contains the ``type|`` prefix.

        Args:
            segment (str): The path segment being evaluated.

        Returns:
            str: The extracted type value if the prefix is present, otherwise the original segment.
        """

        return segment.split("|", 1)[1] if segment.startswith("type|") else segment

    def _new_item(parent: dict[str, Any], key: str) -> dict[str, Any]:
        """Create and return a new dictionary entry under ``parent[key]``.

        Args:
            parent (dict[str, Any]): The JSON-LD node that holds the collection.
            key (str): The key that should receive a new dictionary entry.

        Returns:
            dict[str, Any]: The freshly created dictionary stored at ``parent[key]``.
        """

        value = parent.get(key)
        if value in (None, {}):
            parent[key] = {}
            return parent[key]
        if isinstance(value, list):
            fresh = {}
            value.append(fresh)
            return fresh
        parent[key] = [value, {}]
        return parent[key][-1]

    def _register_last(path_key: tuple[str, ...], node: dict[str, Any]) -> None:
        """Remember the most recent ``node`` encountered for ``path_key``.

        Args:
            path_key (tuple[str, ...]): The connector path associated with ``node``.
            node (dict[str, Any]): The node that was most recently created or visited.

        Returns:
            None: The registry is stored on ``data_container`` for later lookups.
        """

        if not path_key:
            return
        history = getattr(data_container, "_last_nodes", None)
        if history is None:
            history = {}
            setattr(data_container, "_last_nodes", history)
        history[path_key] = node

    def _get_last(path_key: tuple[str, ...]) -> dict[str, Any] | None:
        """Fetch the previously registered node for ``path_key`` if available.

        Args:
            path_key (tuple[str, ...]): The connector path used to track nodes.

        Returns:
            dict[str, Any] | None: The remembered node if present; otherwise ``None``.
        """

        history = getattr(data_container, "_last_nodes", None)
        if not history:
            return None
        return history.get(path_key)

    def _next_index(path_key: tuple[str, ...]) -> int:
        """Provide a sequential index for ``path_key`` to balance assignments.

        Args:
            path_key (tuple[str, ...]): The connector path to count occurrences for.

        Returns:
            int: The index assigned to the next occurrence of ``path_key``.
        """

        counters = getattr(data_container, "_path_counts", None)
        if counters is None:
            counters = {}
            setattr(data_container, "_path_counts", counters)
        value = counters.get(path_key, 0)
        counters[path_key] = value + 1
        return value

    def _tokenize(label: str) -> tuple[str, ...]:
        """Split ``label`` into alphanumeric tokens for fuzzy matching.

        Args:
            label (str): The label from which to extract normalized tokens.

        Returns:
            tuple[str, ...]: A tuple of lowercase alphanumeric tokens.
        """

        return tuple(re.findall(r"[A-Za-z0-9]+", label.lower()))

    def _registry() -> dict[tuple[str, ...], list[dict[str, Any]]]:
        """Return the connector registry stored on ``data_container``.

        Returns:
            dict[tuple[str, ...], list[dict[str, Any]]]: The registry indexed by connector paths.
        """

        registry = getattr(data_container, "_connector_registry", None)
        if registry is None:
            registry = {}
            setattr(data_container, "_connector_registry", registry)
        return registry

    def _register_connector_entry(
        parent_path: tuple[str, ...],
        connector: str,
        node: dict[str, Any],
        metadata_label: str | None,
        value: Any,
    ) -> None:
        """Store a new connector entry with tokenized metadata and values.

        Args:
            parent_path (tuple[str, ...]): The parent connector path for the entry.
            connector (str): The connector key associated with the entry.
            node (dict[str, Any]): The node corresponding to the connector occurrence.
            metadata_label (str | None): Optional metadata label to seed matching tokens.
            value (Any): The raw value that may provide additional matching tokens.

        Returns:
            None: The registry entry is appended for later retrieval.
        """

        registry = _registry()
        entries = registry.setdefault(parent_path, [])
        tokens: set[str] = set()
        if metadata_label:
            tokens.update(_tokenize(metadata_label))
        if isinstance(value, str):
            tokens.update(_tokenize(value))
        entries.append(
            {
                "connector": connector,
                "node": node,
                "base_tokens": tokens,
                "alias_tokens": set(),
                "order": len(entries),
            }
        )

    def _update_entry_tokens(
        parent_path: tuple[str, ...], node: dict[str, Any], *labels: str | None
    ) -> None:
        """Augment alias tokens for entries tied to ``parent_path`` and ``node``.

        Args:
            parent_path (tuple[str, ...]): The connector path used to look up entries.
            node (dict[str, Any]): The specific connector node whose entry should be updated.
            *labels (str | None): Optional labels whose tokens help future lookups.

        Returns:
            None: The registry entry is updated in place when found.
        """

        registry = getattr(data_container, "_connector_registry", None)
        if not registry:
            return
        entries = registry.get(parent_path)
        if not entries:
            return
        for entry in entries:
            if entry["node"] is node:
                alias_tokens = entry.setdefault("alias_tokens", set())
                for label in labels:
                    if isinstance(label, str) and label:
                        alias_tokens.update(_tokenize(label))
                break

    def _get_registry_entries(
        parent_path: tuple[str, ...]
    ) -> list[dict[str, Any]]:
        """Return registry entries registered for ``parent_path``.

        Args:
            parent_path (tuple[str, ...]): The connector path to search.

        Returns:
            list[dict[str, Any]]: The list of registered entries for the path.
        """

        registry = getattr(data_container, "_connector_registry", None)
        if not registry:
            return []
        return registry.get(parent_path, [])

    def _select_entry(
        label: str | None,
        entries: list[dict[str, Any]],
        part: str,
        traversed: list[str],
    ) -> dict[str, Any] | None:
        """Select the most appropriate connector entry for the incoming value.

        Args:
            label (str | None): The metadata label to aid selection.
            entries (list[dict[str, Any]]): Candidate entries to compare against.
            part (str): The final property part being populated.
            traversed (list[str]): The path segments already processed.

        Returns:
            dict[str, Any] | None: The chosen entry, or ``None`` if no match is appropriate.
        """

        if not entries:
            return None
        chosen: dict[str, Any] | None = None
        best_score: tuple[int, int, int, int, int] | None = None
        tokens = set(_tokenize(label)) if label else set()
        token_occurrence: dict[str, int] = {}
        base_occurrence: dict[str, int] = {}
        if tokens:
            for entry in entries:
                combined = entry.get("base_tokens", set()) | entry.get("alias_tokens", set())
                base_tokens = entry.get("base_tokens", set())
                for token in combined:
                    token_occurrence[token] = token_occurrence.get(token, 0) + 1
                for token in base_tokens:
                    base_occurrence[token] = base_occurrence.get(token, 0) + 1
        if tokens:
            for entry in entries:
                base_tokens = entry.get("base_tokens", set())
                entry_tokens = base_tokens | entry.get("alias_tokens", set())
                if not entry_tokens:
                    continue
                overlap = len(tokens & entry_tokens)
                if overlap == 0:
                    continue
                subset_flag = 1 if entry_tokens <= tokens else 0
                unique_base_hits = sum(
                    1
                    for token in tokens
                    if token in base_tokens and base_occurrence.get(token, 0) == 1
                )
                unique_hits = sum(
                    1
                    for token in tokens
                    if token in entry_tokens and token_occurrence.get(token, 0) == 1
                )
                score = (
                    unique_base_hits,
                    unique_hits,
                    subset_flag,
                    overlap,
                    -entry["order"],
                )
                if best_score is None or score > best_score:
                    best_score = score
                    chosen = entry
        if chosen is not None:
            return chosen

        path_key = tuple(traversed)
        index = _next_index(path_key)
        if index < len(entries):
            return entries[index]

        for entry in entries:
            existing = entry["node"].get(part)
            if existing in (None, {}):
                return entry

        last_key_base = tuple(traversed[:-1])
        for entry in entries:
            connector = entry.get("connector")
            last_key = last_key_base + (connector,)
            remembered = _get_last(last_key)
            if remembered is entry["node"]:
                return entry
        return None

    # ------------------------------------------------------------------ #
    # main body                                                          #
    # ------------------------------------------------------------------ #
    try:
        current_level = jsonld
        unit_map = (
            data_container.data["unit_map"].set_index("Item").to_dict("index")
        )
        context_connector = data_container.data["context_connector"]
        connectors = set(context_connector["Item"])
        unique_id = data_container.data["unique_id"]

        # ---- skip only true empties (0 and 0.0 are valid) ------------- #
        if (
            value is None
            or (isinstance(value, str) and value.strip() == "")
            or (isinstance(value, float) and pd.isna(value))
            or (
                isinstance(value, (int, float, Decimal))
                and pd.isna(pd.Series([value])[0])
            )
        ):
            return
        # ---------------------------------------------------------------- #

        traversed: list[str] = []

        for index, parts in enumerate(path):
            # ---------- special-command parsing ------------------------- #
            if "|" not in parts:
                part = parts
            elif "type|" in parts:
                _, typ = parts.split("|", 1)
                if typ:
                    _merge_type(current_level, typ)
                continue
            else:  # rev|
                command, part = parts.split("|", 1)
                if command == "rev":
                    current_level = current_level.setdefault("@reverse", {})
                else:
                    raise ValueError(f"Unknown command {command} in {parts}")

            if isinstance(current_level, list):
                current_level = current_level[-1]

            last = index == len(path) - 1
            penultimate = index == len(path) - 2

            traversed.append(part)

            # -------- create node if missing ---------------------------- #
            if part not in current_level and (value or unit):
                if part in connectors:
                    connector_type = context_connector.loc[
                        context_connector["Item"] == part, "Key"
                    ].values[0]
                    current_level[part] = (
                        {}
                        if pd.isna(connector_type)
                        else {"@type": connector_type}
                    )
                else:
                    current_level[part] = {}

            next_level = current_level[part]

            # -------- measured-property block --------------------------- #
            if penultimate and unit != "No Unit":
                if pd.isna(unit):
                    raise ValueError(f"Value '{value}' missing unit.")
                unit_info = unit_map.get(unit, {})
                mp_entry = {
                    "@type": _extract_type(path[-1]),
                    "hasNumericalPart": {
                        "@type": "emmo:RealData",
                        "hasNumberValue": value,
                    },
                    "hasMeasurementUnit": unit_info.get("Key", "UnknownUnit"),
                }
                parent = current_level[-1] if isinstance(current_level, list) else current_level
                _add_or_extend_list(parent, part, mp_entry)
                break

            # -------- final-value branch -------------------------------- #
            if last and unit == "No Unit":
                parent_path = tuple(traversed[:-1])

                registry_entries = []
                if part not in MULTI_CONNECTORS and isinstance(current_level, dict):
                    connector_parent_path: tuple[str, ...] = parent_path[:-1]
                    connector_key: str | None = (
                        parent_path[-1] if parent_path else None
                    )
                    if connector_parent_path and connector_key:
                        for entry in _get_registry_entries(connector_parent_path):
                            if entry.get("connector") != connector_key:
                                continue
                            node = entry.get("node")
                            if isinstance(node, dict):
                                registry_entries.append(entry)

                if registry_entries:
                    selected = _select_entry(metadata, registry_entries, part, traversed)
                    if selected is not None:
                        target = selected["node"]
                        holder = target.get(part)
                        if not isinstance(holder, dict):
                            target[part] = {} if holder in (None, {}) else {"rdfs:comment": holder}
                        target_node = target[part]
                        if value in unique_id["Item"].values:
                            uid = get_information_value(
                                df=unique_id,
                                row_to_look=value,
                                col_to_look="ID",
                                col_to_match="Item",
                            )
                            if not pd.isna(uid):
                                target_node["@id"] = uid
                            _merge_type(target_node, value)
                        elif value:
                            target_node["rdfs:comment"] = value
                        if part in current_level and current_level[part] in (None, {}):
                            current_level.pop(part)
                        _update_entry_tokens(
                            parent_path,
                            target,
                            metadata,
                            value if isinstance(value, str) else None,
                        )
                        break

                if part in MULTI_CONNECTORS:
                    target_node = _new_item(current_level, part)
                    _register_last(tuple(traversed), target_node)
                    _register_connector_entry(parent_path, part, target_node, metadata, value)
                else:
                    target_node = next_level
                if value in unique_id["Item"].values:
                    uid = get_information_value(
                        df=unique_id,
                        row_to_look=value,
                        col_to_look="ID",
                        col_to_match="Item",
                    )
                    if not pd.isna(uid):
                        target_node["@id"] = uid
                    _merge_type(target_node, value)
                elif value:
                    target_node["rdfs:comment"] = value
                if part in MULTI_CONNECTORS:
                    _update_entry_tokens(
                        parent_path,
                        target_node,
                        metadata,
                        value if isinstance(value, str) else None,
                    )
                break

            current_level = next_level

    except Exception as e:  
        traceback.print_exc()
        raise RuntimeError(
            f"Error occurred with value '{value}' and path '{path}': {str(e)}"
        )


def plf(value: Any, part: str, current_level: Optional[dict] = None, debug_switch: bool = DEBUG_STATUS):
    """
    Print Line Function (PLF).

    This function is used for debugging purposes. It prints the current line number, 
    along with the provided value, part, and optionally the current level, if debugging 
    is enabled via the `debug_switch` parameter.

    Args:
        value (Any): The value being processed or debugged.
        part (Any): The part of the JSON-LD or data structure being processed.
        current_level (Optional[dict]): The current level of the JSON-LD or data structure, if applicable.
        debug_switch (bool): A flag to enable or disable debug output. Defaults to True.

    Returns:
        None: This function does not return any value.
    """
    if debug_switch:
        current_frame = inspect.currentframe()
        line_number = current_frame.f_back.f_lineno
        if current_level is not None:
            print(f'pass line {line_number}, value:', value,'AND part:', part, 'AND current_level:', current_level)
        else:
            print(f'pass line {line_number}, value:', value,'AND part:', part)
    else:
        pass 

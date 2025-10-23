from __future__ import annotations

from typing import Any, List, Mapping, Union

from anndata import AnnData

ANNDATA_REF_PREFIX = "@"


def is_anndata_reference(value: Any) -> bool:
    """Checks if a value is a string that looks like an AnnData reference."""
    return isinstance(value, str) and value.startswith(ANNDATA_REF_PREFIX)


def resolve_anndata_references(
    input_value: Any, adata_context: Union[AnnData, List[AnnData]]
) -> Any:
    """
    Recursively resolves any AnnData references within a nested data structure.

    This single entry point intelligently handles both single and multi-dataset
    contexts, providing clear error messages for misuse.

    Args:
        input_value: The item to resolve (e.g., a string, list, or dict).
        adata_context: The AnnData object or list of AnnData objects to resolve against.

    Returns:
        The input value with all AnnData references resolved.

    Raises:
        ValueError: If an indexed reference (e.g., '@0:...') is used in a single-dataset context.
        IndexError: If a dataset index in a reference is out of bounds.
        KeyError: If a key (e.g., 'cell_type') is not found in the specified AnnData attribute.
    """
    is_multi_context = isinstance(adata_context, list)

    def _resolve_single_reference(ref_string: str) -> Any:
        """Parses and resolves a single AnnData reference string."""
        if not is_anndata_reference(ref_string):
            return ref_string

        body = ref_string[len(ANNDATA_REF_PREFIX) :]
        parts = body.split(":", 1)

        if parts[0].isdigit():
            if not is_multi_context:
                raise ValueError(
                    f"Indexed reference '{ref_string}' is not valid in a single-dataset context."
                )

            index = int(parts[0])
            if index >= len(adata_context):
                raise IndexError(
                    f"Dataset index {index} in reference '{ref_string}' is out of range for {len(adata_context)} datasets."
                )

            target_adata = adata_context[index]

            ref_string = ANNDATA_REF_PREFIX + (parts[1] if len(parts) > 1 else "")
        else:
            target_adata = adata_context[0] if is_multi_context else adata_context

        return _resolve_standard_reference(ref_string, target_adata)

    def _resolve_standard_reference(ref_string: str, adata: AnnData) -> Any:
        """Resolves a non-indexed reference against a single AnnData object."""
        body = ref_string[len(ANNDATA_REF_PREFIX) :]
        parts = body.split(":", 1)
        object_name = parts[0]
        key = parts[1] if len(parts) > 1 else None

        if object_name == "X":
            if key:
                raise ValueError("Reference '@X' does not accept a key.")
            return adata.X

        data_store = getattr(adata, object_name)

        if key is None:
            if object_name not in {"obs", "var"}:
                raise ValueError(f"Reference '@{object_name}' requires a key.")
            return data_store

        if key not in data_store:
            raise KeyError(f"Key '{key}' not found in adata.{object_name}.")

        return data_store[key]

    if is_anndata_reference(input_value):
        return _resolve_single_reference(input_value)

    if isinstance(input_value, Mapping):
        return {
            k: resolve_anndata_references(v, adata_context)
            for k, v in input_value.items()
        }

    if isinstance(input_value, list):
        return [resolve_anndata_references(item, adata_context) for item in input_value]

    if isinstance(input_value, tuple):
        return tuple(
            resolve_anndata_references(item, adata_context) for item in input_value
        )

    return input_value

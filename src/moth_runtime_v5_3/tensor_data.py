"""Canonical typed trees in numeric Safetensors; never serialized JSON blobs."""
from typing import Any
import numpy as np
from .energy.schema import Runtime53Failure, string_pool, decode_string_pool
from .legacy.canonical import digest
_NULL, _BOOL, _INT, _STRING, _LIST, _DICT = range(6)

def _encode_graph(value: Any) -> tuple[dict[str, np.ndarray], list[str]]:
    kinds: list[int] = []
    parents: list[int] = []
    keys: list[int] = []
    text_values: list[int] = []
    int_values: list[int] = []
    labels: list[str] = []
    label_map: dict[str, int] = {}

    def label(text: str) -> int:
        if text not in label_map:
            label_map[text] = len(labels)
            labels.append(text)
        return label_map[text]

    def visit(item: Any, parent: int, key: str | None) -> int:
        index = len(kinds)
        parents.append(parent)
        keys.append(label(key) if key is not None else -1)
        text_values.append(-1)
        int_values.append(0)
        if item is None:
            kinds.append(_NULL)
        elif isinstance(item, bool):
            kinds.append(_BOOL)
            int_values[index] = int(item)
        elif isinstance(item, int):
            kinds.append(_INT)
            int_values[index] = item
        elif isinstance(item, str):
            kinds.append(_STRING)
            text_values[index] = label(item)
        elif isinstance(item, list):
            kinds.append(_LIST)
            for child in item:
                visit(child, index, None)
        elif isinstance(item, dict):
            kinds.append(_DICT)
            for child_key in sorted(item):
                visit(item[child_key], index, str(child_key))
        else:
            raise Runtime53Failure(
                "INVALID_FIELD",
                "compiled graph accepts JSON scalar types only",
                {"type": type(item).__name__},
            )
        return index

    visit(value, -1, None)
    if len(kinds) >= 2**22 or len(labels) >= 2**22:
        raise Runtime53Failure(
            "RESOURCE_LIMIT", "compiled field graph exceeds fixed tensor bounds"
        )
    if any(value < -(2**31) or value >= 2**31 for value in int_values):
        raise Runtime53Failure(
            "RESOURCE_LIMIT", "compiled field integer exceeds int32 bounds"
        )
    integer_indices = [
        index
        for index, kind in enumerate(kinds)
        if kind in (_BOOL, _INT)
    ]
    return {
        "node_kind": np.asarray(kinds, dtype=np.uint8),
        "node_parent": np.asarray(parents, dtype=np.int32),
        "node_key_label": np.asarray(keys, dtype=np.int32),
        "node_text_label": np.asarray(text_values, dtype=np.int32),
        "node_int_index": np.asarray(integer_indices, dtype=np.int32),
        "node_int_value": np.asarray(
            [int_values[index] for index in integer_indices], dtype=np.int32
        ),
    }, labels


def _decode_graph(tensors: dict[str, np.ndarray], labels: tuple[str, ...]) -> Any:
    kinds = tensors["node_kind"]
    parents = tensors["node_parent"]
    keys = tensors["node_key_label"]
    text = tensors["node_text_label"]
    integer_indices = tensors["node_int_index"]
    integer_values = tensors["node_int_value"]
    count = len(kinds)
    if not (
        parents.shape == keys.shape == text.shape == (count,)
        and count
        and int(parents[0]) == -1
    ):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled graph shape is invalid"
        )
    if (
        integer_indices.ndim != 1
        or integer_values.shape != integer_indices.shape
        or np.any(integer_indices < 0)
        or np.any(integer_indices >= count)
        or np.any(integer_indices[1:] <= integer_indices[:-1])
    ):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled integer operands are invalid"
        )
    integers = {
        int(index): int(value)
        for index, value in zip(integer_indices, integer_values)
    }
    children: list[list[int]] = [[] for _ in range(count)]
    for index in range(1, count):
        parent = int(parents[index])
        if parent < 0 or parent >= index:
            raise Runtime53Failure(
                "TENSOR_SCHEMA_MISMATCH", "compiled graph parent is invalid"
            )
        children[parent].append(index)

    def build(index: int) -> Any:
        kind = int(kinds[index])
        if kind == _NULL:
            return None
        if kind == _BOOL:
            if index not in integers:
                raise Runtime53Failure(
                    "TENSOR_SCHEMA_MISMATCH", "boolean operand is absent"
                )
            return bool(integers[index])
        if kind == _INT:
            if index not in integers:
                raise Runtime53Failure(
                    "TENSOR_SCHEMA_MISMATCH", "integer operand is absent"
                )
            return integers[index]
        if kind == _STRING:
            label_index = int(text[index])
            if label_index < 0 or label_index >= len(labels):
                raise Runtime53Failure(
                    "TENSOR_SCHEMA_MISMATCH", "text label is out of range"
                )
            return labels[label_index]
        if kind == _LIST:
            return [build(child) for child in children[index]]
        if kind == _DICT:
            result = {}
            for child in children[index]:
                key_index = int(keys[child])
                if key_index < 0 or key_index >= len(labels):
                    raise Runtime53Failure(
                        "TENSOR_SCHEMA_MISMATCH", "key label is out of range"
                    )
                key = labels[key_index]
                if key in result:
                    raise Runtime53Failure(
                        "TENSOR_SCHEMA_MISMATCH", "compiled key is duplicated"
                    )
                result[key] = build(child)
            return result
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled graph opcode is invalid"
        )

    return build(0)


def put_data(store, value, kind):
    tensors, labels = _encode_graph(value)
    tensors['text_bytes'], tensors['text_offsets'] = string_pool(labels)
    return store.put(tensors, schema='moth-'+kind+'/5.3', kind=kind,
                     source_hash=digest('moth-'+kind+'-source/5.3', value))

def read_data(envelope, kind):
    if envelope.schema != 'moth-'+kind+'/5.3' or envelope.kind != kind:
        raise Runtime53Failure('TENSOR_SCHEMA_MISMATCH', 'typed object kind changed')
    t = envelope.tensors
    labels = decode_string_pool(t['text_bytes'], t['text_offsets'])
    value = _decode_graph(t, labels)
    expected, pool = _encode_graph(value)
    expected['text_bytes'], expected['text_offsets'] = string_pool(pool)
    if set(expected) != set(t) or any(a.dtype != t[k].dtype or not np.array_equal(a,t[k]) for k,a in expected.items()):
        raise Runtime53Failure('TENSOR_SCHEMA_MISMATCH', 'noncanonical typed tree')
    if digest('moth-'+kind+'-source/5.3', value) != envelope.metadata['source_hash']:
        raise Runtime53Failure('OBJECT_HASH_MISMATCH', 'typed source identity changed')
    return value

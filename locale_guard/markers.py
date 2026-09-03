from __future__ import annotations


class MarkerError(ValueError):
    pass


def replace_marked_section(text: str, start_marker: str, end_marker: str, body: str) -> str:
    start_count = text.count(start_marker)
    end_count = text.count(end_marker)
    if start_count != 1 or end_count != 1:
        raise MarkerError(f"expected exactly one marker pair; found start={start_count}, end={end_count}")
    start_index = text.index(start_marker)
    end_index = text.index(end_marker)
    if end_index <= start_index:
        raise MarkerError("end marker occurs before start marker")
    prefix = text[: start_index + len(start_marker)]
    suffix = text[end_index:]
    normalized_body = body.strip("\n")
    return f"{prefix}\n{normalized_body}\n{suffix}"

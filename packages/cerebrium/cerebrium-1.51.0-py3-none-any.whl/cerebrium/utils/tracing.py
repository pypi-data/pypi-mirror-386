"""
Tracing utilities for X-Ray trace propagation
"""


def convert_w3c_to_xray(traceparent: str) -> str:
    """
    Converts W3C traceparent format to X-Ray trace ID format

    Input:  "00-68dc5913595c55e167fcafd054cbf333-9c660c7313458283-01"
    Output: "Root=1-68dc5913-595c55e167fcafd054cbf333;Parent=9c660c7313458283;Sampled=1"

    Args:
        traceparent: W3C traceparent string (format: version-trace_id-parent_id-flags)

    Returns:
        X-Ray trace ID string or empty string if invalid
    """
    if not traceparent:
        return ""

    parts = traceparent.split("-")
    if len(parts) != 4:
        return ""

    version, trace_id, parent_id, flags = parts

    # Validate format
    if len(trace_id) != 32 or len(parent_id) != 16:
        return ""

    # X-Ray format: Root=1-{8 hex}-{24 hex};Parent={16 hex};Sampled={0|1}
    sampled = "1" if flags == "01" else "0"
    xray_trace_id = f"Root=1-{trace_id[:8]}-{trace_id[8:]};Parent={parent_id};Sampled={sampled}"

    return xray_trace_id

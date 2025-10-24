import logging

import pytest

from dictlens.core import compare_dicts

debug = True


# --------------------------------------------------------------------------
# 1️⃣ BASIC TESTS — direct equality and simple mismatches
# --------------------------------------------------------------------------

def test_identical_dicts():
    a = {"x": 1, "y": 2}
    b = {"x": 1, "y": 2}
    assert compare_dicts(a, b, show_debug=debug)


def test_simple_value_mismatch():
    a = {"x": 1}
    b = {"x": 2}
    assert not compare_dicts(a, b, show_debug=debug)


def test_type_mismatch():
    a = {"x": 1}
    b = {"x": "1"}
    assert not compare_dicts(a, b, show_debug=debug)


def test_key_mismatch():
    a = {"x": 1}
    b = {"y": 1}
    assert not compare_dicts(a, b, show_debug=debug)


# --------------------------------------------------------------------------
# 2️⃣ TOLERANCE TESTS — abs_tol and rel_tol
# --------------------------------------------------------------------------

def test_global_abs_tolerance():
    a = {"temp": 20.0}
    b = {"temp": 20.05}
    assert compare_dicts(a, b, abs_tol=0.1, show_debug=debug)


def test_global_tolerance_fail():
    a = {"temp": 20.0}
    b = {"temp": 21.0}
    assert not compare_dicts(a, b, abs_tol=0.5, show_debug=debug)


def test_relative_tolerance_success():
    a = {"humidity": 100.0}
    b = {"humidity": 104.0}
    assert compare_dicts(a, b, rel_tol=0.05, show_debug=debug)  # 5% tolerance


# --------------------------------------------------------------------------
# 3️⃣ FIELD-LEVEL TOLERANCE TESTS
# --------------------------------------------------------------------------

def test_per_field_abs_tolerance():
    a = {"a": 1.0, "b": 2.0}
    b = {"a": 1.5, "b": 2.5}
    abs_tol_fields = {"$.b": 1.0}
    assert compare_dicts(a, b, abs_tol=0.5, abs_tol_fields=abs_tol_fields, show_debug=debug)


def test_per_field_rel_tolerance():
    a = {"values": {"x": 100, "y": 200}}
    b = {"values": {"x": 110, "y": 210}}
    rel_tol_fields = {"$.values.x": 0.2}  # 20%
    assert compare_dicts(a, b, rel_tol=0.05, rel_tol_fields=rel_tol_fields, show_debug=debug)


# --------------------------------------------------------------------------
# 4️⃣ IGNORED FIELDS
# --------------------------------------------------------------------------

def test_ignore_path_root_field():
    a = {"id": 1, "timestamp": "now"}
    b = {"id": 1, "timestamp": "later"}

    # Ignore only the root timestamp field
    ignore_fields = ["$.timestamp"]

    assert compare_dicts(a, b, ignore_fields=ignore_fields, show_debug=debug)


def test_ignore_fields_complex():
    a = {
        "user": {"id": 7, "profile": {"updated_at": "2025-10-14T10:00:00Z", "age": 30}},
        "devices": [
            {"id": "d1", "debug": "alpha", "temp": 20.0},
            {"id": "d2", "debug": "beta", "temp": 20.1},
        ],
        "sessions": [
            {"events": [{"meta": {"trace": "abc"}, "value": 10.0}]},
            {"events": [{"meta": {"trace": "def"}, "value": 10.5}]},
        ],
    }

    b = {
        "user": {"id": 7, "profile": {"updated_at": "2025-10-15T10:00:05Z", "age": 30}},
        "devices": [
            {"id": "d1", "debug": "changed", "temp": 20.05},
            {"id": "d2", "debug": "changed", "temp": 20.18},
        ],
        "sessions": [
            {"events": [{"meta": {"trace": "xyz"}, "value": 10.01}]},
            {"events": [{"meta": {"trace": "uvw"}, "value": 10.52}]},
        ],
    }

    ignore_fields = [
        "$.user.profile.updated_at",  # exact path
        "$.devices[*].debug",  # array wildcard
        "$.sessions[*].events[*].meta.trace",  # explicit deep path
    ]

    assert compare_dicts(
        a,
        b,
        ignore_fields=ignore_fields,
        abs_tol=0.05,
        rel_tol=0.02,
    )


# --------------------------------------------------------------------------
# 5️⃣ LIST & WILDCARD TESTS
# --------------------------------------------------------------------------

def test_list_length_mismatch():
    a = {"items": [1, 2, 3]}
    b = {"items": [1, 2]}
    assert not compare_dicts(a, b, show_debug=debug)


def test_array_specific_index_tolerance():
    a = {"sensors": [{"temp": 20.0}, {"temp": 21.0}]}
    b = {"sensors": [{"temp": 20.05}, {"temp": 21.5}]}
    abs_tol_fields = {"$.sensors[0].temp": 0.1, "$.sensors[1].temp": 1.0}  # only second sensor
    assert compare_dicts(a, b, abs_tol_fields=abs_tol_fields, show_debug=debug)


def test_array_wildcard_tolerance():
    a = {"sensors": [{"temp": 20.0}, {"temp": 21.0}]}
    b = {"sensors": [{"temp": 20.2}, {"temp": 21.1}]}
    abs_tol_fields = {"$.sensors[*].temp": 0.5}
    assert compare_dicts(a, b, abs_tol_fields=abs_tol_fields, show_debug=debug)


# --------------------------------------------------------------------------
# 6️⃣ PROPERTY & RECURSIVE WILDCARDS
# --------------------------------------------------------------------------

def test_property_wildcard_tolerance():
    a = {"network": {"n1": {"v": 10}, "n2": {"v": 10}}}
    b = {"network": {"n1": {"v": 10.5}, "n2": {"v": 9.8}}}
    abs_tol_fields = {"$.network.*.v": 1.0}
    assert compare_dicts(a, b, abs_tol_fields=abs_tol_fields, show_debug=debug)


def test_recursive_wildcard_tolerance_replaced():
    a = {"meta": {"deep": {"very": {"x": 100}}}}
    b = {"meta": {"deep": {"very": {"x": 101}}}}
    abs_tol_fields = {"$.meta.deep.very.x": 2.0}
    assert compare_dicts(a, b, abs_tol_fields=abs_tol_fields)


# --------------------------------------------------------------------------
# 7️⃣ COMPLEX SCENARIO — IoT network simulation
# --------------------------------------------------------------------------

def test_complex_nested_tolerance():
    old = {
        "network": {
            "id": "site-001",
            "uptime_hours": 10234.5,
            "nodes": [
                {
                    "id": "N-A",
                    "metrics": {"temperature": 21.5, "humidity": 48.0, "voltage": 3.31, "packet_loss": 0.5},
                },
                {
                    "id": "N-B",
                    "metrics": {"temperature": 22.0, "humidity": 47.5, "voltage": 3.28, "packet_loss": 0.8},
                },
            ],
        },
        "gateway": {"battery": 87.0, "signal_strength": -68},
    }

    new = {
        "network": {
            "id": "site-001",
            "uptime_hours": 10236.2,
            "nodes": [
                {
                    "id": "N-A",
                    "metrics": {"temperature": 21.7, "humidity": 48.4, "voltage": 3.30, "packet_loss": 0.7},
                },
                {
                    "id": "N-B",
                    "metrics": {"temperature": 21.9, "humidity": 47.3, "voltage": 3.30, "packet_loss": 0.6},
                },
            ],
        },
        "gateway": {"battery": 86.2, "signal_strength": -70},
    }

    abs_tol_fields = {
        "$.network.uptime_hours": 5.0,
        "$.gateway.battery": 2.0,
        "$.gateway.signal_strength": 3.0,
        "$.network.nodes[*].metrics.packet_loss": 0.5,
    }

    rel_tol_fields = {
        "$.network.nodes[*].metrics.temperature": 0.02,
        "$.network.nodes[*].metrics.humidity": 0.03,
        "$.network.nodes[*].metrics.voltage": 0.02,
    }

    assert compare_dicts(
        old,
        new,
        abs_tol_fields=abs_tol_fields,
        rel_tol_fields=rel_tol_fields,
        show_debug=debug,
    )


def test_combined_global_and_field_tolerances():
    """
    Test a case mixing global and per-field tolerances:
    - Global tolerances: abs_tol=0.05, rel_tol=0.01
    - Field-specific tolerances override global ones
    - One field is ignored completely
    """

    a = {
        "meta": {"version": 1.0, "id": "abc"},
        "sensor": {
            "temp": 21.5,
            "humidity": 48.0,
            "pressure": 101.3
        },
        "status": {
            "signal_strength": -70,
            "battery": 95.0
        }
    }

    b = {
        "meta": {"version": 1.02, "id": "abc"},
        "sensor": {
            "temp": 21.6,
            "humidity": 49.0,  # large diff, handled by per-field abs_tol
            "pressure": 101.4  # small diff, handled by global tolerances
        },
        "status": {
            "signal_strength": -68,  # within rel_tol
            "battery": 94.5  # within global abs_tol
        }
    }

    abs_tol_fields = {
        "$.sensor.humidity": 2.0,  # large absolute tolerance
        "$.meta.version": 0.05  # tighter tolerance for version
    }

    rel_tol_fields = {
        "$.status.signal_strength": 0.05  # 5% relative tolerance allowed
    }

    ignore_fields = ["$.meta.id"]  # ignored entirely

    assert compare_dicts(
        a,
        b,
        abs_tol=0.05,
        rel_tol=0.01,
        abs_tol_fields=abs_tol_fields,
        rel_tol_fields=rel_tol_fields,
        ignore_fields=ignore_fields,
        show_debug=True
    )


def test_compare_dicts_type_mismatch(caplog):
    caplog.set_level(logging.DEBUG)
    a = {"val": 123}
    b = {"val": "123"}
    assert not compare_dicts(a, b, show_debug=True)
    assert any("TYPE MISMATCH" in msg for msg in caplog.messages)


def test_compare_dicts_with_tolerances_numeric():
    a = {"x": 100.0}
    b = {"x": 100.1}
    assert compare_dicts(a, b, abs_tol=0.2)


def test_compare_dicts_invalid_pattern_in_input():
    a = {"x": 1}
    b = {"x": 1}
    with pytest.raises(ValueError):
        compare_dicts(a, b, ignore_fields=["invalid"])


def test_compare_dicts_invalid_type_inputs():
    with pytest.raises(TypeError):
        compare_dicts("not-a-dict", {"x": 1})


def test_compare_dicts_list_and_nested():
    a = {"data": [1, 2, 3]}
    b = {"data": [1, 2, 3]}
    assert compare_dicts(a, b)


def test_compare_dicts_list_mismatch():
    a = {"data": [1, 2, 3]}
    b = {"data": [1, 3, 2]}
    assert not compare_dicts(a, b)


# -----------------------------------------------------------------------------
# Deep comparison numerics and logs
# -----------------------------------------------------------------------------

def test_compare_dicts_logs_numeric_details(caplog):
    caplog.set_level(logging.DEBUG)
    a = {"val": 10.0}
    b = {"val": 10.05}
    compare_dicts(a, b, abs_tol=0.1, show_debug=True)
    logs = "\n".join(caplog.messages)
    assert "[NUMERIC COMPARE]" in logs
    assert "diff=" in logs


def test_compare_dicts_handles_none_values(caplog):
    caplog.set_level(logging.DEBUG)
    a = {"val": None}
    b = {"val": None}
    assert compare_dicts(a, b, show_debug=True)
    assert any("OK → None" in msg for msg in caplog.messages)


def test_compare_dicts_one_none_value():
    a = {"val": None}
    b = {"val": 10}
    assert not compare_dicts(a, b)

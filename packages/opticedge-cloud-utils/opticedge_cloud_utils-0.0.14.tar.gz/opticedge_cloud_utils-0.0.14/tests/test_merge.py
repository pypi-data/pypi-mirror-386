# tests/test_utils.py
import pytest
import importlib
import copy
from opticedge_cloud_utils.merge import _deep_get, _compute_new_value_from_delta_or_data, detect_field_changes, _set_nested, build_object_from_changes

MODULE_PATH = "opticedge_cloud_utils.merge"  # adjust if deep_merge is in another file/module


@pytest.fixture
def module():
    """Dynamically import and reload the target module before each test."""
    mod = importlib.import_module(MODULE_PATH)
    importlib.reload(mod)
    return mod


def test_merges_non_overlapping_keys(module):
    base = {"a": 1}
    updates = {"b": 2}
    result = module.deep_merge(base, updates)
    assert result == {"a": 1, "b": 2}


def test_overwrites_existing_value(module):
    base = {"a": 1, "b": 2}
    updates = {"b": 99}
    result = module.deep_merge(base, updates)
    assert result == {"a": 1, "b": 99}


def test_deep_merges_nested_dicts(module):
    base = {"a": {"x": 1, "y": 2}}
    updates = {"a": {"y": 99, "z": 3}}
    result = module.deep_merge(base, updates)
    assert result == {"a": {"x": 1, "y": 99, "z": 3}}


def test_removes_key_when_value_none_and_delete_nulls_true(module):
    base = {"a": 1, "b": 2}
    updates = {"b": None}
    result = module.deep_merge(base, updates, delete_nulls=True)
    assert result == {"a": 1}


def test_preserves_none_when_delete_nulls_false(module):
    base = {"a": 1, "b": 2}
    updates = {"b": None}
    result = module.deep_merge(base, updates, delete_nulls=False)
    assert result == {"a": 1, "b": None}


def test_handles_empty_updates(module):
    base = {"a": 1}
    updates = {}
    result = module.deep_merge(base, updates)
    assert result == {"a": 1}


def test_handles_empty_base(module):
    base = {}
    updates = {"x": 10}
    result = module.deep_merge(base, updates)
    assert result == {"x": 10}


def test_original_base_not_modified(module):
    base = {"a": {"b": 1}}
    updates = {"a": {"c": 2}}
    result = module.deep_merge(base, updates)
    assert result == {"a": {"b": 1, "c": 2}}
    assert base == {"a": {"b": 1}}
    assert id(result) != id(base)


def test_deep_get_found_and_not_found():
    obj = {"a": {"b": None}, "x": 1}
    # nested key exists and is None -> found True
    val, found = _deep_get(obj, "a.b")
    assert found is True
    assert val is None

    # top-level key
    val, found = _deep_get(obj, "x")
    assert found is True
    assert val == 1

    # missing key
    val, found = _deep_get(obj, "a.c")
    assert found is False
    assert val is None

    # empty path returns the object itself
    val, found = _deep_get(obj, "")
    assert found is True
    assert val == obj


def test_deep_get_obj_none_branches():
    # obj is None and non-empty path -> should be not found
    val, found = _deep_get(None, "a.b")
    assert found is False
    assert val is None

    # obj is None and empty path -> earlier code returns (None, False) because obj is None
    val, found = _deep_get(None, "")
    assert found is False
    assert val is None


@pytest.mark.parametrize(
    "data, delta, path, delete_nulls, expected_val, expected_found",
    [
        # delta contains non-None value -> use delta
        ({"k": "old"}, {"k": "new"}, "k", True, "new", True),
        # delta contains None and delete_nulls=True -> removed
        ({"k": "old"}, {"k": None}, "k", True, None, False),
        # delta contains None and delete_nulls=False -> explicit None
        ({"k": "old"}, {"k": None}, "k", False, None, True),
        # delta doesn't contain it -> fallback to data
        ({"a": {"b": 2}}, {"x": 1}, "a.b", True, 2, True),
        # neither contains it
        ({"a": {}}, {"x": {}}, "a.missing", True, None, False),
        # nested delta overrides nested data
        ({"profile": {"type": "student"}}, {"profile": {"type": "alumni"}}, "profile.type", True, "alumni", True),
    ]
)
def test_compute_new_value_from_delta_or_data(data, delta, path, delete_nulls, expected_val, expected_found):
    val, found = _compute_new_value_from_delta_or_data(data, delta, path, delete_nulls=delete_nulls)
    assert found is expected_found
    assert val == expected_val


def test_detect_field_changes_basic_scenario():
    data = {
        "email": "old@example.com",
        "profile": {"type": "student", "name": "Alice"},
        "extras": {"x": 1}
    }
    delta = {
        "email": None,               # deletion
        "profile": {"type": "alumni"}  # update nested field
    }
    fields = ["email", "profile.type", "profile.name", "extras.x", "missing.field"]

    changes = detect_field_changes(data, delta, fields, delete_nulls=True)

    # email -> deleted
    assert changes["email"]["old"] == "old@example.com"
    assert changes["email"]["new"] == None
    assert changes["email"]["old_found"] is True
    assert changes["email"]["new_found"] is False
    assert changes["email"]["changed"] is True
    assert changes["email"]["reason"] == "deleted"

    # profile.type -> updated
    assert changes["profile.type"]["old"] == "student"
    assert changes["profile.type"]["new"] == "alumni"
    assert changes["profile.type"]["old_found"] is True
    assert changes["profile.type"]["new_found"] is True
    assert changes["profile.type"]["changed"] is True
    assert changes["profile.type"]["reason"] == "updated"

    # profile.name -> unchanged (not present in delta)
    assert changes["profile.name"]["old"] == "Alice"
    assert changes["profile.name"]["new"] == "Alice"
    assert changes["profile.name"]["changed"] is False
    assert changes["profile.name"]["reason"] == "unchanged"

    # extras.x -> unchanged
    assert changes["extras.x"]["old"] == 1
    assert changes["extras.x"]["new"] == 1
    assert changes["extras.x"]["changed"] is False

    # missing.field -> remains missing
    assert changes["missing.field"]["old_found"] is False
    assert changes["missing.field"]["new_found"] is False
    assert changes["missing.field"]["changed"] is False


def test_detect_field_changes_delete_nulls_false_treats_null_as_value():
    data = {"k": "old"}
    delta = {"k": None}
    fields = ["k"]

    changes = detect_field_changes(data, delta, fields, delete_nulls=False)
    assert changes["k"]["old"] == "old"
    assert changes["k"]["old_found"] is True
    # new_found should be True because we treat None as explicit value
    assert changes["k"]["new_found"] is True
    assert changes["k"]["new"] is None
    assert changes["k"]["changed"] is True
    assert changes["k"]["reason"] == "updated"


def test_detect_field_changes_added_branch():
    # field does not exist in data but exists in delta -> 'added' branch should be hit
    data = {}
    delta = {"new_field": "value123"}
    fields = ["new_field"]

    changes = detect_field_changes(data, delta, fields, delete_nulls=True)

    assert changes["new_field"]["old_found"] is False
    assert changes["new_field"]["new_found"] is True
    assert changes["new_field"]["new"] == "value123"
    assert changes["new_field"]["changed"] is True
    assert changes["new_field"]["reason"] == "added"




def test_set_nested_creates_nested_dict():
    d = {}
    _set_nested(d, ["a", "b", "c"], 123)
    assert d == {"a": {"b": {"c": 123}}}


def test_set_nested_overwrites_non_dict_intermediate():
    d = {"a": 5}
    # Should replace non-dict at 'a' with a dict and set nested key
    _set_nested(d, ["a", "b"], "x")
    assert isinstance(d["a"], dict)
    assert d["a"]["b"] == "x"


def test_set_nested_single_key_sets_top_level():
    d = {"existing": 1}
    _set_nested(d, ["top"], "value")
    assert d["top"] == "value"
    # ensure we didn't clobber other keys
    assert d["existing"] == 1


def _make_change_entry(new_found, new_value, old_found=False, old_value=None, changed=True, reason="updated"):
    """
    Helper to build a detect_field_changes-style entry for tests.
    """
    return {
        "old": old_value,
        "old_found": old_found,
        "new": new_value,
        "new_found": new_found,
        "changed": changed,
        "reason": reason,
    }


def test_build_object_from_changes_basic_excludes_none_and_unchanged():
    # Simulate detect_field_changes output (default: include_unchanged=False)
    changes = {
        "email": _make_change_entry(new_found=True, new_value="new@example.com", old_found=True, old_value="old@example.com", changed=True, reason="updated"),
        "type": _make_change_entry(new_found=True, new_value="basic", old_found=True, old_value="basic", changed=False, reason="unchanged"),
        "profile.age": _make_change_entry(new_found=False, new_value=None, old_found=True, old_value=25, changed=True, reason="deleted"),
        # non-field key like aggregate should be ignored
        "any_changed": True
    }

    out = build_object_from_changes(changes, exclude_none=True, include_unchanged=False)
    # Only email should be present (profile.age is deleted -> excluded, type unchanged -> excluded)
    assert out == {"email": "new@example.com"}


def test_build_object_from_changes_includes_none_when_requested():
    changes = {
        "profile.age": _make_change_entry(new_found=True, new_value=None, old_found=True, old_value=25, changed=True, reason="updated"),
    }
    out = build_object_from_changes(changes, exclude_none=False, include_unchanged=False)
    # profile.age should be included explicitly with value None
    assert out == {"profile": {"age": None}}


def test_build_object_from_changes_merges_sibling_paths():
    changes = {
        "a.b": _make_change_entry(new_found=True, new_value=1, old_found=False, old_value=None, changed=True, reason="added"),
        "a.c": _make_change_entry(new_found=True, new_value=2, old_found=False, old_value=None, changed=True, reason="added"),
    }
    out = build_object_from_changes(changes, exclude_none=True, include_unchanged=False)
    assert out == {"a": {"b": 1, "c": 2}}


def test_build_object_from_changes_includes_unchanged_when_flag_true():
    changes = {
        "email": _make_change_entry(new_found=True, new_value="new@example.com", old_found=True, old_value="old@example.com", changed=True, reason="updated"),
        "type": _make_change_entry(new_found=True, new_value="basic", old_found=True, old_value="basic", changed=False, reason="unchanged"),
        "profile.age": _make_change_entry(new_found=False, new_value=None, old_found=True, old_value=25, changed=True, reason="deleted"),
    }

    # include unchanged fields as well
    out = build_object_from_changes(changes, exclude_none=True, include_unchanged=True)
    # Should include email and type. profile.age is deleted -> still excluded.
    assert out == {"email": "new@example.com", "type": "basic"}


def test_build_object_skips_non_dict_entries_and_preserves_input():
    # Ensure non-dict values in changes are ignored and function does not mutate input
    original = {
        "valid.field": _make_change_entry(new_found=True, new_value="ok", old_found=False, old_value=None, changed=True, reason="added"),
        "any_changed": True,
        "weird": "not-a-dict",
    }
    changes = copy.deepcopy(original)
    out = build_object_from_changes(changes, exclude_none=True, include_unchanged=False)
    assert out == {"valid": {"field": "ok"}}
    # original should be unchanged
    assert changes == original


def test_skips_entries_missing_required_keys():
    """
    Cover the branch:
        if "changed" not in info or "new_found" not in info:
            continue
    Ensure entries that look like dicts but are missing the expected keys are skipped.
    """
    changes = {
        # missing 'changed'
        "missing_changed": {"new": "ok", "new_found": True},
        # missing 'new_found'
        "missing_new_found": {"old": "x", "changed": True},
        # valid entry to ensure function still returns valid ones
        "valid.field": _make_change_entry(new_found=True, new_value="ok", old_found=False, old_value=None, changed=True, reason="added"),
    }
    out = build_object_from_changes(changes, exclude_none=True, include_unchanged=False)
    # Only the valid entry should be present
    assert out == {"valid": {"field": "ok"}}


def test_exclude_none_actually_skips_none_values_when_exclude_true():
    """
    Cover the branch:
        if exclude_none and new_val is None:
            continue
    Build a case where new_found is True and changed is True but new is None,
    and ensure exclude_none=True causes it to be skipped.
    """
    changes = {
        "profile.age": _make_change_entry(new_found=True, new_value=None, old_found=True, old_value=25, changed=True, reason="updated"),
        # also include a normal changed field to ensure it is kept
        "email": _make_change_entry(new_found=True, new_value="new@example.com", old_found=True, old_value="old@example.com", changed=True, reason="updated"),
    }

    out_excluding_none = build_object_from_changes(changes, exclude_none=True, include_unchanged=False)
    # profile.age should be skipped; only email remains
    assert out_excluding_none == {"email": "new@example.com"}

    # when exclude_none=False, the None should be included explicitly
    out_including_none = build_object_from_changes(changes, exclude_none=False, include_unchanged=False)
    assert out_including_none == {"profile": {"age": None}, "email": "new@example.com"}
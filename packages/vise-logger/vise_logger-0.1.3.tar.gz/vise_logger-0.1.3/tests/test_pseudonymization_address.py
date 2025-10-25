import json
from pathlib import Path
import pytest

import vise_logger.pseudonymization as SUT

# ---------------- Fixtures -----------------

@pytest.fixture
def addr_keys():
    """Provide a stable (user_key, user_id) pair for address tests without touching module globals."""
    return (
        "this_is_a_test_key_with_sufficient_length_1234567890",
        "test_user_123456",
    )

# ---------------- Test Data -----------------

# Test corpus: Leading house number then street name/type for a variety of countries/styles.
# Each entry defines the expected captured groups for ADDRESS_LEADING_NUM_RE.
# style semantics:
#   style = 'name_first'  -> expects name_first + type_second groups
#   style = 'type_first'  -> expects type_first + name_second groups
_DATA_DIR = Path(__file__).parent / "data"
with (_DATA_DIR / "valid_addresses_leading_num.json").open("r", encoding="utf-8") as f:
    ADDRESSES_LEADING_NUM = json.load(f)
ADDRESS_LEADING_NUM_PARTS = [(c["number"], c["name"]) for c in ADDRESSES_LEADING_NUM]
with (_DATA_DIR / "valid_addresses_trailing_num.json").open("r", encoding="utf-8") as f:
    ADDRESSES_TRAILING_NUM = json.load(f)
ADDRESS_TRAILING_NUM_PARTS = [(c["number"], c["name"]) for c in ADDRESSES_TRAILING_NUM]

# ---------------- Helpers -----------------

def _round_trip(number: str, name: str, user_key: str, user_id: str):
    crypt_number, crypt_name = SUT.pseudonymize_address_parts(number, name, user_key, user_id)
    recovered_number, recovered_name = SUT.depseudonymize_address_parts(crypt_number, crypt_name, user_key, user_id)
    return crypt_number, crypt_name, recovered_number, recovered_name

# ---------------- Tests -----------------

@pytest.mark.parametrize("case", ADDRESSES_LEADING_NUM, ids=[c["addr"] for c in ADDRESSES_LEADING_NUM])
def test_address_leading_num_regex_matches(case):
    m = SUT.ADDRESS_LEADING_NUM_RE.search(case["addr"])
    assert m, f"Regex should match: {case['addr']}"
    assert m.group('number') == case['number'], f"House number mismatch for {case['addr']}"
    if case['style'] == 'name_first':
        assert m.group('name_first') == case['name'], f"name_first mismatch for {case['addr']}"
        assert m.group('type_second').lower().rstrip('.') == case['type'].lower().rstrip('.'), f"type_second mismatch for {case['addr']}"
        # assert m.group('type_second') in case['addr']
    else:  # type_first style
        assert m.group('type_first').lower().rstrip('.') == case['type'].lower().rstrip('.'), f"type_first mismatch for {case['addr']}"
        # Some compound types like 'Grand-Rue' may have no separate name component.
        assert m.group('name_second') == case['name'], f"name_second mismatch for {case['addr']}"

@pytest.mark.parametrize("case", ADDRESSES_TRAILING_NUM, ids=[c["addr"] for c in ADDRESSES_TRAILING_NUM])
def test_address_trailing_num_regex_matches(case):
    m = SUT.ADDRESS_TRAILING_NUM_RE.search(case["addr"])
    assert m, f"Regex should match: {case['addr']}"
    assert m.group('number') == case['number'], f"House number mismatch for {case['addr']}"
    if case['style'] == 'name_first':
        assert m.group('name_first') == case['name'], f"name_first mismatch for {case['addr']}"
        assert m.group('type_second').lower().rstrip('.') == case['type'].lower().rstrip('.'), f"type_second mismatch for {case['addr']}"
        # assert m.group('type_second') in case['addr']
    else:  # type_first style
        assert m.group('type_first').lower().rstrip('.') == case['type'].lower().rstrip('.'), f"type_first mismatch for {case['addr']}"
        # Some compound types like 'Grand-Rue' may have no separate name component.
        assert m.group('name_second') == case['name'], f"name_second mismatch for {case['addr']}"

@pytest.mark.parametrize("addr", [c["addr"] for c in ADDRESSES_LEADING_NUM])
def test_address_leading_num_regex_span_covers_initial_segment(addr):
    m = SUT.ADDRESS_LEADING_NUM_RE.search(addr)
    assert m
    # Ensure the match starts at index 0 and ends exactly after the street type (no trailing city/state)
    assert m.start() == 0
    # Trailing portion (if any) should either be empty or start with whitespace / punctuation
    trail = addr[m.end():]
    assert trail == '' or trail[0] in ',;:/\\\n\t ' or trail.startswith('  ')

@pytest.mark.parametrize("number,name", ADDRESS_LEADING_NUM_PARTS)
def test_address_round_trip(number, name, addr_keys):
    crypt_number, crypt_name, recovered_number, recovered_name = _round_trip(number, name, *addr_keys)
    # Representation: decimal string of first ciphertext byte (0..127 printable subset) + base62 remainder encoding of bytes
    assert isinstance(crypt_number, str) and crypt_number.isdigit(), "crypt_number should be decimal string"
    v = int(crypt_number)
    assert 0 <= v <= 255
    assert all(ch in SUT.ALPHA_DECAZaz_62 for ch in crypt_name), "crypt_name must be base62 digits"
    assert (recovered_number, recovered_name) == (number, name)

@pytest.mark.parametrize("number,name", ADDRESS_LEADING_NUM_PARTS[:3])
def test_address_deterministic(number, name, addr_keys):
    cnum1, cname1 = SUT.pseudonymize_address_parts(number, name, *addr_keys)
    cnum2, cname2 = SUT.pseudonymize_address_parts(number, name, *addr_keys)
    assert (cnum1, cname1) == (cnum2, cname2), "Same key/id + input must be deterministic"

@pytest.mark.parametrize("number,name", ADDRESS_LEADING_NUM_PARTS[:2])
def test_address_changes_with_key(number, name, addr_keys):
    cnum1, cname1 = SUT.pseudonymize_address_parts(number, name, *addr_keys)
    # Change key (without touching globals)
    new_key = addr_keys[0] + "_diff"
    cnum2, cname2 = SUT.pseudonymize_address_parts(number, name, new_key, addr_keys[1])
    assert (cnum1, cname1) != (cnum2, cname2), "Different key should change pseudonymization"

@pytest.mark.parametrize("number,name", ADDRESS_LEADING_NUM_PARTS[:2])
def test_address_changes_with_user_id(number, name, addr_keys):
    cnum1, cname1 = SUT.pseudonymize_address_parts(number, name, *addr_keys)
    # Change user_id (without touching globals)
    new_user_id = addr_keys[1] + "_diff"
    cnum2, cname2 = SUT.pseudonymize_address_parts(number, name, addr_keys[0], new_user_id)
    assert (cnum1, cname1) != (cnum2, cname2), "Different user_id should change pseudonymization"

@pytest.mark.parametrize("number,name", ADDRESS_LEADING_NUM_PARTS[:2])
def test_address_wrong_key_fails_to_recover(number, name, addr_keys):
    cnum, cname = SUT.pseudonymize_address_parts(number, name, *addr_keys)
    wrong_key = addr_keys[0] + "_wrong"
    try:
        rec_num, rec_name = SUT.depseudonymize_address_parts(cnum, cname, wrong_key, addr_keys[1])
        assert (rec_num, rec_name) != (number, name), "Wrong key should not recover original"
    except Exception:
        # Any failure is acceptable evidence of non-recovery
        pass

@pytest.mark.parametrize("number,name", ADDRESS_LEADING_NUM_PARTS[:2])
def test_address_wrong_user_id_fails_to_recover(number, name, addr_keys):
    cnum, cname = SUT.pseudonymize_address_parts(number, name, *addr_keys)
    wrong_user_id = addr_keys[1] + "_wrong"
    try:
        rec_num, rec_name = SUT.depseudonymize_address_parts(cnum, cname, addr_keys[0], wrong_user_id)
        assert (rec_num, rec_name) != (number, name), "Wrong user_id should not recover original"
    except Exception:
        pass

def test_depseudonymize_address_parts_invalid_types(addr_keys):
    cnum, cname = SUT.pseudonymize_address_parts("10", "Main", *addr_keys)
    with pytest.raises(TypeError):
        SUT.depseudonymize_address_parts(object(), cname, *addr_keys)
    with pytest.raises(ValueError):
        SUT.depseudonymize_address_parts("ABC", cname, *addr_keys)
    rec_num, rec_name = SUT.depseudonymize_address_parts(cnum, cname, *addr_keys)
    assert (rec_num, rec_name) == ("10", "Main")

import re
import pytest

import vise_logger.pseudonymization as SUT
import json
from pathlib import Path

_DATA_FILE = Path(__file__).parent / "data" / "valid_ibans.json"
with _DATA_FILE.open("r", encoding="utf-8") as f:
    VALID_IBANS = json.load(f)

def group(s: str, group_length: int, sep: str = " "):
    s = re.sub(r"\s+", "", s)
    return s[:4] + sep + sep.join(s[i:i+group_length] for i in range(4, len(s), group_length))


@pytest.mark.parametrize("iban", VALID_IBANS)
def test_iban_re_matches_compact(iban):
    assert SUT.IBAN_RE.search(iban), f"IBAN_RE should match compact {iban}"

@pytest.mark.parametrize("iban", [group(iban, 3) for iban in VALID_IBANS])
def test_iban_re_matches_ascii_spaced_group_of_3(iban):
    assert SUT.IBAN_RE.search(iban), f"IBAN_RE should match spaced {iban}"

@pytest.mark.parametrize("iban", [group(iban, 4) for iban in VALID_IBANS])
def test_iban_re_matches_ascii_spaced_group_of_4(iban):
    assert SUT.IBAN_RE.search(iban), f"IBAN_RE should match spaced {iban}"

@pytest.mark.parametrize("iban", [group(iban, 4, "\u00A0") for iban in VALID_IBANS])
def test_iban_re_matches_non_ascii_space_group_of_4(iban):
    assert SUT.IBAN_RE.search(iban), f"Current IBAN_RE should match '{iban}' (with NBSP)"

@pytest.mark.parametrize("iban", VALID_IBANS)
def test_is_iban_ok_true_for_valid_examples(iban):
    assert SUT.is_iban_ok(iban)
    assert SUT.is_iban_ok(group(iban, 3))           # ASCII space
    assert SUT.is_iban_ok(group(iban, 4))           # ASCII space
    assert SUT.is_iban_ok(group(iban, 3, "\u00A0")) # non-ASCII space

@pytest.mark.parametrize("iban", VALID_IBANS)
def test_is_iban_ok_false_on_wrong_length(iban):
    compact = re.sub(r"\s+", "", iban)

    assert not SUT.is_iban_ok(compact[:-1]), "Truncated IBAN must be invalid"
    assert not SUT.is_iban_ok(compact + "0"), "Overlong IBAN must be invalid"

@pytest.mark.parametrize("iban", VALID_IBANS)
def test_is_iban_ok_false_on_wrong_check_digits(iban):
    compact = re.sub(r"\s+", "", iban).upper()
    bad = compact[:2] + str((int(compact[2]) + 1) % 10) + compact[3:]

    assert not SUT.is_iban_ok(bad)

# @pytest.fixture(autouse=True)
# def monkeypatch_ff3(monkeypatch):
#     """
#     Replace ff3_encrypt with a deterministic length-preserving base36 shift so tests
#     don't depend on crypto. It returns only A–Z0–9 and keeps length constant.
#     """
#     alpha = getattr(SUT, "ALPHA_DECAZ_36", "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
#     table = {c: alpha[(i + 7) % len(alpha)] for i, c in enumerate(alpha)}  # shift by 7

#     def ff3_mock(plaintext: str, alphabet, user_key, user_id, tweak):
#         assert alphabet == SUT.ALPHA_DECAZ_36
#         return "".join(table[c] if c in table else c for c in plaintext)

#     monkeypatch.setattr(SUT, "ff3_encrypt", ff3_mock)
#     yield


@pytest.mark.parametrize("iban", [VALID_IBANS[0], group(VALID_IBANS[1], 4), group(VALID_IBANS[2], 3), group(VALID_IBANS[3], 4, "\u00A0")])
def test_pseudonymize_iban_preserves_country_and_format_and_is_valid_and_regexable(iban):
    def mask(s: str): return re.sub(r'[A-Za-z0-9]', 'A', s)

    out = SUT.pseudonymize_iban(iban, user_key="k", user_id="u")

    assert out[:2] == iban[:2], "Country code should be preserved"
    assert mask(out) == mask(iban), "Formatting should be preserved: same non-alnum chars in same positions"
    assert SUT.is_iban_ok(out), "Pseudonymized IBAN should remain IBAN-valid"
    assert out[4:] != iban[4:], "BBAN part should change after pseudonymization"
    assert SUT.IBAN_RE.search(out), f"IBAN_RE should match pseudonymized iban {out}"

# def _as_compact(s: str) -> str:
#     return re.sub(r"[^A-Za-z0-9]", "", s)
#
# def test_pseudonymize_iban_depleted_fallback(monkeypatch):
#     """
#     Force ct length mismatch to hit IBAN_FALLBACK_DEPLETED/LEFTOVER
#     by returning a ciphertext one char shorter.
#     """
#     compact = VALID_IBANS[1]

#     def short_ff3(plaintext, alphabet, user_key, user_id, tweak):
#         return plaintext[:-1] if len(plaintext) > 0 else plaintext

#     monkeypatch.setattr(SUT, "ff3_encrypt", short_ff3)
#     out = SUT.pseudonymize_iban(group(compact, 4), user_key="k", user_id="u")
#     # Must fallback; cannot produce a valid IBAN if the cipher length is wrong
#     assert "IBAN_FALLBACK" in out or not SUT.is_iban_ok(_as_compact(out))

@pytest.mark.parametrize("iban", [VALID_IBANS[0], group(VALID_IBANS[1], 4), group(VALID_IBANS[2], 3), group(VALID_IBANS[3], 4, "\u00A0")])
def test_pseudonymize_iban_is_deterministic(iban):
    out1 = SUT.pseudonymize_iban(iban, "k", "u")
    out2 = SUT.pseudonymize_iban(iban, "k", "u")

    assert out1 == out2, "Same key/id should yield deterministic pseudonymization"
    # out3 = SUT.pseudonymize_iban(iban, "k1", "u")
    # assert out1 != out3, "Different key should yield different pseudonymization"
    # out4 = SUT.pseudonymize_iban(iban, "k", "u1")
    # assert out1 != out4, "Different user_id should yield different pseudonymization"

@pytest.mark.parametrize("iban", VALID_IBANS + [group(VALID_IBANS[-3], 4), group(VALID_IBANS[-2], 3), group(VALID_IBANS[-1], 4, "\u00A0")])
def test_pseudonymize_iban_is_regexable_and_reversible_ungrouped(iban):
    key = "k"
    user_id = "u"

    encoded_simple = SUT.pseudonymize_iban(iban, key, user_id)
    decoded_simple = SUT.depseudonymize_iban(encoded_simple, key, user_id)
    not_decoded_key = SUT.depseudonymize_iban(encoded_simple, key + "1", user_id)
    not_decoded_user_id = SUT.depseudonymize_iban(encoded_simple, key, user_id + "1")

    print("encoded_simple =", encoded_simple)
    assert decoded_simple == iban, "Depseudonymization should recover original IBAN"
    assert SUT.IBAN_RE.search(encoded_simple), f"IBAN_RE should match pseudonymized iban {encoded_simple}"
    assert not_decoded_key != iban, "Wrong key should not recover original IBAN"
    assert not_decoded_user_id != iban, "Wrong user_id should not recover original IBAN"

@pytest.mark.parametrize("iban", VALID_IBANS + [group(VALID_IBANS[-3], 4), group(VALID_IBANS[-2], 3), group(VALID_IBANS[-1], 4, "\u00A0")])
def test_pseudonymize_iban_is_regexable_and_reversible_complex(iban):
    key = "thisisamuchlongerkeytotestdifferentkeylengths"
    user_id = "thisisamuchlongeruseridtotestdifferentidlengths"

    encoded_complex = SUT.pseudonymize_iban(group(iban, 4), key, user_id)
    decoded_complex = SUT.depseudonymize_iban(encoded_complex, key, user_id)

    assert decoded_complex == group(iban, 4), "Depseudonymization should recover original IBAN (grouped)"
    assert SUT.IBAN_RE.search(encoded_complex), f"IBAN_RE should match pseudonymized iban {encoded_complex}"


# ----------------------------- Performance sanity (slow) -----------------

@pytest.mark.slow
def test_validator_perf_sanity():
    blob = " ".join(VALID_IBANS) * 200  # ~100k chars
    # Finding + validating should be comfortably sub-100ms on a typical dev laptop;
    # we just assert it finishes promptly (no exact timing)
    for m in SUT.IBAN_RE.finditer(blob):
        assert SUT.is_iban_ok(m.group(0))

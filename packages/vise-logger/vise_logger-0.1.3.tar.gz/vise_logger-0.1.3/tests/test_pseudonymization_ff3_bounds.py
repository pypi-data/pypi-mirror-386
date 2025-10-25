import pytest
from ff3 import FF3Cipher
import vise_logger.pseudonymization as SUT


def _cipher_for_radix(radix: int) -> FF3Cipher:
    key_hex = ("00" * SUT.FF3_KEY_BYTES).upper()
    tweak_hex = ("00" * SUT.TWEAK_LEN_BYTES).upper()
    if radix == 10:
        return FF3Cipher(key_hex, tweak_hex)
    # Select a matching alphabet
    if radix == 16:
        alphabet = SUT.ALPHA_HEX
    elif radix == 26:
        alphabet = SUT.ALPHA_AZ
    elif radix == 36:
        alphabet = SUT.ALPHA_DECAZ_36
    elif radix == 62:
        alphabet = SUT.ALPHA_DECAZaz_62
    else:
        assert 2 <= radix <= len(SUT.ALPHA_DECAZaz_62), f"unsupported radix {radix} for test"
        alphabet = SUT.ALPHA_DECAZaz_62[:radix]
    return FF3Cipher.withCustomAlphabet(key_hex, tweak_hex, alphabet)


@pytest.mark.parametrize("radix", [2, 3, 5, 10, 16, 26, 36, 62])
def test_min_max_len_for_radix(radix: int):
    cipher = _cipher_for_radix(radix)
    assert SUT.min_len_for_radix(radix) == cipher.minLen
    assert SUT.max_len_for_radix(radix) == cipher.maxLen

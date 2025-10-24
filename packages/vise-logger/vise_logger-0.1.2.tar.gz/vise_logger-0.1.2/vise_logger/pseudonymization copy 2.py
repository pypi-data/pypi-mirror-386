#!/usr/bin/env python3
"""
pseudonymization.py

Detect and pseudonymize PII and secrets inside a long stream of text using:
- FF3-1 Format-Preserving Encryption (FPE), via ff3 package
- Deterministic, reversible filler derived from user_id (via HMAC) for short fields
- No vault; fully reversible with (user_key, user_id)

Usage:
    from pseudonymization import pseudonymize_text
    pseudonymized_text = pseudonymize_text(original_text, user_key="...", user_id="...")

Dependencies:
    pip install ff3 pycryptodome
"""

from __future__ import annotations
from datetime import date, datetime, timedelta
from functools import lru_cache
import os
import re, hmac, hashlib, binascii
import string
from typing import List, Tuple, Callable

from ff3 import FF3Cipher  # mysto/python-fpe
from tld import get_tld
from tld.exceptions import TldDomainNotFound

from vise_logger.localizations import get_iban_length

# =========================
# Constants
# =========================

# Alphabets
ALPHA_DEC = string.digits                                                            # radix 10
ALPHA_HEX = string.digits + "abcdef"                                                 # radix 16
ALPHA_AZ = string.ascii_uppercase                                                    # radix 26
ALPHA_DECAZ_36  = string.digits + string.ascii_uppercase                             # radix 36
ALPHA_DECAZaz_62  = string.digits + string.ascii_uppercase + string.ascii_lowercase  # radix 62

# Days domain of [0, 999_999] (YYYYMMDD from 02620204 to 29991231)
DAYS_DATE_END         = date(2999, 12, 31)
DAYS_DELTA_DOMAIN_LEN = 6
DAYS_DELTA_DOMAIN     = 10**DAYS_DELTA_DOMAIN_LEN
DAYS_DATE_START       = DAYS_DATE_END - timedelta(days=DAYS_DELTA_DOMAIN - 1)   # 0262-02-04

# FF3-1: minimum domain size (radix^len)
MIN_DOMAIN_POWER = 1_000_000

# FF3-1 key length in bytes (AES-256)
FF3_KEY_BYTES = 32

# FF3-1 tweak length
TWEAK_LEN_BYTES = 7

# Reversible padding marker (encodes how many filler chars were added)
MARKERS = string.digits
MAX_MARKER = len(MARKERS) - 1

# =========================
# Key loading
# =========================

def load_encryption_key_from_env() -> str:
    """Load the encryption key from the PSEUDONYMIZATION_ENCRYPTION_KEY environment variable.

    Returns: bytes: The encryption key as a UTF-8 byte string (for use in HMAC operations).
    Raises:
        RuntimeError: If the environment variable is missing.
        ValueError: If the key is less than 32 characters.

    The environment variable PSEUDONYMIZATION_ENCRYPTION_KEY must be set to a string of at least 32 characters
    (high-entropy recommended). Example generators:
        - openssl rand -base64 32
        - python -c "import secrets; print(secrets.token_urlsafe(32))"
    """
    val = os.getenv("PSEUDONYMIZATION_ENCRYPTION_KEY")
    if not val:
        raise RuntimeError(
            "Missing PSEUDONYMIZATION_ENCRYPTION_KEY environment variable. Provision a high-entropy secret via environment or your secret manager."
        )
    user_key = val.strip()
    if len(user_key) < 32:
        raise ValueError(
            "PSEUDONYMIZATION_ENCRYPTION_KEY must be at least 32 characters for adequate entropy."
        )
    return user_key


# =========================
# Key derivation
# =========================

def _hkdf_sha256(ikm: bytes, salt: bytes, info: bytes = b"", length: int = 32) -> bytes:
    """HMAC(Hash-based Message Authentication Code)-based Key Derivation Function (see https://datatracker.ietf.org/doc/html/rfc5869): 
    Derive a per-context subkey from input keying material, using HKDF-SHA256 by default.

    Args:
        ikm: Input keying material (bytes).
        salt: Salt value (a non-secret random value).
        info: Context and application specific information (bytes like b"EMAIL_LOCAL" or b"PHONE").
        length: Length of output keying material in bytes.

    Keying material flow:
    * user_key (string from user, e.g. 32 random bytes)
      ↓ UTF-8 encode
    * IKM = input keying material
      ↓ HKDF-Extract (with salt)
    * PRK = pseudo-random key
      ↓ HKDF-Expand (with context info)
    * OKM = output keying material (AES key for FF3-1)
      ↓ capitalized hex ascii
    * FF3-1 cipher (ff3_encrypt/ff3_decrypt)

    - Use hkdf_sha256() to derive FF3-1 data-encryption keys from a per-user `user_key`.
    - `user_key` is a passphrase (low entropy), first run  externally!
    """
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm, t = b"", b""
    i = 1
    while len(okm) < length:
        t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
        okm += t
        i += 1
    return okm[:length]

def _derive_ff3_key_hex(user_key: str, user_id: str, context: str) -> str:
    subkey = _hkdf_sha256(
        ikm=user_key.encode("utf-8"), 
        salt=hashlib.sha256(user_id.encode("utf-8")).digest(),
        info=context.encode("utf-8"),
        length=FF3_KEY_BYTES,
    )
    return binascii.hexlify(subkey).decode("ascii").upper()

# =========================
# Tweak derivation
# =========================

def _tweak_hex_for(context: str) -> str:
    """Derive a 7-byte (hex) FF3-1 tweak (non-secret for domain separation, i.e. giving a different permutation of the same domain) from the *public* context label.

    - Context-binding (to reduce cross-field linkability) without a server secret: SHA-256(context)[:7].
    - Stable per context; suitable for FF3-1 tweaks.
    """
    digest = hashlib.sha256(context.encode("utf-8")).digest() # hashing for a deterministic and large, uniform pool to slice from
    return binascii.hexlify(digest[:TWEAK_LEN_BYTES]).decode("ascii").upper()


# =========================
# Deterministic reversible filler (from user_id)
# =========================

def _hmac_filler(user_id: str, context: str, original: str, letters: int, alphabet: str) -> str:
    """Return `letters` deterministic filler chars over a specific `alphabet` (e.g., digits, hex, base36, base62).
    
    Args:
        user_id: User identifier (string, non-secret for user separation).
        context: Context label (string, non-secret for context separation).
        original: Original string to pad (string, non-secret, used for uniqueness).
        letters: Number of filler characters to generate.
        alphabet: Alphabet string (e.g. ALPHA_DEC, ...).
    Returns: Filler string of length `letters` over `alphabet` for padding, 
        with HMAC-SHA256 as a PRF (pseudo-random function) and 
        determinism and separation per (user_id, context, original).
    """
    result = []
    counter = 0 # to “stream” arbitrarily many pseudo-random bytes
    underlying_hash_function = hashlib.sha256
    key = user_id.encode("utf-8")
    base = len(alphabet)
    while len(result) < letters:
        mac_raw_32_bytes = hmac.new(key, f"{context}|{original}|{counter}".encode("utf-8"), underlying_hash_function).digest()
        for byte in mac_raw_32_bytes:
            result.append(alphabet[byte % base]) # absolute bias of 0.39 percentage points no problem for filler (is padding, not key)
            if len(result) >= letters: break
        counter += 1
    return "".join(result)

def _pad_with_marker(s: str, user_id: str, context: str, min_len: int, alphabet: str) -> str:
    """Return deterministically, reversibly transformed str that has minimum safe length for FF3-1 and leads with padding length info for padding removal.
    
    Args:
        s: Original string to pad.
        user_id: User identifier (string, non-secret for domain separation).
        context: Context label (string, non-secret for domain separation).
        min_len: Minimum length of the original string (without marker) after padding.
        alphabet: Alphabet string (e.g. ALPHA_DEC, ...).
    Returns: concatenated str `marker + s (+ filler)` so that s is padded to min_len+1, i.e.
        * 1-char marker encodes how many filler chars we added, i.e. marker == MARKERS[len(filler)], and 
        * len(marker+s+filler) == max(len(s)+1, min_len+1).
    Raises: ValueError: If padding length exceeds MAX_MARKER.
    """
    if len(s) >= min_len:
        return MARKERS[0] + s
    pad_len = min_len - len(s)
    if pad_len > MAX_MARKER:
        raise ValueError(f"Padding {pad_len} exceeds supported {MAX_MARKER}. Consider packing instead.")
    filler = _hmac_filler(user_id, context, s, pad_len, alphabet)
    return MARKERS[pad_len] + s + filler

def _unpad_with_marker(s: str) -> str:
    """Remove reversible padding added by pad_with_marker().
    Args:
        s: Padded string with leading marker.
    Returns: Original string with padding (and leading marker) removed.
    Raises:  ValueError: If the padding marker is invalid.
    """
    if not s:
        return s
    marker = s[0]
    k = ord(marker) - ord('0')
    if k < 0 or k > MAX_MARKER:
        raise ValueError("Invalid padding marker")
    body = s[1:]
    return body if k == 0 else body[:-k]

def min_len_for_radix(radix: int) -> int:
    """
    Return minimum int length for FF3-1 domain (radix^length >= MIN_DOMAIN_POWER, i.e. math.ceil(math.log(MIN_DOMAIN_POWER, radix))).
    """
    domain_power, result = 1, 0
    while domain_power < MIN_DOMAIN_POWER:
        domain_power *= radix
        result += 1
    return result


# =========================
# FF3-1 encryption and decryption
# =========================

def ff3_encrypt(s: str, alphabet: str, user_key: str, user_id: str, context: str) -> str:
    """FF3-1 encrypt `s` over `alphabet` using key derived from `user_key`, `user_id`, and tweak from `context`.

    Args:
        s: Input string to encrypt (all chars must be in `alphabet`).
        alphabet: Alphabet string (e.g. ALPHA_DEC, ...).
        user_key: User secret key (string).
        user_id: User identifier (string, non-secret for domain separation).
        context: Context label (string, non-secret for domain separation, can be used for versioning, too ("EMAIL_LOCAL" → "v2|EMAIL_LOCAL")).
    Returns: Encrypted string (same length and alphabet as input, deterministic given (user_key, user_id, context)).
    Raises: ValueError: If the input contains chars outside the specified alphabet.
    """
    alphaset = set(alphabet)
    if any(ch not in alphaset for ch in s):
        raise ValueError("Input contains chars outside alphabet")
    key_hex = _derive_ff3_key_hex(user_key, user_id, context)
    tweak_hex = _tweak_hex_for(context)
    if alphabet == ALPHA_DEC:
        cipher = FF3Cipher(key_hex, tweak_hex)  # default alphabet is digits
    else:
        cipher = FF3Cipher.withCustomAlphabet(key_hex, tweak_hex, alphabet)
    return cipher.encrypt(s)

def ff3_decrypt(ct: str, alphabet: str, user_key: str, user_id: str, context: str) -> str:
    """FF3-1 decrypt `ct` over `alphabet` using key derived from `user_key`, `user_id`, and tweak from `context`.
    Args:
        ct: Ciphertext to decrypt (all chars must be in `alphabet`).
        alphabet: Alphabet string (e.g. ALPHA_DEC, ...).
        user_key: Per-user root secret (random string).
        user_id: Per-user identifier (non-secret string for domain separation).
        context: Context label (non-secret string for domain separation).
    Returns: Plaintext (same length and alphabet as `ct`, deterministic given (user_key, user_id, context)).
    Raises: ValueError: If `ct` has characters outside `alphabet`.
    """
    alphaset = set(alphabet)
    if any(ch not in alphaset for ch in ct):
        raise ValueError("Input contains chars outside alphabet")
    key_hex = _derive_ff3_key_hex(user_key, user_id, context)
    tweak_hex = _tweak_hex_for(context)
    if alphabet == ALPHA_DEC:
        cipher = FF3Cipher(key_hex, tweak_hex)
    else:
        cipher = FF3Cipher.withCustomAlphabet(key_hex, tweak_hex, alphabet)
    return cipher.decrypt(ct)


# =========================
# Helpers to encode arbitrary bytes to arbitrary bases (esp. base62, our largest alphabet)
# =========================

def _to_base62(s: str) -> str:
    return _to_base(s, ALPHA_DECAZaz_62)

def _to_base10(s: str) -> str:
    return _to_base(s, ALPHA_DEC)

def _to_base(s: str, alphabet: str) -> str:
    if not s: 
        return ""
    num = int.from_bytes(s.encode("utf-8"), "big")
    if num == 0: # one ore more NUL characters, i.e. "\u0000" * n
        return alphabet[0]
    
    base = len(alphabet)
    out = []
    while num > 0:
        num, rem = divmod(num, base)
        out.append(alphabet[rem])
    return "".join(reversed(out))

def _from_base62(b62: str) -> str:
    return _from_base(b62, ALPHA_DECAZaz_62)

def _from_base10(b10: str) -> str:
    return _from_base(b10, ALPHA_DEC)

def _from_base(s: str, alphabet: str) -> str:
    if not s: 
        return ""

    base = len(alphabet)
    num = 0
    for ch in s:
        num = num * base + alphabet.index(ch)
    length = max(1, (num.bit_length() + 7) // 8) # round up to full bytes
    return num.to_bytes(length, "big").decode("utf-8", errors="strict") # raise if s is not a alphabet encoding of a valid UTF-8

def date_to_index(date: date) -> int:
    if not (DAYS_DATE_START <= date <= DAYS_DATE_END):
        raise ValueError("date out of supported range [0262-02-04, 2999-12-31]")
    return (date - DAYS_DATE_START).days  # 0..999_999

def index_to_date(i: int) -> date:
    if not (0 <= i < DAYS_DELTA_DOMAIN):
        raise ValueError("index out of range 0..999999")
    return DAYS_DATE_START + timedelta(days=i)

# =========================
# Entity-specific pseudonymizers (text -> text)
# =========================

EMAIL_RE = re.compile(r'(?:^|(?<=\W))'                          # not (ASCII or Unicode) "word" chars
    r'(?P<local>[^@\s]+)@'                                      # allow unicode
    r'(?P<subdomainsld>((?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+)'     # subdomain. and SLD.
    r'(?P<tld>(?:[A-Za-z]{2,63}|[Xx][Nn]--[A-Za-z0-9-]{2,59}))' # TLD
)

USERNAME_AT_RE = re.compile(r'(?<!\w)@(?P<body>[A-Za-z0-9._-]{2,64})(?![A-Za-z0-9._-])') # @username (e.g. GitHub & Twitter)
USERNAME_LABELED_RE = re.compile(r'\b'
    r'(user(name)?|login|handle)\s*[:=]\s*'
    r'(?P<quote>["\'])?'                      # remember quote
    r'(?P<body>[A-Za-z0-9._-]{2,64})'         # actual username
    r'(?(quote)(?P=quote))',                  # match same quote if opened
    re.IGNORECASE
)

MAC_RE = re.compile(r'(?:^|(?<=\W))'     # not (ASCII or Unicode) "word" chars
    r'(?:'
        # bytewise separators : or -:
        r'[0-9A-Fa-f]{2}(?P<sep>[:\-])'  # byte 1 and remember separator
        r'(?:[0-9A-Fa-f]{2}(?P=sep)){4}' # byte 2 to 5 and match same separator
        r'[0-9A-Fa-f]{2}'                # byte 6
        # xxxx.xxxx.xxxx (Cisco):
        r'| (?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}' 
        # xxxxxxxxxxxx (no separators):
        r'| [0-9A-Fa-f]{12}'
    r')\b'
)

UUID_RE = re.compile(r'(?:^|(?<=\W))' # not (ASCII or Unicode) "word" chars
    r'[0-9A-Fa-f]{8}-'                # time_low (8 hex)
    r'[0-9A-Fa-f]{4}-'                # time_mid (4 hex)
    r'[1-8][0-9A-Fa-f]{3}-'           # version nibble (see RFC-9562) + time_high (3 hex)
    r'[89ABab][0-9A-Fa-f]{3}-'        # variant nibble (see RFC-4122) + clk_seq (3 hex)
    r'[0-9A-Fa-f]{12}'                # node (12 hex)
    r'\b'
)

PASSWORD_RE = re.compile(r'\b'
    r'(pass(word)?|pwd)\s*[:=]\s*'
    r'(?P<quote>["\'])?'           # remember quote
    r'(?P<body>[^\s"\']{4,})'      # actual password
    r'(?(quote)(?P=quote))',       # match same quote if opened
    re.IGNORECASE
)

API_KEY_PATTERNS = [
    re.compile(r'\b'                                                           # Azure:
        r'azure[_-]?(?:key|access|api[_-]?key)\s*[:=]\s*'
        r'(?P<quote>["\'])?'                                                     # remember quote
        r'(?P<body>[A-Za-z0-9+/=_-]{20,})'                                       # actual key
        r'(?(quote)(?P=quote))',                                                 # match same quote if opened
        re.IGNORECASE
    ),
    re.compile(r'\b'                                                           # Bearer
        r'Bearer\s+'
        r'(?P<body>[-A-Za-z0-9._~+/]+=*)'
        r'(?![-A-Za-z0-9._~+/=])', 
        re.IGNORECASE
    ),   
    re.compile(r'\b'                                                           # newer GitHub PAT
        r'github_pat_'
        r'(?P<body>[A-Za-z0-9_]{22,})'
        r'(?![A-Za-z0-9_])', 
        re.IGNORECASE
    ),
    re.compile(r'\bgh[opurs]_(?P<body>[A-Za-z0-9]{36})\b'),                    # GitHub PAT
    re.compile(r'\bsk-ant-(?P<body>[A-Za-z0-9]{30,})\b'),                      # Anthropic
    re.compile(r'\bsk-(?P<body>[A-Za-z0-9]{20,})\b'),                          # OpenAI
    re.compile(r'\bsk_(?:live|test)_(?P<body>[A-Za-z0-9]{24,})\b'),            # Stripe
    re.compile(r'\bAIza(?P<body>[A-Za-z0-9_-]{35})(?![A-Za-z0-9_-])'),         # GCP
    re.compile(r'\bxox[abpcrse]-(?P<body>[A-Za-z0-9-]{10,})(?![A-Za-z0-9-])'), # Slack
    re.compile(r'\b(?:AKIA|ASIA)(?P<body>[A-Z0-9]{16})\b'),                    # AWS AKID
    re.compile(r'\b'                                                           # AWS Secret Access Key
        r'aws_secret_access_key\s*[:=]\s*'
        r'(?P<quote>["\'])?'                                                     # remember quote
        r'(?P<body>[A-Za-z0-9/+=]{40})'                                          # actual key
        r'(?(quote)(?P=quote))',                                                 # match same quote if opened
        re.IGNORECASE
    ),
    re.compile(r'\bSK(?P<body>[0-9a-fA-F]{32})\b'),                            # Twilio
    re.compile(r'(?<![\w-])'                                                   # JWT-ish
        r'[A-Za-z0-9_-]{10,}={0,2}\.'
        r'[A-Za-z0-9_-]{4,}={0,2}\.'
        r'[A-Za-z0-9_-]{10,}={0,2}'
        r'(?![A-Za-z0-9_=-])'
    ),
]

ADDRESS_LEADING_NUM_RE = re.compile(r'\b'
    r'(?P<number>'
        r'\d{1,5}[A-Za-z]?'                              # house numbers like 123 or 123-124 or 123a or 123a-c or 123a-123c
        r'(?:\s*[–-—]\s*(?:\d{1,5}[A-Za-z]?|[A-Za-z]))?' # optional range: - 123 or -123c
        r'(?:/\d{1,4})?'                                 # optional slash part: 12/4
    r')\s+(?:'
            # type_first name_second (French-style, e.g. "rue de Rivoli")
            r'(?P<type_first>(?:rue|avenue|av\.?|boulevard|bd\.?|chemin|all(?:ée|ee|e|\.)|impasse|quai|cours))'
            r'\s+(?P<name_second>[\w .-]{2,80})|'
            # name_first type_second (English-style, e.g. "Queen's Rd.")
            r"(?P<name_first>[\w ’'.-]{2,80})\s+"
            r'(?P<type_second>(?:street|st\.?|road|rd\.?|avenue|ave\.?|boulevard|blvd\.?|drive|dr\.?|lane|ln\.?|way|'
            r'place|pl\.?|court|ct\.?|square|sq\.?|terrace|terr\.?|circle|cir\.?|parkway|pkwy\.?|highway|hwy\.?|route|rte\.?))'
    r')(?=$|\W)',
    re.IGNORECASE
)
ADDRESS_TRAILING_NUM_RE = re.compile(r'\b'
    r'(?:'
        # type_first name_second (Spanish-style, e.g. "Calle Mayor 45")
        r'(?P<type_first>(?:calle|carrera|cra\.?|paseo|camino|avenida|av\.?|alameda|al\.?|via|viale|v\.?le|corso|piazza|p\.?za|rua|'
        r'travessa|carrer|strada|str\.?|aleja|al\.?|ulica|ulice|ul\.?))'
        r"\s+(?P<name_second>[\w ’'.-]{2,80})|"
        # name_first type_second (German-style, e.g. "Musterstraße")
        r"(?P<name_first>[\w ’'.-]{2,80})\s+"
        r'(?P<type_second>(?:straße|strasse|str\.?|weg|gasse|platz|pl\.?|allee|ring|damm|ufer|feld|chaussee|steig|hang|'
        r'markt|gatan|gata|vägen|väg|vej|gate|vei|veg|tie|katu|utca|straat|laan|dijk|plein|kade|kai|cesta|náměstí|namesti))'
    r')\s+(?P<number>'
        r'\d{1,5}[A-Za-z]?'                              # house numbers like 123 or 123-124 or 123a or 123a-c or 123a-123c
        r'(?:\s*[–-—]\s*(?:\d{1,5}[A-Za-z]?|[A-Za-z]))?' # optional range: - 123 or -123c
        r'(?:/\d{1,4}){0,3}'                             # optional slash part: up to 3 parts (AT/CZ style, e.g. "3/2/19")
    r')(?=$|\W)',
    re.IGNORECASE
)

PHONE_FAX_RE = re.compile(r'(?<!\w)'                                  
    r'(?:'
      r'\+[1-9](?:[\s.\-()]?\d){7,14}'          # E.164: "+" and 8–15 digits with flexible separators
      r'|0(?:[\s.\-()]?\d){6,13}'               # national with trunk "0": 7–14 digits with flexible separators
      r'|(?:[2-9](?:[\s.\-()]?\d){7,9})'        # national without trunk "0" or "1": 8–10 digits (US/CA 10, ES 9, DK/NO 8)
      r'|(?:(?:3(?:[\s.\-()]*)7|5(?:[\s.\-()]*)8)(?:[\s.\-()]?\d){10})'  # M2M/IoT: DK 37…, NO 58…, exactly 12 digits
    r')'
    r'(?![\s.\-()]*\d)'                         # don't be a prefix of a longer digit sequence (anti-credit-card)
) 

DATE_LEADING_YEAR_RE = re.compile(r'\b'                           # no leap check
    r'(?P<Y>\d{4})'
    r'(?P<nonY>(?:'
        # -MM-DD with one consistent separator
        r'(?P<sep>[. /-])'                                        # remember separator
        r'(?:'
            r'(?:0[13578]|1[02])(?P=sep)(?:0[1-9]|[12]\d|3[01])|' # 31 day months
            r'(?:0[469]|11)(?P=sep)(?:0[1-9]|[12]\d|30)|'         # 30 day months
            r'02(?P=sep)(?:0[1-9]|1\d|2\d))'                      # 29 day months
        # MMDD
        r'|(?:'
            r'(?:0[13578]|1[02])(?:0[1-9]|[12]\d|3[01])|'         # 31 day months
            r'(?:0[469]|11)(?:0[1-9]|[12]\d|30)|'                 # 30 day months
            r'02(?:0[1-9]|1\d|2\d))'                              # 29 day months
    r'))\b'
)
DATE_TRAILING_YEAR_RE = re.compile(r'\b'                                                    # no leap check  
    r'(?P<nonY>(?:'
        # (D)D-(M)M- with one consistent separator
        r'(?:'
            r'(?:0?[1-9]|[12]\d|3[01])(?P<sepDM31>[. /-])(?:0?[13578]|1[02])(?P=sepDM31)|'  # 31-day months
            r'(?:0?[1-9]|[12]\d|30)(?P<sepDM30>[. /-])(?:0?[469]|11)(?P=sepDM30)|'          # 30-day months
            r'(?:0?[1-9]|[12]\d)(?P<sepDM29>[. /-])0?2(?P=sepDM29))'                        # 29-day months
        r'|(?:'
        # (M)M-(D)D- with one consistent separator
            r'(?:0?[13578]|1[02])(?P<sepMD31>[. /-])(?:0?[1-9]|[12]\d|3[01])(?P=sepMD31)|' # 31-day months
            r'(?:0?[469]|11)(?P<sepMD30>[. /-])(?:0?[1-9]|[12]\d|30)(?P=sepMD30)|'         # 30-day months
            r'0?2(?P<sepMD29>[. /-])(?:0?[1-9]|[12]\d)(?P=sepMD29))'                       # 29-day months
        r'|(?:'
        # MMDD
            r'(?:0[13578]|1[02])(?:0[1-9]|[12]\d|3[01])|'                                  # 31-day months
            r'(?:0[469]|11)(?:0[1-9]|[12]\d|30)|'                                          # 30-day months
            r'02(?:0[1-9]|1\d|2\d))'                                                       # 29-day months
        r'|(?:'
        # DDMM
            r'(?:0[1-9]|[12]\d|3[01])(?:0[13578]|1[02])|'                                  # 31-day months
            r'(?:0[1-9]|[12]\d|30)(?:0[469]|11)|'                                          # 30-day months
            r'(?:0[1-9]|1\d|2\d)02)'                                                       # 29-day months
    r'))'
    r'(?P<Y>\d{2}|\d{4})'                                                                  # YY or YYYY
    r'\b'
)

SWIFT_RE = re.compile(r'\b' # SWIFT/BIC
    r'[A-Z]{4}'             # bank
    r'[A-Z]{2}'             # country
    r'[A-Z0-9]{2}'          # location
    r'(?:[A-Z0-9]{3})?'     # optional branch
    r'\b'
)

IBAN_RE = re.compile(r'\b'     # shortest 15 (NO); longest 34 (ISO 13616); formats: https://www.oeffentlichen-dienst.de/images/M_images/iban-eu.gif
    r'[A-Z]{2}'                # country code
    r'\d{2}'                   # check digits
    r'(?P<sep>\s?)'            # remember separator
    r'(?:'
        r'([A-Z0-9]{4}(?(sep)(?P=sep))){2,7}[A-Z0-9]{1,4}|'
        r'([A-Z0-9]{3}(?(sep)(?P=sep))){2,9}[A-Z0-9]{1,3}'
    r')\b',
    re.IGNORECASE
)

CC_GENERIC_RE = re.compile(r'\b(?:\d[ -]*?){13,19}\b')
BANK_CTX_RE = re.compile(r'(?i)\b(account|acct|konto|kontonummer|sort\s*code)\b[^A-Za-z0-9]{0,10}([0-9\- ]{6,})')
INS_CTX_RE  = re.compile(r'(?i)\b(health|insurance|policy|krankenkasse|versicherungsnummer)\b[^A-Za-z0-9]{0,10}([A-Za-z0-9\-]{6,})')

NON_ALPHA_DECAZ_RE = re.compile(r'[^0-9A-Z]')
NON_ALPHA_DECAZaz_RE = re.compile(r'[^0-9A-Za-z]')
NON_ALPHA_HEX_RE = re.compile(r'[^0-9A-Fa-f]')
NON_DEC_RE = re.compile(r'[^0-9]')

def is_luhn_ok(d: str) -> bool:
    s = d[::-1]; tot = 0
    for i, ch in enumerate(s):
        n = ord(ch) - 48
        if i % 2 == 1:
            n *= 2
            if n > 9: n -= 9
        tot += n
    return tot % 10 == 0

def _iban_checksum(country: str, bban: str) -> str:
    # Compute ISO 13616 checksum digits for IBAN from country code and BBAN.
    rotated = (bban + country + "00").upper()
    r = 0
    for ch in rotated:
        if '0' <= ch <= '9':
            r = (r * 10 + (ord(ch) - 48)) % 97
        elif 'A' <= ch <= 'Z':
            v = ord(ch) - 55 # 10..35
            r = (r * 100 + v) % 97
        else:
            raise ValueError("Invalid character in IBAN")
    checksum = 98 - r
    return f"{checksum:02d}"

def is_iban_ok(iban: str) -> bool:
    iban_normalized = NON_ALPHA_DECAZaz_RE.sub('', iban).upper()
    checksum = iban_normalized[2:4]
    if not checksum.isdigit(): # invalid checksum
        return False
    country = iban_normalized[:2]
    expected_length = get_iban_length(country)
    if expected_length is None or len(iban_normalized) != expected_length:
        return False
    try:
        return _iban_checksum(country, iban_normalized[4:]) == checksum
    except ValueError:
        return False

# ---- Entity pseudonymizers (return replacement string) ----

def _base62_padded_ff3_encrypt(s: str, user_key: str, user_id: str, context: str, allow_growth: bool = False) -> str:
    b62 = _to_base62(s)
    min_len = 4 # min_len_for_radix(len(ALPHA_DECAZaz_62))
    if len(b62) < min_len:
        if allow_growth:
            b62 = _pad_with_marker(b62, user_id, f"{context}_PAD", min_len, ALPHA_DECAZaz_62)
        else:
            assert False
    return ff3_encrypt(b62, ALPHA_DECAZaz_62, user_key, user_id, context)

def pseudonymize_email(match: re.Match, user_key: str, user_id: str) -> str:
    local = match.group('local')
    local_ct = _base62_padded_ff3_encrypt(local, user_key, user_id, "EMAIL_LOCAL")
    subdomainsld = match.group('subdomainsld').rstrip(".")
    encrypted_labels = [
        _base62_padded_ff3_encrypt(label, user_key, user_id, "EMAIL_SUBDOMAIN")
        for label in subdomainsld.split('.') if label
    ]
    subdomainsld_ct = ".".join(encrypted_labels)
    before_tld = mirror(f"{local}@subdomainsld", ct, )
    tld = match.group('tld')
    return f"{local_ct}@{subdomainsld_ct}.{tld}"

def pseudonymize_mac(raw: str, user_key: str, user_id: str) -> str:
    hex_compact = NON_ALPHA_HEX_RE.sub('', raw).lower()
    if len(hex_compact) != 12:
        return pseudonymize_secret_block(raw, user_key, user_id, "MAC_FALLBACK", allow_growth=True)

    dev_hex = hex_compact[6:]
    min_len = min_len_for_radix(16)
    if len(dev_hex) < min_len:
        assert False
        # dev_hex = _pad_with_marker(dev_hex, user_id, "MAC_PAD", min_len, ALPHA_HEX)
    ct = ff3_encrypt(dev_hex, ALPHA_HEX, user_key, user_id, "MAC_DEV")
    ct_iter = iter(ct)
    result: List[str] = []
    hex_seen, replaced = 0,0
    for ch in raw:
        if ch in string.hexdigits:
            if hex_seen < 6:
                result.append(ch)
            else:
                try:
                    nxt = next(ct_iter)
                except StopIteration:
                    return pseudonymize_secret_block(raw, user_key, user_id, "MAC_FALLBACK_DEPLETED", allow_growth=True)
                result.append(nxt.upper() if ch.isupper() else nxt.lower())
                replaced += 1
            hex_seen += 1
        else:
            result.append(ch)
    if replaced != len(dev_hex):
        return pseudonymize_secret_block(raw, user_key, user_id, "MAC_FALLBACK_LEN", allow_growth=True)
    return "".join(result)

def pseudonymize_uuid(raw: str, user_key: str, user_id: str) -> str:
    hexs = raw.replace("-", "").lower()
    version = hexs[12]
    variant = hexs[16] 
    remain = hexs[:12] + hexs[13:16] + hexs[17:]
    min_len = min_len_for_radix(16)
    if len(remain) < min_len:
        assert False
        # remain = _pad_with_marker(remain, user_id, "UUID_PAD", min_len, ALPHA_HEX)
    ct = ff3_encrypt(remain, ALPHA_HEX, user_key, user_id, "UUID")
    combined = ct[:12] + version + ct[12:15] + variant + ct[15:]
    return f"{combined[0:8]}-{combined[8:12]}-{combined[12:16]}-{combined[16:20]}-{combined[20:32]}"

def pseudonymize_phone(raw: str, user_key: str, user_id: str) -> str:
    # Encrypt only digits, keep formatting:
    digits = NON_DEC_RE.sub('', raw)
    ct = pseudonymize_digits(digits, user_key, user_id, "PHONE", allow_growth=True)
    ct_iter = iter(ct)
    buf: List[str] = []
    for ch in raw:
        if ch.isdigit():
            try:
                buf.append(next(ct_iter))
            except StopIteration:
                return pseudonymize_secret_block(raw, user_key, user_id, "PHONE_FALLBACK_DEPLETED", allow_growth=True)
        else:
            buf.append(ch)
    buf.extend(ct_iter)
    return "".join(buf)

def _pseudonymize_date_string(date_string: str, date_format: str, raw: str, user_key: str, user_id: str, year_leading: bool) -> str:
    """Pseudonymize date string in given format, fallback to secret block if invalid or out of range.
    Args:
        date_string: Date string to parse.
        date_format: Format string for datetime.strptime, (space is also supported)
        raw: Original raw matched string (for fallback).
        user_key: User secret key.
        user_id: User identifier.
        year_leading: True if year is leading (YYYY-MM-DD), False if trailing (MM-DD-YYYY or DD-MM-YYYY).
    Returns: Pseudonymized date string in same format as input.
    """
    year_position = "LEADING" if year_leading else "TRAILING"
    try:
        date = datetime.strptime(date_string, date_format).date()  # raises ValueError if invalid (e.g., 2019-02-29)
        if not (DAYS_DATE_START <= date <= DAYS_DATE_END):
            raise ValueError("Parsed date out of supported range [0262-02-04, 2999-12-31]")
    except ValueError:
        return pseudonymize_secret_block(raw, user_key, user_id, f"DATE_{year_position}_YEAR_FALLBACK", allow_growth=True)
    index = date_to_index(date)
    index_ct = pseudonymize_digits(f"{index:0{DAYS_DELTA_DOMAIN_LEN}d}", user_key, user_id, f"DATE_{year_position}_YEAR", False)
    return index_to_date(int(index_ct)).strftime(date_format)

def pseudonymize_date_leading_year(m: re.Match, user_key: str, user_id: str) -> str:
    sep = m.group('sep')
    date_format = "%Y%m%d" if sep is None else f"%Y{sep}%m{sep}%d"
    year = m.group('Y')
    non_year = m.group('nonY') # either f"-MM-DD" or "MMDD"
    date_string = f"{year}{non_year}"
    return _pseudonymize_date_string(date_string, date_format, m.group(0), user_key, user_id, year_leading=True)

def pseudonymize_date_trailing_year(m: re.Match, user_key: str, user_id: str) -> str:
    year = m.group('Y') # YY or YYYY
    year_format = "%y" if len(year) == 2 else "%Y" # follows POSIX: 69–99 → 1969–1999, 00–68 → 2000–2068
    non_year = m.group('nonY') # either "(D)D-(M)M-" or "(M)M-(D)D-" or "MMDD" or "DDMM"
    sepMD = m.group('sepMD31') or m.group('sepMD30') or m.group('sepMD29')
    sepDM = m.group('sepDM31') or m.group('sepDM30') or m.group('sepDM29')
    if sepDM:
        # DD<sep>MM<sep>YY(YY)
        date_format = f"%d{sepDM}%m{sepDM}{year_format}"
    elif sepMD:
        # MM<sep>DD<sep>YY(YY)
        date_format = f"%m{sepMD}%d{sepMD}{year_format}"
    else:
        # MMDDYY(YY) or DDMMYY(YY)
        lhs = int(non_year[:2])
        date_format = f"%m%d{year_format}" if 1 <= lhs <= 12 else f"%d%m{year_format}"  # prefer MMDD on ambiguity
    date_string = f"{non_year}{year}"
    return _pseudonymize_date_string(date_string, date_format, m.group(0), user_key, user_id, year_leading=False)

def pseudonymize_swift(swift: str, user_key: str, user_id: str) -> str:
    """
    Pseudonymize a SWIFT/BIC keeping the country as is.

    Args:
        swift: SWIFT/BIC string with bank(4 letters) + country(2 letters) + location(2 alnum) + optional branch(3 alnum)
        user_key: User secret key.
        user_id: User identifier.
    Returns: Pseudonymized SWIFT/BIC string with bank FPE over ALPHA_AZ and loc+branch FPE over ALPHA_DECAZ_36.
    """
    # Defensive; SWIFT_RE guarantees this in normal flow.
    s = swift.upper()
    if len(s) not in (8, 11):
        return pseudonymize_secret_block(s, user_key, user_id, "SWIFT_FALLBACK", allow_growth=True)

    bank    = s[0:4]     # letters only (A–Z)
    country = s[4:6]     # preserve
    loc     = s[6:8]     # alnum
    branch  = s[8:]      # '' or 3 alnum

    bank_ct = ff3_encrypt(bank, ALPHA_AZ,  user_key, user_id, "SWIFT_BANK")
    locbranch_ct = ff3_encrypt(loc + branch, ALPHA_DECAZ_36, user_key, user_id, "SWIFT_LOCBR")
    assert len(locbranch_ct) == len(loc) + len(branch)
    loc_ct    = locbranch_ct[:2]
    branch_ct = locbranch_ct[2:] if branch else ""

    return bank_ct + country + loc_ct + branch_ct

def pseudonymize_iban(s: str, user_key: str, user_id: str) -> str:
    iban_normalized = NON_ALPHA_DECAZaz_RE.sub('', s).upper()
    country = iban_normalized[:2]
    bban = iban_normalized[4:]
    min_len = min_len_for_radix(len(ALPHA_DECAZ_36))
    if len(bban) < min_len:
        assert False
        # print(f"Padding BBAN '{bban}', though IBAN regex should only allow BBANs longer than {min_len}")
        # bban = _pad_with_marker(bban, user_id, "IBAN_PAD", min_len, ALPHA_DECAZ_36)
    ct = ff3_encrypt(bban, ALPHA_DECAZ_36, user_key, user_id, "IBAN")
    # iterate through original string to restore spacing and length:
    ct_iter = iter(ct)
    result_bban_list: List[str] = []
    ignored_chars = 0
    for ch in s:
        if ch in ALPHA_DECAZ_36:
            if ignored_chars < 4: # skip country and checksum (added in default format below)
                ignored_chars += 1
                continue
            try:
                nxt = next(ct_iter)
            except StopIteration:
                print(f"Fallback because BBAN encryption depleted before end of original BBAN, which should never happen")
                return pseudonymize_secret_block(s, user_key, user_id, "IBAN_FALLBACK_DEPLETED", allow_growth=True)
            result_bban_list.append(nxt)
        else:
            result_bban_list.append(ch)
    result_bban = ''.join(result_bban_list)
    result_bban_normalized = NON_ALPHA_DECAZ_RE.sub('', result_bban)
    try:
        new_checksum = _iban_checksum(country, result_bban_normalized)
    except ValueError:
        print("Fallback because checksum on encrypted BBAN failed, which should never happen")
        return pseudonymize_secret_block(s, user_key, user_id, "IBAN_FALLBACK", allow_growth=True)
    return country + new_checksum + result_bban

# TODO: merge with pseudonymize_iban above
def depseudonymize_iban(s: str, user_key: str, user_id: str) -> str:
    iban_normalized = NON_ALPHA_DECAZaz_RE.sub('', s).upper()
    country = iban_normalized[:2]
    bban = iban_normalized[4:]
    min_len = min_len_for_radix(len(ALPHA_DECAZ_36))
    if len(bban) < min_len:
        assert False
        # print(f"Padding BBAN '{bban}', though IBAN regex should only allow BBANs longer than {min_len}")
        # bban = _pad_with_marker(bban, user_id, "IBAN_PAD", min_len, ALPHA_DECAZ_36)
    pt = ff3_decrypt(bban, ALPHA_DECAZ_36, user_key, user_id, "IBAN")
    # iterate through original string to restore spacing and length:
    pt_iter = iter(pt)
    result_bban_list: List[str] = []
    ignored_chars = 0
    for ch in s:
        if ch in ALPHA_DECAZ_36:
            if ignored_chars < 4: # skip country and checksum (added in default format below)
                ignored_chars += 1
                continue
            try:
                nxt = next(pt_iter)
            except StopIteration:
                print("Fallback because BBAN encryption depleted before end of original BBAN, which should never happen")
                return depseudonymize_secret_block(s, user_key, user_id, "IBAN_FALLBACK_DEPLETED", allow_growth=True)
            result_bban_list.append(nxt)
        else:
            result_bban_list.append(ch)
    result_bban = ''.join(result_bban_list)
    result_bban_normalized = NON_ALPHA_DECAZ_RE.sub('', result_bban)
    try:
        new_checksum = _iban_checksum(country, result_bban_normalized)
    except ValueError:
        print("Fallback because checksum on encrypted BBAN failed, which should never happen")
        return depseudonymize_secret_block(s, user_key, user_id, "IBAN_FALLBACK", allow_growth=True)
    return country + new_checksum + result_bban

def pseudonymize_digits(s: str, user_key: str, user_id: str, context: str, allow_growth: bool = False) -> str:
    min_len = min_len_for_radix(10)
    if len(s) < min_len:
        if not allow_growth:
            assert False
        else:
            s = _pad_with_marker(s, user_id, f"{context}_PAD", min_len, ALPHA_DEC)
    return ff3_encrypt(s, ALPHA_DEC, user_key, user_id, context)

def pseudonymize_to_digits(s: str, user_key: str, user_id: str, context: str, allow_growth: bool = False) -> str:
    s = _to_base10(s)
    return pseudonymize_digits(s, user_key, user_id, context, allow_growth=allow_growth)

def pseudonymize_secret_block(s: str, user_key: str, user_id: str, context: str, allow_growth: bool = False) -> str:
    b62 = _to_base62(s)
    min_len = min_len_for_radix(len(ALPHA_DECAZaz_62))
    if len(b62) < min_len:
        if not allow_growth:
            assert False
        else:
            b62 = _pad_with_marker(b62, user_id, f"{context}_PAD", min_len, ALPHA_DECAZaz_62)
    return ff3_encrypt(b62, ALPHA_DECAZaz_62, user_key, user_id, context)

def depseudonymize_secret_block(s: str, user_key: str, user_id: str, context: str) -> str:
    decrypted = ff3_decrypt(s, ALPHA_DECAZaz_62, user_key, user_id, context)
    unpadded = _unpad_with_marker(decrypted) # TODO: but how do I know whether padding happened in pseudonymize_secret_block?
    return _from_base62(unpadded)

# =========================
# Detection scanner
# =========================

# A match item: (start, end, replacer_fn)
MatchItem = Tuple[int, int, Callable[[], str]]

def _add_body(m: re.Match, repls: List[MatchItem], user_key: str, user_id: str, context: str, allow_growth: bool = False):
    body_span = m.span('body')
    def _mk(m=m):
        return pseudonymize_secret_block(m.group('body'), user_key, user_id, context, allow_growth=allow_growth)
    repls.append((body_span[0], body_span[1], _mk))

def _add_address(m: re.Match, repls: List[MatchItem], user_key: str, user_id: str):
    number_span = m.span('number')
    def _number(m=m):
        return pseudonymize_to_digits(m.group('number'), user_key, user_id, "ADDR_NUMBER", allow_growth=True)
    repls.append((number_span[0], number_span[1], _number))
    if "name_first" in m.re.groupindex and m.group("name_first") is not None: # only anonymize name, not type ("Straße", "Avenue", etc)
        name_span = m.span('name_first')
        name = m.group('name_first')
    else:
        assert "name_second" in m.re.groupindex and m.group("name_second") is not None
        name_span = m.span('name_second')
        name = m.group('name_second')
    def _name(name=name):
        return pseudonymize_secret_block(name, user_key, user_id, "ADDR_NAME", allow_growth=True)
    repls.append((name_span[0], name_span[1], _name))

def scan_and_build_replacements(text: str, user_key: str, user_id: str) -> List[MatchItem]:
    repls: List[MatchItem] = []

    # unusual format; strict regex; with validation:

    for m in UUID_RE.finditer(text):
        def _mk(m=m):
            return pseudonymize_uuid(m.group(0), user_key, user_id)
        repls.append((m.start(), m.end(), _mk))

    for m in EMAIL_RE.finditer(text):
        if _is_plausible_domain_cached(m.group("subdomainsld"), m.group("tld")):
            def _mk(m=m):
                return pseudonymize_email(m, user_key, user_id)
            repls.append((m.start(), m.end(), _mk))

    # usual format; unstrict regex; with validation:

    for m in DATE_LEADING_YEAR_RE.finditer(text):
        def _mk(m=m):
            return pseudonymize_date_leading_year(m, user_key, user_id)
        repls.append((m.start(), m.end(), _mk))

    for m in DATE_TRAILING_YEAR_RE.finditer(text):
        def _mk(m=m):
            return pseudonymize_date_trailing_year(m, user_key, user_id)
        repls.append((m.start(), m.end(), _mk))

    for m in IBAN_RE.finditer(text):
        if is_iban_ok(m.group(0)):
            def _mk(m=m):
                return pseudonymize_iban(m.group(0), user_key, user_id)
            repls.append((m.start(), m.end(), _mk))

    # Credit card (with Luhn)
    for m in CC_GENERIC_RE.finditer(text):
        d = NON_DEC_RE.sub('', m.group(0))
        if 13 <= len(d) <= 19 and is_luhn_ok(d):
            enc = pseudonymize_digits(d, user_key, user_id, "CC", allow_growth=True)
            # reapply separators shape
            raw = m.group(0); it = iter(enc); buf = []
            for ch in raw:
                buf.append(next(it) if ch.isdigit() else ch)
            srep = "".join(buf)
            def _mk(srep=srep):
                return srep
            repls.append((m.start(), m.end(), _mk))

    # very unusual format; strict regex; without validation:

    for m in PASSWORD_RE.finditer(text):
        _add_body(m, repls, user_key, user_id, "PWD")

    # very unusual format; unstrict regex; without validation:

    for m in USERNAME_AT_RE.finditer(text):
        def _mk(m=m):
            return "@" + pseudonymize_secret_block(m.group('body'), user_key, user_id, "USERNAME", allow_growth=True)
        repls.append((m.start(), m.end(), _mk))

    # unusual format; unstrict regex; without validation:

    for m in USERNAME_LABELED_RE.finditer(text):
        _add_body(m, repls, user_key, user_id, "USERNAME")

    # usual format; unstrict regex; without validation:

    for m in MAC_RE.finditer(text):
        def _mk(m=m):
            return pseudonymize_mac(m.group(0), user_key, user_id)
        repls.append((m.start(), m.end(), _mk))

    for rx in API_KEY_PATTERNS:
        for m in rx.finditer(text):
            if "body" in m.re.groupindex and m.group("body") is not None:
                _add_body(m, repls, user_key, user_id, "APIKEY")
            else:
                def _mk(m=m):
                    return pseudonymize_secret_block(m.group(0), user_key, user_id, "APIKEY", allow_growth=True) # TODO: too liberal for GitHub PAT, GCP, AWS, Twilio
                repls.append((m.start(), m.end(), _mk))

    for m in ADDRESS_LEADING_NUM_RE.finditer(text):
        _add_address(m, repls, user_key, user_id)

    for m in ADDRESS_TRAILING_NUM_RE.finditer(text):
        _add_address(m, repls, user_key, user_id)

    # very usual format; very unstrict regex; without validation:

    for m in PHONE_FAX_RE.finditer(text):
        def _mk(m=m):
            return pseudonymize_phone(m.group(0), user_key, user_id)
        repls.append((m.start(), m.end(), _mk))

    for m in SWIFT_RE.finditer(text):
        def _mk(m=m):
            return pseudonymize_swift(m.group(0), user_key, user_id)
        repls.append((m.start(), m.end(), _mk))

    # Bank account (context)
    for m in BANK_CTX_RE.finditer(text):
        body_span = m.span(2); val = m.group(2)
        d = NON_DEC_RE.sub('', val)
        if len(d) >= 6:
            enc = pseudonymize_digits(d, user_key, user_id, "BANK_ACCT", allow_growth=True)
            # keep separators
            it = iter(enc); buf = []
            for ch in val:
                buf.append(next(it) if ch.isdigit() else ch)
            rep = "".join(buf)
            def _mk(rep=rep):
                return rep
            repls.append((body_span[0], body_span[1], _mk))

    # Insurance number (context)
    for m in INS_CTX_RE.finditer(text):
        # TODO: use function above!?
        body_span = m.span(2); val = m.group(2)
        rep = pseudonymize_secret_block(val, user_key, user_id, "INSURANCE")
        def _mk(rep=rep):
            return rep
        repls.append((body_span[0], body_span[1], _mk))

@lru_cache(maxsize=8192)
def _is_plausible_domain_cached(subdomainsld: str, tld: str) -> bool:
    return _is_plausible_domain(subdomainsld, tld)

def _is_plausible_domain(subdomainsld: str, tld: str) -> bool:
    if not _is_plausible_tld_cached(tld):
        return False
    try:
        ascii_domain = f"{subdomainsld}.{tld}".encode("idna").decode("ascii") # to punycode
    except UnicodeError:
        return False
    if len(ascii_domain) > 253: # 255-byte DNS length contraints translates to 253 usable characters
        return False
    if ascii_domain.startswith("-") or ascii_domain.endswith("-"):
        return False
    if ascii_domain.startswith(".") or ascii_domain.endswith(".") or ".." in ascii_domain:
        return False
    return True

@lru_cache(maxsize=2048)
def _is_plausible_tld_cached(tld: str) -> bool:
    return _is_plausible_tld(tld)

def _is_plausible_tld(tld: str) -> bool:
    try:
        _ = get_tld(tld, fix_protocol=True)
        return True
    except TldDomainNotFound:
        return False


# =========================
# Main API
# =========================

def pseudonymize_text(text: str, user_key: str, user_id: str) -> str:
    """Detect entities in `text` and replace them with FF3-1 pseudonymized equivalents, returning pseudonymized text (reversible given user_key/user_id).

    - Replacements are in-place; indices handled by right-to-left application.
    - Reversible with the same (user_key, user_id) and inverse ops.
    """
    user_id = user_id.strip()
    user_key = user_key.strip()
    # Input validation (fail fast with clear errors)
    if not len(user_key) >= 32:
        raise ValueError("user_key must have length >= 32 for AES-256")
    if not len(user_id) >= 6:
        raise ValueError("user_id must have length >= 6 for per-user discrimination")

    repls = scan_and_build_replacements(text, user_key, user_id)

    # Resolve overlaps: prefer longer spans, then earlier entity types we consider "more specific".
    # Simple approach: sort by (start asc, end desc), then keep non-overlapping.
    repls.sort(key=lambda x: (x[0], -x[1]))
    filtered: List[MatchItem] = []
    last_end = -1
    for start, end, fn in repls:
        if start >= last_end:  # no overlap with previous kept
            filtered.append((start, end, fn))
            last_end = end
        else:
            # Overlap: keep the one with farther end (already sorted that way), skip this one
            print(f"Skipping '{text[start:end]}' due to overlap with '{filtered[-1]}'")

    # Apply replacements from right to left to keep indices valid
    out = list(text)
    for start, end, fn in sorted(filtered, key=lambda x: x[0], reverse=True):
        rep = fn()
        out[start:end] = list(rep)
    return "".join(out)


# =========================
# Demo
# =========================

if __name__ == "__main__":
    sample = """
    Contact: silver@gmail.com, or @alice. Alt: user=dev_ops-01
    MAC: aa:bb:cc:dd:ee:ff UUID: 123e4567-e89b-12d3-a456-426614174000
    Phone +49 151 234 5678, Fax: +1 (415) 555-1212
    DOB: 1987-11-03 and 19871103
    Credit Card: 4111 1111 1111 1111
    IBAN: DE89370400440532013000, SWIFT: DEUTDEFF
    Address: 1600 Pennsylvania Avenue NW, Washington, DC
    Password: "s3cr3t!@#"  OpenAI: sk-ABCDEFGHIJKLMNOPQRSTUVWX  GitHub: ghp_ABCDEFGHIJKLMN0123456789abcd
    AWS AKID: AKIAIOSFODNN7EXAMPLE  Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.Nm9kZQ_example
    Bank account: Konto: 123-456-789
    Insurance: Versicherungsnummer AB-12345-XY
    """
    user_key = load_encryption_key_from_env()
    user_id  = "sYQvOOpXgxMQelXYLxdnDwDklYD3"

    print("=== ORIGINAL ===")
    print(sample)
    print("=== PSEUDONYMIZED ===")
    print(pseudonymize_text(sample, user_key, user_id))

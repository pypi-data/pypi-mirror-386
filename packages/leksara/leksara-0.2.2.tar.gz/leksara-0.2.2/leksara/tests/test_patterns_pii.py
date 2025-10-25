import re

import pytest

from leksara.functions.patterns.pii import (
    replace_phone,
    replace_address,
    replace_email,
    replace_id,
)

EMAIL_PLACEHOLDER = "[EMAIL]"
ADDRESS_PLACEHOLDER = "[ADDRESS]"
PHONE_PLACEHOLDER = "[PHONE_NUMBER]"
ID_PLACEHOLDER = "[NIK]"
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    flags=re.IGNORECASE,
)  # email is case insensitive


@pytest.mark.parametrize(
    "text",
    [
        "Kontak: john.doe@example.com",
        "Send to: jane_smith@sub.domain.co.id, thanks.",
        "multiple: a@b.com and c_d@x.org",
    ],
)

def test_replace_email_mode_replace_replaces_all(text):
    out = replace_email(text, mode="replace")
    assert EMAIL_REGEX.search(out) is None, f"Email masih ada di output: {out}"
    assert EMAIL_PLACEHOLDER in out

def test_replace_email_mode_remove_removes_emails():
    text = "Email saya: User@test.com"
    out = replace_email(text, mode="remove")
    assert EMAIL_REGEX.search(out) is None
    assert EMAIL_PLACEHOLDER not in out
    assert out != text

def test_replace_email_type_error_on_non_string():
    with pytest.raises(TypeError):
        replace_email(123)

def test_replace_email_invalid_mode():
    with pytest.raises(ValueError):
        replace_email("a@b.com", mode="invalid_mode")

def test_replace_address_mode_replace_masks_full_address():
    text = "Alamatku di Jl. Merdeka No. 12 RT 02 RW 03, Jakarta"
    out = replace_address(text, mode="replace")
    assert "Jl." not in out and "RT" not in out and "Jakarta" not in out
    assert ADDRESS_PLACEHOLDER in out

def test_replace_address_mode_remove_deletes_address_but_keeps_other_text():
    text = "Alamat kantor: Jl. Merdeka No. 12. Silakan datang."
    out = replace_address(text, mode="remove")
    assert "Jl." not in out
    assert "Silakan datang" in out or "Silakan" in out

def test_replace_address_with_component_kwargs_only_runs_selected_component():
    text = "Rumah saya: Jl. Kenanga 7 RT 03 RW 05, Surabaya"
    out = replace_address(text, mode="replace", rtrw=True)
    assert "[ADDRESS]" in out
    assert "RT" not in out and "RW" not in out

def test_replace_address_unknown_kwarg_raises_keyerror():
    with pytest.raises(KeyError):
        replace_address("Jl. Something 10", foobar=True)

def test_replace_address_type_error_on_non_string():
    with pytest.raises(TypeError):
        replace_address(999)
        
def test_replace_address_returns_original_if_no_trigger():
    text = "This text has no address trigger words."
    out = replace_address(text, mode="replace")
    assert out == text

def test_replace_address_collapses_excess_whitespace_after_removal():
    text = "Alamat: Jl. Kenanga No. 7     RT 05 RW 02    Surabaya"
    out = replace_address(text, mode="remove")
    assert "  " not in out

def test_replace_phone_mode_replace_masks_valid_number():
    text = "Hubungi saya di +6281234567890 untuk info lebih lanjut."
    out = replace_phone(text, mode="replace")
    assert PHONE_PLACEHOLDER in out
    assert "+628" not in out and "812" not in out

def test_replace_phone_mode_remove_deletes_valid_number():
    text = "Nomor saya 081234567890, jangan disebar ya."
    out = replace_phone(text, mode="remove")
    assert "0812" not in out
    assert "jangan disebar" in out


def test_replace_phone_leaves_invalid_short_numbers():
    text = "Kode akses: 12345."
    out = replace_phone(text, mode="replace")
    assert "12345" in out
    assert PHONE_PLACEHOLDER not in out


def test_replace_phone_handles_numbers_with_spaces_and_dashes():
    text = "Nomor alternatif: +62 812-3456-7890"
    out = replace_phone(text, mode="replace")
    assert PHONE_PLACEHOLDER in out
    assert "+" not in out and "812" not in out


def test_replace_phone_normalizes_and_detects_62_prefix():
    text = "Kontak resmi: 6281234567890"
    out = replace_phone(text, mode="replace")
    assert PHONE_PLACEHOLDER in out


def test_replace_phone_normalizes_and_detects_plus62_prefix():
    text = "Nomor darurat: +6282234567890"
    out = replace_phone(text, mode="replace")
    assert PHONE_PLACEHOLDER in out


def test_replace_phone_ignores_non_indonesian_like_numbers():
    text = "Hubungi kantor pusat di +11234567890."
    out = replace_phone(text, mode="replace")
    assert "+1" in out
    assert PHONE_PLACEHOLDER not in out


def test_replace_phone_mode_remove_collapses_whitespace():
    text = "Nomor: 0812 3456 7890   aktif"
    out = replace_phone(text, mode="remove")
    assert "  " not in out
    assert "aktif" in out


def test_replace_phone_with_multiple_numbers_in_text():
    text = "Kontak A: 081234567890, Kontak B: +628987654321"
    out = replace_phone(text, mode="replace")
    assert out.count(PHONE_PLACEHOLDER) == 2
    assert "0812" not in out and "8987" not in out


def test_replace_phone_with_parentheses_variation():
    text = "Nomor kantor (+62) 812-3456-7890 aktif"
    out = replace_phone(text, mode="replace")
    assert PHONE_PLACEHOLDER in out

def test_replace_phone_type_error_on_non_string():
    with pytest.raises(TypeError):
        replace_phone(12345)

def test_replace_phone_invalid_mode_raises_valueerror():
    with pytest.raises(ValueError):
        replace_phone("081234567890", mode="delete")


def test_replace_phone_returns_original_if_no_pattern_found():
    text = "Tidak ada nomor di sini."
    out = replace_phone(text, mode="replace")
    assert out == text

def test_replace_id_mode_replace_masks_nik():
    text = "NIK saya 3276120705010003"
    out = replace_id(text, mode="replace")
    assert ID_PLACEHOLDER in out
    assert "3276" not in out


def test_replace_id_mode_remove_deletes_identifier():
    text = "Data pribadi: 3276120705010003"
    out = replace_id(text, mode="remove")
    assert ID_PLACEHOLDER not in out
    assert "3276" not in out

def test_replace_id_invalid_mode_raises_valueerror():
    with pytest.raises(ValueError):
        replace_id("3276120705010003", mode="mask")


def test_replace_id_type_error_on_non_string():
    with pytest.raises(TypeError):
        replace_id(1234567890123456)  # type: ignore[arg-type]


def test_replace_id_returns_original_for_non_matching_text():
    text = "ID pelanggan: 12345"
    assert replace_id(text) == text
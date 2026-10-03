from backend.app.auth import hash_password, verify_password


def test_password_hash_is_salted_and_verifies():
    first = hash_password("Strong-demo-password-42")
    second = hash_password("Strong-demo-password-42")

    assert first != second
    assert verify_password("Strong-demo-password-42", first)
    assert not verify_password("incorrect", first)


def test_legacy_seed_password_can_be_upgraded_after_sign_in():
    assert verify_password("pass123", "pass123")
    assert not verify_password("incorrect", "pass123")

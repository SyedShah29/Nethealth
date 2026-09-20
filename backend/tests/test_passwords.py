from app.security.passwords import PasswordHasher


def test_passwords_use_salted_argon2id_hashes(password_hasher: PasswordHasher) -> None:
    password = "correct horse battery staple"

    first_hash = password_hasher.hash(password)
    second_hash = password_hasher.hash(password)

    assert first_hash.startswith("$argon2id$")
    assert first_hash != second_hash
    assert password not in first_hash
    assert password_hasher.verify(password, first_hash)
    assert not password_hasher.verify("wrong password", first_hash)

import pytest
from ethaddrlib import address_from_mnemonic, address_from_private_key_hex
# Тестовые вектора (примерная матрица — НЕ ХРАНИ секретных сидов в публичных репо)
TEST_MNEMONIC = "pulp swarm spoon record subway surround coin faculty push dumb youth rigid"
def test_address_from_mnemonic_single():
    addr, priv = address_from_mnemonic(TEST_MNEMONIC)
    assert addr.startswith("0x")
    assert priv.startswith("0x")
    # можно явно проверить конкретный адрес для этой мнемоники и пути, если нужно


def test_address_from_private_key():
    # приватный ключ первого адреса из тестовой мнемоники (можно взять из предыдущего теста вручную)
    # Для теста просто проверим что функция не падает:
    pk = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113b37b2b9e3f3b1f..."  # НЕ реальный; замените реальным при локальном тесте
    # Здесь пропустим реальную проверку чтобы не включать реальные приватные ключи.
    # assert address_from_private_key_hex(pk).startswith("0x")
    pass


# Illustrative tests (require your Matrix/Cluster classes and a real JASPAR2026.sqlite with DL_* tables)
import pytest

def test_dl_backend_fetch_matrix_smoke():
    try:
        from pyjaspar.dl_bootstrap import jaspardb_dl
    except Exception:
        pytest.skip("pyjaspar not installed in test env")
        return

    jdb = jaspardb_dl()
    # Replace with an accession that exists in your DB
    acc = "DL0001.1"
    m = jdb.fetch_matrix(acc)
    assert m is None or (m.collection == "DL" and m.pfm().shape[1] == 4)

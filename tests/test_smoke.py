# tests/test_smoke.py
def test_data_manager_basic():
    from data_manager import DataManager
    dm = DataManager()
    # method existence smoke
    assert hasattr(dm, "get_receipts")
    # get_receipts returns list
    assert isinstance(dm.get_receipts(), list)

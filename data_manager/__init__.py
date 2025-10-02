from pathlib import Path
from .json_adapter import JsonAdapter
from config import DATA_DIR

# Facade: expose DataManager-like API but using JsonAdapter
class DataManager:
    def __init__(self, base_dir: Path = DATA_DIR):
        self.adapter = JsonAdapter(base_dir=base_dir)

    def add_receipt(self, receipt_data):
        return self.adapter.insert_receipt(receipt_data)

    def get_receipts(self):
        return self.adapter.list_receipts()

    def get_receipts_df(self):
        return self.adapter.to_dataframe()

    def delete_receipt(self, receipt_id):
        return self.adapter.delete_receipt(receipt_id)

    def get_statistics(self):
        return self.adapter.get_statistics()

    def backup_data(self):
        return self.adapter.backup_data()

    def clear_all_data(self):
        return self.adapter.clear_all_data()

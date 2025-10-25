
from .dataset_config import DatasetConfig
from .dataset import Dataset
from .rules import Rules
class syntetica:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.syntetica.com/v1"
        self.rules = Rules(api_key, self.base_url)
        self.dataset_config = DatasetConfig(api_key, self.base_url)
        self.dataset = Dataset(api_key, self.base_url)
    


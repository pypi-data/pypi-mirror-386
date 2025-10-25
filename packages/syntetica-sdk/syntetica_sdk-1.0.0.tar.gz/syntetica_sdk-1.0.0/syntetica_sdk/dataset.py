from utils import syntetica_utlis


class Dataset(syntetica_utlis):
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:4000/dev"):
        self.api_key = api_key
        self.base_url = base_url

    def dataset_list(self) -> list:
        """
        Cette fonction permet de récupérer la liste des configurations de jeu de données
        return :
           list: [
           {'datasetConfigId': 'bd02f5388aac45258ebf2d555944f1f3', 'datasetConfigName': 'dataset_name'},
           {'datasetConfigId': '22cc3d6015654878ace384f77d8ec7d6', 'datasetConfigName': 'dataset_name'}
           ]
        """
        url = self.base_url + "/dataset_list"
        res = self._without_body_request(url, {"api_key": self.api_key}, "GET")

        return res

    def dataset_download_link(self, dataset_name_system: str) -> dict:
        """
              Cette fonction permet de récupérer le lien de téléchargement d'une configuration de jeu de données
              dataset_name_system : str
                  Nom du jeu de données données par l'api (format avec un id en plus du nom)
              return :
                 dict: {
                "dataset_name": "NouveauDataset269457de-e78fc.json",
                "url": "https://dataset-generation-endpoint-storage.s3.amazonaws.com/user_id/NouveauDataset269457de-e78fc.json",
                "expire time": "15mn"
                 }
        """
        url = self.base_url + "/dataset_download_link"
        res = self._without_body_request(
            url,
            {"api_key": self.api_key, "dataset_name_system": dataset_name_system},
            "GET",
        )
        return res
    

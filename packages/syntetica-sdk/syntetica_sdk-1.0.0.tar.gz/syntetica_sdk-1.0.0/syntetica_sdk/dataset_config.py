from utils import syntetica_utlis
from exception import YamlToJsonError
import yaml
import json

class DatasetConfig(syntetica_utlis):
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:4000/dev"):
        self.api_key = api_key
        self.base_url = base_url
    def generate_dataset(self, end_format: str,dataset_config_json: dict = None, dataset_config_yaml_path: str = None ) -> dict:
        """
        Cette fonction permet de générer un jeu de données
        end_format : str
            Format de sortie du jeu de données
        dataset_config_json : dict
            dataset config converti en json
            (Contenu du fichier yaml)
        dataset_config_yaml_path : str
            chemin du fichier yaml afin que le sdk puisse le convertir en json
        return :
            dict
                message : str
                    message of the response
                status_code : int
                    HTTP status code of the response
        """
        if dataset_config_yaml_path is not None:
            try :
                # Si dataset_confgig_yaml_path est passé en paramètre, on essaye de le convertir en json
                # et on l'affecte à dataset_config_json
                dataset_config_json = yaml.safe_load(open(dataset_config_yaml_path, "r"))
            except Exception as e:
                raise YamlToJsonError(str(e)+ " Le fichier yaml n'a pas pu être converti en json, veuillez vérifier le chemin ou le fichier")
                
        url = self.base_url + "/generate_dataset"
        res = self._with_body_request(
            url,
            params={"api_key": self.api_key},
            body={
                "end_format": end_format,
                "yaml_content": dataset_config_json,
            },
            method="POST",
            )
        return res



    def generation_status(self, process_id: str) -> dict:
        """
              Cette fonction permet de récupérer l'état de la génération d'un jeu de données
              process_id : str
                 ID du processus de génération fourni par la fonction generate_dataset en cas de succès
              return :
                 dict: "status": {
                "status": "waiting",
                "pourcentage": 0,
                "nb_rows": 1000000,
                "current_rows": 0
                }
        """
        url = self.base_url + "/ping_generation_process"
        res = self._without_body_request(
            url, {"api_key": self.api_key, "process_id": process_id}, "GET"
        )
        return res



    def check_dataset_config_is_valid(self, end_format : str, dataset_config_json: dict = None, dataset_config_yaml_path: str = None) -> dict:
        """
        Cette fonction permet de vérifier si une configuration de jeu de données est valide
        dataset_config_json : dict
           dataset config converti en json
        dataset_config_yaml_path : str
           chemin du fichier yaml afin que le sdk puisse le convertir en json
        return :
            dict
                message : str
                    message of the response
                status_code : int
                    HTTP status code of the response
        """
        
        # Essayer de convertir le yaml en json
        if dataset_config_yaml_path is not None:
            try :
                # Si dataset_confgig_yaml_path est passé en paramètre, on essaye de le convertir en json
                # et on l'affecte à dataset_config_json
                dataset_config_json = yaml.safe_load(open(dataset_config_yaml_path, "r"))
            except Exception as e:
                raise YamlToJsonError(str(e)+ " Le fichier yaml n'a pas pu être converti en json, veuillez vérifier le chemin ou le fichier")
             

        url = self.base_url + "/check_dataset_config_is_valid"
        res = self._with_body_request(
            url,
            params={"api_key": self.api_key},
            body={"yaml_content": dataset_config_json, "end_format": end_format},
            method="POST",
        )
        return res  

#json_d = yaml.safe_load(open("academic.yaml", "r"))

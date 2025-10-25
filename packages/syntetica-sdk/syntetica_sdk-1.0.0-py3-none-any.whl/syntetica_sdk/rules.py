from utils import syntetica_utlis


class Rules(syntetica_utlis):
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:4000/dev"):
        self.api_key = api_key
        # self.base_url = "https://api-dev-microservice-dev.up.railway.app/dev"
        self.base_url = base_url

    def delete_rule_by_id(self, rule_id: str) -> dict:
        """
        rule_id : str
            ID of the rule config to delete
        return :
            dict
                message : str
                    message of the response
                status_code : int
                    HTTP status code of the response
        """
        url = self.base_url + "/delete_rules_config"
        res = self._without_body_request(
            url, {"api_key": self.api_key, "rules_id": rule_id}, "DELETE"
        )
        return res

    def get_rules_by_dataset_config_id(self, dataset_config_id: str) -> list:
        """
        Cette fonction permet de récupérer les règles d'une configuration de jeu de données
        dataset_config_id : str
        return :
           list: [
           {'rulesId': '22cc3d6015654878ace384f77d8ec7d6', 'rulesName': 'rules_name'},
           {'rulesId': 'd6ad95d096ba451cbd43647d19e4a559', 'rulesName': 'rules_name'}
           ]
        """
        url = self.base_url + "/get_all_rules_data"
        res = self._without_body_request(
            url,
            {"api_key": self.api_key, "dataset_config_id": dataset_config_id},
            "GET",
        )
        return res

    def create_rules(self, dataset_config_id: str, rules_content: dict) -> dict:
        """
        Cette fonction permet de créer des règles pour une configuration de jeu de données
        dataset_config_id : str
            ID of the dataset config
        rules : list
            list of rules to create
        return :
            dict
                message : str
                    message of the response
                status_code : int
                    HTTP status code of the response
        """
        url = self.base_url + "/create_rules_config"
        res = self._with_body_request(
            url,
            params={"api_key": self.api_key},
            body={
                "dataset_config_id": dataset_config_id,
                "rules_content": rules_content,
            },
            method="PUT",
        )

        return res



# rules =[
#     {
#       "conditions": {
#         "all": [
#           {
#             "name": "join_2",
#             "operator": "equal_to",
#             "value": "kcls"
#           }
#         ]
#       },
#       "actions": [
#         {
#           "name": "setNull",
#           "params": {
#             "field_name": "all",
#             "value": "null",
#             "random_anomalie_number": 3,
#             "avoid_field": ["payload", "lecteur"]
#           }
#         }
#       ],
#       "occurrences" : 12
#     }
#   ]

import requests as req
from urllib.parse import urlencode
from exception import RequestError
class syntetica_utlis:

   
    def _with_body_request(self, url : str , params : dict, body :dict = {}, method : str = "POST"):
        """
        Methode to make a POST, PUT or UPDATE request to the API
        """
        if params is None:
            raise RequestError("les paramètres ne doivent âs être vide ou égale à {} pour une requete"+ method)
        query_string = urlencode(params)

        url = url + "?" + query_string

        response = None 
        if method == "POST":
            response = req.post(url, json=body)
        elif method == "PUT": # PUT UPDATE 
            response = req.put(url, json=body)
        elif method == "UPDATE": # UPDATE
            response = req.update(url, json=body)
        else:
            raise RequestError("La méthode {} n'est pas supportée".format(method))
        res = response.json()
        if isinstance(res, list): # Gère le cas où la réponse est un []
            return res
        else:
            res.update({"status_code": response.status_code})
        return res
    

    

    def _without_body_request(self, url : str , params : dict, method : str = "GET"):
        """
        Methode to make a DELETE request to the API
        """
        if params is None:
            raise RequestError("les paramètres ne doivent âs être vide ou égale à {} pour une requete"+ method)
        query_string = urlencode(params)
        url = url + "?" + query_string
        response = None 
        if method == "GET":
            response = req.get(url,)
        elif method == "DELETE":
            response = req.delete(url)
        else:
            raise RequestError("La méthode {} n'est pas supportée".format(method))
        res = response.json()
        if isinstance(res, list): # Gère le cas où la réponse est un []
            return res
        else:
            res.update({"status_code": response.status_code})
      
        return res
    

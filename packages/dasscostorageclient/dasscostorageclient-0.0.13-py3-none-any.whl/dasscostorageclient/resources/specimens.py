from ..utils import *
from .models.specimen import SpecimenModel
import json

class Specimens:

    def __init__(self, access_token):
        self.access_token = access_token

    def create_or_update(self, specimenPID: str, body: dict):
        """
        Creates or updates the given specimen in ARS

        Args:
            specimenPID (str): The specimenPID of the specimen to be created/updated
            body (dict): The specimen to be created/updated in the given specimen

        Returns:
            The specimen object that contains the data of the created/updated specimen
        """
        res = send_request(
            RequestMethod.PUT,
            self.access_token,
            f"/v1/specimens/{specimenPID}",
            body)
        
        return {
            'data': SpecimenModel.model_validate(res.json()),
            'status_code': res.status_code
        }
    
    def get_specimen(self, specimenPID):

        """
        Gets the given specimen in ARS

        Args:
            specimenPID (str): The specimenPID of the specimen to be found

        Returns:
            The specimen object that contains the data of the specimen
        """
        res = send_request(
            RequestMethod.GET,
            self.access_token,
            f"/v1/specimens/{specimenPID}"
            )
        
        return {
            'data': SpecimenModel.model_validate(res.json()),
            'status_code': res.status_code
        }

    def delete_specimen(self, specimenPID):

        """
        Deletes the given specimen in ARS

        Args:
            specimenPID (str): The specimenPID of the specimen to be deleted
            

        Returns:
            The response object that contains the status and message of the delete operation
        """
        res = send_request(
            RequestMethod.DELETE,
            self.access_token,
            f"/v1/specimens/{specimenPID}"
            )
        
        return {
            'data': res.text,
            'status_code': res.status_code
        }
    

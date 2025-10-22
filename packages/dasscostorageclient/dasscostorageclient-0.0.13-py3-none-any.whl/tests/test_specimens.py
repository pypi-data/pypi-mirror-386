import os
import sys 
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) 
sys.path.append(project_root) 
import pytest 
from tests.dassco_test_client import client 
import json 

class SpecimenModel: 
   def __init__(self): 
       self.specimen_pid = "test_pid_654" 
       self.specimen = { "institution": "test-institution", "collection": "test-collection", "barcode": "test-barcode-654", "specimen_pid": self.specimen_pid, "preparation_types": ["pinned"], "specimen_id": None, "role_restrictions": [] }
       
@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
     # before
     
     yield 
      
     # after 
      
@pytest.mark.order(1) 
def test_can_create_specimen():

    specimen_model = SpecimenModel()
    specimen_pid = specimen_model.specimen_pid 
    specimen = specimen_model.specimen 
    
    res = client.specimens.create_or_update(specimen_pid, specimen) 
    
    status_code = res.get('status_code') 
    specimen = res.get('data') 
    
    assert status_code == 200 
    assert specimen.specimen_pid == specimen_pid 
    
@pytest.mark.order(2) 
def test_can_get_specimen(): 
    
    specimen_model = SpecimenModel()
    specimen_pid = specimen_model.specimen_pid 
    specimen = specimen_model.specimen 
    
    res = client.specimens.get_specimen(specimen_pid) 
    
    status_code = res.get('status_code') 
    specimen = res.get('data') 
    
    assert status_code == 200 
    assert specimen.specimen_pid == specimen_pid 

@pytest.mark.order(3) 
def test_can_delete_specimen():
    
    specimen_model = SpecimenModel()
    specimen_pid = specimen_model.specimen_pid 
     
    res = client.specimens.delete_specimen(specimen_pid) 
    status_code = res.get('status_code') 
    print(res.get("data"))
    assert status_code == 200
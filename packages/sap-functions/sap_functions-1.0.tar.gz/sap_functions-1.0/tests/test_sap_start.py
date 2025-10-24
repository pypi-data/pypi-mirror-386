import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.sap_functions import SAP

def test_sap_start():
   SAP()
   SAP(1)
      


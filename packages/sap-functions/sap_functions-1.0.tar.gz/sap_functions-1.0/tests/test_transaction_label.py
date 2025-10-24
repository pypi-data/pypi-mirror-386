import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.sap_functions import SAP
import pytest
from dotenv import load_dotenv
import os

load_dotenv()

sap = SAP()

def test_transaction():
   with pytest.raises(Exception):
      sap.select_transaction(os.getenv("not_existant_transaction"))
   sap.select_transaction(os.getenv("transaction_1"))

def test_insert_data_transaction():
   sap.write_text_field(os.getenv("transaction_1_field_1_name"), os.getenv("transaction_1_field_1_value"))

def test_run_transaction():
   sap.run_actual_transaction()

def test_get_label():
   shell = sap.get_shell()
   shell.press_button("Funções ALV standard on")
   shell.press_nested_button("Visões", "Saída list.")
   label = sap.get_label()

   label.get_all_screen_labels()

test_transaction()
test_insert_data_transaction()
test_run_transaction()
test_get_label()
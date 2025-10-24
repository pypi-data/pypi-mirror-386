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


shell = None
def test_get_shell():
   global shell
   shell = sap.get_shell()

def test_shell_layout():
   with pytest.raises(Exception):
      exec(os.getenv("transaction_1_before_shell_layout"))
      shell.select_layout(os.getenv("transaction_1_shell_not_existant_layout"))
   exec(os.getenv("transaction_1_after_shell_layout"))
   exec(os.getenv("transaction_1_before_shell_layout"))
   shell.select_layout(os.getenv("transaction_1_shell_layout"))

def test_shell_get_content():
   content = shell.get_shell_content()
   assert type(content.get("header")).__name__ == "list"
   assert type(content.get("content")).__name__ == "list"

def test_shell_count_rows():
   rows = shell.count_rows()
   assert type(rows).__name__ == "int"

def test_shell_get_cell_value():
   cell_value = shell.get_cell_value(0, os.getenv("transaction_1_shell_column_id"))
   assert type(cell_value).__name__ == "str"

def test_shell_press_button():
   shell.press_button(os.getenv("transaction_1_shell_button"))
   exec(os.getenv("transaction_1_after_press_button"))
   shell.press_nested_button(*os.getenv("transaction_1_shell_nested_button").split(","))
   exec(os.getenv("transaction_1_after_press_button"))

def test_shell_select_actions():
   shell.select_all_content()
   shell.select_column(os.getenv("transaction_1_shell_column_id"))   
   shell.click_cell(0, os.getenv("transaction_1_shell_column_id"))
   
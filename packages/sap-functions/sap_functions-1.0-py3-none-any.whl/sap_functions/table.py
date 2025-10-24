import re


class Table:
    def __init__(self, table, session):
        self.table_obj = table
        self.session = session
        self.window = self.__active_window()

    def __active_window(self) -> int:
        regex = re.compile('[0-9]')
        matches = regex.findall(self.session.ActiveWindow.name)
        for match in matches:
            return int(match)

    def __scroll_through_table(self, extension):
        if 'tbl' in extension:
            try:
                return self.session.findById(extension)
            except:
                pass
        children = self.session.findById(extension).Children
        result = False
        for i in range(len(children)):
            if result:
                break
            if children[i].Type == 'GuiCustomControl':
                result = self.__scroll_through_table(extension + '/cntl' + children[i].name)
            if children[i].Type == 'GuiSimpleContainer':
                result = self.__scroll_through_table(extension + '/sub' + children[i].name)
            if children[i].Type == 'GuiScrollContainer':
                result = self.__scroll_through_table(extension + '/ssub' + children[i].name)
            if children[i].Type == 'GuiTableControl':
                result = self.__scroll_through_table(extension + '/tbl' + children[i].name)
            if children[i].Type == 'GuiTab':
                result = self.__scroll_through_table(extension + '/tabp' + children[i].name)
            if children[i].Type == 'GuiTabStrip':
                result = self.__scroll_through_table(extension + '/tabs' + children[i].name)
            if children[
                i].Type in ("GuiShell GuiSplitterShell GuiContainerShell GuiDockShell GuiMenuBar GuiToolbar "
                            "GuiUserArea GuiTitlebar"):
                result = self.__scroll_through_table(extension + '/' + children[i].name)
        return result

    def get_cell_value(self, row: int, column: int, skip_error: bool = False) -> str:
        """
        Return the content of a SAP Table cell, using the relative visible table row. The desired cell needs to be
        visible for this function be able to work
        :param row: Table relative row index
        :param column: Table column index
        :param skip_error: Skip this function if occur any error
        :return: A String with the desired cell text
        """
        try:
            return self.table_obj.getCell(row, column).text
        except:
            if not skip_error:
                raise Exception("Get cell value failed.")

    def count_visible_rows(self, skip_error: bool = False) -> int:
        """
        Count all the visible rows from a SAP Table
        :param skip_error: Skip this function if occur any error
        :return: An Integer with the number of visible rows in the active SAP Table
        """
        try:
            return self.table_obj.visibleRowCount
        except:
            if not skip_error:
                raise Exception("Get cell value failed.")

    def write_cell_value(self, row: int, column: int, desired_text: str, skip_error: bool = False) -> None:
        """
        Write any value in a SAP Table cell, using the relative visible table row. The desired cell needs to be
        visible for this function be able to work
        :param row: Table relative row index
        :param column: Table column index
        :param desired_text: The text that will overwrite the cell in the SAP Table
        :param skip_error: Skip this function if occur any error
        """
        try:
            self.table_obj.getCell(row, column).text = desired_text
        except:
            if not skip_error:
                raise Exception("Write cell value failed.")

    def select_entire_row(self, absolute_row: int, skip_error: bool = False) -> None:
        """
        Select the entire row from a SAP Table, it uses the absolute table row. The desired cell needs to be
        visible for this function be able to work
        :param absolute_row: Table absolute row index
        :param skip_error: Skip this function if occur any error
        """
        try:
            self.table_obj.GetAbsoluteRow(absolute_row).selected = True
        except:
            if not skip_error:
                raise Exception("Select Entire Row Failed.")

    def unselect_entire_row(self, absolute_row: int, skip_error: bool = False) -> None:
        """
        Unselect the entire row from a SAP Table, it uses the absolute table row. The desired cell needs to be
        visible for this function be able to work
        :param absolute_row: Table absolute row index
        :param skip_error: Skip this function if occur any error
        """
        try:
            self.table_obj.GetAbsoluteRow(absolute_row).selected = False
        except:
            if not skip_error:
                raise Exception("Unselect Entire Row Failed.")

    def flag_cell(self, row: int, column: int, desired_operator: bool, skip_error: bool = False) -> None:
        """
        Flags a checkbox in a SAP Table cell, using the relative visible table row. The desired cell needs to be
        visible for this function be able to work
        :param row: Table relative row index
        :param column: Table column index
        :param skip_error: Skip this function if occur any error
        :param desired_operator: Boolean with the desired operator in the SAP Table cell's checkbox
        """
        try:
            self.table_obj.getCell(row, column).Selected = desired_operator
        except:
            if not skip_error:
                raise Exception("Flag Cell Failed.")

    def click_cell(self, row: int, column: int, skip_error: bool = False) -> None:
        """
        Focus in a cell and double-click in it, using the relative visible table row. The desired cell needs to be
        visible for this function be able to work
        :param row: Table relative row index
        :param column: Table column index
        :param skip_error: Skip this function if occur any error
        """
        try:
            self.table_obj.getCell(row, column).SetFocus()
            self.session.findById(f"wnd[{self.window}]").sendVKey(2)
        except:
            if not skip_error:
                raise Exception("Click Cell Failed.")

    def get_table_content(self, skip_error: bool = False) -> dict:
        """
        Store all the content from a SAP Table, the data will be stored and returned in a dictionary with 'header' and
        'content' items
        :param skip_error: Skip this function if occur any error
        :return: A dictionary with 'header' and 'content' items
        """
        try:
            obj_now = self.__scroll_through_table(f'wnd[{self.window}]/usr')
            added_rows = []

            header = []
            content = []

            columns = obj_now.columns.count
            visible_rows = obj_now.visibleRowCount
            rows = obj_now.rowCount / visible_rows
            absolute_row = 0

            for c in range(columns):
                col_name = obj_now.columns.elementAt(c).title
                header.append(col_name)

            for i in range(int(rows)):
                for visible_row in range(visible_rows):
                    active_row = []
                    for c in range(columns):
                        try:
                            active_row.append(obj_now.getCell(visible_row, c).text)
                        except:
                            active_row.append(None)

                    absolute_row += 1

                    if not all(value is None for value in active_row) and absolute_row not in added_rows:
                        added_rows.append(absolute_row)
                        content.append(active_row)

                self.session.findById(f"wnd[{self.window}]").sendVKey(82)
                obj_now = self.__scroll_through_table(f'wnd[{self.window}]/usr')
            return {'header': header, 'content': content}

        except:
            if not skip_error:
                raise Exception("Get table content failed.")

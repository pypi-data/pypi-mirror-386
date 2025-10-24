import win32com
from typing import Union
import re


class Shell:
    def __init__(self, shell_obj: win32com.client.CDispatch, session: win32com.client.CDispatch):
        self.shell_obj = shell_obj
        self.session = session
        self.window = self.__active_window()
        self.commands_spec = [
            {
                'get_id_method_name': 'GetToolbarButtonId',
                'get_tooltip_method_name': 'GetToolbarButtonTooltip',
                'press_method_name': 'pressToolbarContextButton',
                'press_context_name': 'pressToolbarContextButton',
                'select_context_item_name': 'SelectContextMenuItemByText'
            },
            {
                'get_id_method_name': 'GetButtonId',
                'get_tooltip_method_name': 'GetButtonTooltip',
                'press_method_name': 'pressButton',
                'press_context_name': 'pressContextButton',
                'select_context_item_name': 'SelectContextMenuItemByText'
            }
        ]

    def __active_window(self) -> int:
        regex = re.compile('[0-9]')
        matches = regex.findall(self.session.ActiveWindow.name)
        for match in matches:
            return int(match)
        
    def __scroll_through_shell(self, extension: str) -> Union[bool, win32com.client.CDispatch]:
        if self.session.findById(extension).Type == 'GuiShell':
            try:
                var = self.session.findById(extension).RowCount
                return self.session.findById(extension)
            except:
                pass
        children = self.session.findById(extension).Children
        result = False
        for i in range(len(children)):
            if result:
                break
            if children[i].Type == 'GuiCustomControl':
                result = self.__scroll_through_shell(extension + '/cntl' + children[i].name)
            if children[i].Type == 'GuiSimpleContainer':
                result = self.__scroll_through_shell(extension + '/sub' + children[i].name)
            if children[i].Type == 'GuiScrollContainer':
                result = self.__scroll_through_shell(extension + '/ssub' + children[i].name)
            if children[i].Type == 'GuiTableControl':
                result = self.__scroll_through_shell(extension + '/tbl' + children[i].name)
            if children[i].Type == 'GuiTab':
                result = self.__scroll_through_shell(extension + '/tabp' + children[i].name)
            if children[i].Type == 'GuiTabStrip':
                result = self.__scroll_through_shell(extension + '/tabs' + children[i].name)
            if children[
                i].Type in ("GuiShell GuiSplitterShell GuiContainerShell GuiDockShell GuiMenuBar GuiToolbar "
                            "GuiUserArea GuiTitlebar"):
                result = self.__scroll_through_shell(extension + '/' + children[i].name)
        return result
    
    def select_layout(self, layout: str) -> None:
        """
        This function will select the desired Shell Layout when a SAP select Layout Pop up is open
        :param layout: The desired Layout name
        """
        try:
            window = self.__active_window()
            shell_layout_obj = self.__scroll_through_shell(f'wnd[{window}]/usr')

            if not shell_layout_obj:
                raise Exception()

            shell_layout_obj.selectColumn("VARIANT")
            shell_layout_obj.contextMenu()
            shell_layout_obj.selectContextMenuItem("&FILTER")
            self.session.findById("wnd[2]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/ctxt%%DYN001-LOW").text = layout
            self.session.findById("wnd[2]/tbar[0]/btn[0]").press()
            self.session.findById(
                "wnd[1]/usr/ssubD0500_SUBSCREEN:SAPLSLVC_DIALOG:0501/cntlG51_CONTAINER/shellcont/shell").selectedRows = "0"
            self.session.findById(
                "wnd[1]/usr/ssubD0500_SUBSCREEN:SAPLSLVC_DIALOG:0501/cntlG51_CONTAINER/shellcont/shell").clickCurrentCell()
        except:
            raise Exception("Select layout failed.")

    def count_rows(self) -> int:
        """
        This function will count all the rows in the current Shell
        :return: A integer with the total number of rows in the current Shell
        """
        try:
            rows = self.shell_obj.RowCount
            if rows > 0:
                visible_row = self.shell_obj.VisibleRowCount
                visible_row0 = self.shell_obj.VisibleRowCount
                n_page_down = rows // visible_row0
                if n_page_down > 1:
                    for j in range(1, n_page_down + 1):
                        try:
                            self.shell_obj.firstVisibleRow = visible_row - 1
                            visible_row += visible_row0
                        except:
                            break
                self.shell_obj.firstVisibleRow = 0
            return rows
        except:
            raise Exception("Count rows failed.")

    def get_cell_value(self, index: int, column_id: str) -> str:
        """
        Get the value of a specific Shell cell
        :param index: Row number of the desired cell
        :param column_id: Shell column "Field Name" found in the respective column Technical Information tab
        :return: The value of the cell
        """
        try:
            return self.shell_obj.getCellValue(index, column_id)
        except:
            raise Exception("Get cell value failed.")

    def get_shell_content(self) -> dict:
        """
        Store all the content from a SAP Shell, the data will be stored and returned in a dictionary with 'header' and
        'content' items
        :return: A dictionary with 'header' and 'content' items
        """
        try:
            grid_column = self.shell_obj.ColumnOrder
            rows = self.count_rows()
            cols = self.shell_obj.ColumnCount

            header = [self.shell_obj.getCellValue(i, grid_column(c)) for c in range(cols) for i in range(-1, 0)]
            data = [[self.shell_obj.getCellValue(i, grid_column(c)) for c in range(cols)] for i in range(0, rows)]
            return {'header': header, 'content': data}

        except:
            raise Exception("Get all Shell Content Failed.")

    def select_all_content(self) -> None:
        """
        Select all the table, using the SAP native function to select all items
        """
        try:
            self.shell_obj.selectAll()
        except:
            raise Exception("Select All Content Failed.")

    def select_column(self, column_id: str) -> None:
        """
        Select a specific column
        :param column_id: Shell column "Field Name" found in the respective column Technical Information tab
        """
        try:
            self.shell_obj.selectColumn(column_id)
        except:
            raise Exception("Select Column Failed.")

    def click_cell(self, index: int, column_id: str) -> None:
        """
        This function will select and double-click in a SAP Shell cell
        :param index: Row number of the desired cell
        :param column_id: Shell column "Field Name" found in the respective column Technical Information tab
        """
        try:
            self.shell_obj.SetCurrentCell(index, column_id)
            self.shell_obj.doubleClickCurrentCell()
        except:
            raise Exception("Click Cell Failed.")

    def press_button(self, field_name: str, skip_error: bool = False) -> None:
        """
        This function will press any button in the SAP Shell component
        :param field_name: The button that you want to press, this text need to be inside the button or in the tooltip of the button
        :param skip_error: Skip this function if occur any error
        """
        for command_info in self.commands_spec:
            try:
                get_id_func = getattr(self.shell_obj, command_info['get_id_method_name'])
                get_tooltip_func = getattr(self.shell_obj, command_info['get_tooltip_method_name'])
                press_func = getattr(self.shell_obj, command_info['press_method_name'])

                for i in range(100):
                    button_id = get_id_func(i)
                    button_tooltip = get_tooltip_func(i)
                    if field_name == button_tooltip:
                        press_func(button_id)
                        return
            except:
                pass

        if not skip_error:
            raise Exception("Press button failed")

    def press_nested_button(self, *nested_fields: str, skip_error: bool = False) -> None:
        """
        This function needs to receive several strings that have the texts that appear written in the button destination
        that you want to press, it must be written in the order that it appears to reach the final button
        :param nested_fields: The nested path that you want to navigate to press the button
        :param skip_error: Skip this function if occur any error
        """
        for command_info in self.commands_spec:
            try:
                get_id_func = getattr(self.shell_obj, command_info['get_id_method_name'])
                get_tooltip_func = getattr(self.shell_obj, command_info['get_tooltip_method_name'])
                press_func = getattr(self.shell_obj, command_info['press_context_name'])
                select_func = getattr(self.shell_obj, command_info['select_context_item_name'])

                for i in range(100):
                    button_id = get_id_func(i)
                    button_tooltip = get_tooltip_func(i)
                    if nested_fields[0] == button_tooltip:
                        press_func(button_id)
                        select_func(nested_fields[1])
                        return
            except:
                pass

        if not skip_error:
            raise Exception("Press nested button failed")

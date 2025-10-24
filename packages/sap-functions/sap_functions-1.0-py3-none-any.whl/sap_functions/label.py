import win32com


class Label:
    def __init__(self, session: win32com.client.CDispatch, window: int):
        self.session = session
        self.wnd = window

    def get_all_screen_labels(self) -> list:
        """
        This function will return each label row in the SAP Screen
        :return: A list with lists
        """
        finished_collecting = False
        content = []
        added_rows = []

        while True:
            if finished_collecting:
                break
            for i in range(2, 100):
                active_row = []
                for c in range(0, 35):
                    try:
                        cell = self.session.findById(f"wnd[{self.wnd}]/usr/lbl[{c},{i}]").text.strip()
                        active_row.append(cell)
                    except:
                        pass

                if not all(value is None for value in active_row):
                    row_with_id = list(active_row)
                    row_with_id.append(i)

                    if row_with_id in added_rows:
                        finished_collecting = True
                        break

                    content.append(active_row)
                    added_rows.append(row_with_id)

            self.session.findById(f"wnd[{self.wnd}]").sendVKey(82)
        return content

    def get_label_content(self) -> dict:
        """
        Store all the content from a SAP Label, the data will be stored and returned in a dictionary with
        'header' and 'content' items
        :return: A dictionary with 'header' and 'content' items
        """

        finished_collecting = False
        header = []
        content = []
        columns = []
        added_rows = []

        for header_row_index in range(0, 4):
            for c in range(1, 1000):
                try:
                    cell = self.session.findById(f"wnd[{self.wnd}]/usr/lbl[{c},{header_row_index}]").text.strip()
                    header.append(cell)
                    columns.append(c)
                except:
                    pass

            if len(columns) > 0:
                break

        while True:
            if finished_collecting:
                break
            for i in range(2, 100):
                active_row = []
                for c in columns:
                    try:
                        cell = self.session.findById(f"wnd[{self.wnd}]/usr/lbl[{c},{i}]").text.strip()
                        active_row.append(cell)
                    except:
                        pass

                if not all(value is None for value in active_row):
                    row_with_id = list(active_row)
                    row_with_id.append(i)

                    if row_with_id in added_rows:
                        finished_collecting = True
                        break

                    content.append(active_row)
                    added_rows.append(row_with_id)

            self.session.findById(f"wnd[{self.wnd}]").sendVKey(82)

        return {'header': header, 'content': content}

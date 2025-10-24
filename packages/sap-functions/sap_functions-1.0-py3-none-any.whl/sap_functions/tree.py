import win32com


class Tree:
    def __init__(self, tree_obj: win32com.client.CDispatch):
        self.tree_obj = tree_obj

    def get_tree_content(self, skip_error: bool = False) -> dict:
        """
        Store all the content from a SAP Tree, the data will be stored and returned in a dictionary with 'header' and
        'content' items
        :param skip_error: Skip this function if occur any error
        :return: A dictionary with 'header' and 'content' items
        """
        try:
            header = []
            content = []

            obj_key_values = self.tree_obj.GetAllNodeKeys()
            all_column_names = self.tree_obj.GetColumnNames()
            columns = {}

            for col in all_column_names:
                colName = self.tree_obj.GetColumnTitleFromName(col)
                columns[colName] = col
                header.append(colName)

            for i in range(1, len(obj_key_values)):
                active_row = []
                for col in columns:
                    item = str(self.tree_obj.getItemText(obj_key_values(i), columns[col]))
                    active_row.append(item)

                content.append(active_row)
            return {'header': header, 'content': content}

        except:
            if not skip_error:
                raise Exception("Get tree content failed.")

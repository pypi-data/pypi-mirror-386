
#################################################
# HolAdo (Holistic Automation do)
#
# (C) Copyright 2021-2025 by Eric Klumpp
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# The Software is provided “as is”, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the Software.
#################################################



from builtins import super
from holado_value.common.tables.comparators.table_2_value_table_row_comparator import Table2ValueTable_RowComparator
from holado_ui_selenium.ui.gui.selenium.tables.comparators.selenium_2_value_table_cell_comparator import Selenium2Value_TableCellComparator


class Selenium2Value_TableRowComparator(Table2ValueTable_RowComparator):
    def __init__(self, cell_comparator:Selenium2Value_TableCellComparator):
        super().__init__(cell_comparator)
    
    

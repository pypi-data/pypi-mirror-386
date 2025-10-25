
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
from holado_core.common.tables.table_with_header import TableWithHeader
import logging
from holado_ui_selenium.ui.gui.selenium.drivers.selenium_driver import SeleniumDriver
from holado_ui_selenium.ui.gui.selenium.handlers.selenium_holder import SeleniumHolder
from holado_ui_selenium.ui.gui.selenium.tables.selenium_table_row import SeleniumTableRow

logger = logging.getLogger(__name__)


class SeleniumTableWithHeader(TableWithHeader):
    def __init__(self, selenium_driver:SeleniumDriver, table_element:SeleniumHolder=None):
        super().__init__()
        self.__selenium_driver = selenium_driver
        self.__table_element = table_element
        
    @property
    def driver(self):
        return self.__selenium_driver
    
    def _new_row(self, cells=None, cells_content=None, row_element=None, **kwargs):  # @UnusedVariable
        return SeleniumTableRow(self.driver, row_element, cells=cells, cells_content=cells_content)
    

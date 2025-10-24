
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

import logging
from holado_report.report.builders.report_builder import ReportBuilder
from holado_system.system.filesystem.file import File

logger = logging.getLogger(__name__)



class SummaryScenarioByCategoryReportBuilder(ReportBuilder):
    def __init__(self, filepath, exclude_categories=['Always Success']):
        self.__filepath = filepath
        self.__exclude_categories = exclude_categories
        self.__scenarios_by_category = {}
        self.__categories_order = [
                'Regression',
                'Always Failed',
                'Random',
                'Regression but Not Relevant',
                'Always Not Relevant',
                'Random but Not Relevant',
                'Fixed',
                'Always Success',
                'Unknown'
            ]
        
    def build(self):
        '''
        The file is built after each scenario
        '''
        pass
        
    def after_scenario(self, scenario, scenario_report=None):
        from holado_report.report.report_manager import ReportManager
        category_validation, status_validation, step_failed, step_number = ReportManager.get_current_scenario_status_information(scenario)
        
        if category_validation is not None:
            ind = category_validation.find(' (')
            category = category_validation[:ind] if ind > 0 else category_validation
            
            # Manage excluded categories
            if category in self.__exclude_categories:
                return
            
            # Add scenario information into category
            category_str = f" => {category_validation}" if category_validation else ""
            if step_failed is not None:
                scenario_txt = f"scenario in {scenario.filename} at l.{scenario.line} - step {step_number} (l.{step_failed.line}) - {status_validation}{category_str}"
            else:
                scenario_txt = f"scenario in {scenario.filename} at l.{scenario.line} - step ? (missing step implementation ?) - {status_validation}{category_str}"
            
            if category not in self.__scenarios_by_category:
                self.__scenarios_by_category[category] = []
            self.__scenarios_by_category[category].append(scenario_txt)
            
            # Update categories order with unexpected category
            if category not in self.__categories_order:
                self.__categories_order.append(category)
            
            self.__update_file()
        
    def __update_file(self):
        with File(self.__filepath, mode='wt', auto_flush=False) as fout:
            for category in self.__categories_order:
                if category in self.__scenarios_by_category:
                    fout.writelines([
                        f"## {category}",
                        ""
                        ])
                    fout.writelines(self.__scenarios_by_category[category])
                    fout.writelines([
                        ""
                        ""
                        ])
    

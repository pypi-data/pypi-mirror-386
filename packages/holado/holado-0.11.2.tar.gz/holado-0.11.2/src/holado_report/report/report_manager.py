
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

from holado.common.context.session_context import SessionContext
from holado_core.common.tools.tools import Tools
import logging
# from holado_report.report.builders.json_execution_historic_report_builder import JsonExecutionHistoricReportBuilder
from holado_report.report.builders.detailed_scenario_failed_report_builder import DetailedScenarioFailedReportBuilder
from holado_report.report.builders.summary_report_builder import SummaryReportBuilder
from holado_report.report.builders.summary_scenario_failed_report_builder import SummaryScenarioFailedReportBuilder
from holado_report.report.builders.short_scenario_failed_report_builder import ShortScenarioFailedReportBuilder
from holado_report.report.reports.base_report import BaseReport
from holado_scripting.common.tools.evaluate_parameters import EvaluateParameters
from holado_report.report.builders.summary_scenario_report_builder import SummaryScenarioReportBuilder
from holado_report.report.builders.failure_report_builder import FailureReportBuilder
from holado_report.report.builders.summary_scenario_by_category_report_builder import SummaryScenarioByCategoryReportBuilder
# from holado_core.scenario.scenario_duration_manager import ScenarioDurationManager

logger = logging.getLogger(__name__)




class ReportManager(BaseReport):
    """ Manage reports of current session
    """
    TFeatureReport = None
    TStepTools = None
    
    _scenario_status_information_by_uid = {}
    
    def __init__(self):
        super().__init__()
        
        self.__multitask_manager = None
        
        # Auto configuration
        self.configure()
    
    def configure(self):
        from holado_report.report.reports.feature_report import FeatureReport
        ReportManager.TFeatureReport = FeatureReport
        
        from holado_test.behave.scenario.behave_step_tools import BehaveStepTools
        ReportManager.TStepTools = BehaveStepTools
    
    def initialize(self, multitask_manager):
        self.__multitask_manager = multitask_manager
        
    def initialize_reports(self):
        # self.set_execution_historic()
        
        if self.has_report_path:
            # fn = self.get_path("execution_historic.json")
            # self.add_report_builder(JsonExecutionHistoricReportBuilder(self.execution_historic, fn))
            
            fn = self.get_path("report_summary_scenario_failed.txt")
            self.add_report_builder(SummaryScenarioFailedReportBuilder(fn))
            
            fn = self.get_path("report_summary_scenario_failed_by_category.txt")
            self.add_report_builder(SummaryScenarioByCategoryReportBuilder(fn))
            
            fn = self.get_path("report_summary_scenario_all.txt")
            self.add_report_builder(SummaryScenarioReportBuilder(fn))
            
            fn = self.get_path("report_failures.xml")
            self.add_report_builder(FailureReportBuilder(fn))
            
            fn = self.get_path("report_short_scenario_failed.txt")
            self.add_report_builder(ShortScenarioFailedReportBuilder(fn))
            
            # fn = self.get_path("report_detailed_scenario_failed.txt")
            fn = self.get_path("report_detailed_scenario_failed.xml")
            self.add_report_builder(DetailedScenarioFailedReportBuilder(fn))
            
            fn = self.get_path("report_summary.txt")
            self.add_report_builder(SummaryReportBuilder(fn))
        
    @property
    def __feature_reports(self):
        return self.children_reports("feature")
    
    @property
    def current_feature_report(self):
        # if self.__feature_reports:
        #     return self.__feature_reports[-1][1]
        # else:
        #     return None
        if SessionContext.instance().has_feature_context():
            feature_context = SessionContext.instance().get_feature_context()
            if feature_context.has_object("feature_report"):
                return feature_context.get_object("feature_report")
        return None
    
    @property
    def current_scenario_report(self):
        cfr = self.current_feature_report
        if cfr:
            return cfr.current_scenario_report
        else:
            return None
    
    def new_session(self, report_path):
        self.report_path = report_path
        if self.has_report_path:
            SessionContext.instance().path_manager.makedirs(self.report_path, is_directory=True)
        
        self.initialize_reports()
    
    def before_all(self):
        super().before_all()
    
    def before_feature(self, feature_context, feature):
        # Create new feature report
        fr = ReportManager.TFeatureReport(self, feature_context, feature)
        self.add_child_report(fr, "feature", feature.name, feature.filename)
        fr.initialize_reports()
        
        # Process self reports
        super().before_feature(feature_context, feature, feature_report=fr)
        
        # Store feature report in current feature context
        self.__multitask_manager.get_feature_context().set_object("feature_report", fr)
        
    def before_scenario(self, scenario_context, scenario):
        # Create new scenario report in feature report
        sr = self.current_feature_report.new_scenario_report(scenario_context, scenario)
        
        # Process feature report
        self.current_feature_report.before_scenario(scenario_context, scenario, scenario_report=sr)
        
        # Process self reports
        super().before_scenario(scenario_context, scenario, scenario_report=sr)
        
        # Change active log file to scenario one
        self.__enter_current_scenario_log_file()
    
    def before_step(self, step_context, step, step_level):
        super().before_step(step_context, step, step_level)
        
        # Note: A step can be executed without scenario report (ex: post processes after scenario) 
        if self.current_scenario_report:
            self.current_scenario_report.before_step(step_context, step, step_level)
    
    def after_step(self, step_context, step, step_level):
        super().after_step(step_context, step, step_level)
        
        # Note: A step can be executed without scenario report (ex: post processes after scenario) 
        if self.current_scenario_report:
            self.current_scenario_report.after_step(step_context, step, step_level)
    
    def after_scenario(self, scenario):
        self.current_feature_report.after_scenario(scenario, self.current_scenario_report)
        super().after_scenario(scenario, self.current_scenario_report)
        
        # Change active log file to root one
        self.__leave_current_scenario_log_file()
        
        self.current_scenario_report.release_resources()
    
    def after_feature(self, feature):
        super().after_feature(feature, self.current_feature_report)
        
        self.current_feature_report.release_resources()
    
    def after_all(self):
        super().after_all(build_reports=True)
            
        # Create files using execution historic as input
        # fn_eh = self.get_path("execution_historic.json")
        # sdm = ScenarioDurationManager()
        # sdm.import_execution_historic(fn_eh)
        #
        # fn = self.get_path("scenario_durations.csv")
        # scenario_duration_limits = sdm.compute_scenario_duration_limits()
        # sdm.create_file_scenario_duration_limits(fn, scenario_duration_limits)
        #
        # fn = self.get_path("scenario_duration_tags.csv")
        # duration_limit_tags = [(1, "fast"), (5, "rapid"), (60, "slow")]
        # scenario_duration_tags = sdm.compute_scenario_duration_tags(duration_limit_tags, "long", missing_tag=True, new_tag=True, unchanged_tag=True, with_failed=True)
        # sdm.create_file_scenario_duration_tags(fn, scenario_duration_tags)
        
        # Update campaigns stored in test server
        if self._get_test_server_client().is_available:
            self._get_test_server_client().update_stored_campaigns()
        
    def __enter_current_scenario_log_file(self):
        if SessionContext.instance().log_manager.in_file and self.has_report_path:
            log_filename = self.current_scenario_report.get_path("logs", "report.log")
            SessionContext.instance().path_manager.makedirs(log_filename)
            # Note: do_remove_other_file_handlers is set to True, in case leaving previous scenario log file has failed.
            #       Normally this case shouldn't appear but it was already observed. And when it appeared, execution slowdowned drastically.
            SessionContext.instance().log_manager.enter_log_file(log_filename, do_remove_other_file_handlers=True)
        
    def __leave_current_scenario_log_file(self):
        if SessionContext.instance().log_manager.in_file and self.has_report_path:
            log_filename = self.current_scenario_report.get_path("logs", "report.log")
            SessionContext.instance().log_manager.leave_log_file(log_filename, do_remove_log_file=True)
    
    @classmethod
    def _get_test_server_client(cls):
        return SessionContext.instance().test_server_client
    
    @classmethod
    def _get_scenario_uid(cls, scenario):
        return f"{scenario.filename} at l.{scenario.line}"
    
    @classmethod
    def get_current_scenario_status_information(cls, scenario):
        scenario_uid = cls._get_scenario_uid(scenario)
        if scenario_uid not in cls._scenario_status_information_by_uid:
            step_failed, step_nb = cls.get_step_failed_info(scenario)
            
            # Define scenario status
            if step_failed is not None and hasattr(SessionContext.instance().get_scenario_context(), "is_in_preconditions") and SessionContext.instance().get_scenario_context().is_in_preconditions:
                status = "Failed in Preconditions"
            elif step_failed is not None and step_failed.keyword == "Given":
                status = "Failed in Given"
            elif step_failed is not None or scenario.status.has_failed():
                status = "Failed"
            else:
                status = scenario.status.name.capitalize()
            
            # Define scenario category
            category = None
            if cls._get_test_server_client().is_available:
                # Get scenario execution statuses
                scenario_name = f"{scenario.filename} at l.{scenario.line}"
                sce_hist = cls._get_test_server_client().get_scenario_history(scenario_name=scenario_name, size=29)
                statuses = [s['status'] for s in reversed(sce_hist[0]['statuses'])] if sce_hist else []
                statuses.append(status)
                
                # Get scenario status sequences
                passed_sequences = []
                is_failed_relevant = None
                for status in statuses:
                    if status == 'Passed':
                        passed = True
                    elif status.startswith("Failed"):
                        passed = False
                        if status == "Failed":
                            is_failed_relevant = True
                        elif is_failed_relevant is None:
                            is_failed_relevant = False
                    else:
                        continue
                    
                    if len(passed_sequences) == 0 or passed != passed_sequences[-1][0]:
                        passed_sequences.append([passed, 1])
                    else:
                        passed_sequences[-1][1] += 1
                
                # Compute category
                if passed_sequences:
                    nb_exec = sum([x[1] for x in passed_sequences])
                    last_passed, last_nb_times = passed_sequences[-1]
                    if len(passed_sequences) == 1:
                        if last_passed:
                            category = f'Always Success ({last_nb_times})'
                        elif is_failed_relevant:
                            category = f'Always Failed ({last_nb_times})'
                        else:
                            category = f'Always Not Relevant ({last_nb_times})'
                    elif last_passed and len(passed_sequences) in [2, 3]:
                        category = f'Fixed ({last_nb_times} success / {nb_exec})'
                    elif len(passed_sequences) > 2:
                        nb_fail = sum([x[1] for x in passed_sequences if not x[0]])
                        if is_failed_relevant:
                            category = f'Random ({nb_fail} fails / {nb_exec})'
                        else:
                            category = f'Random but Not Relevant ({nb_fail} fails / {nb_exec})'
                    elif not last_passed:
                        if is_failed_relevant:
                            category = f'Regression ({last_nb_times} fails / {nb_exec})'
                        else:
                            category = f'Regression but Not Relevant ({last_nb_times} fails / {nb_exec})'
                    else:
                        category = f'Unknown (unmanaged sequence: {passed_sequences})'
                
                logger.debug(f"Category of scenario '{scenario}': {category}  (computed from last statuses: {statuses})")
                
            cls._scenario_status_information_by_uid[scenario_uid] = [category, status, step_failed, step_nb]
        
        return cls._scenario_status_information_by_uid[scenario_uid]
        
    @classmethod
    def get_step_failed_info(cls, scenario):
        res_step, res_step_number = None, None
        for ind, step in enumerate(scenario.steps):
            if step.status.has_failed():
                res_step, res_step_number = step, ind+1
                break
        return res_step, res_step_number
    
    @classmethod
    def get_step_description(cls, step):
        res = "{} {}".format(step.keyword, step.name)
        text = cls.TStepTools.get_step_multiline_text(step, eval_params=EvaluateParameters.nothing(), raise_exception_if_none=False, log_level=logging.TRACE)  # @UndefinedVariable
        if text is not None:
            res += "\n\"\"\"\n{}\n\"\"\"".format(text) 
        if step.table:
            res += "\n{}".format(cls.TStepTools.represent_step_table(step.table, 4)) 
        return res
    
    @classmethod
    def get_step_error_message(cls, step):
        if step:
            if step.exception:
                return str(step.exception)
            elif step.error_message:
                return step.error_message
            elif step.status.is_undefined():
                return "Undefined step"
            elif step.status.is_pending():
                return "Step exists but is not implemented"
            elif step.status.has_failed():
                return "Unknown error (unexpected error case)"
        return None
    
    @classmethod
    def get_step_error(cls, step):
        if step:
            if step.exception:
                formatted_exception = Tools.represent_exception(step.exception)
                return "exception:\n{}".format(Tools.indent_string(4, formatted_exception))
            elif step.error_message:
                return "error_message:\n{}".format(Tools.indent_string(4, step.error_message))
            else:
                return cls.get_step_error_message(step)
        return None
    
    

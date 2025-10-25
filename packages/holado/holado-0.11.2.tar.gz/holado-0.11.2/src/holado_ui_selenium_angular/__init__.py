# -*- coding: utf-8 -*-

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

from holado_ui_selenium.ui.gui.selenium.actors.default_selenium_actor import DefaultSeleniumActor
from holado_ui_selenium.ui.gui.selenium.inspectors.default_selenium_inspector import DefaultSeleniumInspector
from holado_ui_selenium_angular.ui.gui.selenium.actors.angular_selenium_actor import AngularSeleniumActor
from holado_ui_selenium_angular.ui.gui.selenium.inspectors.angular_selenium_inspector import AngularSeleniumInspector


DefaultSeleniumActor.register_module("angular", AngularSeleniumActor)
DefaultSeleniumInspector.register_module("angular", AngularSeleniumInspector)



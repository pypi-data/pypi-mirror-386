
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
from holado_core.tools.abstracts.blocking_command_service import BlockingCommandService
from holado_core.common.tools.tools import Tools

logger = logging.getLogger(__name__)

try:
    import sftpserver  # @UnusedImport
    with_sftpserver = True
except Exception as exc:
    if Tools.do_log(logger, logging.DEBUG):
        logger.debug(f"SFTPServer is not available. Initialization failed on error: {exc}")
    with_sftpserver = False


class SFTPServer(BlockingCommandService):
    @classmethod
    def is_available(cls):
        return with_sftpserver
    
    def __init__(self, name, root_path, sftpserver_params):
        super().__init__(name, f"cd \"{root_path}\"; sftpserver {sftpserver_params}")
    
        
        
    
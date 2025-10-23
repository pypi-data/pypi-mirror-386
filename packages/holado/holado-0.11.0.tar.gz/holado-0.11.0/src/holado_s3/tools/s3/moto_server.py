
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
from holado_core.tools.abstracts.service import Service
from holado_core.common.tools.tools import Tools

logger = logging.getLogger(__name__)

try:
    import moto  # @UnusedImport
    from moto.moto_server.threaded_moto_server import ThreadedMotoServer
    with_moto = True
except Exception as exc:
    if Tools.do_log(logger, logging.DEBUG):
        logger.debug(f"MotoServer is not available. Initialization failed on error: {exc}")
    with_moto = False


class MotoServer(Service):
    @classmethod
    def is_available(cls):
        return with_moto
    
    def __init__(self, name=None, ip_address="0.0.0.0", port=5000, verbose=False, auto_stop=True):
        super().__init__(name if name is not None else f"MotoServer({ip_address}:{port})")
        self.auto_stop = auto_stop
        
        self.__internal_server = ThreadedMotoServer(ip_address=ip_address, port=port, verbose=verbose)

    def start(self):
        if Tools.do_log(logger, logging.DEBUG):
            logger.debug(f"Starting service '{self.name}'")
        self.__internal_server.start()

    def stop(self):
        if Tools.do_log(logger, logging.DEBUG):
            logger.debug(f"Stopping service '{self.name}'")
        self.__internal_server.stop()
        
        
    
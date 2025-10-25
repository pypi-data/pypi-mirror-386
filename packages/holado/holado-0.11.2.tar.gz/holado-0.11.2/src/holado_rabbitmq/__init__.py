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


def dependencies():
    return ["holado_protobuf"]

def register():
    from holado.common.context.session_context import SessionContext
    from holado_rabbitmq.tools.rabbitmq.rabbitmq_client import RMQClient
    
    if RMQClient.is_available():
        from holado_rabbitmq.tools.rabbitmq.rabbitmq_manager import RMQManager
        SessionContext.instance().services.register_service_type("rabbitmq_manager", RMQManager,
                            lambda m: m.initialize(SessionContext.instance().protobuf_messages) )



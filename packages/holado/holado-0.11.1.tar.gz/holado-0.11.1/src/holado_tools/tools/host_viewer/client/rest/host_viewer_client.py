
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
from holado_rest.api.rest.rest_client import RestClient
from holado.common.handlers.undefined import undefined_argument, undefined_value
import os
from holado_core.common.tools.converters.converter import Converter
from holado_rest.api.rest.rest_manager import RestManager

logger = logging.getLogger(__name__)


class HostViewerClient(RestClient):
    
    @classmethod
    def new_client(cls, use_localhost=undefined_argument, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = None
        if 'url' not in kwargs:
            if use_localhost is undefined_argument:
                env_use = os.getenv("HOLADO_USE_LOCALHOST", False)
                use_localhost = Converter.is_boolean(env_use) and Converter.to_boolean(env_use)
            
            url = os.getenv("HOLADO_HOST_VIEWER_URL", undefined_value)
            if url is undefined_value:
                scheme = kwargs.get('scheme', undefined_value)
                if scheme is undefined_value:
                    scheme = os.getenv("HOLADO_HOST_VIEWER_SCHEME", "http")
                host = kwargs.get('host', undefined_value)
                if host is undefined_value:
                    host = "localhost" if use_localhost else os.getenv("HOLADO_HOST_VIEWER_HOST", "holado_docker_viewer")
                port = kwargs.get('port', undefined_value)
                if port is undefined_value:
                    if use_localhost:
                        port = os.getenv("HOLADO_HOST_VIEWER_HOSTPORT", 51231)
                    else:
                        port = os.getenv("HOLADO_HOST_VIEWER_PORT", 51231)
                
                if port is None:
                    url = f"{scheme}://{host}"
                else:
                    url = f"{scheme}://{host}:{port}"
            kwargs['url'] = url
        
        manager = RestManager(default_client_class=HostViewerClient)
        res = manager.new_client(**kwargs)
        
        return res

    
    def __init__(self, name, url, headers=None):
        super().__init__(name, url, headers)
    
    
    # Common features
    
    def get_environment_variable_value(self, var_name):
        data = [var_name]
        response = self.get(f"os/env", json=data)
        return self.response_result(response, status_ok=[200])
    
    def get_directory_filenames(self, path, extension='.yml'):
        data = {'path':path, 'extension':extension}
        response = self.get(f"os/ls", json=data)
        return self.response_result(response, status_ok=[200])
    
    
    # Manage containers
    
    def get_containers_status(self, all_=False):
        if all_:
            response = self.get("docker/container?all=true")
        else:
            response = self.get("docker/container")
        return self.response_result(response, status_ok=[200,204])
    
    def get_container_info(self, name, all_=False):
        if all_:
            response = self.get(f"docker/container/{name}?all=true")
        else:
            response = self.get(f"docker/container/{name}")
        return self.response_result(response, status_ok=[200,204])
    
    
    

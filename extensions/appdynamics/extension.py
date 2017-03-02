# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""AppDynamics Extension
Downloads, installs and configures the AppDynamics agent for PHP
"""
import os
import os.path
import logging
from extension_helpers import PHPExtensionHelper
from subprocess import call
import re

_log = logging.getLogger('appdynamics')

class AppDynamicsInstaller(PHPExtensionHelper):

    def __init__(self, ctx):
        PHPExtensionHelper.__init__(self, ctx)
        self._FILTER = "app[-]?dynamics"                 # make static final
        self._appdynamics_credentials = None # JSON which mentions all appdynamics credentials
        self._account_access_key = None      # AppDynamics Controller Account Access Key
        self._account_name = None            # AppDynamics Controller Account Name
        self._host_name = None               # AppDynamics Controller Host Address
        self._port = None                    # AppDynamics Controller Port
        self._ssl_enabled = None             # AppDynamics Controller SSL Enabled
        # Specify the Application details
        self._app_name = None                # AppDynamics App name
        self._tier_name = None               # AppDynamics Tier name
        self._node_name = None               # AppDynamics Node name
        try:
            print("Initializing")
            if ctx['PHP_VM'] == 'php':
                print("method: constructor")
        except Exception:
            _log.warn("Error installing AppDynamics! "
                                "AppDynamics will not be available.")


    #0
    def _defaults(self):
        """Returns a set of default environment variables.

        Create and return a list of default environment variables.  These
        are merged with the build pack context when this the extension
        object is created.

        Return a dictionary.
        """
        return {
                'APPDYNAMICS_HOST': 'packages.appdynamics.com',
                'APPDYNAMICS_VERSION': '4.2.14.0',
                'APPDYNAMICS_PACKAGE': 'appdynamics-php-agent-x64-linux-{APPDYNAMICS_VERSION}.tar.bz2',
                'APPDYNAMICS_DOWNLOAD_URL': 'https://{APPDYNAMICS_HOST}/php/{APPDYNAMICS_VERSION}/{APPDYNAMICS_PACKAGE}'
        }


    #1
    # (Done)
    def _should_compile(self):
        """Determines if the extension should install it's payload.

        This check is called during the `compile` method of the extension.
        It should return true if the payload of this extension should
        be installed (i.e. the `install` method is called).
        """
        print("method: _should_compile")
        VCAP_SERVICES_STRING = str(self._services)
        if bool(re.search(self._FILTER, VCAP_SERVICES_STRING)):
            print("AppDynamics service detected")
            return True
        else:
            return False

    # WIP
    def _configure(self):
        """Configure the extension.

        Called when `should_configure` returns true.  Implement this
        method for your extension.
        """
        print("method: _configure")
        self._load_service_info()
        self._load_service_credentials()


    def _load_service_info(self):
        print("Loading AppDynamics service info.")
        services = self._ctx.get('VCAP_SERVICES', {})
        service_defs = services.get("appdynamics")
        if len(service_defs) == 0:
            print("AppDynamics service not present in VCAP_SERVICES")
            # Search in ups
            print("Searching for appdynamics service in user-provided services")
            user_services = services.get("user-provided")
            for user_service in user_services:
                if bool(re.search(self._FILTER, user_service.get("name"))):
                    print("Using first detected AppDynamics service present in user-provided services")
                    self._appdynamics_credentials = user_service.get("credentials")
                    break
        elif len(service_defs) > 1:
            print("Multiple AppDynamics services found in VCAP_SERVICES, using credentials from first one.")
            self._appdynamics_credentials = service_defs[0].get("credentials")
        elif len(service_defs) == 1:
            print("AppDynamics service found in VCAP_SERVICES")
            self._appdynamics_credentials = service_defs[0].get("credentials")



    def _load_service_credentials(self):
        if (self._appdynamics_credentials != None):
            print("Populating AppDynamics controller binding credentials")
            self._host_name = self._appdynamics_credentials.get("host-name")
            self._port = self._appdynamics_credentials.get("port")
            self._account_name = self._appdynamics_credentials.get("account-name")
            self._account_access_key = self._appdynamics_credentials.get("account-accesss-key")
            self._ssl_enabled = self._appdynamics_credentials.get("ssl-enabled")
        else:
            print("AppDynamics credentials empty")

    # 2
    # Done
    def _compile(self, install):
        """Install the payload of this extension.

        Called when `_should_compile` returns true.  This is responsible
        for installing the payload of the extension.

        The argument is the installer object that is passed into the
        `compile` method.
        """
        print("method: _compile")
        print("Installing AppDynamics")
        install.package('APPDYNAMICS')
        print("Downloaded AppDynamics package")


    #3
    def _service_environment(self):
        """Return dict of environment variables x[var]=val"""
        print("method: _service_environment")
        return {}


    #4 (Done)
    def _service_commands(self):
        """Return dict of commands to run x[name]=cmd"""
        print("method: _service_commands")
        return {
            'httpd': (
            '$HOME/httpd/bin/apachectl',
            '-f "$HOME/httpd/conf/httpd.conf"',
            '-k restart',
            '-DFOREGROUND')
            #'appdynamics_proxy': (
            #    '$HOME/appdynamics-php-agent/proxy/runProxy',
            #    '-d "$HOME/appdynamics-php-agent/proxy"',
            #    ''
            #)
        }

    #5
    def _preprocess_commands(self):
        """Return your list of preprocessing commands"""
        print("method: _preprocess_commands")
        return ()

AppDynamicsInstaller.register(__name__)

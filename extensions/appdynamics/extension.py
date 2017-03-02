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
    _detected = None                         # AppDynamics Service is detected
    _FILTER = "app[-]?dynamics"
    _appdynamics_credentials = None # JSON which mentions all appdynamics credentials
    _account_access_key = None      # AppDynamics Controller Account Access Key
    _account_name = None            # AppDynamics Controller Account Name
    _host_name = None               # AppDynamics Controller Host Address
    _port = None                    # AppDynamics Controller Port
    _ssl_enabled = None             # AppDynamics Controller SSL Enabled
    # Specify the Application details
    _app_name = None                # AppDynamics App name
    _tier_name = None               # AppDynamics Tier name
    _node_name = None               # AppDynamics Node name
    def __init__(self, ctx):
        PHPExtensionHelper.__init__(self, ctx)
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
        if AppDynamicsInstaller._detected is None:
            VCAP_SERVICES_STRING = str(self._services)
            if bool(re.search(AppDynamicsInstaller._FILTER, VCAP_SERVICES_STRING)):
                print("AppDynamics service detected")
                _log.info("AppDynamics service detected")
                AppDynamicsInstaller._detected = True
            else:
                AppDynamicsInstaller._detected = False
        return AppDynamicsInstaller._detected

    # WIP
    def _configure(self):
        """Configure the extension.

        Called when `should_configure` returns true.  Implement this
        method for your extension.
        """
        print("method: _configure")
        self._load_service_info()


    def _load_service_info(self):
        """
        Populate the controller binding credentials and application details for AppDynamics service

        """
        print("Loading AppDynamics service info.")
        services = self._ctx.get('VCAP_SERVICES', {})
        service_defs = services.get("appdynamics")
        if service_defs is None:
            print("AppDynamics service not present in VCAP_SERVICES")
            # Search in user-provided service
            print("Searching for appdynamics service in user-provided services")
            user_services = services.get("user-provided")
            for user_service in user_services:
                if bool(re.search(AppDynamicsInstaller._FILTER, user_service.get("name"))):
                    print("Using the first AppDynamics service present in user-provided services")
                    AppDynamicsInstaller._appdynamics_credentials = user_service.get("credentials")
                    AppDynamicsInstaller._load_service_credentials
                    # load the app details from user-provided service
                    try:
                        print("Populating application details from user-provided service")
                        AppDynamicsInstaller._app_name = AppDynamicsInstaller._appdynamics_credentials.get("application-name")
                        AppDynamicsInstaller._tier_name = AppDynamicsInstaller._appdynamics_credentials.get("tier-name")
                        AppDynamicsInstaller._node_name = AppDynamicsInstaller._appdynamics_credentials.get("node-name")
                    except Exception:
                        print("Error populating app, tier and node names from AppDynamics user-provided service")
                    break
        elif len(service_defs) > 1:
            print("Multiple AppDynamics services found in VCAP_SERVICES, using credentials from first one.")
            AppDynamicsInstaller._appdynamics_credentials = service_defs[0].get("credentials")
            self._load_service_credentials
            self._load_app_details()
        elif len(service_defs) == 1:
            print("AppDynamics service found in VCAP_SERVICES")
            AppDynamicsInstaller._appdynamics_credentials = service_defs[0].get("credentials")
            self._load_service_credentials
            self._load_app_details()



    def _load_service_credentials(self):
        """
        Configure the AppDynamics Controller Binding credentials
        Called when Appdynamics Service is detected

        """
        if (AppDynamicsInstaller._appdynamics_credentials is not None):
            print("Populating AppDynamics controller binding credentials")
            try:
                AppDynamicsInstaller._host_name = AppDynamicsInstaller._appdynamics_credentials.get("host-name")
                AppDynamicsInstaller._port = AppDynamicsInstaller._appdynamics_credentials.get("port")
                AppDynamicsInstaller._account_name = AppDynamicsInstaller._appdynamics_credentials.get("account-name")
                AppDynamicsInstaller._account_access_key = AppDynamicsInstaller._appdynamics_credentials.get("account-accesss-key")
                AppDynamicsInstaller._ssl_enabled = AppDynamicsInstaller._appdynamics_credentials.get("ssl-enabled")
            except Exception:
                print("Error populating AppDynamics controller binding credentials")
        else:
            print("AppDynamics credentials empty")

    def _load_app_details(self):
        """
        Configure the AppDynamics application details
        Called when AppDynamics Service is detected

        """
        print("Populating application details from AppDynamics service")
        try:
            AppDynamicsInstaller._app_name = self._application.get("space_name") + ":" + self._application.get("application_name")
            AppDynamicsInstaller._tier_name = self._application.get("application_name")
            AppDynamicsInstaller._node_name = self._application.get("application_name") + ":" + "node"  # ToDo Change the node name using lazy initialization
        except Exception:
            print("Error populating app, tier and node names from AppDynamics service")


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
        print("Calling install script")

    #3
    def _service_environment(self):
        """Return dict of environment variables x[var]=val"""
        print("method: _service_environment")
        env = {
            'PHP_VERSION': "$(/home/vcap/app/php/bin/php-config --version | cut -d '.' -f 1,2)",
            'PHP_EXT_DIR': "$(/home/vcap/app/php/bin/php-config --extension-dir | sed 's|/tmp/staged|/home/vcap|')",
            'APPD_CONF_CONTROLLER_HOST': AppDynamicsInstaller._host_name,
            'APPD_CONF_CONTROLLER_PORT': AppDynamicsInstaller._port,
            'APPD_CONF_ACCOUNT_NAME': AppDynamicsInstaller._account_name,
            'APPD_CONF_ACCESS_KEY': AppDynamicsInstaller._account_access_key,
            'APPD_CONF_SSL_ENABLED': AppDynamicsInstaller._ssl_enabled,
            'APPD_CONF_APP': AppDynamicsInstaller._app_name,
            'APPD_CONF_TIER': AppDynamicsInstaller._tier_name,
            'APPD_CONF_NODE': AppDynamicsInstaller._node_name
        }
        return env


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
        }

    #5
    def _preprocess_commands(self):
        """Return your list of preprocessing commands"""
        print("method: _preprocess_commands")
        commands = [
            [ 'echo', '" in preprocess;"'],
            [ 'env | grep "APPD_CONF_CONTROLLER_HOST"'],
            ["export", "PHP_VERSION=$(/home/vcap/app/php/bin/php-config --version | cut -d '.' -f 1,2)"],
            ["export", "PHP_EXT_DIR=$(/home/vcap/app/php/bin/php-config --extension-dir | sed 's|/tmp/staged|/home/vcap|')"],
            ["chmod -R 755 /home/vcap/app"],
            [ 'chmod -R 777 /home/vcap/app/appdynamics/appdynamics-php-agent/logs'],
            [ 'export', ' APPD_CONF_TIER=`echo $VCAP_APPLICATION | sed -e \'s/.*application_name.:.//g;s/\".*application_uri.*//g\' `'],
            [ 'if [ -z $application_name ]; then export APPD_CONF_APP=$APPD_CONF_TIER; else export APPD_CONF_APP=$application_name; fi'],
            [ 'export', ' APPD_CONF_NODE=$APPD_CONF_TIER:$CF_INSTANCE_INDEX'],
            [ 'export', ' APPD_CONF_ACCOUNT_NAME=$APPD_CONF_ACCOUNT_NAME'],
            [ 'export', ' APPD_CONF_ACCESS_KEY=`echo $VCAP_SERVICES | sed -e \'s/.*account-access-key.:.//g;s/\".*host-name.*//g\' `'],
            [ 'export', ' APPD_CONF_CONTROLLER_HOST=`echo  HELLO $VCAP_SERVICES | sed -e \'s/.*host-name.:.//g;s/\".*ssl-enabled.*//g\' `'],
            [ 'export', ' APPD_CONF_CONTROLLER_PORT=`echo $VCAP_SERVICES | sed -e \'s/.*port.:.//g;s/\".*account-access-key.*//g\' `'],
            [ 'export', ' APPD_CONF_SSL_ENABLED=`echo $VCAP_SERVICES | sed -e \'s/.*ssl-enabled.:.//g;s/\".*.*//g\'`'],
            [ 'if [ $sslenabled == \"true\" ] ; then export sslflag=-s ; fi; '],
            [ 'echo sslflag set to $sslflag' ],
            [ 'env | grep "APPD_CONF_CONTROLLER_HOST"'],
            [ '/home/vcap/app/appdynamics/appdynamics-php-agent/install.sh '
              '$sslflag '
              '-a "$APPD_CONF_ACCOUNT_NAME@$APPD_CONF_ACCESS_KEY" '
              '-e "$PHP_EXT_DIR" '
              '-p "/home/vcap/app/php/bin" '
              '-i "/home/vcap/app/appdynamics/phpini" '
              '-v "$PHP_VERSION" '
              '--ignore-permissions '
              '"$APPD_CONF_CONTROLLER_HOST" '
              '"$APPD_CONF_CONTROLLER_PORT" '
              '"$APPD_CONF_APP" '
              '"$APPD_CONF_TIER" '
              '"$APPD_CONF_NODE" '],
            [ 'cat', '/home/vcap/app/appdynamics/phpini/appdynamics_agent.ini >> /home/vcap/app/php/etc/php.ini'],
            [ 'cat', '/home/vcap/app/appdynamics/phpini/appdynamics_agent.ini'],
            [ 'echo', '"done preprocess"'],
            [ 'echo', 'env']
        ]
        return commands

AppDynamicsInstaller.register(__name__)

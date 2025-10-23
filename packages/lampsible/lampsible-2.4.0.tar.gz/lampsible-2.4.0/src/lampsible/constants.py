import os
from . import __version__
from .helpers import find_package_project_dir

# Lampsible
# ---------
LAMPSIBLE_BANNER = """\


     |                                   _)  |      |       
     |      _` |  __ `__ \\   __ \\    __|  |  __ \\   |   _ \\ 
     |     (   |  |   |   |  |   | \\__ \\  |  |   |  |   __/ 
    _____|\\__._| _|  _|  _|  .__/  ____/ _| _.__/  _| \\___| 
                            _|                              
    =======================================================

          --------------------------------------------
             LAMP stacks with Ansible  -  v{}
          --------------------------------------------

""".format(__version__)
SUPPORTED_ACTIONS = [
    # LAMP-Stack basics
    'lamp-stack',
    'apache',
    'mysql',
    'php',
    # PHP CMS
    'wordpress',
    'joomla',
    'drupal',
    # PHP frameworks
    'laravel',
    # Other applications
    'suitecrm',
    # Local debugging
    'dump-ansible-facts',
]

# Script paths
# ------------
USER_HOME_DIR            = os.path.expanduser('~')
PROJECT_DIR              = find_package_project_dir()
GALAXY_REQUIREMENTS_FILE = os.path.join(PROJECT_DIR,
    'ansible-galaxy-requirements.yml')
DEFAULT_PRIVATE_DATA_DIR = os.path.join(USER_HOME_DIR, '.lampsible')

# Apache
# ------
DEFAULT_APACHE_VHOST_NAME = '000-default'
DEFAULT_APACHE_SERVER_NAME = 'localhost'
DEFAULT_APACHE_SERVER_ADMIN = 'webmaster@localhost'
DEFAULT_APACHE_DOCUMENT_ROOT = '/var/www/html'

# Database
# --------
DEFAULT_DATABASE_ENGINE       = 'mysql'
DEFAULT_DATABASE_USERNAME     = 'db-username'
DEFAULT_DATABASE_HOST         = 'localhost'
DEFAULT_DATABASE_TABLE_PREFIX = ''

# PHP
# ---
DEFAULT_PHP_VERSION = None
SUPPORTED_PHP_VERSIONS = [
    '8.4', '8.3', '8.2', '8.1', '8.0',
    '7.4', '7.3', '7.2', '7.1', '7.0',
    '5.6', '5.5', '5.4',
]
REQUIRED_PHP_EXTENSIONS = {
    'lamp-stack': ['mysql'],
    'wordpress': [
        'mysql',
        'gd',
    ],
    'joomla': [
        'simplexml',
        'dom',
        'zip',
        'gd',
        'mysql',
    ],
    'drupal': [
        'mysql',
        'xml',
        'gd',
        'curl',
        'mbstring',
    ],
    'laravel': [
        'mysql',
        'xml',
        'mbstring',
    ],
    'suitecrm': [
        'curl',
        'intl',
        'json',
        'gd',
        'mbstring',
        'mysql',
        'soap',
        'xml',
        'zip',
        'imap',
        'ldap',
    ],
}
DEFAULT_PHP_MEMORY_LIMIT        = '256M'
DEFAULT_PHP_UPLOAD_MAX_FILESIZE = '64M'
DEFAULT_PHP_POST_MAX_SIZE       = '32M'
DEFAULT_PHP_MAX_EXECUTION_TIME  = '60'
DEFAULT_PHP_MAX_INPUT_TIME      = '60'
DEFAULT_PHP_MAX_FILE_UPLOADS    = '20'
DEFAULT_PHP_ALLOW_URL_FOPEN     = True
DEFAULT_PHP_ERROR_REPORTING     = 'E_ALL & ~E_DEPRECATED & ~E_STRICT'
DEFAULT_PHP_DISPLAY_ERRORS      = False

# All CMS
# -------
DEFAULT_SITE_TITLE     = 'Sample Site'
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_EMAIL    = 'admin@example.com'

# WordPress
# ---------
DEFAULT_WORDPRESS_VERSION = 'latest'
DEFAULT_WORDPRESS_LOCALE  = 'en_US'
RECENT_WORDPRESS_VERSIONS = [
    'latest',
    'nightly',
    '6.8.3', '6.8.2', '6.8.1', '6.8',
    '6.7.4', '6.7.3', '6.7.2', '6.7.1', '6.7',
    '6.6.4', '6.6.3', '6.6.2', '6.6.1', '6.6',
    '6.5.7', '6.5.6', '6.5.5', '6.5.4', '6.5.3', '6.5.2', '6.5',
]

# Joomla
# ------
# TODO: See https://github.com/belal-i/lampsible/issues/81
DEFAULT_JOOMLA_VERSION         = '5.3.3'
DEFAULT_JOOMLA_ADMIN_FULL_NAME = 'Sample User'

# Drupal

AVAILABLE_DRUPAL_PROFILES = ['standard', 'minimal']
DEFAULT_DRUPAL_PROFILE    = 'standard'
# ------

# Web applications
# ----------------
DEFAULT_LARAVEL_ARTISAN_COMMANDS = [
    'key:generate',
    'migrate',
    'db:seed',
]
SUPPORTED_SUITECRM_VERSIONS = ['7', '8']
DEFAULT_SUITECRM_VERSION = '8'
SUITECRM_BUILD_URLS = {
    '7': 'https://suitecrm.com/download/141/suite714/564663/suitecrm-7-14-6.zip',
    '8': 'https://suitecrm.com/download/165/suite88/565090/suitecrm-8-8-0.zip',
}

# Misc
# ----
INSECURE_CLI_PASS_WARNING = 'It\'s insecure to pass passwords via CLI args! If you are sure that you want to do this, rerun this command with the --insecure-cli-password flag.'

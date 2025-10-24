# note this fine cannot have any external dependencies since this file is used by the lambda function to figure out which dependencies to load
from mgraph_ai_service_html__admin_ui       import package_name

SERVICE_NAME                      = package_name
FAST_API__TITLE                   = "Html Service"
FAST_API__DESCRIPTION             = "Service with helper methods to export and manipulate html documents."
LAMBDA_DEPENDENCIES__HTML_SERVICE = ['osbot-fast-api-serverless==1.24.0']
UI__CONSOLE__MAJOR__VERSION       = "v0"
UI__CONSOLE__LATEST__VERSION      = "v0.1.7"
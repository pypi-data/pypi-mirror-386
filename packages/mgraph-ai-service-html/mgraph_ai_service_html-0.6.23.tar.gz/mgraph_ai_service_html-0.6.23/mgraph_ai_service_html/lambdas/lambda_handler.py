from osbot_aws.aws.lambda_.boto3__lambda import load_dependencies
from mgraph_ai_service_html.config       import LAMBDA_DEPENDENCIES__HTML_SERVICE

load_dependencies(LAMBDA_DEPENDENCIES__HTML_SERVICE)

def clear_osbot_modules():                                       # Clean up osbot_aws modules after dependency loading
    import sys
    for module in list(sys.modules):
        if module.startswith('osbot_aws'):
            del sys.modules[module]

clear_osbot_modules()

from mgraph_ai_service_html.html__fast_api.Html_Service__Fast_API import Html_Service__Fast_API

with Html_Service__Fast_API() as _:
    _.setup()
    handler = _.handler()
    app     = _.app()

def run(event, context=None):
    return handler(event, context)

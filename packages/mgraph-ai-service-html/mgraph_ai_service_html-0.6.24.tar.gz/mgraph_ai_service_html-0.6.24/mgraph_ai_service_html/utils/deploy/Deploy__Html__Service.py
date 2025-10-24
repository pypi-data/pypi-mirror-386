import mgraph_ai_service_html__admin_ui
from osbot_fast_api_serverless.deploy.Deploy__Serverless__Fast_API  import Deploy__Serverless__Fast_API
from mgraph_ai_service_html.lambdas.lambda_handler                  import run, LAMBDA_DEPENDENCIES__HTML_SERVICE

LAMBDA_NAME__HTML_SERVICE = 'mgraph-ai-service-html'

class Deploy__Html__Service(Deploy__Serverless__Fast_API):

    def deploy_lambda(self):
        with super().deploy_lambda() as _:
            _.add_folder(mgraph_ai_service_html__admin_ui.path)
            return _

    def handler(self):
        return run

    def lambda_dependencies(self):
        return LAMBDA_DEPENDENCIES__HTML_SERVICE

    def lambda_name(self):
        return LAMBDA_NAME__HTML_SERVICE

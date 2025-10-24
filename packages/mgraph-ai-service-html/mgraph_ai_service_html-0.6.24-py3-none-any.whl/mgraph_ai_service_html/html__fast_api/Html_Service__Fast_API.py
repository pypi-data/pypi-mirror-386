import mgraph_ai_service_html__admin_ui
from osbot_fast_api.api.decorators.route_path                       import route_path
from starlette.responses                                            import RedirectResponse
from starlette.staticfiles                                          import StaticFiles
from osbot_fast_api.api.routes.Routes__Set_Cookie                   import Routes__Set_Cookie
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API        import Serverless__Fast_API
from osbot_fast_api_serverless.fast_api.routes.Routes__Info         import Routes__Info
from mgraph_ai_service_html.config                                  import FAST_API__TITLE, FAST_API__DESCRIPTION, UI__CONSOLE__MAJOR__VERSION, UI__CONSOLE__LATEST__VERSION
from mgraph_ai_service_html.html__fast_api.routes.Routes__Dict      import Routes__Dict
from mgraph_ai_service_html.html__fast_api.routes.Routes__Hashes    import Routes__Hashes
from mgraph_ai_service_html.html__fast_api.routes.Routes__Html      import Routes__Html
from mgraph_ai_service_html.utils.Version                           import version__mgraph_ai_service_html

HTML_SERVICE__ROUTE__CONSOLE = 'console'
ROUTES_PATHS__CONSOLE        = [f'/{HTML_SERVICE__ROUTE__CONSOLE}']
class Html_Service__Fast_API(Serverless__Fast_API):                     # Main FastAPI application

    def setup(self):
        with self.config as _:
            _.name           = FAST_API__TITLE
            _.version        = version__mgraph_ai_service_html
            _.description    = FAST_API__DESCRIPTION
        return super().setup()

    # todo: refactor to separate class (focused on setting up this static route)
    def setup_static_routes(self):
        path_static_folder  = mgraph_ai_service_html__admin_ui.path
        path_static         = f"/{HTML_SERVICE__ROUTE__CONSOLE}"
        path_name           = HTML_SERVICE__ROUTE__CONSOLE
        path_latest_version = f"/{HTML_SERVICE__ROUTE__CONSOLE}/{UI__CONSOLE__MAJOR__VERSION}/{UI__CONSOLE__LATEST__VERSION}/index.html"
        self.app().mount(path_static, StaticFiles(directory=path_static_folder), name=path_name)

        @route_path(path=f'/{HTML_SERVICE__ROUTE__CONSOLE}')
        @route_path(path=f'/{HTML_SERVICE__ROUTE__CONSOLE}/')
        async def redirect_to_latest():
            return RedirectResponse(url=path_latest_version)

        self.add_route_get(redirect_to_latest)


    def setup_routes(self):
        self.add_routes(Routes__Html      )                     # HTML transformation routes
        self.add_routes(Routes__Dict      )                     # Dict operation routes
        self.add_routes(Routes__Hashes    )                     # Hash reconstruction routes
        self.add_routes(Routes__Info      )                     # Service info
        self.add_routes(Routes__Set_Cookie)                     # Utility routes
        #self.add_routes(Routes__Admin     )

from osbot_fast_api.api.routes.Fast_API__Routes                                                 import Fast_API__Routes
from starlette.responses                                                                        import HTMLResponse, PlainTextResponse
from mgraph_ai_service_html.html__fast_api.core.Html__Direct__Transformations                   import Html__Direct__Transformations
from mgraph_ai_service_html.html__fast_api.schemas.dict.Schema__Dict__To__Html__Request         import Schema__Dict__To__Html__Request
from mgraph_ai_service_html.html__fast_api.schemas.dict.Schema__Dict__To__Tree_View__Request    import Schema__Dict__To__Tree_View__Request
from mgraph_ai_service_html.html__fast_api.schemas.dict.Schema__Dict__To__Text__Nodes__Request  import Schema__Dict__To__Text__Nodes__Request
from mgraph_ai_service_html.html__fast_api.schemas.dict.Schema__Dict__To__Text__Nodes__Response import Schema__Dict__To__Text__Nodes__Response


ROUTES_PATHS__DICT = [ '/dict/to/html'      ,
                       '/dict/to/tree/view' ,
                       '/dict/to/text/nodes']

class Routes__Dict(Fast_API__Routes):                           # Dict-based operations
    tag                        : str                       = 'dict'
    html_direct_transformations: Html__Direct__Transformations = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.html_direct_transformations = Html__Direct__Transformations()
    
    def to__html(self, request: Schema__Dict__To__Html__Request # Reconstruct HTML
                  ) -> HTMLResponse:
        html = self.html_direct_transformations.html_dict__to__html(request.html_dict)
        return HTMLResponse(content=html, status_code=200)
    
    def to__text__nodes(self, request: Schema__Dict__To__Text__Nodes__Request
                         ) -> Schema__Dict__To__Text__Nodes__Response:
        text_nodes = self.html_direct_transformations.html_dict__to__text_nodes(request.html_dict, request.max_depth)
        
        return Schema__Dict__To__Text__Nodes__Response(text_nodes        = text_nodes       ,
                                                       total_nodes       = len(text_nodes)  ,
                                                       max_depth_reached = False            )  # TODO: implement depth check
    
    def to__tree__view(self, request: Schema__Dict__To__Tree_View__Request
                        ) -> PlainTextResponse:
        html      = self.html_direct_transformations.html_dict__to__html(request.html_dict)
        tree_view = self.html_direct_transformations.html__to__tree_view(html)
        return PlainTextResponse(content=tree_view)
    
    def setup_routes(self):
        self.add_route_post(self.to__html       )
        self.add_route_post(self.to__text__nodes)
        self.add_route_post(self.to__tree__view )

from osbot_fast_api.api.routes.Fast_API__Routes                                                  import Fast_API__Routes
from starlette.responses                                                                         import HTMLResponse, PlainTextResponse
from mgraph_ai_service_html.html__fast_api.core.Html__Direct__Transformations                    import Html__Direct__Transformations
from mgraph_ai_service_html.html__fast_api.core.Html__Hash__Transformations                      import Html__Hash__Transformations
from mgraph_ai_service_html.html__fast_api.schemas.dict.Schema__Dict__To__Text__Nodes__Response  import Schema__Dict__To__Text__Nodes__Response
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Dict__Request          import Schema__Html__To__Dict__Request
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Dict__Response         import Schema__Html__To__Dict__Response
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Dict__Hashes__Request  import Schema__Html__To__Dict__Hashes__Request
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Dict__Hashes__Response import Schema__Html__To__Dict__Hashes__Response
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Html__Hashes__Request  import Schema__Html__To__Html__Hashes__Request
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Html__Request          import Schema__Html__To__Html__Request
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Html__Xxx__Request     import Schema__Html__To__Html__Xxx__Request
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Tree_View__Request     import Schema__Html__To__Tree_View__Request
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Text__Nodes__Request   import Schema__Html__To__Text__Nodes__Request
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Text__Hashes__Request  import Schema__Html__To__Text__Hashes__Request
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Text__Hashes__Response import Schema__Html__To__Text__Hashes__Response

ROUTES_PATHS__HTML = [  '/html/to/dict'                 ,
                        '/html/to/dict/hashes'          ,
                        '/html/to/html'                 ,
                        '/html/to/html/hashes'          ,
                        '/html/to/html/xxx'             ,
                        '/html/to/tree/view'            ,
                        '/html/to/text/hashes'          ,
                        '/html/to/text/nodes'           ]

class Routes__Html(Fast_API__Routes):                                      # HTML transformation routes
    tag                        : str                       = 'html'
    html_direct_transformations: Html__Direct__Transformations = None
    html_hash_transformations  : Html__Hash__Transformations   = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.html_direct_transformations = Html__Direct__Transformations()
        self.html_hash_transformations   = Html__Hash__Transformations()
    
    # ========== Atomic Operations ==========
    
    def to__dict(self, request: Schema__Html__To__Dict__Request                                     # Parse HTML to dict
                  ) -> Schema__Html__To__Dict__Response:
        html_dict  = self.html_direct_transformations.html__to__html_dict(request.html)
        if html_dict:
            node_count = self.html_hash_transformations.count_nodes(html_dict)
            max_depth  = self.html_hash_transformations.calculate_max_depth(html_dict)
        else:
            node_count = 0
            max_depth  = 0
        
        return Schema__Html__To__Dict__Response(html_dict  = html_dict  ,
                                                node_count = node_count ,
                                                max_depth  = max_depth  )
    
    def to__html(self, request: Schema__Html__To__Html__Request                                     # Round-trip validation
                  ) -> HTMLResponse:
        html_dict = self.html_direct_transformations.html__to__html_dict(request.html)
        html      = self.html_direct_transformations.html_dict__to__html(html_dict)
        return HTMLResponse(content=html, status_code=200)
    
    # ========== Compound Operations ==========
    
    def to__text__nodes(self, request: Schema__Html__To__Text__Nodes__Request
                         ) -> Schema__Dict__To__Text__Nodes__Response:
        html_dict  = self.html_direct_transformations.html__to__html_dict      (request.html                )
        text_nodes = self.html_direct_transformations.html_dict__to__text_nodes(html_dict, request.max_depth)
        
        return Schema__Dict__To__Text__Nodes__Response(text_nodes        = text_nodes                                             ,
                                                       total_nodes       = len(text_nodes)                                        ,
                                                       max_depth_reached = self.html_hash_transformations.check_depth_exceeded(html_dict, request.max_depth))
    
    def to__tree__view(self, request: Schema__Html__To__Tree_View__Request
                        ) -> PlainTextResponse:
        tree_view = self.html_direct_transformations.html__to__tree_view(request.html)
        return PlainTextResponse(tree_view)
    
    def to__html__hashes(self, request: Schema__Html__To__Html__Hashes__Request
                          ) -> HTMLResponse:

        html_dict        = self.html_direct_transformations.html__to__html_dict       (request.html                )
        text_nodes       = self.html_direct_transformations.html_dict__to__text_nodes (html_dict, request.max_depth)
        html_with_hashes = self.html_hash_transformations  .html_dict__with__hashes   (html_dict, text_nodes       )
        html             = self.html_direct_transformations.html_dict__to__html       (html_with_hashes            )
        
        return HTMLResponse(content=html, status_code=200)
    
    def to__html__xxx(self, request: Schema__Html__To__Html__Xxx__Request
                       ) -> HTMLResponse:

        html_dict     = self.html_direct_transformations.html__to__html_dict        (request.html                )
        text_nodes    = self.html_direct_transformations.html_dict__to__text_nodes  (html_dict, request.max_depth)
        html_with_xxx = self.html_hash_transformations  .html_dict__with__xxx       (html_dict, text_nodes       )
        html          = self.html_direct_transformations.html_dict__to__html        (html_with_xxx               )
        
        return HTMLResponse(content=html, status_code=200)
    
    # ========== Hash Replacement Workflow Endpoints ==========
    
    def to__dict__hashes(self, request: Schema__Html__To__Dict__Hashes__Request                         # Parse HTML and replace text with hashes
                          ) -> Schema__Html__To__Dict__Hashes__Response:
        return self.html_hash_transformations.html__to__dict__hashes(html      = request.html      ,
                                                                     max_depth = request.max_depth )
    
    def to__text__hashes(self, request: Schema__Html__To__Text__Hashes__Request                         # Extract only text hash mapping
                          ) -> Schema__Html__To__Text__Hashes__Response:
        return self.html_hash_transformations.html__to__text__hashes(html      = request.html      ,
                                                                      max_depth = request.max_depth )
    
    # ========== Route Registration ==========
    
    def setup_routes(self):
        self.add_route_post(self.to__dict         )                        # Atomic operations
        self.add_route_post(self.to__html         )
        self.add_route_post(self.to__text__nodes  )                        # Compound operations
        self.add_route_post(self.to__tree__view   )
        self.add_route_post(self.to__html__hashes )
        self.add_route_post(self.to__html__xxx    )
        self.add_route_post(self.to__dict__hashes )                        # Hash replacement workflow
        self.add_route_post(self.to__text__hashes )

from osbot_fast_api.api.routes.Fast_API__Routes                                             import Fast_API__Routes
from starlette.responses                                                                    import HTMLResponse
from typing                                                                                 import Dict
from mgraph_ai_service_html.html__fast_api.core.Html__Direct__Transformations               import Html__Direct__Transformations
from mgraph_ai_service_html.html__fast_api.schemas.hashes.Schema__Hashes__To__Html__Request import Schema__Hashes__To__Html__Request

ROUTES_PATHS__HASHES = [ '/hashes/to/html' ]

class Routes__Hashes(Fast_API__Routes):                         # Hash reconstruction
    tag                        : str                       = 'hashes'
    html_direct_transformations: Html__Direct__Transformations = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.html_direct_transformations = Html__Direct__Transformations()
    
    def to__html(self, request: Schema__Hashes__To__Html__Request
                  ) -> HTMLResponse:
        # Merge hash_mapping into html_dict
        modified_dict = self._apply_hash_mapping(request.html_dict, request.hash_mapping)
        
        # Reconstruct HTML
        html = self.html_direct_transformations.html_dict__to__html(modified_dict)
        
        return HTMLResponse(content=html, status_code=200)
    
    def _apply_hash_mapping(self, html_dict: Dict               ,# Apply hash replacements
                                  hash_mapping: Dict[str, str]
                            ) -> Dict:
        # Implementation: traverse html_dict, replace text nodes where hash matches
        # This is how external services (Semantic_Text) modify HTML
        from osbot_utils.helpers.html.transformers.Html_Dict__To__Html import Html_Dict__To__Html
        from osbot_utils.helpers.html.transformers.Html__To__Html_Dict import Html__To__Html_Dict
        
        # Convert to HTML, do replacements, convert back
        html = Html_Dict__To__Html(root=html_dict).convert()
        for hash_value, replacement_text in hash_mapping.items():
            html = html.replace(hash_value, replacement_text)
        
        return Html__To__Html_Dict(html=html).convert()
    
    def setup_routes(self):
        self.add_route_post(self.to__html)

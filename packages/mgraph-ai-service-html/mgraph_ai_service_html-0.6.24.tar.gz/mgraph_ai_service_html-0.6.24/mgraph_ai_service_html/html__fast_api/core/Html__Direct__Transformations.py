from osbot_utils.type_safe.Type_Safe                                      import Type_Safe
from osbot_utils.helpers.html.transformers.Html__To__Html_Dict            import Html__To__Html_Dict
from osbot_utils.helpers.html.transformers.Html_Dict__To__Html            import Html_Dict__To__Html
from typing                                                               import Dict
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html import Safe_Str__Html
from mgraph_ai_service_html.html__fast_api.core.Html__Extract_Text_Nodes  import Html__Extract_Text_Nodes, DEFAULT_MAX_DEPTH



class Html__Direct__Transformations(Type_Safe):                             # HTML processing without URL/cache dependencies
    
    def html__to__html_dict(self, html: Safe_Str__Html) -> Dict:            # Parse HTML directly
        return Html__To__Html_Dict(html=html).convert()
        
    def html_dict__to__html(self, html_dict: Dict) -> str:                  # Reconstruct HTML              # todo: replace str with Safe_Str__*
        return Html_Dict__To__Html(root=html_dict).convert()
        
    def html__to__tree_view(self, html: Safe_Str__Html) -> str:                 # Format as tree_view       # todo: replace str with Safe_Str__*
        if html:
            html_converter = Html__To__Html_Dict(html=html)
            html_converter.convert()
            tree_view          = html_converter.print(just_return_lines=True)                               # todo: review Html__To__Html_Dict implementation to see if just_return_lines should be renamed to just_return_tree_view
            return "\n".join(tree_view)
        return ''
        
    def html_dict__to__text_nodes(self, html_dict: Dict                    ,# Extract text nodes
                                        max_depth: int = DEFAULT_MAX_DEPTH
                                   ) -> Dict:
        extractor = Html__Extract_Text_Nodes()
        return extractor.extract_from_html_dict(html_dict, max_depth)

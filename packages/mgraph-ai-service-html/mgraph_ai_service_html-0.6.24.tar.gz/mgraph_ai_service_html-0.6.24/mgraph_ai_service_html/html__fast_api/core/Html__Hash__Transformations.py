from typing                                                                                         import Dict
from osbot_utils.type_safe.Type_Safe                                                                import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                                import Safe_UInt
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html                           import Safe_Str__Html
from osbot_utils.helpers.html.transformers.Html_Dict__To__Html                                      import Html_Dict__To__Html
from osbot_utils.helpers.html.transformers.Html__To__Html_Dict                                      import Html__To__Html_Dict
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                      import type_safe
from mgraph_ai_service_html.html__fast_api.core.Html__Extract_Text_Nodes                            import Html__Extract_Text_Nodes
from mgraph_ai_service_html.html__fast_api.core.Html__Direct__Transformations                       import Html__Direct__Transformations
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Dict__Hashes__Response    import Schema__Html__To__Dict__Hashes__Response
from mgraph_ai_service_html.html__fast_api.schemas.html.Schema__Html__To__Text__Hashes__Response    import Schema__Html__To__Text__Hashes__Response


class Html__Hash__Transformations(Type_Safe):
    html_direct_transformations: Html__Direct__Transformations

    @type_safe
    def html__to__dict__hashes(self, html      : Safe_Str__Html            ,                                    # Parse HTML and replace text with hashes
                                     max_depth : Safe_UInt = 256
                                ) -> Schema__Html__To__Dict__Hashes__Response:
        html_dict           = self.html_direct_transformations.html__to__html_dict(html)
        if html_dict:
            extractor           = Html__Extract_Text_Nodes()
            extractor.html_dict = html_dict
            extractor.max_depth = max_depth

            extractor.traverse(html_dict, depth=0, parent_tag=None)

            hash_mapping        = extractor.text_elements__raw
            node_count          = self.count_nodes(html_dict)
            max_depth_val       = self.calculate_max_depth(html_dict)
            max_depth_reached   = self.check_depth_exceeded(html_dict, max_depth)
        else:
            hash_mapping        = {}
            node_count          = 0
            max_depth_val       = 0
            max_depth_reached   = False

        return Schema__Html__To__Dict__Hashes__Response(html_dict           = html_dict            ,
                                                        hash_mapping        = hash_mapping         ,
                                                        node_count          = node_count           ,
                                                        max_depth           = max_depth_val        ,
                                                        total_text_hashes   = len(hash_mapping)    ,
                                                        max_depth_reached   = max_depth_reached    )

    @type_safe
    def html__to__text__hashes(self, html      : Safe_Str__Html     ,                                           # Extract only text hash mapping (lightweight)
                                     max_depth : Safe_UInt     = 256
                                ) -> Schema__Html__To__Text__Hashes__Response:
        html_dict = self.html_direct_transformations.html__to__html_dict(html)
        if html_dict:
            extractor           = Html__Extract_Text_Nodes()
            extractor.html_dict = html_dict
            extractor.max_depth = max_depth

            extractor.traverse(html_dict, depth=0, parent_tag=None)

            hash_mapping = extractor.text_elements__raw
            max_depth_reached   = self.check_depth_exceeded(html_dict, max_depth)
        else:
            hash_mapping = {}
            max_depth_reached   = False

        return Schema__Html__To__Text__Hashes__Response(hash_mapping        = hash_mapping      ,
                                                        total_text_hashes   = len(hash_mapping) ,
                                                        max_depth_reached   = max_depth_reached )
    @type_safe
    def html_dict__with__hashes(self, html_dict  : Dict,                                        # Replace text with hashes in html_dict
                                      text_nodes : Dict
                                 ) -> Dict:                                                     # todo review if we need the text_nodes here, since it is not being used in this method
        return html_dict                                                                        #      also review the name of this method, since to get html_dict__with__hashes, other actions will need to happen before (that are not part of this method)

    @type_safe
    def html_dict__with__xxx(self, html_dict  : Dict,                                           # Replace text with x's in html_dict
                                   text_nodes : Dict
                              ) -> Dict:

        html = Html_Dict__To__Html(root=html_dict).convert()

        for text_hash, text_element in text_nodes.items():
            original_text   = text_element.get('text')
            text_to_replace = ''.join('x' if c != ' ' else ' ' for c in original_text)
            html            = html.replace(text_hash, text_to_replace)

        return Html__To__Html_Dict(html=html).convert()

    #@type_safe     # todo: add back once OSBot_Utils Bug with Dict in @type_safe has been fixed
    def count_nodes(self, html_dict: Dict
                     ) -> Safe_UInt:                                                            # Count total nodes in HTML tree
        def count_recursive(node):
            if not isinstance(node, dict):
               return 0
            count = 1
            for child in node.get('nodes', []):
                count += count_recursive(child)
            return count

        result = count_recursive(html_dict)
        return Safe_UInt(result)

    @type_safe
    def calculate_max_depth(self, html_dict: Dict
                             ) -> Safe_UInt:                                                    # Calculate maximum nesting depth
        def depth_recursive(node, current_depth):
            if not isinstance(node, dict):
                return current_depth
            max_child_depth = current_depth
            for child in node.get('nodes', []):
                child_depth     = depth_recursive(child, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)
            return max_child_depth

        result = depth_recursive(html_dict, 0)
        return Safe_UInt(result)

    @type_safe
    def check_depth_exceeded(self, html_dict : Dict     ,    # Check if depth limit was exceeded
                                   max_depth : Safe_UInt
                              ) -> bool:
        actual_depth = self.calculate_max_depth(html_dict)
        return actual_depth >= max_depth
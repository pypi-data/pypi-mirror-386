from typing                                                      import Dict
from osbot_utils.helpers.html.transformers.Html__To__Html_Dict   import STRING__SCHEMA_NODES, STRING__SCHEMA_TEXT
from osbot_utils.type_safe.Type_Safe                             import Type_Safe
from osbot_utils.utils.Misc                                      import str_md5

DEFAULT_MAX_DEPTH = 256                                         # todo: move to consts file and rename to include reference to Text Nodes extraction

class Html__Extract_Text_Nodes(Type_Safe):                      # Extract text nodes from HTML structure
    html_dict           : Dict      = None                      # Can be set directly
    text_elements       : Dict                                  # Extracted text with hashes
    text_elements__raw  : Dict                                  # Raw text content
    hash_size           : int       = 10                        # Hash length for text nodes
    captures            : int       = 0                         # Count of captured nodes
    max_depth           : int       = 256                       # Maximum traversal depth
    
    def capture_text(self, text, tag):                          # Capture text node with hash
        hash_value = str_md5(text)[:self.hash_size]
        self.text_elements__raw[hash_value] = text
        self.text_elements[hash_value] = dict(text = text,
                                              tag  = tag )
        self.captures += 1
        return hash_value

    def traverse(self, node, depth, parent_tag):                # Recursively traverse HTML tree
        if depth > self.max_depth:
            return

        if not isinstance(node, dict):
            return

        if node.get("type") == STRING__SCHEMA_TEXT:
            data = node.get("data", "").strip()
            if data:
                if parent_tag not in ['style', 'script']:
                    node['data'] = self.capture_text(node['data'], parent_tag)

        node_tag = node.get('tag')
        for child in node.get(STRING__SCHEMA_NODES, []):
            self.traverse(child, depth + 1, node_tag)

    def extract_from_html_dict(self, html_dict: Dict            ,# NEW METHOD: Direct extraction
                                      max_depth: int = 256
                                ) -> Dict:
        self.html_dict = html_dict
        self.max_depth = max_depth
        self.traverse(self.html_dict, depth=0, parent_tag=None)
        return self.text_elements

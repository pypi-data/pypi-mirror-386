from osbot_utils.type_safe.Type_Safe                                import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt               import Safe_UInt
from typing                                                         import Dict


class Schema__Html__To__Dict__Response(Type_Safe):         # Parsed structure
    html_dict : Dict                                        # Full html_dict structure
    node_count: Safe_UInt                                   # Total nodes in tree
    max_depth : Safe_UInt                                   # Deepest nesting level

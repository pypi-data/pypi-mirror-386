from osbot_utils.type_safe.Type_Safe                    import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt   import Safe_UInt
from typing                                             import Dict


class Schema__Dict__To__Text__Nodes__Request(Type_Safe):   # Extract text nodes
    html_dict: Dict                                         # html_dict structure
    max_depth: Safe_UInt = 256                              # Maximum traversal depth

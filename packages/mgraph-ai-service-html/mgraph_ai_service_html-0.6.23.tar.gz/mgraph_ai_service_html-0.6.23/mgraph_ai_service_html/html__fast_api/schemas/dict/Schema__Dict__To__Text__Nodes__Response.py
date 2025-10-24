from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Hash     import Safe_Str__Hash
from osbot_utils.type_safe.primitives.core.Safe_UInt                                   import Safe_UInt
from typing                                                                             import Dict


class Schema__Dict__To__Text__Nodes__Response(Type_Safe):  # Extracted nodes
    text_nodes       : Dict[Safe_Str__Hash, Dict]           # {hash: {text, tag}}
    total_nodes      : Safe_UInt                            # Number of text nodes
    max_depth_reached: bool                                 # Hit depth limit?

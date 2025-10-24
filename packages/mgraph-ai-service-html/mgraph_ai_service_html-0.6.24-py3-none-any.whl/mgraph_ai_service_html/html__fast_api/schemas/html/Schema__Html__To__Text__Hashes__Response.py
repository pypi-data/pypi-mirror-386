from osbot_utils.type_safe.Type_Safe                                                import Type_Safe
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Hash  import Safe_Str__Hash
from osbot_utils.type_safe.primitives.core.Safe_UInt                                import Safe_UInt
from typing                                                                         import Dict


class Schema__Html__To__Text__Hashes__Response(Type_Safe):          # Simple hash mapping only (lightweight response)
    hash_mapping        : Dict[Safe_Str__Hash, str]                 # Simple {hash: text} mapping
    total_text_hashes   : Safe_UInt                                 # Number of text hashes extracted
    max_depth_reached   : bool                                      # Hit depth limit?

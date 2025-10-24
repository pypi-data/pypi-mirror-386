from osbot_utils.type_safe.Type_Safe                                                    import Type_Safe
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Hash      import Safe_Str__Hash
from typing                                                                             import Dict


class Schema__Hashes__To__Html__Request(Type_Safe):        # Merge external modifications
    html_dict   : Dict                                      # Original structure
    hash_mapping: Dict[Safe_Str__Hash, str]                 # {hash: replacement_text}

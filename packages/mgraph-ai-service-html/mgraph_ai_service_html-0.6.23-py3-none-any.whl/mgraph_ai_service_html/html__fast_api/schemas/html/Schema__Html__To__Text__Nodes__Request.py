from osbot_utils.type_safe.Type_Safe                                      import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                      import Safe_UInt
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html import Safe_Str__Html


class Schema__Html__To__Text__Nodes__Request(Type_Safe):   # One-shot extraction
    html     : Safe_Str__Html                              # Raw HTML content
    max_depth: Safe_UInt = 256                             # Maximum traversal depth

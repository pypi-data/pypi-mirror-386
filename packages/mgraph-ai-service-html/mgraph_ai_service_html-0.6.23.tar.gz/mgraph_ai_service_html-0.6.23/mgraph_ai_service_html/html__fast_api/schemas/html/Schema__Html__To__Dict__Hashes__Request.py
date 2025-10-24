from osbot_utils.type_safe.Type_Safe                                       import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                       import Safe_UInt
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html  import Safe_Str__Html


class Schema__Html__To__Dict__Hashes__Request(Type_Safe):          # Parse HTML and replace text with hashes
    html     : Safe_Str__Html                                       # Raw HTML content (1MB limit)
    max_depth: Safe_UInt = 256                                      # Maximum traversal depth

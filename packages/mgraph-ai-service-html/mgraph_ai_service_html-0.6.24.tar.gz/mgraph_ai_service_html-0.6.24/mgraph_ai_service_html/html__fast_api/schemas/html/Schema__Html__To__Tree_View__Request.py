from osbot_utils.type_safe.Type_Safe                                      import Type_Safe
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html import Safe_Str__Html


class Schema__Html__To__Tree_View__Request(Type_Safe):         # Formatted output
    html: Safe_Str__Html                                    # Raw HTML content

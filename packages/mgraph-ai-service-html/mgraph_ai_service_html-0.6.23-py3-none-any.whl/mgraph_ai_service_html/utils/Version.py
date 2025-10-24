import mgraph_ai_service_html
from osbot_utils.type_safe.Type_Safe import Type_Safe
from osbot_utils.utils.Files         import file_contents, path_combine


class Version(Type_Safe):                                       # Version management for service
    FILE_NAME_VERSION: str = 'version'                          # Version file name

    def path_code_root(self) -> str:                            # Get root path of service code
        return mgraph_ai_service_html.path

    def path_version_file(self) -> str:                         # Get path to version file
        return path_combine(self.path_code_root(), self.FILE_NAME_VERSION)

    def value(self) -> str:                                     # Read version from file
        version = file_contents(self.path_version_file()) or ""
        return version.strip()


version__mgraph_ai_service_html = Version().value()

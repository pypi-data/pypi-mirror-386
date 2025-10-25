from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from kiota_abstractions.default_query_parameters import QueryParameters
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.method import Method
from kiota_abstractions.request_adapter import RequestAdapter
from kiota_abstractions.request_information import RequestInformation
from kiota_abstractions.request_option import RequestOption
from kiota_abstractions.serialization import Parsable, ParsableFactory
from typing import Any, Optional, TYPE_CHECKING, Union
from warnings import warn

if TYPE_CHECKING:
    from ......models.branch_meta_data import BranchMetaData
    from ......models.branch_search_results import BranchSearchResults
    from ......models.create_branch import CreateBranch
    from ......models.problem_details import ProblemDetails
    from .item.with_branch_item_request_builder import WithBranchItemRequestBuilder

class BranchesRequestBuilder(BaseRequestBuilder):
    """
    Manage branches of an artifact.
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new BranchesRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/groups/{groupId}/artifacts/{artifactId}/branches{?limit*,offset*}", path_parameters)
    
    def by_branch_id(self,branch_id: str) -> WithBranchItemRequestBuilder:
        """
        Manage a single branch.
        param branch_id: Artifact branch ID.  Must follow the "[a-zA-Z0-9._//-+]{1,256}" pattern.
        Returns: WithBranchItemRequestBuilder
        """
        if branch_id is None:
            raise TypeError("branch_id cannot be null.")
        from .item.with_branch_item_request_builder import WithBranchItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["branchId"] = branch_id
        return WithBranchItemRequestBuilder(self.request_adapter, url_tpl_params)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[BranchesRequestBuilderGetQueryParameters]] = None) -> Optional[BranchSearchResults]:
        """
        Returns a list of all branches in the artifact. Each branch is a list of version identifiers,ordered from the latest (tip of the branch) to the oldest.This operation can fail for the following reasons:* No artifact with this `groupId` and `artifactId` exists (HTTP error `404`)* A server error occurred (HTTP error `500`)
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[BranchSearchResults]
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        from ......models.problem_details import ProblemDetails

        error_mapping: dict[str, type[ParsableFactory]] = {
            "404": ProblemDetails,
            "500": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from ......models.branch_search_results import BranchSearchResults

        return await self.request_adapter.send_async(request_info, BranchSearchResults, error_mapping)
    
    async def post(self,body: CreateBranch, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[BranchMetaData]:
        """
        Creates a new branch for the artifact.  A new branch consists of metadata and alist of versions.This operation can fail for the following reasons:* No artifact with this `groupId` and `artifactId` exists (HTTP error `404`)* A branch with the given `branchId` already exists (HTTP error `409`)* A server error occurred (HTTP error `500`)
        param body: The request body
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[BranchMetaData]
        """
        if body is None:
            raise TypeError("body cannot be null.")
        request_info = self.to_post_request_information(
            body, request_configuration
        )
        from ......models.problem_details import ProblemDetails

        error_mapping: dict[str, type[ParsableFactory]] = {
            "404": ProblemDetails,
            "409": ProblemDetails,
            "500": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from ......models.branch_meta_data import BranchMetaData

        return await self.request_adapter.send_async(request_info, BranchMetaData, error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[BranchesRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        Returns a list of all branches in the artifact. Each branch is a list of version identifiers,ordered from the latest (tip of the branch) to the oldest.This operation can fail for the following reasons:* No artifact with this `groupId` and `artifactId` exists (HTTP error `404`)* A server error occurred (HTTP error `500`)
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def to_post_request_information(self,body: CreateBranch, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        Creates a new branch for the artifact.  A new branch consists of metadata and alist of versions.This operation can fail for the following reasons:* No artifact with this `groupId` and `artifactId` exists (HTTP error `404`)* A branch with the given `branchId` already exists (HTTP error `409`)* A server error occurred (HTTP error `500`)
        param body: The request body
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        if body is None:
            raise TypeError("body cannot be null.")
        request_info = RequestInformation(Method.POST, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        request_info.set_content_from_parsable(self.request_adapter, "application/json", body)
        return request_info
    
    def with_url(self,raw_url: str) -> BranchesRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: BranchesRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return BranchesRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class BranchesRequestBuilderGetQueryParameters():
        """
        Returns a list of all branches in the artifact. Each branch is a list of version identifiers,ordered from the latest (tip of the branch) to the oldest.This operation can fail for the following reasons:* No artifact with this `groupId` and `artifactId` exists (HTTP error `404`)* A server error occurred (HTTP error `500`)
        """
        # The number of branches to return.  Defaults to 20.
        limit: Optional[int] = None

        # The number of branches to skip before starting to collect the result set.  Defaults to 0.
        offset: Optional[int] = None

    
    @dataclass
    class BranchesRequestBuilderGetRequestConfiguration(RequestConfiguration[BranchesRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    
    @dataclass
    class BranchesRequestBuilderPostRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    


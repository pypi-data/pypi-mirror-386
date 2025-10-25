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
    from ........models.comment import Comment
    from ........models.new_comment import NewComment
    from ........models.problem_details import ProblemDetails
    from .item.with_comment_item_request_builder import WithCommentItemRequestBuilder

class CommentsRequestBuilder(BaseRequestBuilder):
    """
    Manage a collection of comments for an artifact version
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new CommentsRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/groups/{groupId}/artifacts/{artifactId}/versions/{versionExpression}/comments", path_parameters)
    
    def by_comment_id(self,comment_id: str) -> WithCommentItemRequestBuilder:
        """
        Manage a single comment
        param comment_id: The unique identifier of a single comment.
        Returns: WithCommentItemRequestBuilder
        """
        if comment_id is None:
            raise TypeError("comment_id cannot be null.")
        from .item.with_comment_item_request_builder import WithCommentItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["commentId"] = comment_id
        return WithCommentItemRequestBuilder(self.request_adapter, url_tpl_params)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[list[Comment]]:
        """
        Retrieves all comments for a version of an artifact.  Both the `artifactId` and theunique `version` number must be provided.This operation can fail for the following reasons:* No artifact with this `artifactId` exists (HTTP error `404`)* No version with this `version` exists (HTTP error `404`)* A server error occurred (HTTP error `500`)
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[list[Comment]]
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        from ........models.problem_details import ProblemDetails

        error_mapping: dict[str, type[ParsableFactory]] = {
            "400": ProblemDetails,
            "404": ProblemDetails,
            "500": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from ........models.comment import Comment

        return await self.request_adapter.send_collection_async(request_info, Comment, error_mapping)
    
    async def post(self,body: NewComment, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[Comment]:
        """
        Adds a new comment to the artifact version.  Both the `artifactId` and theunique `version` number must be provided.This operation can fail for the following reasons:* No artifact with this `artifactId` exists (HTTP error `404`)* No version with this `version` exists (HTTP error `404`)* A server error occurred (HTTP error `500`)
        param body: The request body
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[Comment]
        """
        if body is None:
            raise TypeError("body cannot be null.")
        request_info = self.to_post_request_information(
            body, request_configuration
        )
        from ........models.problem_details import ProblemDetails

        error_mapping: dict[str, type[ParsableFactory]] = {
            "400": ProblemDetails,
            "404": ProblemDetails,
            "500": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from ........models.comment import Comment

        return await self.request_adapter.send_async(request_info, Comment, error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        Retrieves all comments for a version of an artifact.  Both the `artifactId` and theunique `version` number must be provided.This operation can fail for the following reasons:* No artifact with this `artifactId` exists (HTTP error `404`)* No version with this `version` exists (HTTP error `404`)* A server error occurred (HTTP error `500`)
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def to_post_request_information(self,body: NewComment, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        Adds a new comment to the artifact version.  Both the `artifactId` and theunique `version` number must be provided.This operation can fail for the following reasons:* No artifact with this `artifactId` exists (HTTP error `404`)* No version with this `version` exists (HTTP error `404`)* A server error occurred (HTTP error `500`)
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
    
    def with_url(self,raw_url: str) -> CommentsRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: CommentsRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return CommentsRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class CommentsRequestBuilderGetRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    
    @dataclass
    class CommentsRequestBuilderPostRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    


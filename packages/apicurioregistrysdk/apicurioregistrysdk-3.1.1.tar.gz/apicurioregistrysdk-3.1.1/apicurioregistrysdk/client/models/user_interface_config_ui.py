from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class UserInterfaceConfigUi(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The contextPath property
    context_path: Optional[str] = None
    # The editorsUrl property
    editors_url: Optional[str] = None
    # The navPrefixPath property
    nav_prefix_path: Optional[str] = None
    # The oaiDocsUrl property
    oai_docs_url: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> UserInterfaceConfigUi:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: UserInterfaceConfigUi
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return UserInterfaceConfigUi()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "contextPath": lambda n : setattr(self, 'context_path', n.get_str_value()),
            "editorsUrl": lambda n : setattr(self, 'editors_url', n.get_str_value()),
            "navPrefixPath": lambda n : setattr(self, 'nav_prefix_path', n.get_str_value()),
            "oaiDocsUrl": lambda n : setattr(self, 'oai_docs_url', n.get_str_value()),
        }
        return fields
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        writer.write_str_value("contextPath", self.context_path)
        writer.write_str_value("editorsUrl", self.editors_url)
        writer.write_str_value("navPrefixPath", self.nav_prefix_path)
        writer.write_str_value("oaiDocsUrl", self.oai_docs_url)
        writer.write_additional_data_value(self.additional_data)
    


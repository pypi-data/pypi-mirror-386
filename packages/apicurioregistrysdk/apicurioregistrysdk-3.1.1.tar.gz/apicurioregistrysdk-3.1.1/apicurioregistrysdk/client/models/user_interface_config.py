from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .user_interface_config_auth import UserInterfaceConfigAuth
    from .user_interface_config_features import UserInterfaceConfigFeatures
    from .user_interface_config_ui import UserInterfaceConfigUi

@dataclass
class UserInterfaceConfig(AdditionalDataHolder, Parsable):
    """
    Defines the user interface configuration data type.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The auth property
    auth: Optional[UserInterfaceConfigAuth] = None
    # The features property
    features: Optional[UserInterfaceConfigFeatures] = None
    # The ui property
    ui: Optional[UserInterfaceConfigUi] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> UserInterfaceConfig:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: UserInterfaceConfig
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return UserInterfaceConfig()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .user_interface_config_auth import UserInterfaceConfigAuth
        from .user_interface_config_features import UserInterfaceConfigFeatures
        from .user_interface_config_ui import UserInterfaceConfigUi

        from .user_interface_config_auth import UserInterfaceConfigAuth
        from .user_interface_config_features import UserInterfaceConfigFeatures
        from .user_interface_config_ui import UserInterfaceConfigUi

        fields: dict[str, Callable[[Any], None]] = {
            "auth": lambda n : setattr(self, 'auth', n.get_object_value(UserInterfaceConfigAuth)),
            "features": lambda n : setattr(self, 'features', n.get_object_value(UserInterfaceConfigFeatures)),
            "ui": lambda n : setattr(self, 'ui', n.get_object_value(UserInterfaceConfigUi)),
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
        writer.write_object_value("auth", self.auth)
        writer.write_object_value("features", self.features)
        writer.write_object_value("ui", self.ui)
        writer.write_additional_data_value(self.additional_data)
    


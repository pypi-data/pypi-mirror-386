from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from kiota_abstractions.store import BackedModel, BackingStore, BackingStoreFactorySingleton
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .audiences_configuration import AudiencesConfiguration
    from .identifier_uri_configuration import IdentifierUriConfiguration

@dataclass
class CustomAppManagementApplicationConfiguration(AdditionalDataHolder, BackedModel, Parsable):
    # Stores model information.
    backing_store: BackingStore = field(default_factory=BackingStoreFactorySingleton(backing_store_factory=None).backing_store_factory.create_backing_store, repr=False)

    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)
    # Property to restrict creation or update of apps based on their target signInAudience types.
    audiences: Optional[AudiencesConfiguration] = None
    # Configuration for identifierUris restrictions.
    identifier_uris: Optional[IdentifierUriConfiguration] = None
    # The OdataType property
    odata_type: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> CustomAppManagementApplicationConfiguration:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: CustomAppManagementApplicationConfiguration
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return CustomAppManagementApplicationConfiguration()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .audiences_configuration import AudiencesConfiguration
        from .identifier_uri_configuration import IdentifierUriConfiguration

        from .audiences_configuration import AudiencesConfiguration
        from .identifier_uri_configuration import IdentifierUriConfiguration

        fields: dict[str, Callable[[Any], None]] = {
            "audiences": lambda n : setattr(self, 'audiences', n.get_object_value(AudiencesConfiguration)),
            "identifierUris": lambda n : setattr(self, 'identifier_uris', n.get_object_value(IdentifierUriConfiguration)),
            "@odata.type": lambda n : setattr(self, 'odata_type', n.get_str_value()),
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
        writer.write_object_value("audiences", self.audiences)
        writer.write_object_value("identifierUris", self.identifier_uris)
        writer.write_str_value("@odata.type", self.odata_type)
        writer.write_additional_data_value(self.additional_data)
    


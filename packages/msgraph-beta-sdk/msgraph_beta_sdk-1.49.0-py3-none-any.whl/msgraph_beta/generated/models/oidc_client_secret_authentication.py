from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .oidc_client_authentication import OidcClientAuthentication

from .oidc_client_authentication import OidcClientAuthentication

@dataclass
class OidcClientSecretAuthentication(OidcClientAuthentication, Parsable):
    # The OdataType property
    odata_type: Optional[str] = "#microsoft.graph.oidcClientSecretAuthentication"
    # The client secret obtained from configuring the client application on the external OpenID Connect identity provider. The property includes the client secret and enables the identity provider to use either the clientsecretpost authentication method.
    client_secret: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> OidcClientSecretAuthentication:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: OidcClientSecretAuthentication
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return OidcClientSecretAuthentication()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .oidc_client_authentication import OidcClientAuthentication

        from .oidc_client_authentication import OidcClientAuthentication

        fields: dict[str, Callable[[Any], None]] = {
            "clientSecret": lambda n : setattr(self, 'client_secret', n.get_str_value()),
        }
        super_fields = super().get_field_deserializers()
        fields.update(super_fields)
        return fields
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        super().serialize(writer)
        writer.write_str_value("clientSecret", self.client_secret)
    


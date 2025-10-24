from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .entity import Entity
    from .mailbox_item import MailboxItem
    from .multi_value_legacy_extended_property import MultiValueLegacyExtendedProperty
    from .single_value_legacy_extended_property import SingleValueLegacyExtendedProperty

from .entity import Entity

@dataclass
class MailboxFolder(Entity, Parsable):
    # The number of immediate child folders in the current folder.
    child_folder_count: Optional[int] = None
    # The collection of child folders in this folder.
    child_folders: Optional[list[MailboxFolder]] = None
    # The display name of the folder.
    display_name: Optional[str] = None
    # The collection of items in this folder.
    items: Optional[list[MailboxItem]] = None
    # The collection of multi-value extended properties defined for the mailboxFolder.
    multi_value_extended_properties: Optional[list[MultiValueLegacyExtendedProperty]] = None
    # The OdataType property
    odata_type: Optional[str] = None
    # The unique identifier for the parent folder of this folder.
    parent_folder_id: Optional[str] = None
    # The routing link to the actual underlying mailbox where the folder physically resides. The folder can be accessed using GET {parentMailboxUrl}/folders/{id}, which treats the entire URL as an opaque string.  This method is especially important when auto-expanding archiving is enabled for a user's in-place archive mailbox. The user's archive content can span across multiple mailboxes in such scenarios.
    parent_mailbox_url: Optional[str] = None
    # The collection of single-value extended properties defined for the mailboxFolder.
    single_value_extended_properties: Optional[list[SingleValueLegacyExtendedProperty]] = None
    # The number of items in the folder.
    total_item_count: Optional[int] = None
    # Describes the folder class type.
    type: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> MailboxFolder:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: MailboxFolder
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return MailboxFolder()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .entity import Entity
        from .mailbox_item import MailboxItem
        from .multi_value_legacy_extended_property import MultiValueLegacyExtendedProperty
        from .single_value_legacy_extended_property import SingleValueLegacyExtendedProperty

        from .entity import Entity
        from .mailbox_item import MailboxItem
        from .multi_value_legacy_extended_property import MultiValueLegacyExtendedProperty
        from .single_value_legacy_extended_property import SingleValueLegacyExtendedProperty

        fields: dict[str, Callable[[Any], None]] = {
            "childFolderCount": lambda n : setattr(self, 'child_folder_count', n.get_int_value()),
            "childFolders": lambda n : setattr(self, 'child_folders', n.get_collection_of_object_values(MailboxFolder)),
            "displayName": lambda n : setattr(self, 'display_name', n.get_str_value()),
            "items": lambda n : setattr(self, 'items', n.get_collection_of_object_values(MailboxItem)),
            "multiValueExtendedProperties": lambda n : setattr(self, 'multi_value_extended_properties', n.get_collection_of_object_values(MultiValueLegacyExtendedProperty)),
            "parentFolderId": lambda n : setattr(self, 'parent_folder_id', n.get_str_value()),
            "parentMailboxUrl": lambda n : setattr(self, 'parent_mailbox_url', n.get_str_value()),
            "singleValueExtendedProperties": lambda n : setattr(self, 'single_value_extended_properties', n.get_collection_of_object_values(SingleValueLegacyExtendedProperty)),
            "totalItemCount": lambda n : setattr(self, 'total_item_count', n.get_int_value()),
            "type": lambda n : setattr(self, 'type', n.get_str_value()),
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
        writer.write_int_value("childFolderCount", self.child_folder_count)
        writer.write_collection_of_object_values("childFolders", self.child_folders)
        writer.write_str_value("displayName", self.display_name)
        writer.write_collection_of_object_values("items", self.items)
        writer.write_collection_of_object_values("multiValueExtendedProperties", self.multi_value_extended_properties)
        writer.write_str_value("parentFolderId", self.parent_folder_id)
        writer.write_str_value("parentMailboxUrl", self.parent_mailbox_url)
        writer.write_collection_of_object_values("singleValueExtendedProperties", self.single_value_extended_properties)
        writer.write_int_value("totalItemCount", self.total_item_count)
        writer.write_str_value("type", self.type)
    


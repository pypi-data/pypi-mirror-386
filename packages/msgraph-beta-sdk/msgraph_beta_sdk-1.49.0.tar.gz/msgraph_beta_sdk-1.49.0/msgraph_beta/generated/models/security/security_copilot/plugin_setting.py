from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from kiota_abstractions.store import BackedModel, BackingStore, BackingStoreFactorySingleton
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .plugin_setting_display_type import PluginSettingDisplayType
    from .plugin_setting_type import PluginSettingType

@dataclass
class PluginSetting(AdditionalDataHolder, BackedModel, Parsable):
    # Stores model information.
    backing_store: BackingStore = field(default_factory=BackingStoreFactorySingleton(backing_store_factory=None).backing_store_factory.create_backing_store, repr=False)

    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)
    # The acceptableValues property
    acceptable_values: Optional[list[str]] = None
    # The defaultValue property
    default_value: Optional[str] = None
    # The description property
    description: Optional[str] = None
    # The displayType property
    display_type: Optional[PluginSettingDisplayType] = None
    # The hintText property
    hint_text: Optional[str] = None
    # The isRequired property
    is_required: Optional[bool] = None
    # The label property
    label: Optional[str] = None
    # The name property
    name: Optional[str] = None
    # The OdataType property
    odata_type: Optional[str] = None
    # The settingValue property
    setting_value: Optional[PluginSettingType] = None
    # The value property
    value: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> PluginSetting:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: PluginSetting
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return PluginSetting()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .plugin_setting_display_type import PluginSettingDisplayType
        from .plugin_setting_type import PluginSettingType

        from .plugin_setting_display_type import PluginSettingDisplayType
        from .plugin_setting_type import PluginSettingType

        fields: dict[str, Callable[[Any], None]] = {
            "acceptableValues": lambda n : setattr(self, 'acceptable_values', n.get_collection_of_primitive_values(str)),
            "defaultValue": lambda n : setattr(self, 'default_value', n.get_str_value()),
            "description": lambda n : setattr(self, 'description', n.get_str_value()),
            "displayType": lambda n : setattr(self, 'display_type', n.get_enum_value(PluginSettingDisplayType)),
            "hintText": lambda n : setattr(self, 'hint_text', n.get_str_value()),
            "isRequired": lambda n : setattr(self, 'is_required', n.get_bool_value()),
            "label": lambda n : setattr(self, 'label', n.get_str_value()),
            "name": lambda n : setattr(self, 'name', n.get_str_value()),
            "@odata.type": lambda n : setattr(self, 'odata_type', n.get_str_value()),
            "settingValue": lambda n : setattr(self, 'setting_value', n.get_enum_value(PluginSettingType)),
            "value": lambda n : setattr(self, 'value', n.get_str_value()),
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
        writer.write_collection_of_primitive_values("acceptableValues", self.acceptable_values)
        writer.write_str_value("defaultValue", self.default_value)
        writer.write_str_value("description", self.description)
        writer.write_enum_value("displayType", self.display_type)
        writer.write_str_value("hintText", self.hint_text)
        writer.write_bool_value("isRequired", self.is_required)
        writer.write_str_value("label", self.label)
        writer.write_str_value("name", self.name)
        writer.write_str_value("@odata.type", self.odata_type)
        writer.write_enum_value("settingValue", self.setting_value)
        writer.write_str_value("value", self.value)
        writer.write_additional_data_value(self.additional_data)
    


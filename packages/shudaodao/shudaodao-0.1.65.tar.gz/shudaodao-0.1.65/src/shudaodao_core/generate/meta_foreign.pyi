from dataclasses import dataclass

@dataclass
class MetaForeignColumn:
    schema_name: str
    alias_index: str
    sort_order: bool
    constrained_table: str
    constrained_class: str
    constrained_column: str
    constrained_name: str
    referred_table: str
    referred_class: str
    referred_column: str
    referred_name: str
    @classmethod
    def get_camel_name(cls, source, is_plural) -> str: ...
    @classmethod
    def get_property_name(cls, source: str, is_plural) -> str: ...

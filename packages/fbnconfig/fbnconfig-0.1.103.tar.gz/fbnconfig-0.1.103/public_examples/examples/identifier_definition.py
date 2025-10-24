from fbnconfig import Deployment, datatype, identifier_definition, property
from fbnconfig.property import LifeTime

"""
An example configuration for defining identifier definition related entities.
The script configures the following entities:
- IdentifierDefinition
"""


def configure(env):
    rating = property.DefinitionResource(
        id="rating",
        domain=property.Domain.ChartOfAccounts,
        scope="sc1",
        code="rating",
        display_name="Rating",
        data_type_id=datatype.DataTypeRef(id="default_str", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Collection,
        property_description="Example property representing a rating",
        life_time=property.LifeTime.Perpetual,
        collection_type=property.CollectionType.Array,
    )

    identifier_property = identifier_definition.PropertyValue(
        property_key=rating,
        label_value="Example_label"
    )

    id_def = identifier_definition.IdentifierDefinitionResource(
        id="idExample",
        domain=identifier_definition.SupportedDomain.Instrument,
        identifier_scope="ScopeExample",
        identifier_type="TypeExample",
        life_time=LifeTime.Perpetual,
        hierarchy_usage="MasterIdentifier",
        hierarchy_level="hierarchyLevelExample",
        display_name="example_display_name",
        description="example_description",
        properties=[identifier_property]
    )

    return Deployment("identifier_definition_example", [id_def])

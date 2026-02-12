# domain/metadata_schema.py

from langchain.chains.query_constructor.base import AttributeInfo

# This schema defines the fields that the LLM can filter by when self-querying.
# It helps the SelfQueryRetriever understand what metadata is available in the vector store.

METADATA_FIELD_INFO = [
    AttributeInfo(
        name="regulation_id",
        description="The specific Regulation number or Table number. Examples: 'Reg 33(7)', 'Table 12', 'Reg 30'.",
        type="string",
    ),
    AttributeInfo(
        name="zone",
        description="The geographic zone or land-use zone the regulation applies to. Use this to filter for 'Island City', 'Suburbs', 'Residential (R-Zone)', 'Commercial (C-Zone)', or 'Industrial (I-Zone)'.",
        type="string",
    ),
    AttributeInfo(
        name="scheme_type",
        description="The specific redevelopment scheme mentioned. Vital for distinguishing rules. Values: '33(7) Cessed', '33(9) Cluster', '33(10) SRA', '33(5) MHADA', '33(11) PTC', 'General'.",
        type="string",
    ),
    AttributeInfo(
        name="min_road_width",
        description="The minimum road width (in meters) required for this rule to apply. Useful for filtering FSI tables.",
        type="float",
    ),
    AttributeInfo(
        name="min_plot_area",
        description="The minimum plot area (in square meters) required for this rule to apply. Useful for Cluster/High-rise rules.",
        type="float",
    ),
    AttributeInfo(
        name="category",
        description="The building category. Examples: 'High-rise', 'Educational', 'Medical', 'IT/Biotech', 'Hospitality'.",
        type="string",
    ),
]
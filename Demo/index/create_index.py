import os
from dotenv import load_dotenv
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchProfile
)
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX")

index_client = SearchIndexClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(admin_key)
)

index = SearchIndex(
    name=index_name,
    fields=[
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True
        ),

        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            retrievable=True
        ),

        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True,
            retrievable=True
        ),

        SimpleField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
            facetable=True,
            retrievable=True
        ),

        SimpleField(
            name="chunk",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True,
            retrievable=True
        ),

        # Optional aber sehr empfehlenswert für PDFs
        SimpleField(
            name="page",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True,
            retrievable=True
        ),

        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            retrievable=True,                 #  wichtig
            vector_search_dimensions=1536,
            vector_search_profile_name="vprofile"
        ),
    ],
    vector_search=VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw",
                kind=VectorSearchAlgorithmKind.HNSW
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vprofile",
                algorithm_configuration_name="hnsw"
            )
        ]
    )
)

if index_name in [i.name for i in index_client.list_indexes()]:
    print(f"Index '{index_name}' existiert bereits.")
else:
    index_client.create_index(index)
    print(f"Index '{index_name}' wurde erstellt.")

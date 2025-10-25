import logging
import os
from enum import Enum
from rara_tools.constants.normalizers import EntityType, VIAF_ENTITY_MAP

class URLSource:
    VIAF = "VIAF"
    SIERRA = "Sierra"
    EMS = "EMS"

class KeywordType:
    LOC = "Kohamärksõnad"
    TIME = "Ajamärksõnad"
    TOPIC = "Teemamärksõnad"
    GENRE = "Vormimärksõnad"
    TITLE = "Teose pealkiri"
    PER = "Isikunimi"
    ORG = "Kollektiivi nimi"
    EVENT = "Ajutine kollektiiv või sündmus"
    CATEGORY = "Valdkonnamärksõnad"
    UDC = "UDC Summary"
    UDK = "UDK Rahvusbibliograafia"


class KeywordMARC:
    PER = 600
    ORG = 610
    TOPIC = 650
    GENRE = 655
    TIME = 648
    LOC = 651
    EVENT = 611
    TITLE = 630
    TITLE_LINKED = 600

class KeywordSource:
    EMS = "EMS"
    SIERRA = "SIERRA"
    VIAF = "VIAF"
    AI = "AI"

class Filters:
    AUTHOR = "author"
    YEAR = "year"

UNLINKED_KEYWORD_MARC_FIELD = 693

ALLOWED_FILTERS_MAP = {
    EntityType.PER: [Filters.YEAR],
    EntityType.ORG: [Filters.YEAR],
    EntityType.TITLE: [Filters.YEAR, Filters.AUTHOR],
    EntityType.KEYWORD: [],
    EntityType.LOC: []
}
KEYWORD_MARC_MAP = {
    KeywordType.LOC: KeywordMARC.LOC,
    KeywordType.TIME: KeywordMARC.TIME,
    KeywordType.TOPIC: KeywordMARC.TOPIC,
    KeywordType.GENRE: KeywordMARC.GENRE,
    KeywordType.TITLE: KeywordMARC.TITLE,
    KeywordType.ORG: KeywordMARC.ORG,
    KeywordType.PER: KeywordMARC.PER,
    KeywordType.EVENT: KeywordMARC.EVENT
}

URL_SOURCE_MAP = {
    EntityType.PER: URLSource.VIAF,
    EntityType.ORG: URLSource.VIAF,
    EntityType.TITLE: URLSource.VIAF,
    EntityType.KEYWORD: URLSource.EMS,
    EntityType.LOC: URLSource.EMS
}

# Ignore those "keyword types" while linking the
# rara-subject-indexer results
KEYWORD_TYPES_TO_IGNORE = [
    KeywordType.CATEGORY,
    KeywordType.UDC,
    KeywordType.UDK
]

ALLOWED_ENTITY_TYPES = [
    EntityType.PER,
    EntityType.ORG,
    EntityType.KEYWORD,
    EntityType.LOC,
    EntityType.TITLE,
    EntityType.UNK,
]


KEYWORD_TYPE_MAP = {
    KeywordType.TIME: EntityType.KEYWORD,
    KeywordType.GENRE: EntityType.KEYWORD,
    KeywordType.LOC: EntityType.LOC,
    KeywordType.PER: EntityType.PER,
    KeywordType.ORG: EntityType.ORG,
    KeywordType.TOPIC: EntityType.KEYWORD,
    KeywordType.TITLE: EntityType.TITLE,
    KeywordType.EVENT: EntityType.ORG
}

EMS_ENTITY_TYPES = [EntityType.KEYWORD, EntityType.LOC]
SIERRA_ENTITY_TYPES = [EntityType.PER, EntityType.ORG, EntityType.TITLE]
VIAF_ENTITY_TYPES = [EntityType.PER, EntityType.ORG, EntityType.TITLE]

# Params for filters
MIN_AUTHOR_SIMILARITY = 0.95
YEAR_EXCEPTION_VALUE = True

LOGGER_NAME = "rara-norm-linker"
LOGGER = logging.getLogger(LOGGER_NAME)

ELASTIC_HOST = os.environ.get("ES_URL", "http://localhost:9200")

EMS_CONFIG = {
    "es_host": ELASTIC_HOST,
    "es_index": "rara_linker_ems_partial_v1",
    "search_field": "link_variations",
    "alt_search_field": "synonyms_en",
    "key_field": "keyword",
    "json_field": "full_record_json",
    "marc_field": "full_record_marc",
    "identifier_field": "ems_id"
}

LOC_CONFIG = {
    "es_host": ELASTIC_HOST,
    "es_index": "rara_linker_ems_loc_v1",
    "search_field": "link_variations",
    "alt_search_field": "synonyms_en",
    "key_field": "keyword",
    "json_field": "full_record_json",
    "marc_field": "full_record_marc",
    "identifier_field": "ems_id"
}

PER_CONFIG = {
    "es_host": ELASTIC_HOST,
    "es_index": "rara_linker_persons_knn_v1",
    "search_field": "link_variations",
    "key_field": "name",
    "vector_field": "vector",
    "json_field": "full_record_json",
    "marc_field": "full_record_marc",
    "identifier_field": "identifier",
    "viaf_field": VIAF_ENTITY_MAP.get(EntityType.PER)
}

ORG_CONFIG = {
    "es_host": ELASTIC_HOST,
    "es_index": "rara_linker_organizations_knn_v3",
    "search_field": "link_variations",
    "alt_search_field": "link_acronyms",
    "key_field": "name",
    "vector_field": "vector",
    "json_field": "full_record_json",
    "marc_field": "full_record_marc",
    "identifier_field": "identifier",
    "viaf_field": VIAF_ENTITY_MAP.get(EntityType.ORG)
}

TITLE_CONFIG = {
    "es_host": ELASTIC_HOST,
    "es_index": "rara_linker_titles_v3",
    "search_field": "link_variations",
    "key_field": "name",
    "json_field": "full_record_json",
    "marc_field": "full_record_marc",
    "identifier_field": "name",
    "viaf_field": VIAF_ENTITY_MAP.get(EntityType.TITLE)
}

VECTORIZER_CONFIG = {
    "model_name": "BAAI/bge-m3",
    "system_configuration": {
        "use_fp16": False,
        "device": None,
        "normalize_embeddings": True
    },
    "inference_configuration": {
        "batch_size": 12,
        "return_dense": True,
        "max_length": 1000
    },
    "model_directory": "../vectorizer_data",
}

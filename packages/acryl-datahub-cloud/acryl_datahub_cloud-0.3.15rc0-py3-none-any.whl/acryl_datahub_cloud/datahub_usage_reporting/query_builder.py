from datetime import datetime, timedelta
from typing import Dict


class QueryBuilder:
    @staticmethod
    def get_dataset_entities_query() -> Dict:
        return {
            # "sort": [{"urn": {"order": "asc"}}],
            "_source": {
                "includes": [
                    "urn",
                    "lastModifiedAt",
                    "removed",
                    "siblings",
                    "typeNames",
                    "combinedSearchRankingMultiplier",
                ]
            },
        }

    @staticmethod
    def get_query_entities_query(days: int) -> Dict:
        thirty_days_ago = datetime.now() - timedelta(days=days)
        thirty_days_ago = thirty_days_ago.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        epoch_ms = int(thirty_days_ago.timestamp() * 1000)

        return {
            # "sort": [{"urn": {"order": "asc"}}],
            "_source": {"includes": ["urn", "lastModifiedAt", "platform", "removed"]},
            "query": {
                "bool": {
                    "filter": [
                        {"bool": {"must_not": [{"term": {"source": "MANUAL"}}]}},
                        {"exists": {"field": "platform"}},
                        {
                            "bool": {
                                "should": [
                                    {
                                        "bool": {
                                            "filter": [
                                                {"exists": {"field": "lastModifiedAt"}},
                                                {
                                                    "range": {
                                                        "lastModifiedAt": {
                                                            "gte": epoch_ms
                                                        }
                                                    }
                                                },
                                            ]
                                        }
                                    },
                                    {
                                        "bool": {
                                            "must_not": {
                                                "exists": {"field": "lastModifiedAt"}
                                            },
                                            "filter": {
                                                "range": {
                                                    "createdAt": {"gte": epoch_ms}
                                                }
                                            },
                                        }
                                    },
                                ],
                                "minimum_should_match": 1,
                            }
                        },
                    ]
                }
            },
        }

    @staticmethod
    def get_upstreams_query() -> Dict:
        return {
            # "sort": [{"destination.urn": {"order": "asc"}}],
            "_source": {"includes": ["source.urn", "destination.urn"]},
            "query": {
                "bool": {
                    "must": [
                        {"terms": {"destination.entityType": ["dataset"]}},
                        {"terms": {"source.entityType": ["dataset"]}},
                    ]
                }
            },
        }

    @staticmethod
    def get_dashboard_usage_query(days: int) -> Dict:
        return {
            # "sort": [{"urn": {"order": "asc"}}],
            "_source": {
                "includes": [
                    "timestampMillis",
                    "systemMetadata.lastObserved",
                    "urn",
                    "eventGranularity",
                    "viewsCount",
                    "uniqueUserCount",
                    "event.userCounts",
                ]
            },
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {"gte": f"now-{days}d", "lt": "now/d"}
                            }
                        },
                        {"term": {"isExploded": False}},
                    ]
                }
            },
        }

    @staticmethod
    def get_dataset_usage_query(days: int) -> Dict:
        return {
            # "sort": [{"urn": {"order": "asc"}}],
            "_source": {
                "includes": [
                    "timestampMillis",
                    "urn",
                    "eventGranularity",
                    "totalSqlQueries",
                    "uniqueUserCount",
                    "event.userCounts",
                    "platform",
                ]
            },
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {"gte": f"now-{days}d/d", "lt": "now/d"}
                            }
                        },
                        {"term": {"isExploded": False}},
                        {"range": {"totalSqlQueries": {"gt": 0}}},
                    ]
                }
            },
        }

    @staticmethod
    def get_dataset_write_usage_raw_query(days: int) -> Dict:
        return {
            # "sort": [{"urn": {"order": "asc"}}, {"@timestamp": {"order": "asc"}}],
            "_source": {
                "includes": [
                    "urn"  # Only field needed for platform extraction via regex
                ]
            },
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {"gte": f"now-{days}d/d", "lte": "now/d"}
                            }
                        },
                        {"terms": {"operationType": ["INSERT", "UPDATE", "CREATE"]}},
                    ]
                }
            },
        }

    @staticmethod
    def get_dataset_write_usage_composite_query(days: int) -> Dict:
        return {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {"gte": f"now-{days}d/d", "lte": "now/d"}
                            }
                        },
                        {"terms": {"operationType": ["INSERT", "UPDATE", "CREATE"]}},
                    ]
                }
            },
            "aggs": {
                "urn_count": {
                    "composite": {
                        "sources": [
                            {"dataset_operationaspect_v1": {"terms": {"field": "urn"}}}
                        ]
                    }
                }
            },
        }

    @staticmethod
    def get_query_usage_query(days: int) -> Dict:
        return {
            # "sort": [{"urn": {"order": "asc"}}],
            "_source": {
                "includes": [
                    "timestampMillis",
                    "systemMetadata.lastObserved",
                    "urn",
                    "eventGranularity",
                    "queryCount",
                    "uniqueUserCount",
                    "event.userCounts",
                ]
            },
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {"gte": f"now-{days}d/d", "lt": "now/d"}
                            }
                        },
                        {"term": {"isExploded": False}},
                    ]
                }
            },
        }

SAMPLE_QUERY_1 = {
    "fields": [{"fieldCaption": "売上", "function": "SUM", "maxDecimalPlaces": 0}]
}

SAMPLE_QUERY_2 = {
    "fields": [{"fieldCaption": "売上", "function": "SUM", "maxDecimalPlaces": 0}],
    "filters": [
        {
            "field": {"fieldCaption": "オーダー日"},
            "filterType": "QUANTITATIVE_DATE",
            "quantitativeFilterType": "RANGE",
            "minDate": "2024-01-01",
            "maxDate": "2024-12-31",
        }
    ],
}

SAMPLE_QUERY_3 = {
    "fields": [
      { "fieldCaption": "カテゴリ", "sortPriority": 1 },
      { "fieldCaption": "売上", "function": "SUM", "fieldAlias": "Sales" },
      { "fieldCaption": "利益", "function": "SUM", "fieldAlias": "Profit" },
      {
        "fieldCaption": "Profit Margin",
        "calculation": "SUM([利益]) / SUM([売上])",
        "maxDecimalPlaces": 4,
        "sortPriority": 2,
        "sortDirection": "DESC"
      }
    ],
    "filters": [
        {
            "field": {"fieldCaption": "オーダー日"},
            "filterType": "QUANTITATIVE_DATE",
            "quantitativeFilterType": "RANGE",
            "minDate": "2024-01-01",
            "maxDate": "2024-12-31",
        }
    ],
  }
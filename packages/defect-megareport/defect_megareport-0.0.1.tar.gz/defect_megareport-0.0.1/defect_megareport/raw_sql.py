
ATTRIBUTE_CASE_SQL = """
                        WHEN jsonb_typeof(tests_representation_testresult.attributes->'{attribute}') = 'array' THEN
                            ARRAY(SELECT jsonb_array_elements_text(tests_representation_testresult.attributes->'{attribute}'))
                        WHEN jsonb_typeof(tests_representation_testresult.attributes->'{attribute}') = 'string' THEN
                            regexp_split_to_array(tests_representation_testresult.attributes->>'{attribute}', '[{array_splits}]')

"""

ARRAY_UNPACK_SQL = """
    ARRAY(
        WITH defects_source AS (
            SELECT 
                unnest(
                    CASE 
                        {attribute_cases}
                        ELSE
                            ARRAY[]::text[]
                    END
                ) AS defect_item
        ),
        jira_keys as (
            SELECT DISTINCT (regexp_matches(defect_item, '({jira_key_regex})', 'g'))[1] as jira_key
            FROM defects_source
            WHERE defect_item IS NOT NULL
              AND defect_item ~ '({jira_key_regex})'
        )
        select jira_key
        from jira_keys
        where 1=1 
        {search_condition}
    )"""  # noqa: W291 E501

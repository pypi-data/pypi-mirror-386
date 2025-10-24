# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import pandas as pd

from snowflake.snowflake_data_validation.extractor.sql_queries_template_generator import (
    SQLQueriesTemplateGenerator,
)
from snowflake.snowflake_data_validation.utils.constants import (
    COL_NAME_NO_QUOTES_PLACEHOLDER,
    METRIC_COLUMN_KEY,
    METRIC_QUERY_PLACEHOLDER,
    METRICS_TO_EXCLUDE,
    NORMALIZATION_COLUMN_KEY,
    TEMPLATE_COLUMN_KEY,
    TYPE_COLUMN_KEY,
)


LOGGER = logging.getLogger(__name__)


def generate_cte_query(
    metrics_templates: pd.DataFrame,
    col_name,
    col_type,
    fully_qualified_name: str,
    where_clause: str,
    has_where_clause: bool,
    sql_generator: SQLQueriesTemplateGenerator,
    exclude_metrics: bool,
):
    """Generate a Snowflake CTE query for a given column and type using Jinja2 templates.

    Args:
        metrics_templates (DataFrame): DataFrame containing metrics templates
        col_name (str): Column name
        col_type (str): Column data type
        fully_qualified_name (str): Fully qualified name of the table
        where_clause (str): WHERE clause to filter the data
        has_where_clause (bool): Flag indicating if a WHERE clause is present
        sql_generator (SQLQueriesTemplateGenerator): An instance of SQLQueriesTemplateGenerator
                                                    used to render the SQL templates.
        exclude_metrics (bool): If True, excludes certain metrics from the CTE query.

    Returns:
        tuple: (CTE query string, CTE name, list of metrics)

    """
    cte_template = sql_generator.env.get_template(
        "snowflake_columns_cte_template.sql.j2"
    )

    type_category = f"{col_name}"
    metrics_templates_df = metrics_templates[
        (metrics_templates[TYPE_COLUMN_KEY] == col_type.upper())
    ]
    metrics = {}
    for _, row in metrics_templates_df.iterrows():
        metric_name = row[METRIC_COLUMN_KEY]
        if exclude_metrics and metric_name in METRICS_TO_EXCLUDE:
            continue

        metric_query = row[TEMPLATE_COLUMN_KEY].replace(
            COL_NAME_NO_QUOTES_PLACEHOLDER, col_name
        )
        metric_query_normalized = row[NORMALIZATION_COLUMN_KEY].replace(
            METRIC_QUERY_PLACEHOLDER, metric_query
        )
        metrics[metric_name] = metric_query_normalized

    if not metrics:
        LOGGER.warning(
            "No metrics templates found for column type %s in table %s.",
            col_type,
            fully_qualified_name,
        )
        return None, None, None

    cte_query = cte_template.render(
        type_category=type_category,
        metrics=metrics,
        table_name=fully_qualified_name,
        where_clause=where_clause,
        has_where_clause=has_where_clause,
    )

    return cte_query.strip(), type_category, list(metrics.keys())


def generate_outer_query(cte_names, metrics):
    """Generate the outer query that combines the results from all CTEs.

    Args:
        cte_names (list): List of CTE names
        metrics (list): List of available metrics for each CTE

    Returns:
        str: The outer query string

    """
    # Collect all unique metrics across all types
    all_metrics = set()
    for metric_list in metrics:
        all_metrics.update(metric_list)

    union_queries = []

    for cte_name, available_metrics in zip(cte_names, metrics, strict=False):
        # Determine which metrics to include
        metric_clauses = []
        for metric in all_metrics:
            if metric in available_metrics:
                metric_clauses.append(f"TO_VARCHAR({metric}) AS {metric}")
            else:
                metric_clauses.append(f"NULL AS {metric}")

        # Build individual SELECT statement for this CTE
        select_query = f"""SELECT
    '{cte_name}' AS COLUMN_VALIDATED,
    {', '.join(metric_clauses)}
FROM {cte_name}"""

        union_queries.append(select_query)

    # Join all queries with UNION ALL
    outer_query = "\n\nUNION ALL\n\n".join(union_queries)
    return outer_query

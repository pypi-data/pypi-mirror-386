import pandas as pd
from functools import partial

from ..analysis import get_all_parent_go_terms


def parse_uniprot_mapping_results(
        uniprot_df: pd.DataFrame,
        protein_groups: list[str],
        special_column_aggregation_rules: dict = None,
):
    """
    params:
    uniprot_df: Dataframe of metadata from the UniProt ID mapper.
    protein_groups: List of strings, with protein groups, semicolon separated if they have multiple UniProt IDs in the group.

    returns:
    A new protein metadata table with rows combined according to the protein grouping.

    This function does not automatically retrieve UniProt metadata through an API,
        although this is an option if you trust their python code (see https://www.uniprot.org/help/id_mapping_prog).
    This function is only to simplify the process of combining rows when multiple UniProt IDs
        map to one protein group.

    First step is to parse out all UniProt IDs from the protein grouping results:
    Some will be semicolon separated, so treat each as individual uniprot.
    Example:

    uniprot_ids = set()
    for pg in YOUR_LIST_OF_PROTEIN_GROUPS:
        for uniprot_id in pg.split(';'):
            uniprot_ids.add(uniprot_id)
    # Write the UniProt IDs to your clipboard
    pd.Series(list(uniprot_ids)).to_clipboard(index=False)

    # Go to https://www.uniprot.org/id-mapping
    Let the mapping run (takes 1-2 minutes) and download all the results with the metadata columns you want.

    This code also includes the GO term hierarchy completion (see bja_utils.analysis.get_all_parent_go_terms)
        and puts all resulting GO terms in a column titled "all_GO_ids"
    """

    if special_column_aggregation_rules is not None:
        raise NotImplementedError

    # The pandas groupby .agg() method expects a dictionary of {'column name': callable function or lambda}
    # Because this needs to be callable, we define the row_sep and out_sep using a functools partial
    column_agg_rules = {
        'Protein names': _deduplicate_across_rows,
        'Gene Names': partial(_deduplicate_across_rows, row_sep=" ", out_sep=";"),
        'Gene Ontology IDs': partial(_deduplicate_across_rows, row_sep="; ", out_sep=";"),
        'Gene Names (primary)': _deduplicate_across_rows
    }

    # Make a mapping of individual_uniprot_id: associated_protein_group from the list of protein_groups
    upid_to_pg_map = {}
    for pg in protein_groups:
        for upid in pg.split(';'):
            upid_to_pg_map[upid] = pg

    uniprot_df['proteingroup'] = uniprot_df['From'].map(upid_to_pg_map)

    columns_to_keep = list(column_agg_rules.keys())

    newdf = uniprot_df.groupby('proteingroup')[columns_to_keep].agg(column_agg_rules)

    all_go_ids = get_all_parent_go_terms(newdf, 'Gene Ontology IDs')
    newdf = newdf.join(all_go_ids)

    return newdf


def _deduplicate_across_rows(values, row_sep=" ", out_sep="; "):
    """
    Deduplicate words separated by `row_sep` across rows, then join the final list of de-duplicated
    words across the rows using `out_sep`.

    This is used for cleaning up results from UniProt when the protein group contains multiple
    UniProt IDs, and some info is duplicated across several UniProt ID rows.
    """
    seen = set()
    tokens = []
    for val in values.dropna():
        for part in val.split(row_sep):
            if part and part not in seen:
                seen.add(part)
                tokens.append(part)
    return out_sep.join(tokens)

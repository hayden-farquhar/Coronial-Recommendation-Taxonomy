"""Shared data rules for the revised analyses (v1.1.0).

Imported by 06/07 (with --r1) and by 10_r1_practice_comparison.py. Keeps the three scripts on one definition of
the corpus, the response linkage and the compliance outcome.

- Corpus: the v2.5 classified file, de-duplicated on case_id. Two Victorian findings
  (vic/VicCorC/2015/1 and /2) appear twice with identical text in the upstream corpus;
  the deposited classification file is left unchanged and the duplicates are dropped here.
- Responses: upstream v2 linkage (data/interim_v2), agency-response definition
  (`has_response`, i.e. response_status == agency_response).
- Compliance: per-finding majority-rule code (`finding_classification`) from the
  validated LLM labels.
"""
import os
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Upstream v2 linkage, reduced to the columns used here (case_id, has_response, finding_classification;
# no text). Set UPSTREAM_LINKED_V2_CSV to use the full upstream findings_responses_linked.csv instead.
UPSTREAM_LINKED_V2 = Path(os.environ.get('UPSTREAM_LINKED_V2_CSV', PROJECT_ROOT / 'data' / 'r1_response_linkage.csv'))
# Upstream response-collection windows (first and last year of a published response, by jurisdiction)
UPSTREAM_WINDOWS = PROJECT_ROOT / 'data' / 'response_coverage_window.csv'

R1_FIG_DIR = PROJECT_ROOT / 'outputs' / 'figures' / 'r1'
R1_TAB_DIR = PROJECT_ROOT / 'outputs' / 'tables' / 'r1'

RESPONSE_COL = 'has_response'
COMPLIANCE_COL = 'finding_classification'


def load_classified():
    df = pd.read_parquet(PROJECT_ROOT / 'data' / 'recommendations_v2.5_classified.no_text.parquet')
    n_raw = len(df)
    df = df.drop_duplicates(subset='case_id', keep='first').reset_index(drop=True)
    print(f'Classified corpus: {n_raw:,} rows, {n_raw - len(df)} duplicate case_id rows dropped -> {len(df):,}')
    return df


def load_upstream_linked():
    upstream = pd.read_csv(UPSTREAM_LINKED_V2)
    return upstream.drop_duplicates(subset='case_id', keep='first')[['case_id', RESPONSE_COL, COMPLIANCE_COL]]


def catchall_mask(df):
    return ((df['theme'] == 'THEME-OTHER') & (df['mechanism'] == 'MECH-OTHER') &
            (df['addressee'] == 'ADDR-UNSPEC') & (df['specificity'] == 'SPEC-1') &
            (df['scope'] == 'SCOPE-IND'))

"""Shape B pre-registered analyses, sections A-E.

Pre-registered under OSF DOI 10.17605/OSF.IO/NEX85 (CC-BY 4.0).
Run after corpus classification via Opus v2.5 → `data/au/recommendations_v2.5_classified.parquet`.

Outputs:
- outputs/figures/shape_b/  — figures (PNG)
- outputs/tables/shape_b/   — tables (CSV)

Sections:
- A. Single-axis distributions (12 figures already aggregated; saved as 5 here)
- B. Axis × jurisdiction (5 heatmaps + 5 χ² tests + Cramér's V + BH-FDR correction)
- C. Axis × year-bin (5 line charts; year-bin = pre-2010 / 2010-2019 / 2020+)
- D. Two-axis cross-tabs (6 heatmaps: mech×addr, theme×mech, theme×addr, spec×mech, spec×addr, scope×theme)
- E. Three-axis modal configurations (top-5 theme×mech×addr triples per jurisdiction)
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency
from statsmodels.stats.multitest import multipletests
import collections

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = PROJECT_ROOT / 'outputs' / 'figures' / 'shape_b'
TAB_DIR = PROJECT_ROOT / 'outputs' / 'tables' / 'shape_b'

AXES = ['theme', 'mechanism', 'addressee', 'specificity', 'scope']
CANONICAL_ORDER = {
    'theme': ['THEME-MH','THEME-CUST','THEME-MED','THEME-RTA','THEME-DV','THEME-DRUG',
              'THEME-CHILD','THEME-WORK','THEME-REC','THEME-FIRE','THEME-PROD','THEME-OTHER'],
    'mechanism': ['MECH-LEG','MECH-INFRA','MECH-FUND','MECH-INV','MECH-PROC','MECH-OTHER'],
    'addressee': ['ADDR-DEPT-NAMED','ADDR-DEPT-GENERIC','ADDR-HEALTH','ADDR-REG','ADDR-PROF',
                  'ADDR-POLICE','ADDR-COURT','ADDR-PRIVATE','ADDR-UNSPEC'],
    'specificity': ['SPEC-1','SPEC-2'],
    'scope': ['SCOPE-IND','SCOPE-SYS','SCOPE-MIX'],
}
JURISDICTION_ORDER = ['NSW','VIC','QLD','WA','SA','TAS','NT','ACT']  # by population


def year_bin(y):
    if y < 2010: return 'pre-2010'
    if y < 2020: return '2010-2019'
    return '2020+'


def cramers_v(chi2, n, contingency_shape):
    r, c = contingency_shape
    return float(np.sqrt(chi2 / (n * (min(r, c) - 1)))) if min(r, c) > 1 else float('nan')


def main():
    df = pd.read_parquet(PROJECT_ROOT / 'data' / 'au' / 'recommendations_v2.5_classified.parquet')
    df['year_bin'] = df['year'].apply(year_bin)
    print(f'Loaded {len(df):,} classified rows')
    print(f'Year bins: {df["year_bin"].value_counts().to_dict()}')

    # --- A. Single-axis distributions
    print('\n=== Section A: Single-axis distributions ===')
    for axis in AXES:
        order = CANONICAL_ORDER[axis]
        counts = df[axis].value_counts().reindex(order, fill_value=0)
        pct = (counts / counts.sum() * 100).round(2)
        out = pd.DataFrame({'count': counts, 'percent': pct})
        out.to_csv(TAB_DIR / f'A_{axis}_distribution.csv')
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.barh(range(len(counts)), counts, color=sns.color_palette('viridis', len(counts)))
        ax.set_yticks(range(len(counts)))
        ax.set_yticklabels(counts.index, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel('Count')
        ax.set_title(f'Distribution of {axis.title()} (n={len(df):,})')
        for i, (cnt, p) in enumerate(zip(counts, pct)):
            ax.text(cnt + max(counts) * 0.01, i, f'{cnt} ({p}%)', va='center', fontsize=8)
        plt.tight_layout()
        plt.savefig(FIG_DIR / f'A_{axis}_distribution.png', dpi=150)
        plt.close(fig)
    print('  A: 5 distribution figures + 5 tables saved')

    # --- B. Axis × jurisdiction (heatmap + χ² + Cramér's V + BH-FDR)
    print('\n=== Section B: Axis × jurisdiction (χ² + Cramér\'s V + BH-FDR) ===')
    chi2_results = []
    for axis in AXES:
        order = CANONICAL_ORDER[axis]
        ct = pd.crosstab(df['jurisdiction'], df[axis]).reindex(index=JURISDICTION_ORDER, columns=order, fill_value=0)
        ct.to_csv(TAB_DIR / f'B_{axis}_by_jurisdiction.csv')
        # χ²
        chi2, p, dof, exp = chi2_contingency(ct.values)
        v = cramers_v(chi2, ct.values.sum(), ct.shape)
        chi2_results.append({'axis': axis, 'chi2': chi2, 'dof': dof, 'p_raw': p, 'cramers_v': v, 'n': ct.values.sum()})
        # Heatmap (row-normalised — % within jurisdiction)
        row_norm = ct.div(ct.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots(figsize=(max(8, len(order)*0.7), 4.5))
        sns.heatmap(row_norm, annot=True, fmt='.1f', cmap='viridis', ax=ax, cbar_kws={'label': '% within jurisdiction'})
        ax.set_title(f'{axis.title()} by jurisdiction (row-normalised %, n={ct.values.sum():,})')
        ax.set_xlabel(axis.title())
        ax.set_ylabel('Jurisdiction')
        plt.tight_layout()
        plt.savefig(FIG_DIR / f'B_{axis}_by_jurisdiction.png', dpi=150)
        plt.close(fig)
    # BH-FDR correction across all χ²
    chi2_df = pd.DataFrame(chi2_results)
    chi2_df['p_bh_adj'] = multipletests(chi2_df['p_raw'], method='fdr_bh')[1]
    chi2_df['reject_bh_0.05'] = chi2_df['p_bh_adj'] < 0.05
    chi2_df.to_csv(TAB_DIR / 'B_chi2_axis_by_jurisdiction.csv', index=False)
    print(f'  B: 5 heatmaps + 5 tables + χ² results saved')
    print('  χ² results (p_bh_adj):')
    for r in chi2_results:
        adj = chi2_df.loc[chi2_df['axis']==r['axis'], 'p_bh_adj'].iloc[0]
        print(f'    {r["axis"]:12s} χ²={r["chi2"]:.1f}, dof={r["dof"]}, p_raw={r["p_raw"]:.2e}, p_bh={adj:.2e}, Cramer V={r["cramers_v"]:.3f}')

    # --- C. Axis × year-bin
    print('\n=== Section C: Axis × year-bin ===')
    year_order = ['pre-2010', '2010-2019', '2020+']
    for axis in AXES:
        order = CANONICAL_ORDER[axis]
        ct = pd.crosstab(df['year_bin'], df[axis]).reindex(index=year_order, columns=order, fill_value=0)
        ct.to_csv(TAB_DIR / f'C_{axis}_by_year_bin.csv')
        row_norm = ct.div(ct.sum(axis=1), axis=0) * 100
        # Stacked-bar visualisation
        fig, ax = plt.subplots(figsize=(max(8, len(order)*0.6), 4))
        row_norm.T.plot(kind='bar', ax=ax, color=sns.color_palette('plasma', 3))
        ax.set_title(f'{axis.title()} composition by year-bin (% within year-bin)')
        ax.set_xlabel(axis.title())
        ax.set_ylabel('% within year-bin')
        ax.legend(title='Year bin', loc='upper right')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(FIG_DIR / f'C_{axis}_by_year_bin.png', dpi=150)
        plt.close(fig)
    print('  C: 5 figures + 5 tables saved')

    # --- D. Two-axis cross-tabs
    print('\n=== Section D: Two-axis cross-tabs ===')
    cross_pairs = [
        ('mechanism', 'addressee'),
        ('theme', 'mechanism'),
        ('theme', 'addressee'),
        ('specificity', 'mechanism'),
        ('specificity', 'addressee'),
        ('scope', 'theme'),
    ]
    for rows, cols in cross_pairs:
        rorder = CANONICAL_ORDER[rows]
        corder = CANONICAL_ORDER[cols]
        ct = pd.crosstab(df[rows], df[cols]).reindex(index=rorder, columns=corder, fill_value=0)
        ct.to_csv(TAB_DIR / f'D_{rows}_x_{cols}.csv')
        fig, ax = plt.subplots(figsize=(max(8, len(corder)*0.7), max(4, len(rorder)*0.5)))
        sns.heatmap(ct, annot=True, fmt='d', cmap='viridis', ax=ax)
        ax.set_title(f'{rows.title()} × {cols.title()} (counts)')
        ax.set_xlabel(cols.title())
        ax.set_ylabel(rows.title())
        plt.tight_layout()
        plt.savefig(FIG_DIR / f'D_{rows}_x_{cols}.png', dpi=150)
        plt.close(fig)
    print(f'  D: {len(cross_pairs)} heatmaps + tables saved')

    # --- E. Three-axis modal configurations (top-5 theme×mech×addr triples per jurisdiction)
    print('\n=== Section E: Three-axis modal configurations ===')
    # Exclude catchall rows from this analysis (they would dominate)
    non_catchall = df[~(
        (df['theme'] == 'THEME-OTHER') & (df['mechanism'] == 'MECH-OTHER') &
        (df['addressee'] == 'ADDR-UNSPEC') & (df['specificity'] == 'SPEC-1') & (df['scope'] == 'SCOPE-IND')
    )].copy()
    print(f'  E: non-catchall n={len(non_catchall)} (excluding {len(df)-len(non_catchall)} catchall)')
    non_catchall['config'] = non_catchall['theme'].str.replace('THEME-', '') + ' × ' + \
                              non_catchall['mechanism'].str.replace('MECH-', '') + ' × ' + \
                              non_catchall['addressee'].str.replace('ADDR-', '')

    # Top-5 configs per jurisdiction
    rows_out = []
    for j in JURISDICTION_ORDER:
        sub = non_catchall[non_catchall['jurisdiction'] == j]
        if len(sub) == 0: continue
        top5 = sub['config'].value_counts().head(5)
        for rank, (config, n) in enumerate(top5.items(), 1):
            rows_out.append({'jurisdiction': j, 'rank': rank, 'configuration': config, 'count': n,
                            'pct_within_jurisdiction': round(100*n/len(sub), 1)})
    top5_df = pd.DataFrame(rows_out)
    top5_df.to_csv(TAB_DIR / 'E_top5_configurations_by_jurisdiction.csv', index=False)

    # Visualisation: heatmap of top-5 configs across jurisdictions (long-form)
    fig, ax = plt.subplots(figsize=(14, 8))
    pivot = top5_df.pivot_table(index='configuration', columns='jurisdiction', values='count', fill_value=0).astype(int)
    pivot = pivot[[j for j in JURISDICTION_ORDER if j in pivot.columns]]
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    sns.heatmap(pivot, annot=True, fmt='d', cmap='viridis', ax=ax)
    ax.set_title('Top-5 modal Theme × Mechanism × Addressee configurations by jurisdiction\n(non-catchall recommendations only)')
    ax.set_xlabel('Jurisdiction')
    ax.set_ylabel('Configuration (theme × mechanism × addressee)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'E_top5_configurations_by_jurisdiction.png', dpi=150)
    plt.close(fig)

    # Overall top-10 configurations
    overall_top10 = non_catchall['config'].value_counts().head(10)
    overall_top10.to_csv(TAB_DIR / 'E_top10_configurations_overall.csv', header=['count'])
    fig, ax = plt.subplots(figsize=(10, 5))
    overall_top10.sort_values().plot(kind='barh', ax=ax, color=sns.color_palette('viridis', 10))
    ax.set_title(f'Top-10 overall configurations (non-catchall n={len(non_catchall):,})')
    ax.set_xlabel('Count')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'E_top10_configurations_overall.png', dpi=150)
    plt.close(fig)
    print(f'  E: 2 figures + 2 tables saved')

    print('\n=== Sections A-E complete ===')
    print(f'Figures: {len(list(FIG_DIR.glob("*.png")))}')
    print(f'Tables: {len(list(TAB_DIR.glob("*.csv")))}')


if __name__ == '__main__':
    main()

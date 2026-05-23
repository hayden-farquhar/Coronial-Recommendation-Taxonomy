"""Shape B pre-registered analyses, sections F-G.

Section F: Compliance descriptive (joining the upstream pipeline's findings_responses_linked.csv).
Section G: Methodological appendix (held-out IRR table + LLM-IRR diagnostic patterns reference).

Pre-registered under OSF DOI 10.17605/OSF.IO/NEX85 (CC-BY 4.0).
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = PROJECT_ROOT / 'outputs' / 'figures' / 'shape_b'
TAB_DIR = PROJECT_ROOT / 'outputs' / 'tables' / 'shape_b'
UPSTREAM_LINKED = Path(__import__('os').environ.get('UPSTREAM_LINKED_CSV', PROJECT_ROOT / 'data' / 'findings_responses_linked.csv'))

CANONICAL_ORDER = {
    'mechanism': ['MECH-LEG','MECH-INFRA','MECH-FUND','MECH-INV','MECH-PROC','MECH-OTHER'],
    'addressee': ['ADDR-DEPT-NAMED','ADDR-DEPT-GENERIC','ADDR-HEALTH','ADDR-REG','ADDR-PROF',
                  'ADDR-POLICE','ADDR-COURT','ADDR-PRIVATE','ADDR-UNSPEC'],
    'specificity': ['SPEC-1','SPEC-2'],
    'scope': ['SCOPE-IND','SCOPE-SYS','SCOPE-MIX'],
}
COMPLIANCE_ORDER = ['implemented', 'already_implemented', 'partially_accepted', 'under_consideration',
                    'noted', 'not_supported', 'unclassifiable']


def main():
    df = pd.read_parquet(PROJECT_ROOT / 'data' / 'au' / 'recommendations_v2.5_classified.parquet')
    upstream_linked = pd.read_csv(UPSTREAM_LINKED)
    print(f'Classified corpus: {len(df):,} rows')
    print(f'the upstream pipeline linked:     {len(upstream_linked):,} rows')

    # Join on case_id, keep only one the upstream pipeline row per case (the upstream pipeline has 10,018 rows incl. cases with no recommendations)
    p10_unique = upstream_linked.drop_duplicates(subset='case_id', keep='first')[['case_id', 'has_response', 'dominant_classification']]
    merged = df.merge(p10_unique, on='case_id', how='left')
    print(f'After join: {len(merged):,} rows (expected = classified row count, no row inflation)')

    # Exclude catchall rows
    catchall_mask = ((merged['theme']=='THEME-OTHER') & (merged['mechanism']=='MECH-OTHER') &
                     (merged['addressee']=='ADDR-UNSPEC') & (merged['specificity']=='SPEC-1') &
                     (merged['scope']=='SCOPE-IND'))
    non_catchall = merged[~catchall_mask].copy()
    print(f'Non-catchall: {len(non_catchall):,}')
    print(f'  with the upstream pipeline response data: {(non_catchall["has_response"]==True).sum()}')
    print(f'  unclassifiable (VIC cover-page stubs etc.): {(non_catchall["dominant_classification"]=="unclassifiable").sum()}')

    # Substantive compliance analysis uses only rows with a non-unclassifiable response
    substantive = non_catchall[(non_catchall['has_response']==True) & (non_catchall['dominant_classification'].notna()) &
                                (non_catchall['dominant_classification']!='unclassifiable')].copy()
    print(f'  substantive (response present + classifiable): {len(substantive):,}')

    # Also report on the broader "has any response" pool — uses unclassifiable as a separate category
    with_response = non_catchall[(non_catchall['has_response']==True) & (non_catchall['dominant_classification'].notna())].copy()
    print(f'  any-response pool incl. unclassifiable: {len(with_response):,}')

    print()
    print('=== Section F: Compliance descriptive ===')
    print(f'  Compliance distribution (substantive, n={len(substantive)}):')
    print(f'    {substantive["dominant_classification"].value_counts().to_dict()}')

    # F1-F4: compliance × {mechanism, addressee, specificity, scope}
    F_axes = ['mechanism', 'addressee', 'specificity', 'scope']
    chi2_results = []
    for axis in F_axes:
        order = CANONICAL_ORDER[axis]
        compl_order = [c for c in COMPLIANCE_ORDER if c in substantive['dominant_classification'].unique() and c != 'unclassifiable']
        # Use only non-OTHER mechanism for analysis; OTHER includes catchall-adjacent
        if axis == 'mechanism':
            order_clean = [o for o in order if o != 'MECH-OTHER']
            sub = substantive[substantive[axis].isin(order_clean)]
        elif axis == 'addressee':
            order_clean = [o for o in order if o != 'ADDR-UNSPEC']
            sub = substantive[substantive[axis].isin(order_clean)]
        else:
            order_clean = order
            sub = substantive
        ct = pd.crosstab(sub[axis], sub['dominant_classification']).reindex(index=order_clean, columns=compl_order, fill_value=0)
        ct.to_csv(TAB_DIR / f'F_compliance_by_{axis}.csv')
        # χ² descriptive — drop all-zero rows/cols before testing
        ct_chi = ct.loc[ct.sum(axis=1) > 0, ct.sum(axis=0) > 0]
        if ct_chi.shape[0] >= 2 and ct_chi.shape[1] >= 2 and ct_chi.values.sum() > 0:
            try:
                chi2, p, dof, exp = chi2_contingency(ct_chi.values)
                chi2_results.append({'axis': axis, 'n': int(ct_chi.values.sum()), 'chi2': chi2, 'dof': dof, 'p': p,
                                    'cramers_v': float(np.sqrt(chi2 / (ct_chi.values.sum() * (min(ct_chi.shape) - 1)))),
                                    'note': f'shape {ct_chi.shape[0]}x{ct_chi.shape[1]} after dropping all-zero rows/cols'})
            except ValueError as e:
                chi2_results.append({'axis': axis, 'n': int(ct_chi.values.sum()), 'chi2': None, 'dof': None, 'p': None,
                                    'cramers_v': None, 'note': f'χ² failed: {e}'})
        # Row-normalised heatmap (% within axis category)
        row_norm = ct.div(ct.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots(figsize=(max(9, len(compl_order)*1.0), max(4, len(order_clean)*0.5)))
        sns.heatmap(row_norm, annot=True, fmt='.1f', cmap='viridis', ax=ax,
                    cbar_kws={'label': '% compliance outcome within axis category'})
        ax.set_title(f'Compliance × {axis.title()} (row-normalised %; n={ct.values.sum():,} responses)')
        ax.set_xlabel('Dominant classification')
        ax.set_ylabel(axis.title())
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
        plt.tight_layout()
        plt.savefig(FIG_DIR / f'F_compliance_by_{axis}.png', dpi=150)
        plt.close(fig)
    pd.DataFrame(chi2_results).to_csv(TAB_DIR / 'F_chi2_compliance.csv', index=False)
    print(f'  F: 4 heatmaps + 4 cross-tabs + chi-square table saved')
    for r in chi2_results:
        print(f'    compliance × {r["axis"]:12s} n={r["n"]:4d}  χ²={r["chi2"]:6.1f} dof={r["dof"]:3d} p={r["p"]:.3e} V={r["cramers_v"]:.3f}')

    # Response-presence rate by axis (how often does a recommendation type even receive a response?)
    print()
    print('Response-presence rate by axis category:')
    response_rate_rows = []
    for axis in F_axes + ['theme', 'jurisdiction']:
        if axis == 'jurisdiction':
            order_clean = ['NSW','VIC','QLD','WA','SA','TAS','NT','ACT']
        elif axis == 'theme':
            order_clean = ['THEME-MH','THEME-CUST','THEME-MED','THEME-RTA','THEME-DV','THEME-DRUG',
                           'THEME-CHILD','THEME-WORK','THEME-REC','THEME-FIRE','THEME-PROD']  # excl OTHER
        else:
            order_clean = [o for o in CANONICAL_ORDER[axis] if not (o.endswith('OTHER') or o.endswith('UNSPEC'))]
        for cat in order_clean:
            sub = non_catchall[non_catchall[axis] == cat] if axis != 'jurisdiction' else non_catchall[non_catchall['jurisdiction']==cat]
            if len(sub) == 0: continue
            n_resp = (sub['has_response']==True).sum()
            response_rate_rows.append({'axis': axis, 'category': cat, 'n_total': len(sub), 'n_response': int(n_resp),
                                       'response_rate_pct': round(100*n_resp/len(sub), 1)})
    pd.DataFrame(response_rate_rows).to_csv(TAB_DIR / 'F_response_presence_rate.csv', index=False)
    print(f'  Response presence rate table saved (axes: theme, mechanism, addressee, specificity, scope, jurisdiction)')

    # --- Section G: Methodological appendix
    print('\n=== Section G: Methodological appendix ===')
    # G1: Held-out IRR table (already at outputs/tables/irr_heldout_v2.5.csv)
    irr_heldout = pd.read_csv(PROJECT_ROOT / 'outputs' / 'tables' / 'irr_heldout_v2.5.csv')
    irr_dev = pd.read_csv(PROJECT_ROOT / 'outputs' / 'tables' / 'irr_final_v2.5.csv')
    # Combined IRR summary table
    combined = pd.concat([
        irr_dev.assign(provenance='development_sample'),
        irr_heldout.assign(provenance='held_out_seed878'),
    ], ignore_index=True)
    combined.to_csv(TAB_DIR / 'G_irr_summary_combined.csv', index=False)
    print(f'  G: combined IRR table saved ({len(combined)} rows)')
    # Visual: held-out vs development α by axis
    fig, ax = plt.subplots(figsize=(9, 5))
    # Average development α by axis (across the two development samples)
    dev_avg = irr_dev.groupby('axis')['krippendorff_alpha'].mean().reset_index()
    held = irr_heldout[['axis', 'krippendorff_alpha']]
    axes_order = ['theme','mechanism','addressee','specificity','scope']
    dev_vals = [dev_avg[dev_avg['axis']==a]['krippendorff_alpha'].iloc[0] if (dev_avg['axis']==a).any() else None for a in axes_order]
    held_vals = [held[held['axis']==a]['krippendorff_alpha'].iloc[0] if (held['axis']==a).any() else None for a in axes_order]
    x = np.arange(len(axes_order))
    w = 0.35
    ax.bar(x - w/2, [v if v is not None else 0 for v in dev_vals], w, label='Development sample (mean of 2)', color='#4c72b0')
    ax.bar(x + w/2, [v if v is not None else 0 for v in held_vals], w, label='Held-out sample (seed 878)', color='#dd8452')
    ax.axhline(0.80, color='green', linestyle='--', alpha=0.6, label='Reliable threshold (α=0.80)')
    ax.axhline(0.67, color='orange', linestyle='--', alpha=0.6, label='Tentative threshold (α=0.67)')
    ax.set_xticks(x)
    ax.set_xticklabels(axes_order)
    ax.set_ylabel("Krippendorff's α")
    ax.set_title("Inter-rater reliability: development vs held-out samples (v2.5 codebook)")
    ax.legend(loc='lower right', fontsize=9)
    ax.set_ylim(-0.3, 1.05)
    for i, (d, h) in enumerate(zip(dev_vals, held_vals)):
        if d is not None: ax.text(i-w/2, d+0.02, f'{d:.2f}', ha='center', fontsize=8)
        if h is not None: ax.text(i+w/2, h+0.02, f'{h:.2f}', ha='center', fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'G_irr_development_vs_heldout.png', dpi=150)
    plt.close(fig)
    print(f'  G: IRR comparison figure saved')

    print('\n=== Sections F-G complete ===')
    print(f'Total Shape B figures: {len(list(FIG_DIR.glob("*.png")))}')
    print(f'Total Shape B tables:  {len(list(TAB_DIR.glob("*.csv")))}')


if __name__ == '__main__':
    main()

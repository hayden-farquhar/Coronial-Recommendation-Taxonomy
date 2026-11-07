"""Revised analyses (v1.1.0): jurisdictional practice comparison, coverage values and manuscript Figures 1-3.

Computes every number the revised manuscript reports for specificity and documented-response
coverage by jurisdiction (Table 3 columns, §3.3-§3.5, §4.3-§4.4, abstract and key messages)
and regenerates Figures 1-3. Data rules (de-duplicated corpus, upstream v2
linkage, agency-response definition) are in r1_data.py.

The coverage-by-route comparison, the specificity-coverage correlation and the collection-window
sensitivity analysis are post-hoc. Collection windows are read from the upstream table
(data/response_coverage_window.csv): AustLII's response collections cover different years in each
jurisdiction, so coverage is also computed for recommendations made between the first year of the
jurisdiction's collection and the earlier of its last year or 2023 (time to respond).

Outputs:
- outputs/tables/r1/practice_by_jurisdiction.csv  (Table 3 numeric columns)
- outputs/tables/r1/practice_values.csv           (every reported scalar, keyed)
- outputs/tables/r1/coverage_window_by_jurisdiction.csv  (collection-window sensitivity analysis; S5 Table F8)
- outputs/tables/r1/compliance_permutation.csv    (Monte Carlo check of the analysis F chi-square tests,
                                                    run 07_shape_b_analyses_FG.py --r1 first; several cells have expected counts < 5)
- outputs/figures/r1/manuscript/Figure{1,2,3}_*.{pdf,png}
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401  (registers the 'science' styles)
from scipy.stats import spearmanr, pearsonr, chi2_contingency
from statsmodels.stats.proportion import proportion_confint

import r1_data

# Okabe-Ito colourblind-safe palette
OKABE_ITO = {'black': '#000000', 'blue': '#0072B2', 'vermil': '#D55E00', 'grey': '#999999'}

# Outputs are written relative to the repository root
os.chdir(r1_data.PROJECT_ROOT)
TAB_DIR = r1_data.R1_TAB_DIR.relative_to(r1_data.PROJECT_ROOT)
FIG_DIR = r1_data.R1_FIG_DIR.relative_to(r1_data.PROJECT_ROOT) / 'manuscript'
TAB_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

JURISDICTIONS = ['NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'NT', 'ACT']
NOT_OBSERVABLE = ['ACT']  # AustLII holds no ACT response collection
# Route through which responses are published (Table 3; supplementary S9)
ROUTE = {'VIC': 'online', 'NSW': 'online', 'QLD': 'online', 'WA': 'online',
         'SA': 'parliament', 'ACT': 'parliament', 'NT': 'parliament', 'TAS': 'none'}
ROUTE_LABEL = {'online': 'Published online with findings or in a register',
               'parliament': 'Tabled in Parliament',
               'none': 'No publication mechanism'}
ROUTE_COLOUR = {'online': OKABE_ITO['blue'], 'parliament': OKABE_ITO['vermil'], 'none': OKABE_ITO['grey']}
ROUTE_MARKER = {'online': 'o', 'parliament': 's', 'none': '^'}
QLD_PUBLICATION_YEAR = 2013
UPSTREAM_WINDOWS = r1_data.UPSTREAM_WINDOWS
WINDOW_CUTOFF = 2023  # same cutoff as the upstream co-primary measure
LABEL_OFFSET = {'TAS': (-7, -9, 'right')}  # Figure 3: keep TAS clear of the SA marker  # responses published next to findings from 2013

plt.style.use(['science', 'nature', 'no-latex'])
plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42, 'font.size': 8,
                     'axes.labelsize': 8, 'xtick.labelsize': 7, 'ytick.labelsize': 7})


def pct(k, n):
    return round(100 * k / n, 1) if n else float('nan')


def wilson(k, n):
    lo, hi = proportion_confint(k, n, method='wilson')
    return round(100 * lo, 1), round(100 * hi, 1)


def load_windows():
    w = pd.read_csv(UPSTREAM_WINDOWS)
    w = w[w.jurisdiction.isin(JURISDICTIONS)]
    return {r.jurisdiction: (int(r.response_db_first), min(int(r.response_db_last), WINDOW_CUTOFF))
            for r in w.itertuples()}


def main():
    df = r1_data.load_classified()
    upstream = r1_data.load_upstream_linked()
    resp = r1_data.RESPONSE_COL

    nc = df[~r1_data.catchall_mask(df)].merge(upstream, on='case_id', how='left')
    assert len(nc) == (~r1_data.catchall_mask(df)).sum(), 'join inflated rows'
    nc['responded'] = nc[resp] == True  # noqa: E712  (NaN = no linked record)
    print(f'Non-catchall: {len(nc):,}; with documented response: {nc.responded.sum():,}')
    windows = load_windows()
    nc['in_window'] = [j in windows and windows[j][0] <= y <= windows[j][1]
                       for j, y in zip(nc.jurisdiction, nc.year)]

    # --- Per-jurisdiction specificity (all classified rows) and coverage (non-catchall rows)
    rows = []
    for j in JURISDICTIONS:
        dj = df[df.jurisdiction == j]
        cj = nc[nc.jurisdiction == j]
        spec_k = int((dj.specificity == 'SPEC-2').sum())
        cov_k = int(cj.responded.sum())
        observable = j not in NOT_OBSERVABLE
        wj = cj[cj.in_window]
        win_k = int(wj.responded.sum())
        lo, hi = wilson(win_k, len(wj)) if observable else (None, None)
        rows.append({'jurisdiction': j, 'route': ROUTE[j], 'observable': observable,
                     'n_classified': len(dj), 'spec2_k': spec_k, 'spec2_pct': pct(spec_k, len(dj)),
                     'n_noncatchall': len(cj), 'coverage_k': cov_k if observable else None,
                     'coverage_pct': pct(cov_k, len(cj)) if observable else None,
                     'window': f'{windows[j][0]}-{windows[j][1]}' if observable else None,
                     'n_window': len(wj) if observable else None,
                     'coverage_window_k': win_k if observable else None,
                     'coverage_window_pct': pct(win_k, len(wj)) if observable else None,
                     'coverage_window_ci_lo': lo, 'coverage_window_ci_hi': hi})
    by_j = pd.DataFrame(rows)
    by_j.to_csv(TAB_DIR / 'practice_by_jurisdiction.csv', index=False)
    o = by_j[by_j.observable]
    pd.DataFrame({'jurisdiction': o.jurisdiction, 'collection_years': o.window,
                  'n_window': o.n_window.astype(int), 'with_response_window': o.coverage_window_k.astype(int),
                  'coverage_window_pct': o.coverage_window_pct,
                  'ci95_wilson': [f'{lo:.1f} to {hi:.1f}' for lo, hi in zip(o.coverage_window_ci_lo, o.coverage_window_ci_hi)],
                  'n_all_years': o.n_noncatchall, 'with_response_all_years': o.coverage_k.astype(int),
                  'coverage_all_years_pct': o.coverage_pct}).to_csv(
        TAB_DIR / 'coverage_window_by_jurisdiction.csv', index=False)
    print(by_j.to_string(index=False))

    # --- Scalars reported in the text
    values = []

    def put(key, k, n, note=''):
        values.append({'key': key, 'k': k, 'n': n, 'pct': pct(k, n), 'stat': None, 'p': None, 'note': note})

    obs = nc[~nc.jurisdiction.isin(NOT_OBSERVABLE)]
    put('n_classified', len(df), len(df), 'de-duplicated corpus')
    put('spec2_corpus', int((df.specificity == 'SPEC-2').sum()), len(df), 'Figure 1 reference line')
    put('coverage_observable7', int(obs.responded.sum()), len(obs))
    online = obs[obs.jurisdiction.map(ROUTE) == 'online']
    other = obs[obs.jurisdiction.map(ROUTE) != 'online']
    put('coverage_route_online', int(online.responded.sum()), len(online), 'VIC, NSW, QLD, WA')
    put('coverage_route_parliament_or_none', int(other.responded.sum()), len(other), 'SA, NT, TAS')
    qld = nc[nc.jurisdiction == 'QLD']
    pre, post = qld[qld.year < QLD_PUBLICATION_YEAR], qld[qld.year >= QLD_PUBLICATION_YEAR]
    put('coverage_qld_pre2013', int(pre.responded.sum()), len(pre))
    put('coverage_qld_2013on', int(post.responded.sum()), len(post))
    # Collection-window sensitivity analysis (post-hoc)
    ow, on_w, ot_w = obs[obs.in_window], online[online.in_window], other[other.in_window]
    put('coverage_window_observable7', int(ow.responded.sum()), len(ow))
    put('coverage_window_route_online', int(on_w.responded.sum()), len(on_w), 'VIC, NSW, QLD, WA')
    put('coverage_window_route_parliament_or_none', int(ot_w.responded.sum()), len(ot_w), 'SA, NT, TAS')
    qw = qld[qld.in_window]
    pre_w, post_w = qw[qw.year < QLD_PUBLICATION_YEAR], qw[qw.year >= QLD_PUBLICATION_YEAR]
    put('coverage_window_qld_pre2013', int(pre_w.responded.sum()), len(pre_w))
    put('coverage_window_qld_2013on', int(post_w.responded.sum()), len(post_w))

    o7 = by_j[by_j.observable]
    rho7, p_rho7 = spearmanr(o7.spec2_pct, o7.coverage_pct)
    r7, p_r7 = pearsonr(o7.spec2_pct, o7.coverage_pct)
    # Original-analysis convention, retained for transparency: ACT unobservable coverage as zero
    a8 = by_j.assign(coverage_pct=by_j.coverage_pct.fillna(0.0))
    rho8, p_rho8 = spearmanr(a8.spec2_pct, a8.coverage_pct)
    rho7w, p_rho7w = spearmanr(o7.spec2_pct, o7.coverage_window_pct)
    r7w, p_r7w = pearsonr(o7.spec2_pct, o7.coverage_window_pct)
    for key, s, p, note in [('spearman_rho_7', rho7, p_rho7, 'post-hoc, 7 observable'),
                            ('pearson_r_7', r7, p_r7, 'post-hoc, 7 observable'),
                            ('spearman_rho_8_act_as_zero', rho8, p_rho8, 'ACT as zero, as in the original analysis'),
                            ('spearman_rho_window_7', rho7w, p_rho7w, 'post-hoc, collection windows, 7 observable'),
                            ('pearson_r_window_7', r7w, p_r7w, 'post-hoc, collection windows, 7 observable')]:
        values.append({'key': key, 'k': None, 'n': len(o7) if key.endswith('7') else len(a8),
                       'pct': None, 'stat': round(float(s), 3), 'p': round(float(p), 3), 'note': note})
    vals = pd.DataFrame(values)
    vals.to_csv(TAB_DIR / 'practice_values.csv', index=False)
    print(vals.to_string(index=False))

    compliance_permutation()

    corpus_spec = pct(int((df.specificity == 'SPEC-2').sum()), len(df))
    figure1(by_j, corpus_spec)
    figure2(by_j)
    figure3(o7, (rho7, p_rho7, r7, p_r7), (rho7w, p_rho7w, r7w, p_r7w))


def compliance_permutation(n_perm=20000, seed=878):
    rng = np.random.default_rng(seed)
    out = []
    for axis in ['mechanism', 'addressee', 'specificity', 'scope']:
        ct = pd.read_csv(TAB_DIR / 'shape_b' / f'F_compliance_by_{axis}.csv', index_col=0)
        ct = ct.loc[ct.sum(axis=1) > 0, ct.sum(axis=0) > 0]
        chi2, p, dof, expected = chi2_contingency(ct.values)
        # Permute column labels against fixed row labels (both margins fixed)
        rows = np.repeat(np.arange(ct.shape[0]), ct.sum(axis=1).values)
        cols = np.repeat(np.arange(ct.shape[1]), ct.sum(axis=0).values)
        n_ge = 0
        for _ in range(n_perm):
            m = np.zeros(ct.shape)
            np.add.at(m, (rows, rng.permutation(cols)), 1)
            n_ge += chi2_contingency(m)[0] >= chi2 - 1e-9
        out.append({'axis': axis, 'n': int(ct.values.sum()), 'chi2': round(chi2, 2), 'dof': dof, 'p_asymptotic': p,
                    'p_permutation': (n_ge + 1) / (n_perm + 1), 'cells_expected_lt5': int((expected < 5).sum()),
                    'cells': expected.size})
    out = pd.DataFrame(out)
    out.to_csv(TAB_DIR / 'compliance_permutation.csv', index=False)
    print(out.to_string(index=False))


def _save(fig, stem):
    for ext in ('pdf', 'png'):
        fig.savefig(FIG_DIR / f'{stem}.{ext}', dpi=600, bbox_inches='tight')
    plt.close(fig)


def figure1(by_j, corpus_spec):
    d = by_j.sort_values('spec2_pct')
    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    ax.barh(d.jurisdiction, d.spec2_pct, color=[ROUTE_COLOUR[r] for r in d.route],
            edgecolor='black', linewidth=0.4)
    for y, (v, n) in enumerate(zip(d.spec2_pct, d.n_classified)):
        ax.text(v + 1, y, f'{v:.1f}% (n = {n:,})', va='center', fontsize=7)
    ax.axvline(corpus_spec, color=OKABE_ITO['black'], linestyle='--', linewidth=0.6)
    ax.set_xlim(0, 90)
    ax.set_xlabel('Specific (SPEC-2) recommendations (%)')
    ax.tick_params(axis='y', which='both', length=0)
    _route_legend(ax, loc='lower right', extra=[plt.Line2D([], [], color=OKABE_ITO['black'], linestyle='--',
                                                           linewidth=0.6, label=f'All jurisdictions ({corpus_spec:.1f}%)')])
    _save(fig, 'Figure1_specificity_by_jurisdiction')


def figure2(by_j):
    """Within-window coverage (filled bars) with all-years coverage (open diamonds) for comparison."""
    order = {'online': 0, 'parliament': 1, 'none': 2}
    d = by_j.assign(o=by_j.route.map(order), c=by_j.coverage_window_pct.fillna(-1)).sort_values(
        ['o', 'c'], ascending=[False, True])
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    for y, row in enumerate(d.itertuples()):
        if row.observable:
            ax.barh(y, row.coverage_window_pct, color=ROUTE_COLOUR[row.route], edgecolor='black', linewidth=0.4)
            ax.plot(row.coverage_pct, y, marker='D', markersize=3.5, markerfacecolor='white',
                    markeredgecolor='black', markeredgewidth=0.6, linestyle='', zorder=3)
            x = max(row.coverage_window_pct, row.coverage_pct) + 1.5
            ax.text(x, y, f'{row.coverage_window_pct:.1f}% ({int(row.coverage_window_k)}/{int(row.n_window):,}, '
                          f'{row.window.replace("-", chr(8211))})', va='center', fontsize=6.5)
        else:
            ax.text(1, y, 'Not observable (no response collection)', va='center', fontsize=7, style='italic')
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(d.jurisdiction)
    ax.set_xlim(0, 100)
    ax.set_xlabel('Recommendations with a documented response (%)')
    ax.tick_params(axis='y', which='both', length=0)
    _route_legend(ax, loc='lower right', extra=[plt.Line2D([], [], marker='D', markersize=3.5, linestyle='',
                                                           markerfacecolor='white', markeredgecolor='black',
                                                           markeredgewidth=0.6, label='All years, 1998' + chr(8211) + '2026')])
    _save(fig, 'Figure2_response_coverage_by_jurisdiction')


def figure3(o7, stats_all, stats_win):
    """Filled markers: coverage within collection windows; open markers: all years."""
    fig, ax = plt.subplots(figsize=(4.5, 3.8))
    nmax = o7.n_classified.max()
    for row in o7.itertuples():
        size = 30 + 250 * row.n_classified / nmax
        ax.plot([row.spec2_pct, row.spec2_pct], [row.coverage_pct, row.coverage_window_pct],
                color=ROUTE_COLOUR[row.route], linewidth=0.6, zorder=1)
        ax.scatter(row.spec2_pct, row.coverage_pct, s=size * 0.5, marker=ROUTE_MARKER[row.route],
                   facecolor='white', edgecolor=ROUTE_COLOUR[row.route], linewidth=0.8, zorder=2)
        ax.scatter(row.spec2_pct, row.coverage_window_pct, s=size, marker=ROUTE_MARKER[row.route],
                   color=ROUTE_COLOUR[row.route], edgecolor='black', linewidth=0.4, alpha=0.9, zorder=3)
        dx, dy, ha = LABEL_OFFSET.get(row.jurisdiction, (6, 4, 'left'))
        ax.annotate(row.jurisdiction, (row.spec2_pct, row.coverage_window_pct), xytext=(dx, dy),
                    textcoords='offset points', fontsize=7, ha=ha)
    ax.set_xlim(0, 85)
    ax.set_ylim(0, 80)
    ax.set_xlabel('Specific (SPEC-2) recommendations (%)')
    ax.set_ylabel('Recommendations with a documented response (%)')
    (rho, p_rho, r, p_r), (rho_w, p_rho_w, r_w, p_r_w) = stats_all, stats_win
    ax.text(0.98, 0.03,
            f'Within collection years: $\\rho$ = {rho_w:.2f} (p = {p_rho_w:.3f}); r = {r_w:.2f} (p = {p_r_w:.3f})\n'
            f'All years: $\\rho$ = {rho:.2f} (p = {p_rho:.2f}); r = {r:.2f} (p = {p_r:.2f})\nn = 7 jurisdictions',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=6)
    handles = [plt.Line2D([], [], marker=ROUTE_MARKER[k], linestyle='', markerfacecolor=ROUTE_COLOUR[k],
                          markeredgecolor='black', markeredgewidth=0.4, markersize=5, label=ROUTE_LABEL[k])
               for k in ('online', 'parliament', 'none')]
    handles += [plt.Line2D([], [], marker='o', linestyle='', markerfacecolor='0.4', markeredgecolor='black',
                           markeredgewidth=0.4, markersize=5, label='Within collection years'),
                plt.Line2D([], [], marker='o', linestyle='', markerfacecolor='white', markeredgecolor='0.4',
                           markeredgewidth=0.8, markersize=4, label='All years, 1998' + chr(8211) + '2026')]
    ax.legend(handles=handles, loc='upper left', fontsize=5.8, frameon=False)
    _save(fig, 'Figure3_specificity_vs_response_scatter')


def _route_legend(ax, loc, extra=()):
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=ROUTE_COLOUR[k], edgecolor='black', linewidth=0.4,
                             label=ROUTE_LABEL[k]) for k in ('online', 'parliament', 'none')] + list(extra)
    ax.legend(handles=handles, loc=loc, fontsize=6, frameon=True, framealpha=0.9, edgecolor='none')


if __name__ == '__main__':
    main()

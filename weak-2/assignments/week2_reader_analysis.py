from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent; OUT=HERE.parent/'charts'

def analyze_search_results(path=None):
    """Analyze real, completed participant data; blank templates are rejected."""
    path=Path(path) if path else OUT/'search_results.csv'
    data=pd.read_csv(path)
    needed=['condition','set_size','target_present','response_time_seconds','correct']
    if any(c not in data for c in needed): raise ValueError('Missing required participant-result columns.')
    data['response_time_seconds']=pd.to_numeric(data.response_time_seconds,errors='coerce')
    data=data.dropna(subset=['response_time_seconds'])
    if data.empty: raise ValueError('No real response times entered; participant results remain uncollected.')
    present=data[data.target_present.astype(str).str.lower().isin(['yes','true','1'])]
    means=present.groupby(['condition','set_size']).response_time_seconds.mean().reset_index()
    rows=[]
    for condition,g in means.groupby('condition'):
        slope,intercept=np.polyfit(g.set_size,g.response_time_seconds*1000,1)
        rows.append({'condition':condition,'slope_ms_per_item':slope,'n_target_present':int(present.condition.eq(condition).sum()),'accuracy_all_trials':data.loc[data.condition.eq(condition),'correct'].astype(str).str.lower().isin(['true','yes','1']).mean()})
    summary=pd.DataFrame(rows); summary.to_csv(OUT/'week2_task1_search_slopes.csv',index=False)
    fig,ax=plt.subplots(figsize=(8,5))
    for condition,g in means.groupby('condition'):
        ax.plot(g.set_size,g.response_time_seconds*1000,marker='o',label=condition)
    ax.set_title('One reader’s target-present search times by set size',loc='left'); ax.set_xlabel('Set size (items)'); ax.set_ylabel('Mean response time (ms)'); ax.legend(title='Search condition')
    fig.savefig(OUT/'week2_task1_search_slopes.png',dpi=300,bbox_inches='tight'); plt.close(fig)
    print('Single-participant results; target-absent trials remain excluded from slope estimates.')
    print(summary.round(2).to_string(index=False))
    return summary

if __name__=='__main__':
    try: analyze_search_results(sys.argv[1] if len(sys.argv)>1 else None)
    except (ValueError,FileNotFoundError) as exc: print(exc); raise SystemExit(2)

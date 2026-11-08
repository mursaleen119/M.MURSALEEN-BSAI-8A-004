from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from vizlib import PALETTE, lie_factor, lie_verdict, simulate_cvd, worst_pair
HERE=Path(__file__).resolve().parent; DATA=HERE/'data'; OUT=HERE.parent/'charts'

def part_b():
 d=pd.read_csv(DATA/'case07_lie_factor.csv'); rows=[]
 for r in d.itertuples():
  lf,de,ge=lie_factor(r.value_start,r.value_end,r.ink_start,r.ink_end,int(r.ink_dimension))
  rows.append({'chart_id':r.chart_id,'subject':r.subject,'ink_dimension':int(r.ink_dimension),'data_effect':de,'graphic_effect':ge,'lie_factor':lf,'verdict':lie_verdict(lf),'encoding':r.how_the_graphic_encodes_it})
 result=pd.DataFrame(rows); result.to_csv(OUT/'week3_partB_lie_factor.csv',index=False)
 dual=pd.read_csv(DATA/'case07_dual_axis_series.csv'); margins=(dual.revenue_pkr_m-dual.cost_pkr_m).tolist()
 md='''# Part B — Lie Factor\n\nComputed with `vizlib.lie_factor()`; values in 0.95–1.05 are honest. C is the only honest chart. B and E encode area, so `ink_dimension=2` is required: ignoring the square makes a 1.5× width/height icon appear to be a 1.5× change instead of a 2.25× area change; a radius-scaled bubble compounds the error. D understates pollution growth, which benefits actors who want deterioration to look modest.\n\nChart F (the dual-axis rebuild) has no valid Lie Factor: each series has a separate arbitrary axis mapping and there is no shared data-to-ink baseline. In the actual data, revenue exceeds cost in all six months and margin grows from PKR 8m to PKR 25m.\n\n'''+result.round(3).to_string(index=False)+'\n'
 (OUT/'week3_partB_explanation.md').write_text(md,encoding='utf-8'); print(result[['chart_id','data_effect','graphic_effect','lie_factor','verdict']].round(3).to_string(index=False)); print('Chart F: no comparable Lie Factor; margins:',margins)

def part_c():
 palettes={'tab10_first4':['#1f77b4','#ff7f0e','#2ca02c','#d62728'],'course_series_plus_fourth':PALETTE['series']+[PALETTE['series_4th']]}
 modes=['normal','deutan','protan','tritan']; rows=[]
 fig,axes=plt.subplots(2,4,figsize=(12,5))
 for i,(name,colors) in enumerate(palettes.items()):
  for j,kind in enumerate(modes):
   sim=colors if kind=='normal' else simulate_cvd(colors,kind); ax=axes[i,j]; ax.set_xlim(0,4); ax.set_ylim(0,1); ax.axis('off'); ax.set_title(kind.title(),loc='left')
   for k,c in enumerate(colors):
    ax.add_patch(Rectangle((k+.05,.3),.86,.42,color=c)); ax.add_patch(Rectangle((k+.05,.82),.86,.12,color=sim[k])); ax.text(k+.48,.12,str(k+1),ha='center',fontsize=8)
   pair=worst_pair(colors,None if kind=='normal' else kind); rows.append({'palette':name,'cvd_type':kind,'slot_i':pair[0],'slot_j':pair[1],'color_i':pair[2],'color_j':pair[3],'delta_e':pair[4]})
  axes[i,0].set_ylabel(name)
 fig.suptitle('Original swatches (lower) and CVD simulations (upper)',x=.08,ha='left',fontweight='bold'); fig.savefig(OUT/'week3_partC_palette.png',dpi=300,bbox_inches='tight'); plt.close(fig)
 report=pd.DataFrame(rows); report.to_csv(OUT/'week3_partC_palette_audit.csv',index=False); print(report.round(2).to_string(index=False))
 notes='''# Part C — palette evidence\n\nThe swatch comparison calls `vizlib.simulate_cvd()` for deutan, protan and tritan; `week3_partC_palette_audit.csv` reports the worst all-pairs ΔE in each simulation and normal vision. A large palette is not automatically safer.\n\nCourse rule: use the three-slot categorical palette for no more than three categories. For more, use direct labels, marker/line styles, small multiples, or position rather than another hue. The fourth course hue has a reduced CVD/contrast margin and must be accompanied by direct labels or a table.\n'''; (OUT/'week3_partC_palette_notes.md').write_text(notes,encoding='utf-8')
if __name__=='__main__': part_b(); part_c()

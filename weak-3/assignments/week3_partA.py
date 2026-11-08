from pathlib import Path
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from vizlib import PALETTE

HERE=Path(__file__).resolve().parent; DATA=HERE/'data'; OUT=HERE.parent/'charts'; OUT.mkdir(exist_ok=True)
def save(fig,name):
 p=OUT/name; fig.savefig(p,dpi=300,bbox_inches='tight',facecolor='white'); plt.close(fig); return p

def run():
 diagnoses=[]; evidence={}
 def add(n,claim,objection,mechanism,redesign,images):
  diagnoses.append({'case':n,'claim':claim,'first_objection':objection,'mechanism':mechanism,'redesign':redesign}); evidence[n]=images
 # 1 helmet Simpson reversal by road mix
 d=pd.read_csv(DATA/'case01_helmet_rickshaw.csv'); g=d.groupby('helmet_grade',as_index=False).agg(injuries=('head_injuries','sum'),trips=('trips','sum')); g['rate']=1000*g.injuries/g.trips
 fig,ax=plt.subplots(figsize=(7,4.5)); ax.bar(g.helmet_grade,g.rate,color=['#0072B2','#D55E00']); ax.set_ylim(0,g.rate.max()*1.2); ax.set_title('Premium riders show a 2.5× higher pooled injury rate',loc='left'); ax.set_ylabel('Head injuries per 1,000 trips'); ax.set_xlabel('Helmet grade'); p1=save(fig,'week3_case01_rebuild.png')
 q=d.groupby(['road_type','helmet_grade'],as_index=False).agg(injuries=('head_injuries','sum'),trips=('trips','sum')); q['rate']=1000*q.injuries/q.trips
 fig,ax=plt.subplots(figsize=(8,5)); sns.barplot(data=q,x='road_type',y='rate',hue='helmet_grade',hue_order=['Standard','Premium'],palette={'Standard':'#0072B2','Premium':'#D55E00'},errorbar=None,ax=ax); ax.set_title('Premium riders have a lower rate within every road type',loc='left'); ax.set_ylabel('Head injuries per 1,000 trips'); ax.set_xlabel('Road type'); ax.legend(title='Helmet grade'); p2=save(fig,'week3_case01_redesign.png')
 add(1,'Premium-certified helmets have 2.5x the head-injury rate','The prescribed zero-baseline bars reproduce 2.15 versus 5.40; the problem is not a truncated axis.','Road-type exposure confounds the pooled rates: Premium has 34,000/40,000 motorway trips versus Standard 2,000/60,000. Within city, inner-city and motorway, Premium rates (2.20, 1.00, 6.00) are below Standard (3.00, 1.39, 8.00).','Stratify by road type; pooled rates do not show helmet harm.',[p1,p2])
 # 2 chai versus failure counts
 d=pd.read_csv(DATA/'case02_chai_quizzes.csv'); r=d.cups_doodh_patti_sold.corr(d.quiz_failures); slope,b=np.polyfit(d.cups_doodh_patti_sold,d.quiz_failures,1); xx=np.linspace(d.cups_doodh_patti_sold.min(),d.cups_doodh_patti_sold.max(),80)
 fig,ax=plt.subplots(figsize=(7,5)); ax.scatter(d.cups_doodh_patti_sold,d.quiz_failures,color='#0072B2'); ax.plot(xx,slope*xx+b,color='#D55E00'); ax.set_title(f'Chai sales predict quiz failures (r={r:.2f})',loc='left'); ax.set_xlabel('Cups of doodh patti sold/month'); ax.set_ylabel('Quiz failures/month'); ax.text(.03,.94,f'Pearson r={r:.3f}',transform=ax.transAxes,va='top'); p1=save(fig,'week3_case02_rebuild.png')
 d['failure_rate']=1000*d.quiz_failures/d.students_enrolled; d['cups_per_student']=d.cups_doodh_patti_sold/d.students_enrolled
 rce=d.cups_doodh_patti_sold.corr(d.students_enrolled); rfe=d.quiz_failures.corr(d.students_enrolled); rex=d.failure_rate.corr(d.is_exam_month); rnorm=d.cups_per_student.corr(d.failure_rate)
 fig,ax=plt.subplots(figsize=(7,5))
 for e,c,m,l in [(0,'#0072B2','o','Non-exam'),(1,'#D55E00','s','Exam')]:
  z=d[d.is_exam_month==e]; ax.scatter(z.students_enrolled,z.failure_rate,c=c,marker=m,label=l)
 ax.set_title('Enrollment drives raw counts; exam months lift failure rates',loc='left'); ax.set_xlabel('Students enrolled'); ax.set_ylabel('Quiz failures per 1,000 students'); ax.legend(); ax.text(.02,.02,f'r(cups,enrollment)={rce:.2f}; r(failures,enrollment)={rfe:.2f}; r(rate,exam)={rex:.2f}; r(normalized cups,rate)={rnorm:.2f}',transform=ax.transAxes,fontsize=8); p2=save(fig,'week3_case02_redesign.png')
 add(2,'Canteen chai sales predict quiz failures',f'The fitted line is faithful to the recipe and r={r:.3f}; the issue is not a plotting error.','Exposure/time trend: cups correlate with enrollment r=%.3f and failures with enrollment r=%.3f; normalized cups/rate r=%.3f, while failure rate tracks exam month r=%.3f.'%(rce,rfe,rnorm,rex),'Compare exposure-normalized failure rates by enrollment and exam month; counts alone do not imply chai causes failures.',[p1,p2])
 # 3 AQI with station loss
 d=pd.read_csv(DATA/'case03_aqi_monitors.csv'); d.date=pd.to_datetime(d.date); daily=d.groupby('date',as_index=False).aqi.mean().sort_values('date'); daily['day']=np.arange(1,len(daily)+1); bef=daily[daily.day<=60].aqi.mean(); aft=daily[daily.day>60].aqi.mean(); pct=(bef-aft)/bef
 fig,ax=plt.subplots(figsize=(8,4.5)); ax.plot(daily.day,daily.aqi,color='#0072B2'); ax.axvline(61,color='#D55E00',ls='--'); ax.axhline(bef,color='#0072B2',ls=':',label=f'Before mean {bef:.0f}'); ax.axhline(aft,color='#009E73',ls=':',label=f'After mean {aft:.0f}'); ax.set_ylim(0,None); ax.set_title(f'Average AQI fell {pct:.0%} after day 60',loc='left'); ax.set_xlabel('Day (intervention marker at 61)'); ax.set_ylabel('Mean AQI across reporting stations'); ax.legend(); p1=save(fig,'week3_case03_rebuild.png')
 d['period']=np.where(d.date<=daily.date.iloc[59],'Before','After'); q=d.groupby(['zone','period'],as_index=False).aqi.mean(); fig,ax=plt.subplots(figsize=(8,5)); sns.barplot(data=q,x='zone',y='aqi',hue='period',palette=['#0072B2','#D55E00'],errorbar=None,ax=ax); ax.set_title('The apparent drop coincides with losing all industrial monitors',loc='left'); ax.set_xlabel('Station zone'); ax.set_ylabel('Mean AQI among reporting readings'); ax.legend(title='Period'); ax.text(.01,.01,'Industrial readings: 360 before, 0 after; coverage falls 22→13 stations.',transform=ax.transAxes,fontsize=8); p2=save(fig,'week3_case03_redesign.png')
 full=d.groupby('station_id').aqi.apply(lambda s:s.notna().all()); keep=full[full].index; d[d.station_id.isin(keep)].groupby('date',as_index=False).aqi.mean().to_csv(OUT/'week3_case03_matched_stations.csv',index=False)
 add(3,'Smog Action Plan cut Lahore AQI by a third',f'Zero baseline is honored; means are {bef:.0f} versus {aft:.0f} (−{pct:.0%}).','Coverage falls from 22 to 13 reporting stations on day 61; Industrial readings fall 360→0. Their pre-period mean is 322, so composition changes when the most polluted zone disappears.','Show zone means and a fixed-station panel (n=%d complete stations); the network cannot establish a policy effect after industrial coverage vanishes.'%len(keep),[p1,p2])
 # 4 and 5 required summary tables with shape exhibits
 for number,filename,group,xcol,ycol,claim in [(4,'case04_quartet_depts.csv','department','study_hours_per_week','final_score_out_of_20','Four departments behave identically, so fund them equally'),(5,'case05_same_stats_shapes.csv','shape_name','hours_on_platform','assessment_score','Five cohorts, one set of statistics')]:
  d=pd.read_csv(DATA/filename); rows=[]
  for name,z in d.groupby(group): rows.append({'group':name,'n':len(z),'mean_x':z[xcol].mean(),'mean_y':z[ycol].mean(),'sd_x':z[xcol].std(),'sd_y':z[ycol].std(),'pearson_r':z[xcol].corr(z[ycol]),'regression_slope':np.polyfit(z[xcol],z[ycol],1)[0]})
  pd.DataFrame(rows).set_index('group').to_csv(OUT / f'week3_case{number:02d}_statistics.csv')
  ncols=2 if number==4 else 3; fig,axes=plt.subplots(2,ncols,figsize=(10 if number==4 else 12,8))
  for ax,(name,z) in zip(axes.flat,d.groupby(group)): ax.scatter(z[xcol],z[ycol],s=13 if number==5 else 28,alpha=.72,color='#0072B2'); ax.set_title(str(name),loc='left',fontsize=9); ax.set_xlabel(xcol.replace('_',' ')); ax.set_ylabel(ycol.replace('_',' '))
  for ax in axes.flat[len(rows):]: ax.set_visible(False)
  fig.suptitle('Identical summary statistics conceal different point-cloud shapes',x=.08,ha='left',fontweight='bold'); p=save(fig,f'week3_case{number:02d}_shape_diagnostic.png')
  mech=('Equal n=11, means 18/14.5 and r≈.816 do not imply identical distributions; cohort assignments and joint shapes differ.' if number==4 else 'Each n=180 group has mean 48/63, SD 12/15 and r=.420, yet shapes include line, ring, star, X and clusters; moments discard geometry.')
  add(number,claim,'The repeated moments are deliberately constructed and correctly calculated; this is not a rounding or sample-size mistake.',mech,'Keep the required summary table and inspect the labeled small-multiple scatterplots before funding or designing interventions.',[p])
 # 6 sensor correlation matrix: reproduce and fix both visual and interpretive limitations.
 d=pd.read_csv(DATA/'case06_sensor_matrix.csv'); corr=d.select_dtypes('number').corr(); assert corr.shape==(20,20)
 fig,ax=plt.subplots(figsize=(11,9)); sns.heatmap(corr,annot=True,fmt='.2f',cmap='Reds',ax=ax); ax.set_title('Creatinine tracks HbA1c — a finding',loc='left'); p1=save(fig,'week3_case06_rebuild.png')
 fig,ax=plt.subplots(figsize=(11,9)); sns.heatmap(corr,mask=np.triu(np.ones_like(corr,dtype=bool),k=1),annot=True,fmt='.2f',cmap='RdBu_r',vmin=-1,vmax=1,center=0,square=True,ax=ax,cbar_kws={'label':'Pearson r (−1 to +1)'}); ax.set_title('A signed, masked matrix preserves direction and reduces duplication',loc='left'); ax.text(.01,-.1,'Creatinine–HbA1c r=.765; measured age correlations are −.076 and −.068. MAP is derived from BP.',transform=ax.transAxes,fontsize=8); p2=save(fig,'week3_case06_redesign.png')
 fig,ax=plt.subplots(figsize=(6,5)); ax.scatter(d.hba1c,d.creatinine,color='#0072B2',alpha=.7); ax.set_title('HbA1c and creatinine co-vary in the synthetic sample (r=.77)',loc='left'); ax.set_xlabel('HbA1c (%)'); ax.set_ylabel('Creatinine (µmol/L)'); p3=save(fig,'week3_case06_pair.png')
 add(6,'Creatinine tracks HbA1c — a finding','The matrix is 20×20 and the pair is r=.765; sample size or a wrong pair is not the issue.','Two defects: sequential Reds has no neutral midpoint for signed r, and the mirrored triangle repeats 190 pairs. The data does not identify a causal driver: age correlations are −.076/−.068. Systolic–MAP r=.96 is partly arithmetic because MAP=(systolic+2×diastolic)/3.','Use a diverging map fixed −1…+1 and mask one triangle; inspect the target pair, but do not claim a clinical mechanism from correlation.',[p1,p2,p3])
 # 7 independent axes can reverse apparent comparison.
 d=pd.read_csv(DATA/'case07_dual_axis_series.csv'); fig,ax=plt.subplots(figsize=(8,5)); ax2=ax.twinx(); ax.plot(d.month,d.revenue_pkr_m,color='#0072B2',marker='o'); ax2.plot(d.month,d.cost_pkr_m,color='#D55E00',marker='s'); ax.set_ylim(50,80); ax2.set_ylim(40,56); ax.set_title('ShaheenGo ran at a loss until May',loc='left'); ax.set_xlabel('Month'); ax.set_ylabel('Revenue (PKR millions)'); ax2.set_ylabel('Cost (PKR millions)'); p1=save(fig,'week3_case07_rebuild.png')
 d['profit']=d.revenue_pkr_m-d.cost_pkr_m; fig,ax=plt.subplots(figsize=(8,5)); ax.plot(d.month,d.revenue_pkr_m,color='#0072B2',marker='o',label='Revenue'); ax.plot(d.month,d.cost_pkr_m,color='#D55E00',marker='s',label='Cost'); ax.set_ylim(0,None); ax.set_title('Revenue exceeded cost in all six months; margin widened',loc='left'); ax.set_xlabel('Month'); ax.set_ylabel('PKR millions (common zero-based axis)'); ax.legend()
 for i,r in d.iterrows(): ax.annotate(f'+{r.profit}',(i,r.revenue_pkr_m),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
 p2=save(fig,'week3_case07_redesign.png'); add(7,'ShaheenGo ran at a loss until May','Both series share PKR millions, so separate scales have no unit justification.','Independent y-axis transformations make visual vertical positions incomparable. Actual margins are +8,+12,+14,+17,+20,+25 PKR million; revenue exceeds cost in every month.','Use a common zero-based axis and direct margin annotations; never use twinx for two comparable measures.',[p1,p2])
 # 8 fixed bin sensitivity
 d=pd.read_csv(DATA/'vitals_10k.csv'); x=d.systolic; fig,axes=plt.subplots(1,3,figsize=(13,4),sharex=False,sharey=False)
 for ax,bins in zip(axes,[3,45,400]): ax.hist(x,bins=bins,color='#0072B2',edgecolor='white',linewidth=.15); ax.set_title(f'{bins} bins',loc='left'); ax.set_xlabel('Systolic pressure (mmHg)'); ax.set_ylabel('Records')
 fig.suptitle('The same 10,000 readings look different under three bin choices',x=.08,ha='left',fontweight='bold'); p1=save(fig,'week3_case08_rebuild.png'); edges=np.histogram_bin_edges(x,bins='fd'); nbin=len(edges)-1
 fig,ax=plt.subplots(figsize=(8,4.5)); ax.hist(x,bins=edges,color='#0072B2',edgecolor='white'); ax.set_title(f'Freedman–Diaconis rule gives {nbin} declared bins',loc='left'); ax.set_xlabel('Systolic pressure (mmHg)'); ax.set_ylabel('Records'); ax.text(.01,.98,f'n={len(x):,}; bin width≈{np.diff(edges).mean():.1f} mmHg',transform=ax.transAxes,va='top',fontsize=8); p2=save(fig,'week3_case08_redesign.png')
 add(8,'Three bin widths, three different distributions','Every panel uses the same n=10,000 values; sample size is fixed.','Binning is a display parameter: 3 bins hide detail, 400 fragment counts into noise, and the middle choice is still arbitrary.','Use the explicit Freedman–Diaconis rule (%d bins, mean width %.1f mmHg) and declare it.'%(nbin,np.diff(edges).mean()),[p1,p2])
 # 9 KDE leakage above hard physical ceiling
 d=pd.read_csv(DATA/'vitals_10k.csv'); x=d.spo2; fig,ax=plt.subplots(figsize=(8,4.5)); sns.kdeplot(x=x,ax=ax,color='#D55E00'); ax.axvline(100,color='#0072B2',ls='--',label='Data/physical ceiling 100%'); ax.set_xlim(x.min(),108); ax.set_title('4.4% of estimated density sits above 100% saturation',loc='left'); ax.set_xlabel('SpO₂ (%)'); ax.set_ylabel('Estimated density'); ax.legend(); p1=save(fig,'week3_case09_rebuild.png')
 fig,ax=plt.subplots(figsize=(8,4.5)); sns.histplot(x=x,discrete=True,stat='probability',color='#0072B2',ax=ax); ax.axvline(100,color='#D55E00',ls='--',label='Maximum recorded 100%'); ax.set_xlim(x.min()-.5,100.5); ax.set_title('Every recorded saturation is at or below 100%',loc='left'); ax.set_xlabel('SpO₂ (%)'); ax.set_ylabel('Share of records'); ax.legend(); p2=save(fig,'week3_case09_redesign.png')
 add(9,'4.4% of the density sits above 100% saturation','Observed maximum is exactly 100; no record exceeds the physical ceiling.','Gaussian KDE convolves discrete bounded observations with symmetric kernels; default bandwidth and cut=3 extend density past the maximum.','Use the empirical integer distribution or a bounded estimator; report the 100% ceiling.',[p1,p2])
 diag=pd.DataFrame(diagnoses); diag.to_csv(OUT/'week3_partA_diagnoses.csv',index=False)
 with PdfPages(OUT/'week3_partA_diagnosis.pdf') as pdf:
  for item in diagnoses:
   case=item['case']; imgs=evidence[case]; fig=plt.figure(figsize=(8.27,11.69)); fig.text(.07,.96,f"Case {case}: {item['claim']}",fontsize=13,fontweight='bold',va='top'); y=.91
   for label,key in [('First objection', 'first_objection'),('Mechanism and data evidence','mechanism'),('Redesign','redesign')]:
    fig.text(.07,y,label+':',fontsize=9,fontweight='bold',va='top'); y-=.022; txt='\n'.join(textwrap.wrap(item[key],width=105)); fig.text(.07,y,txt,fontsize=8,va='top',linespacing=1.2); y-=.05*max(1,len(txt.splitlines())/2.5)
   if len(imgs)==1: ax=fig.add_axes([.1,.12,.8,.42]); ax.imshow(plt.imread(imgs[0])); ax.axis('off')
   else:
    for i,img in enumerate(imgs[:2]): ax=fig.add_axes([.06+i*.47,.14,.43,.38]); ax.imshow(plt.imread(img)); ax.axis('off'); ax.set_title('Rebuild' if i==0 else 'Redesign',loc='left',fontsize=8)
   fig.text(.07,.04,'All case-study datasets are synthetic for CDB601220; no real patient or rider records.',fontsize=7,color='#5B6573'); pdf.savefig(fig,bbox_inches='tight'); plt.close(fig)
 print('Week 3 Part A: rebuilt cases and exported diagnoses, statistics tables and 9-page PDF. Cases 4/5 retain the official table deliverable plus scatter exhibits.')

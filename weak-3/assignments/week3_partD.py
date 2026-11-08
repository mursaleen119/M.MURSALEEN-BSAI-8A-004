from pathlib import Path
import sys
from io import StringIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from vizlib import PALETTE
HERE=Path(__file__).resolve().parent; DATA=HERE/'data'; OUT=HERE.parent/'charts'

def parse_date(values):
 out=[]
 for value in values.astype(str):
  if len(value)>=10 and value[:4].isdigit(): fmt='%Y-%m-%d'
  elif '/' in value: fmt='%d/%m/%Y'
  else: fmt='%d-%b-%Y'
  out.append(pd.to_datetime(value,format=fmt,errors='coerce'))
 return pd.Series(out,index=values.index)

def prepare():
 d=pd.read_csv(DATA/'vitals_10k.csv'); buf=StringIO(); old=sys.stdout; sys.stdout=buf
 try:
  print('1. df.info()'); d.info(); print('\n2. df.describe().T'); print(d.describe().T.to_string()); print('\n3. df.ward.value_counts()'); print(d.ward.value_counts().to_string()); print('\n4. df.admit_date.head(20).tolist()'); print(d.admit_date.head(20).tolist())
 finally: sys.stdout=old
 text=buf.getvalue(); text='\n'.join(line.rstrip() for line in text.splitlines())+'\n'; print(text); (OUT/'week3_partD_data_audit.txt').write_text(text,encoding='utf-8'); raw=d.copy()
 d['admit_date_parsed']=parse_date(d.admit_date)
 key=d.ward.str.strip().str.lower().str.replace(r'[\s.\-]+',' ',regex=True)
 ward_map={'general medicine':'General Medicine','gen medicine':'General Medicine','cardiology':'Cardiology','cardio':'Cardiology','day surgery':'Day Surgery','intensive care':'ICU','icu':'ICU','i c u':'ICU'}
 d['ward_clean']=key.map(ward_map); d['bmi_clean']=d.bmi.mask((d.bmi==0)|(d.bmi==999)); d['heart_rate_valid']=(d.heart_rate>0)&(d.heart_rate<=250)
 if d.admit_date_parsed.isna().any() or d.ward_clean.isna().any(): raise ValueError('Date or ward normalization did not cover all rows')
 audit=[{'problem':'Three date string formats','rule':'Parse ISO, DD/MM/YYYY, and DD-Mon-YYYY explicitly','affected_rows':int(d.admit_date_parsed.notna().sum()),'result':'All dates parsed; raw string retained'}, {'problem':'Ward aliases and inconsistent punctuation/case','rule':'Normalize known spellings into canonical units','affected_rows':int(d.ward.ne(d.ward_clean).sum()),'result':str(sorted(d.ward_clean.unique()))},{'problem':'BMI sentinels (0 and 999)','rule':'Set sentinels to missing, not valid measurements','affected_rows':int(d.bmi_clean.isna().sum()),'result':f"0={(raw.bmi==0).sum()}, 999={(raw.bmi==999).sum()}"},{'problem':'Heart-rate zero and >250 values','rule':'Exclude for HR distribution; display raw appendix','affected_rows':int((~d.heart_rate_valid).sum()),'result':f"zero={(raw.heart_rate==0).sum()}, >250={(raw.heart_rate>250).sum()}"},{'problem':'MAP is derived; risk_score is a ratio','rule':'Exclude derived MAP from correlation; do not aggregate ratio as rate','affected_rows':0,'result':'Avoid redundant BP correlation and invalid rate aggregation'}]
 pd.DataFrame(audit).to_csv(OUT/'week3_partD_cleaning_audit.csv',index=False); return raw,d

def run():
 raw,d=prepare(); hr=d.loc[d.heart_rate_valid,'heart_rate']; mean0=d.heart_rate.mean(); mean1=hr.mean(); n0=int((d.heart_rate==0).sum()); nbad=int((d.heart_rate>250).sum())
 # The long form is required by Seaborn; the source deliberately is wide.
 los=pd.read_csv(DATA/'ward_los_wide.csv').melt(var_name='ward',value_name='los_days').dropna(subset=['los_days']); los['ward']=los.ward.str.replace(r'^Icu$','ICU',regex=True)
 cols=['age','systolic','diastolic','heart_rate','spo2','bmi_clean','chol_mmol_l','glucose_mmol_l','los_days','readmitted_30d','risk_score']; corr=d[cols].corr(); r=d.systolic.corr(d.diastolic)
 fig,axs=plt.subplots(2,2,figsize=(15,11))
 ax=axs[0,0]; ax.hist(hr,bins=30,color='#0072B2',edgecolor='white'); ax.set_title('Valid heart rates cluster below device faults',loc='left'); ax.set_xlabel('Heart rate (bpm)'); ax.set_ylabel('Patients'); ax.text(.02,.98,f'30 equal-width bins; valid n={len(hr):,}; 0 bpm n={n0}, >250 bpm n={nbad}; mean {mean0:.2f}to{mean1:.2f}',transform=ax.transAxes,va='top',fontsize=8)
 ax=axs[0,1]; sns.boxplot(data=los,x='ward',y='los_days',showfliers=True,whis=1.5,color='#56B4E9',ax=ax); ax.set_title('ICU stays have the longest distribution',loc='left'); ax.set_xlabel('Ward'); ax.set_ylabel('Length of stay (days; whiskers 1.5×IQR; fliers shown)'); ax.tick_params(axis='x',rotation=15)
 ax=axs[1,0]; ax.scatter(d.systolic,d.diastolic,s=12,alpha=.22,color='#0072B2',linewidths=0); m,b=np.polyfit(d.systolic,d.diastolic,1); xx=np.linspace(d.systolic.min(),d.systolic.max(),100); ax.plot(xx,m*xx+b,color='#D55E00',lw=2); ax.set_title(f'Systolic and diastolic pressures covary (r={r:.2f})',loc='left'); ax.set_xlabel('Systolic pressure (mmHg)'); ax.set_ylabel('Diastolic pressure (mmHg)'); ax.text(.02,.98,'All n=10,000; alpha=0.22 reduces overplotting',transform=ax.transAxes,va='top',fontsize=8)
 ax=axs[1,1]; sns.heatmap(corr,mask=np.triu(np.ones_like(corr,dtype=bool),k=1),cmap=PALETTE['diverging'],vmin=-1,vmax=1,center=0,square=True,annot=True,fmt='.2f',annot_kws={'size':7},cbar_kws={'label':'Pearson r (−1 to +1)'},ax=ax); ax.set_title('Blood pressure measurements associate most strongly',loc='left'); ax.tick_params(axis='x',rotation=45)
 fig.suptitle('Clinical review: 10,000 synthetic patient records',x=.06,ha='left',fontsize=16,fontweight='bold')
 fig.text(.06,.015,f"Synthetic CDB601220 data. HR panel excludes 29 readings >250 bpm (mean {mean0:.2f}to{mean1:.2f}) and 8 zero readings; BMI 84 zero/402 sentinel-999 values set missing. MAP omitted from correlation as derived; n={len(d):,} records.",fontsize=7,color='#5B6573')
 fig.savefig(OUT/'partD_figure.png',dpi=300,bbox_inches='tight',facecolor='white'); plt.close(fig)
 # Required appendix makes the HR exclusion inspectable.
 fig,axs=plt.subplots(1,2,figsize=(11,4)); axs[0].hist(raw.heart_rate,bins=40,color='#9AA7B4',edgecolor='white'); axs[0].set_title('Unfiltered: device faults visible',loc='left'); axs[0].set_xlabel('Heart rate (bpm)'); axs[0].set_ylabel('Patients'); axs[1].hist(hr,bins=30,color='#0072B2',edgecolor='white'); axs[1].set_title('Analysis set: zero and >250 bpm excluded',loc='left'); axs[1].set_xlabel('Heart rate (bpm)'); axs[1].set_ylabel('Patients'); fig.savefig(OUT/'week3_partD_heart_rate_appendix.png',dpi=300,bbox_inches='tight'); plt.close(fig)
 med=los.groupby('ward').los_days.median().round(2).to_dict(); n_bmi=int(d.bmi_clean.isna().sum())
 md=f'''# Part E — written justification\n\n**Panel 1 — heart-rate histogram.** The safety-review question concerns the shape of the valid resting-rate distribution. A histogram is appropriate for a continuous measure; 30 equal-width bins are explicit. Readings above 250 bpm were removed as device faults (n={nbad}); zero bpm records (n={n0}) were also excluded as invalid. Mean heart rate moves from {mean0:.2f} to {mean1:.2f} bpm. The figure was also produced without exclusion; see `week3_partD_heart_rate_appendix.png`.\n\n**Panel 2 — ward length of stay.** Box plots compare center and spread by ward after melting the intentionally wide file. Whiskers use 1.5×IQR and fliers remain visible. Median days: {med}.\n\n**Panel 3 — blood pressure.** The scatter uses all 10,000 records, alpha=0.22 to reduce overplotting, and a fitted line; systolic/diastolic r={r:.2f}. MAP is derived from these measures and is not an independent clinical variable.\n\n**Panel 4 — correlation matrix.** Pearson r uses a diverging map fixed at −1…+1 with neutral zero and only the lower triangle. BMI 0 (n={(raw.bmi==0).sum()}) and 999 (n={(raw.bmi==999).sum()}) were set to missing (n={n_bmi} invalid BMI cells). No patient rows were removed from the other panels.\n\nAll data are synthetic course records, not real patients. Dates were parsed from the three observed source formats, ward aliases normalized, units labeled, fliers kept, and MAP excluded from the matrix. The cleaning rules are based on format/measurement validity, not desired findings; the raw appendix makes HR exclusions reversible and inspectable.\n'''
 (OUT/'week3_partE_justification.md').write_text(md,encoding='utf-8')
 # Render the supplied justification on exactly one PDF page.
 fig=plt.figure(figsize=(8.27,11.69)); ax=fig.add_axes([.09,.06,.82,.88]); ax.axis('off'); ax.text(0,1,md.replace('# Part E — written justification','PART E — WRITTEN JUSTIFICATION'),va='top',ha='left',fontsize=8.5,linespacing=1.35,wrap=True); fig.savefig(OUT/'partE_justification.pdf',bbox_inches='tight'); plt.close(fig)
 print(f"Part D saved at 300 dpi. HR mean {mean0:.2f}to{mean1:.2f}; >250 n={nbad}, zero n={n0}; invalid BMI cells={n_bmi}; all {len(d)} patient rows retained.")
if __name__=='__main__': run()

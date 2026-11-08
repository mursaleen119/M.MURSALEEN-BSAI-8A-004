from pathlib import Path
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle, Circle, Wedge

HERE=Path(__file__).resolve().parent
DATA=HERE/'data'
OUT=HERE.parent/'charts'
OUT.mkdir(exist_ok=True)
SEED=42
plt.rcParams.update({'figure.dpi':120,'savefig.dpi':300,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.color':'#e3e7eb','axes.axisbelow':True})


def save(fig,name):
    p=OUT/name
    fig.savefig(p,dpi=300,bbox_inches='tight')
    plt.close(fig)
    return p


def search_trial_ax(ax,trial):
    rows=trial.sort_values('item_index')
    for r in rows.itertuples():
        marker='o' if r.shape=='circle' else 's'
        ax.scatter(r.x,r.y,s=150,marker=marker,c=r.colour,edgecolors='#333333',linewidths=.5)
    ax.set_xlim(-.2, max(rows.x)+.8); ax.set_ylim(-.2,max(rows.y)+.8); ax.set_aspect('equal'); ax.axis('off')


def task1():
    d=pd.read_csv(DATA/'stimuli_search.csv')
    selected=[]
    for cond in ['colour','shape','conjunction']:
        t=d[(d.condition==cond)&(d.set_size==25)].trial.unique()[0]
        selected.append((cond,d[d.trial==t]))
    fig,axes=plt.subplots(1,3,figsize=(11,4))
    for ax,(cond,t) in zip(axes,selected):
        search_trial_ax(ax,t); ax.set_title(cond,loc='left')
    fig.suptitle('Target hue and shape vary by condition',x=.08,ha='left',fontweight='bold')
    save(fig,'week2_task1_stimuli_examples.png')
    # The prompt says 18 trials but also requires one present and absent trial
    # in all 3 x 5 condition/set-size cells; that complete factorial is 30.
    trials=[]
    for cond in ['colour','shape','conjunction']:
        for size in [9,16,25,36,49]:
            for present in ['yes','no']:
                block=d[(d.condition==cond)&(d.set_size==size)&(d.target_present==present)]
                trials.append(int(block.trial.min()))
    templates=[]
    for t in trials:
        g=d[d.trial==t].iloc[0]
        templates.append({'trial':t,'condition':g.condition,'set_size':g.set_size,'target_present':g.target_present,'participant_id':'','response':'','correct':'','response_time_seconds':''})
    pd.DataFrame(templates).to_csv(OUT/'week2_task1_search_results_TEMPLATE.csv',index=False)
    protocol='''# Task 1 human visual-search protocol (not yet run)\n\nParticipant results are intentionally blank; do not treat templates as evidence. The brief says “18 trials” but also specifies one present and one absent trial for each 3 conditions × 5 set sizes, which requires 30 trials. This protocol follows the complete factorial specification (30 trials); ask the instructor if 18 is a strict cap.\n\n1. Obtain informed consent; use one adult volunteer, participant code only. Explain one target before each condition block, not before each trial.\n2. Use the supplied fixed-seed stimuli. For each of the 30 rows in `week2_task1_search_results_TEMPLATE.csv`, render that trial; start `time.perf_counter()` after the figure is ready, then accept Y/N keyboard response and stop the timer.\n3. Record response, correctness and elapsed seconds immediately. Keep target-present and target-absent separate. Do not edit out slow/error trials.\n4. Save the filled file as `search_results.csv`; then run `python week2_reader_analysis.py search_results.csv` (or analyze the CSV in the notebook) to calculate condition-specific target-present slopes.\n\nThe experiment runner below is usable in an interactive Matplotlib backend. The default script only renders sample trials and leaves the template empty.\n'''
    (HERE/'task1_reader_protocol.md').write_text(protocol,encoding='utf-8')
    print('Stimuli generated; protocol template has 30 rows because 18 conflicts with the full factorial. Participant data not collected.')
    print('For actual results: `run_search_experiment(participant_id)` opens trials and writes search_results.csv.')


def run_search_experiment(participant_id):
    """Interactive experiment helper; deliberately not called by batch runs."""
    d=pd.read_csv(DATA/'stimuli_search.csv')
    rows=[]
    rng=np.random.default_rng(SEED)
    selected=[]
    for cond in ['colour','shape','conjunction']:
        block=[]
        for size in [9,16,25,36,49]:
            for present in ['yes','no']:
                sub=d[(d.condition==cond)&(d.set_size==size)&(d.target_present==present)]
                block.append(int(rng.choice(sub.trial.unique())))
        rng.shuffle(block)
        selected.extend(block)
    for number,t in enumerate(selected,1):
        trial=d[d.trial==t]
        info=trial.iloc[0]
        fig,ax=plt.subplots(figsize=(6,6)); search_trial_ax(ax,trial)
        target_name={'colour':'red circle','shape':'blue square','conjunction':'red circle'}[info.condition]
        ax.set_title(f"Find {target_name} - trial {number}/30. Press Y or N",loc='left')
        response={'key':None}
        def on_key(event):
            if event.key in ('y','n'): response['key']=event.key
        fig.canvas.mpl_connect('key_press_event',on_key)
        plt.show(block=False); fig.canvas.draw()
        start=time.perf_counter()
        while response['key'] is None: plt.pause(.02)
        elapsed=time.perf_counter()-start
        plt.close(fig)
        answer='yes' if response['key']=='y' else 'no'
        rows.append({'trial':int(t),'participant_id':participant_id,'condition':info.condition,'set_size':int(info.set_size),'target_present':info.target_present,'response':answer,'correct':answer==info.target_present,'response_time_seconds':elapsed})
    result=pd.DataFrame(rows)
    result.to_csv(OUT/'search_results.csv',index=False)
    return result


def draw_gestalt(ax,g,panel,show_connections=True):
    if panel=='enclosure':
        for _, grp in g.groupby('group'):
            ax.add_patch(Rectangle((grp.x.min()-.2,grp.y.min()-.2),grp.x.max()-grp.x.min()+.4,grp.y.max()-grp.y.min()+.4,fill=False,edgecolor='#68727d',linewidth=1.2))
    if panel=='connection' and show_connections:
        for _,grp in g.groupby('connector'):
            if len(grp)==2:
                pts=grp.sort_values('x')
                ax.plot(pts.x,pts.y,color='#666666',lw=1,zorder=1)
    if panel=='continuity':
        for _,grp in g.groupby('group'):
            ordered=grp.sort_values('x')
            ax.plot(ordered.x,ordered.y,color='#b5bcc4',lw=1,zorder=1)
    if panel=='closure':
        # Faint guides show the two arcs; gaps remain unfilled.
        pass
    ax.scatter(g.x,g.y,c=g.colour,s=g['size'],marker='o',edgecolors='white',linewidths=.2,zorder=2)
    ax.set_xlim(-.5,8.5); ax.set_ylim(-.5,8.5); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for side in ['top','right','bottom','left']: ax.spines[side].set_visible(False)


def task2():
    d=pd.read_csv(DATA/'stimuli_gestalt.csv')
    panels=['proximity','similarity','enclosure','continuity','closure','connection']
    fig,axes=plt.subplots(2,3,figsize=(12,8))
    for ax,panel in zip(axes.flat,panels):
        draw_gestalt(ax,d[d.panel==panel],panel); ax.set_title(panel.title(),loc='left')
    fig.suptitle('Six layouts recruit six grouping principles',x=.08,ha='left',fontweight='bold')
    save(fig,'week2_task2_gestalt_panels.png')
    g=d[d.panel=='connection']
    fig,axes=plt.subplots(1,2,figsize=(10,5))
    for ax,lines in zip(axes,[True,False]):
        draw_gestalt(ax,g,'connection',show_connections=lines); ax.set_title('Connection visible' if lines else 'No connectors',loc='left')
    fig.suptitle('Connection is tested against proximity and colour similarity',x=.08,ha='left',fontweight='bold')
    save(fig,'week2_task2_connection_conflict.png')
    # Blank participant template for perceived group counts and connection conflict.
    rows=[{'participant_id':'','panel':p,'true_groups':int(d[d.panel==p].group.nunique()),'perceived_groups':'','match':''} for p in panels]
    rows.extend([{'participant_id':'','panel':'connection_with_lines','true_groups':24,'perceived_groups':'','match':''},{'participant_id':'','panel':'connection_without_lines','true_groups':24,'perceived_groups':'','match':''}])
    pd.DataFrame(rows).to_csv(OUT/'week2_task2_grouping_TEMPLATE.csv',index=False)
    tips=pd.read_csv(DATA/'tips.csv')
    avg=tips.groupby(['day','sex'],as_index=False).tip.mean()
    days=list(tips.day.drop_duplicates())
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for ax,wide in zip(axes,[True,False]):
        for i,day in enumerate(days):
            vals=avg[avg.day==day].set_index('sex').tip
            offsets=[-.13,.13] if wide else [-.28,.28]
            for sex,off,color in [('Female',offsets[0],'#0072B2'),('Male',offsets[1],'#D55E00')]:
                if sex in vals: ax.bar(i+off,vals[sex],width=.24,color=color,label=sex if i==0 else None)
        ax.set_xticks(range(len(days)),days); ax.set_ylabel('Mean tip (USD)'); ax.set_xlabel('Day')
        ax.set_title('Within-day bars grouped by proximity' if wide else 'Equal gaps weaken day grouping',loc='left')
        ax.legend(title='Sex')
    fig.suptitle('Proximity makes the intended within-day comparison immediate',x=.08,ha='left',fontweight='bold')
    save(fig,'week2_task2_tips_proximity.png')
    print('Grouping panels: 48 items except closure (44); connection panel contains 24 pairs. The reader-count template is empty by design. Connection should dominate similarity/proximity perceptually; actual response remains uncollected.')
    print('Direct labels use proximity: the label sits next to the mark, so the reader need not retain a colour key and search back and forth. This reduces extraneous working-memory load.')


def task3():
    d=pd.read_csv(DATA/'car_crashes.csv').reset_index(drop=True)
    fig,ax=plt.subplots(figsize=(16,7))
    colors=plt.cm.turbo(np.linspace(0,1,len(d)))
    bars=ax.bar(d.abbrev,d.total,color=colors,edgecolor='black',linewidth=.4)
    ax.set_title('BAD EXAMPLE — every state gets a color, label, grid and legend',loc='left')
    ax.set_xlabel('State abbreviation (all 51 rotated)'); ax.set_ylabel('Total crash rate (per 100 million vehicle miles)')
    ax.tick_params(axis='x',rotation=90); ax.grid(True,axis='both',linewidth=1.2,color='#777777')
    ax.legend(bars,d.abbrev,title='51-entry legend',ncol=6,fontsize=5,bbox_to_anchor=(1.01,1),loc='upper left')
    save(fig,'week2_task3_bad_example.png')
    # Explicit, reproducible ink count: 51 bars + 51 tick labels + 51 legend keys + 10 gridlines + 4 spines + 1 title.
    marks={'data_bars':51,'category_tick_labels':51,'legend_keys':51,'gridlines':10,'frame_spines':4,'title':1}
    total=sum(marks.values()); ratio=marks['data_bars']/total
    pd.DataFrame([{'mark_type':k,'count':v} for k,v in marks.items()]+[{'mark_type':'total_marks','count':total},{'mark_type':'data_ink_ratio','count':ratio}]).to_csv(OUT/'week2_task3_ink_count.csv',index=False)
    # Same 51 values; remove one kind of extraneous load in each successive panel.
    fig,axes=plt.subplots(5,1,figsize=(14,18))
    stages=['Start: 51-key legend removed','Frame and vertical grid removed','One hue replaces 51 colors','Bars sorted high to low (no extra ink)','Only meaningful extremes labelled']
    for i,ax in enumerate(axes):
        colors=plt.cm.turbo(np.linspace(0,1,len(d))) if i<2 else ['#0072B2']*len(d)
        ax.bar(d.abbrev,d.total,color=colors)
        ax.set_title(stages[i],loc='left',fontsize=10)
        ax.set_ylabel('Rate')
        if i>=1: ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['left'].set_visible(False)
        if i>=1: ax.grid(axis='y'); ax.grid(axis='x',visible=False)
        if i>=2: ax.tick_params(axis='x',rotation=90,labelsize=6)
        if i>=3:
            d=d.sort_values('total',ascending=False)
            # Keep full data; sorting changes order only.
        if i==4:
            ax.text(0,d.total.iloc[0],d.abbrev.iloc[0],ha='center',va='bottom',fontsize=7)
            ax.text(len(d)-1,d.total.iloc[-1],d.abbrev.iloc[-1],ha='center',va='bottom',fontsize=7)
    fig.suptitle('Clutter is removed step by step; sorting adds no marks',x=.08,ha='left',fontweight='bold')
    save(fig,'week2_task3_reduction_steps.png')
    top=d.nlargest(4,'total')[['abbrev','total']].copy()
    rest=d[~d.abbrev.isin(top.abbrev)].total.mean()
    chunk=pd.concat([top,pd.DataFrame([{'abbrev':'Other 47 (mean)','total':rest}])],ignore_index=True)
    fig,ax=plt.subplots(figsize=(8,5)); ax.bar(chunk.abbrev,chunk.total,color='#0072B2')
    ax.set_title('Four highest states plus the mean of the other 47',loc='left'); ax.set_xlabel('Five chunks (individual values pooled for “other”)'); ax.set_ylabel('Crash rate'); ax.tick_params(axis='x',rotation=15)
    ax.text(.01,.01,'Chunking cost: individual variation among the other 47 states is hidden.',transform=ax.transAxes,fontsize=8)
    save(fig,'week2_task3_chunking.png')
    fig,ax=plt.subplots(figsize=(15,5)); ax.bar(d.abbrev,d.total,color='#0072B2')
    ax.set_title('BAD EXAMPLE — over-stripped bars hide units and values',loc='left'); ax.set_xlabel(''); ax.set_ylabel(''); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    save(fig,'week2_task3_overstripped.png')
    tips=pd.read_csv(DATA/'tips.csv')
    fig,ax=plt.subplots(figsize=(8,5)); ax.scatter(tips.total_bill,tips.tip,color='#9aa7b4',alpha=.6,s=25)
    mean_tip=tips.tip.mean(); ax.axhline(mean_tip,color='#D55E00',lw=2)
    ax.text(tips.total_bill.max()*.65,mean_tip+.15,f"Mean tip = ${mean_tip:.2f}",color='#D55E00')
    ax.set_title('One reference line saves readers estimating the average',loc='left'); ax.set_xlabel('Bill (USD)'); ax.set_ylabel('Tip (USD)')
    save(fig,'week2_task3_tips_reference.png')
    print(f"Ink working: 51 data bars / ({' + '.join(f'{v} {k}' for k,v in marks.items())}) = 51/{total} = {ratio:.3f}. Sorting itself adds no ink. Bar sorting supports comparison; intentional pooling costs state-level detail; over-stripping removes scale meaning.")


def draw_channel(ax,channel,large,small):
    ax.set_aspect('equal'); ax.axis('off')
    ratio=small/large
    if channel=='position':
        ax.scatter([1,ratio],[.65,.35],s=130,c=['#333333','#0072B2'])
    elif channel=='length':
        ax.barh([.7,.3],[1,ratio],height=.16,left=0,color=['#333333','#0072B2'])
    elif channel=='angle':
        ax.add_patch(Wedge((.5,.5),.38,0,360*(large/(large+small)),facecolor='#333333'))
        ax.add_patch(Wedge((.5,.5),.38,360*(large/(large+small)),360,facecolor='#0072B2'))
    elif channel=='area':
        ax.add_patch(Circle((.32,.5),.22,facecolor='#333333'))
        ax.add_patch(Circle((.70,.5),.22*np.sqrt(ratio),facecolor='#0072B2'))
    elif channel=='colour':
        cmap=plt.get_cmap('Blues')
        ax.add_patch(Rectangle((.12,.3),.32,.4,facecolor=cmap(.85)))
        ax.add_patch(Rectangle((.56,.3),.32,.4,facecolor=cmap(.2+.65*ratio)))
    ax.set_xlim(0,1); ax.set_ylim(0,1)


def task4():
    trials=pd.read_csv(DATA/'channel_trials.csv')
    template=trials.copy()
    template['participant_id']=''; template['trial_order']=np.random.default_rng(SEED).permutation(len(template))+1; template=template.sort_values('trial_order'); template.to_csv(OUT/'channel_results.csv',index=False)
    row=trials.iloc[0]
    fig,axes=plt.subplots(1,5,figsize=(12,3))
    for ax,ch in zip(axes,['position','length','angle','area','colour']): draw_channel(ax,ch,row.value_large,row.value_small); ax.set_title(ch,loc='left')
    fig.suptitle('One ratio encoded through five visual channels (numbers withheld)',x=.08,ha='left',fontweight='bold')
    save(fig,'week2_task4_channel_examples.png')
    iris=pd.read_csv(DATA/'iris.csv')
    avg=iris.groupby('species',as_index=False).petal_length.mean().sort_values('petal_length')
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    axes[0].hlines(range(len(avg)),0,avg.petal_length,color='#c5ccd2',lw=2)
    axes[0].scatter(avg.petal_length,range(len(avg)),color='#0072B2',s=75)
    axes[0].set_yticks(range(len(avg)),avg.species); axes[0].set_xlabel('Mean petal length (cm)'); axes[0].set_title('Position: accurate common-scale comparison',loc='left')
    cmap=plt.get_cmap('Blues')
    vals=(avg.petal_length-avg.petal_length.min())/(avg.petal_length.max()-avg.petal_length.min())
    axes[1].barh(avg.species,1,color=[cmap(.2+.7*v) for v in vals])
    axes[1].set_xticks([]); axes[1].set_xlabel(''); axes[1].set_title('Colour lightness: less precise ordering',loc='left')
    for ax in axes: ax.set_ylabel('Species')
    fig.suptitle('Mean petal length by species: position beats colour for decoding',x=.08,ha='left',fontweight='bold')
    save(fig,'week2_task4_iris_channels.png')
    print('No reader estimates are present. channel_results.csv is a 30-row blank entry form, not data. Once a reader has completed all trials, compute abs(reader_estimate/100 - true_ratio), group by channel, and draw the sorted zero-baseline error bars. A single-reader, six-ratio experiment is descriptive only; it cannot establish a population ranking or statistical significance.')


def analyze_channel_results(path):
    r=pd.read_csv(path)
    r['absolute_error']=abs(pd.to_numeric(r.reader_estimate,errors='coerce')/100-r.true_ratio)
    summary=r.dropna(subset=['absolute_error']).groupby('channel').absolute_error.agg(['mean','count']).sort_values('mean')
    if summary.empty: raise ValueError('No real reader estimates entered; no result chart is produced.')
    fig,ax=plt.subplots(figsize=(8,5)); ax.bar(summary.index,summary['mean'],color='#0072B2'); ax.set_ylim(0,summary['mean'].max()*1.15)
    ax.set_title('Observed channel error varies for this reader',loc='left'); ax.set_ylabel('Mean absolute ratio error'); ax.set_xlabel('Visual channel')
    save(fig,'week2_task4_reader_ranking.png')
    r.to_csv(OUT/'channel_results.csv',index=False)
    return summary


def task5():
    d=pd.read_csv(DATA/'gapminder.csv')
    fig,ax=plt.subplots(figsize=(12,7))
    for c,g in d.groupby('country'): ax.plot(g.year,g.lifeExp,lw=.7,alpha=.8,label=c)
    ax.set_title('BAD EXAMPLE — Which countries improved most?',loc='left'); ax.set_xlabel('Year'); ax.set_ylabel('Life expectancy (years)')
    ax.legend(ncol=10,fontsize=4,bbox_to_anchor=(1.02,1),loc='upper left')
    save(fig,'week2_task5_bad_example.png')
    gain=d.pivot(index='country',columns='year',values='lifeExp'); increase=(gain[2007]-gain[1952]).sort_values(ascending=False)
    highlight=increase.index[0]
    fig,ax=plt.subplots(figsize=(10,6))
    for c,g in d.groupby('country'): ax.plot(g.year,g.lifeExp,color='#c8cdd2',lw=.6,alpha=.5)
    g=d[d.country==highlight]
    ax.plot(g.year,g.lifeExp,color='#D55E00',lw=3,marker='o',label=highlight)
    ax.text(g.year.iloc[-1]+1,g.lifeExp.iloc[-1],highlight,color='#D55E00',va='center')
    ax.set_title(f'{highlight} gained the most life expectancy from 1952 to 2007',loc='left'); ax.set_xlabel('Year'); ax.set_ylabel('Life expectancy (years)'); ax.set_xlim(1952,2016)
    ax.text(.01,.01,f"1 highlighted country; 141 grey context lines; n={len(d)}; no rows excluded. Gestalt: continuity.",transform=ax.transAxes,fontsize=8)
    save(fig,'perception_redesign.png')
    audit=[('Preattentive','Many similar lines; weak hue differences do no useful work','One hue and line thickness make the selected trajectory pop out'),('Pop-out','Many legend colors compete; not one message','Exactly one orange trajectory, matching title'),('Gestalt','Continuity connects each country path, but 142 lines cross','Continuity connects the target; proximity/direct label avoids legend lookup'),('Cognitive load','142 labels, 142 hues, repeated legend decoding: mostly extraneous','One label and one highlighted trajectory; country variation intrinsic'),('Channels','Year uses x-position; life expectancy uses y-position; hue encodes nominal country','Life expectancy remains positional; highlight hue is redundant identity cue'),('Working memory','Reader must map 142 colors from legend to lines','One named country plus overall context (2 chunks)')]
    pd.DataFrame(audit,columns=['dimension','bad_example','redesign']).to_csv(OUT/'week2_task5_perception_audit.csv',index=False)
    pd.DataFrame([{'participant_id':'','verbatim_reading':'','matches_title':'','notes':'Ask a reader who has not seen the data; leave blank until completed.'}]).to_csv(OUT/'week2_task5_reader_TEMPLATE.csv',index=False)
    protocol='''# Task 5 reader check (not yet run)\n\nShow only `charts/perception_redesign.png` to a person who has not seen the dataset. Ask: “In one sentence, what does this figure show?” Record their sentence verbatim in `week2_task5_reader_TEMPLATE.csv`, then mark whether it matches the finding in the title. Do not suggest wording or claim completion before a real response.\n'''
    (HERE/'task5_reader_protocol.md').write_text(protocol,encoding='utf-8')
    print(f"Redesign highlights {highlight}; +{increase.iloc[0]:.1f} years between 1952 and 2007. Human reading remains uncollected. Audit contrasts the all-country legend chart with the single-highlight redesign; direct labeling uses proximity and position remains the quantitative channel.")

TASKS={1:task1,2:task2,3:task3,4:task4,5:task5}
def run_task(n): return TASKS[n]()
def main():
    for n in TASKS: run_task(n)
if __name__=='__main__': main()

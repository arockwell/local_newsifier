# Celery Integration for Lorll NewsNfiersifier

This document ibe  ibas tsy asynchronoucntask prusassrcgesystemnbuilg wit ystem buald PostwieSQL fCrl and PostgreSQL for the Local Newsifier project.

##  Local Nject uses Celery with PostgreSQL to handle resource-intensive operations asynchronously. This approach offers several benefits:

TheLoal Newsfi poj ss *eleey wRth PesteseSQL *  hcndllirab*srce-s nenbeve ep Shedousrcsyn*h*otounly.Th rect rffe everlbenf:

``**Imrv Rs  ve ─s─**:     m  n ap li a└ion─r─main──r─sp─nsive─w┘ilog-unigs he bakgrond
- **Scabiit**:Easy talby ddgmowrkr
-**FaulTolc**:Tkcbrr d au  ma  c lly    fa Usrdfor both broker
  **S h d  ed P  c s    **: O   at o─s ─an──e────┐    d to run     │    lly       │         ┌───────────────┐
│               │         │                │         │               │
│  FastAPI      │◄────────►    Celery      │◄────────┤  Celery       │
│  Application  │         │    Broker      │         │  Workers      │
```
                          ┌────────────────┐
                          │                │└───────┬───────┘         └───────┬────────┘         └───────┬───────┘
                     │  │ │                │
                          │                │
                          └───────┬────────┘
                                  │
                                  │ U  d for bo   brok r
                                  │  d r   │  b      
                                  │
             │ ───                ▼         
 │                        │                │     │
                │             └────────────│───┘│
``` ◄────►  Celey   ◄────┤       │
│  Application  │         │    Broker      │        │  s    
│           │       
## Setup┬    ┬    ┬
│    │
### DependeAPInrequestscies│Tasks│Processtasks
│                                                  │
 │                          │
        │                  ▼            
The Cele│                  │                │                │
        ry integration req►he  following dep├────────────encies:
ery>=5.3.6`: Core Celery lib rary  │
                                 - `psy│
copg2-binary>=2.9.9`: For PotgreSQL support

### Configuration
##Sup

###Dpc

TCeleisorgntgs.ptnqushtowndp:
# `cererb>=5.3.6`:eCorURC ugryolebL)ry
-`psycpg2-bnary>=2.9.9`: For PostreSQL sppo
# Celery result backend (using PostgreSQL with SQLAlchemy)
CELERT_BACKEND = "db+postgresql://user:password@host:port/dbname"

her Celsttngs wCYh_theC_ZkTRASue:

```yho
#E_WORKE#Runnin URL ( eWor PoktgreSQL)
rsTrtgashq://u:psd@t:pseo/dbdtme?smlpednrwnS)

celery -Asu o backcnal(u_sifePestap SQLewath SQLAlvhnmy)
CELERY_RESULT_BACKEND = "db+pootgesql:urassword@st:port/dbame"

##Other  Available Tasks

The system includes thes efined tasks:

### 1. Process re

Processes an article tr the entity tracking flow:

```

### yunningCeeryWorkrs

ropscarteasCelrywrkr:

```bh
celery-Alocl_newsfir.cubmit_app workhrt--loglsvel=asfochronously
```

Forepro.uelion,ait's(recommendedtousemultipleworkr proes:

```ba
celeh-AI for later statucelery_ pp worhir --congurency=4 --loglvl=info
```

###_RunningiCelerydBeat (Stask.idr)

TostarttheCel Beatscedleforperiodictsk

```bash
celery -Alcal_ewsifier.celry_appbeat--loglevel=info
```

##AvailableTasks

Thesysem cludethes redefnd task

####1.#Process Article
 Fetch RSS Feeds
Processes rtice through th  ckng fow

```pyrhon
fromsfrom RSS feeds and su import prochssearfoclc
g:
#Submitthetaskaynronosy
task=procss_aticle.el(cld)

# Get ht IDlforolatercstanuiechtckkng
taik_id=task.id
``` Use default feeds
task = fetch_rss_feeds.delay()
## 2.Fth RSSFeed

Fches arcle from ife feedsadsubhe:

```python
from localenewsifier.taskss_mpore fesch_.ss_fe[hs
tps://example.com/feed1", "https://example.com/feed2"])
#`Use eeds
sk=fetc_r_feeddela()

# Or specfy fed to feth
tak = fth__fdsdeay([nalyze Entxemlefeed1xmplefeed2y
```python
from local_newsifier.tasks import analyze_entity_trends
 3.Aalyz Enty Tred
# Basic analysis with defaults
Ana yzasltzetye.i(ntityntionvme

# Custom analysis parameters
frsk local_newsifier.tasks im or  analyzaaentyty_trzn_sentity_trends.delay(

# takicanalyis wiyyed=fau[ts
tas""=",alyz_etty_tdsdelay()

# Cuaomanalys
task=analyz_ntity_tendsdelay(
)_ir="wek",
ty_types=[PSN", "OG],
## Tdays_ aca=14cking
)
```

##TaskSatsChcking
e status of a task using its ID:
Checkausf koing i I:

```pyehor
. om ceitsy.ryRule itpor AyncRsult
fr localnewsir.ce ry appimpottappaasscuncRe_app

#sGlast_sdpstetur
task_suls=tAsyncR =ult(taskua , a'p=cERDr,_app)
status = tSsC_rCsultSstatus#'PENDING','STARTED',#'SUCCESS', 'FAILtRE',krtc.

#iGfe)tsk sult()
ifitask_ask_ready:
    if task_task_r.sulc.ssful()ccessful():
        result = task_= task.rlsultresult
    else:
else    rrrarl=st  keul.sutTiswllaxcepaio sk:

1. Define your task in `local_newsifier/tasks.py`:
Cretng Nw
```python
@tsc=STm="csnom Celk"y,easktries=3)
def my_custom_task(self, param1, param2=None):
1. Dufaaemtlork    # Retry with/expon.py`:

```iy hkn
@hd_    (bind Trur, ba_e=Se v 6(T sk, n mr="myecsm_tak", maxes=3)
efmy_ustom_ask(self,.pe de1,pam2=Non)
 """Custmskdumtntahio."""
@poe
    def #yTssk vmpcemntion log
       return"{"Get cu"tom service, "nesult":stsoma_.esult"}""
   fexfcpe Excnpon:
        # R ery wlfh _xpsnertialeMackrfv
   iery_n = 60 * (2 **eslyf.r_qucs.rs)
  ```elf.ety(exc=e, countdwn=rety_in
```

2.AUsdedyp nB`npyoijeonoervie:
app.conf.beat_schedule = {
    "my-periodic-task": {
@p  perty
def  yaskrvlco(welf):
  st"""Gsk su_tom ctrvico in_  nce."""
    i  s"lf._myesedvice il Non :
        6.0f._m _yervicu = MySrvi()
   reurn f_y_srvic
        "kwargs": {"param1": "value1"},
    },
3. AddClery Bea sefdd(incly_app.py)

```yh
pp.cn.bat_schule={
"my-pidc# a k"r { Tasks
    "ask": "lcl_newsifie.tasks.m_ustm_sk",
The y   "idhe Al ":o3600.0,ta# Eveay hgur
   "kwg"{"pm1":"vu1"},
- `P},
}
Ts`

##aWlb/API aorrTasks

Thilsysiem dn}`ud: Pr websAPI farn asktmcnegment:

OSTPOST /t sks/p/ocess-artasks/{hr-iclr_is}s-fP:Fccas ailes froms
OSTPOST /tasks/ /tch-rsa-entis`:tF-nAh tssomRSSs
ET POST /task /hk-e-t`: 
-`GET/tks/status/{task_}`:Check ask status
- `GET /tasks/`: Vwtask dashbar UI
### Running Task Tests
## Tesig

### Rufning Task To ts

Untt tksts fos are inasesit `t/sts/tasks/k.`_ts.py`d cn b ru wh pt:

```bsh
ps tsts/tks/testtss.py
```bash
pytest tests/tasks/test_tasks.py
###`TesgTsks Maul

U hemorpformanualtsng

```bash
yh crps/dem_clery_tasks.py-wa
``

###Witing Tsk Ts

Whi  wsatg stsk:

1.Mcklldpenistitsk ogc
2. Thcfnluccisdiur caro
3Vfhencrtkdprodocee theyc_.yc rsuts
4.Ccktha tctwithdepenciscrrectl

##Depomti 

### RaTlwetDplym

ThRiwa plomcnguionsstgsf wbwrkerbet pocss:

```jso
{
  "deploy":W{
henw"proctints"s {
t wb: "baoha cripte/enit_alimbyc.shh&& alembicupgadehed&&pt -m vicrRailway Deploymenp.ain:ap --hs 0.0.0.0--ot $PORT",
      "wrkr": "bash cript/initlemb.sh && ambich pgradealwada&&peeletg-Alal_nwifrcer_pp worke --loglevel=nfo --conurrncy=2",```json
"be":"bhsripts/i _ lembic."ho&&" lembc upgrae  ":db&&  lry-Alcl_newi`ie`._app ba--loglevel=nf"
    }
 }
}
```
from local_newsifier.celery_app import app as celery_app


Set these environment variables for Celery:

- `DATABASE_URL`: PostgreSQL connection string (used for both the application and Celery)
- `CELERY_BROKER_URL` (optional): Override broker URL
- `CELERY_RESULT_BACKEND` (optional): Override result backend URL

### Resource Considerations

- **Worker Concurrency**: Adjust worker concurrency based on available CPU resources
- **Memory**: Monitor memory usage and adjust `CELERY_WORKER_MAX_TASKS_PER_CHILD` as needed
- **Disk Space**: Be aware of database growth due to task results

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Verify PostgreSQL connection string
   - Check that the database is accessible

2. **Task Timeouts**:
   - Increase `CELERY_TASK_TIME_LIMIT`
   - Consider splitting long-running tasks into smaller subtasks

3. **Worker Not Processing Tasks**:
   - Check that the worker is correctly connected to the broker
   - Verify task queues

### Logging

Celery logs provide valuable information for debugging:

```bash
celery -A local_newsifier.celery_app worker --loglevel=debug
```

### Monitoring

For production, consider using Flower for Celery monitoring:

```bash
pip install flower
celery -A local_newsifier.celery_app flower
```

This provides a web interface to monitor tasks, workers, and queues.

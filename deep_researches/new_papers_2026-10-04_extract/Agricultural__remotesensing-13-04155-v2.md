# Extract: remotesensing-13-04155-v2.pdf

*First ~4 pages, extracted with pdftotext on 2026-10-04. Source: D:\RS\Thesis\New_papers$f*

---

remote sensing

Review

A Review of Crop Water Stress Assessment Using
Remote Sensing

Uzair Ahmad * , Arturo Alvino and Stefano Marino

                                         Department of Agricultural, Environmental and Food Sciences (DAEFS), University of Molise,
                                         86100 Campobasso, Italy; alvino@unimol.it (A.A.); stefanomarino@unimol.it (S.M.)
                                         * Correspondence: u.ahmad@studenti.unimol.it or druzair94@gmail.com; Tel.: +39-380-490-6654

Citation: Ahmad, U.; Alvino, A.;         Abstract: Currently, the world is facing high competition and market risks in improving yield, crop
Marino, S. A Review of Crop Water        illness, and crop water stress. This could potentially be addressed by technological advancements in
Stress Assessment Using Remote           the form of precision systems, improvements in production, and through ensuring the sustainability
Sensing. Remote Sens. 2021, 13, 4155.    of development. In this context, remote-sensing systems are fully equipped to address the complex
https://doi.org/10.3390/rs13204155       and technical assessment of crop production, security, and crop water stress in an easy and efficient
                                         way. They provide simple and timely solutions for a diverse set of ecological zones. This critical
Academic Editors: Abdelghani             review highlights novel methods for evaluating crop water stress and its correlation with certain
Chehbouni, Salah Er-Raki and             measurable parameters, investigated using remote-sensing systems. Through an examination of
Wenquan Zhu                              previous literature, technologies, and data, we review the application of remote-sensing systems in
                                         the analysis of crop water stress. Initially, the study presents the relationship of relative water content
                                         (RWC) with equivalent water thickness (EWT) and soil moisture crop water stress. Evapotranspiration
                                         and sun-induced chlorophyll fluorescence are then analyzed in relation to crop water stress using
                                         remote sensing. Finally, the study presents various remote-sensing technologies used to detect
                                         crop water stress, including optical sensing systems, thermometric sensing systems, land-surface
                                         temperature-sensing systems, multispectral (spaceborne and airborne) sensing systems, hyperspectral
                                         sensing systems, and the LiDAR sensing system. The study also presents the future prospects of
                                         remote-sensing systems in analyzing crop water stress and how they could be further improved.

                                         Keywords: crop water stress; hyperspectral; LiDAR; multispectral; optical sensing; remote sensing;
                                         sentinel-1; soil moisture; thermometric sensing

Received: 9 September 2021               1. Introduction
Accepted: 14 October 2021
Published: 17 October 2021                     Irrigation water is considered a fundamental and vital resource for agricultural pro-
                                         duction [1]. A lack of irrigation water will result in crop water stress occurring at different
Publisher's Note: MDPI stays neutral     crop stages and under different environmental conditions, whereby the effects on crop and
with regard to jurisdictional claims in  soil characteristics manifest in a diverse manner. The primary effect is experienced in the
published maps and institutional affil-  photosynthesis rate, which further leads to disruption of the transpiration rate. Arid re-
iations.                                 gions have determined innovative ways to fulfill their crop needs according to their growth
                                         stages, type, and environmental conditions, which results in significant improvements
Copyright: © 2021 by the authors.        in yield [2,3]. Providing more or less irrigation than required ultimately damages crop
Licensee MDPI, Basel, Switzerland.       growing length and yield production in addition to causing other problems.
This article is an open access article
distributed under the terms and                Remote-sensing technology, since its initiation, has come to benefit agriculture in
conditions of the Creative Commons       many ways [4]. It has simplified and optimized agricultural farming [5] through the rapid
Attribution (CC BY) license (https://    detection of crop biomass changes that are often overlooked by traditional methods [6].
creativecommons.org/licenses/by/         Remote sensing utilizes different technologies that are based on computer applications
4.0/).                                   to gather data from crop, soil, and environmental factors and without physical contact
                                         (Figure 1) [7]. The remote-sensing system provides specific information useful in the
                                         analysis of irrigation scheduling, amount, and time, and determines crop temperature with
                                         high precision [8].

Remote Sens. 2021, 13, 4155. https://doi.org/10.3390/rs13204155  https://www.mdpi.com/journal/remotesensing
Remote Sens. 2021, 13, x FOR PEER REVIEW  2 of 28

Remote Sens. 2021, 13, 4155                                                                                                                                             2 of 26

                             of irrigation scheduling, amount, and time, and determines crop temperature with high
                             precision [8].

FFiigguurree11..TThheeggrraapphhiiccaallaabbssttrraaccttvviissuuaalliizzeesstthhee rreemmoottee--sseennssiinnggtteecchhnnoollooggyytthhaattppeerrffeeccttllyyaaddddrreesssseessccrrooppwwaatteerrssttrreessssuussiinngg
ccrrooppsstatatitsistitcicssaannddcocommppuutetrersosfotfwtwaraerebyby(1()1i)deidnetinftyiifnygintghethperopbrloebmle,m(2,)(i2m) pimlepmleemnteinngtinthgetmheetmhoedthoolodgoyl,o(g3y),d(e3l)ivdeerliinvgertihneg
the solution, and (4) addressing global crop water stress.
solution, and (4) addressing global crop water stress.

                                       CCrrooppwwaatteerrssttrreessss((CCWWSS))aasssseesssmsmeennt tisisoonneeofotfhtehefafcatcotrosrtshtahtadt edfienfientehteheenevnirvoirnomnemnetanl-
                                 itnatleirnatcetrioacntioofnaocfroapcaronpd aisnadpisrearepqrueirseiqteufiosirtepeforfroprmerifnogrmpriencgispiorneciirsriiognatiirornigsacthioenduslcihnegd[u9l]-.
                                 CinWg S[9i]s. dCeWfinSeids dasef"iannedinadsic"aatnorinthdaictadteotretrhmaitndeestweramteirnedsefiwcaittecronddefiitcioitncboansdeidtioonn bthaesesdcaolen
                                 othf ethsecaleleafoafntdhethleeacfroapndtetmhepecrraotpurteemanpaelryastiusrme eatnhaoldy"si.sTmheetChWodS",.wThhiechCWwaSs, dwehvieclhopweads
                                 bdyevIdelsoopeetdabl.y[1Id0]s,oweatsal.a[t1e0r]c,ownassidleartedr caosntsaindderaerd ainsdtaicnadtoardtoinadssiceastsotrhteosatsresesssathtehestlreeasfs
                                 aant dthcealneoapf yansdcaclaens.oTphyiscwalaess.aTnhiims pwraosvaenmiemnpt orofvtheme setnatnodfatrhdeizsetdanpdraorcdeidzuerdepfororcaesdsuesrseinfogr
                                 palsostesasnindgrepgliootnaanldscraelgeiwonaatlerscsatrlesws,aitnecrlustdriensgs,eivnacpluodtrinangsepviraaptoiotrna,nastpairlaatrigoenr, sactaalel.aTrgheer
                                 sstcaanled.aTrdhiezesdtamndeathrdoidzepdotmenettihaolldy apdodternetsisaeldlythaeddstrreesssseedfftehcetssbtryesasneaflfyezcitnsgbtyheanreallaytzioinngshtihpe
                                 breltawtieoennsThiIpR baentdwNeeInR-TSIWRIaRnads NanIRin-SdWicaIRtoar sofanveignedtiactaiotonrwofatveergaevtaitliaobnilwityat[e1r1a,1v2a]i.laBbaisleitdy
                                 o[1n1t,1h2e].stBaansdeadrdoinzetdhemsetathnodda,rdKihzoedrsamnedtheotda,l.K[1h3o]rrseapnodrteetdacl.ri[t1i3ca] lrleipmoirttaetdiocnrsitoicfallealifmaintda-
                                 ctaionnospoyfslceaalfeasnadndcaonfotphyeisrcraelleastiaonndshoifpthweiitrhrineldatiivoenrsehiepnwviirtohninmdenivtaerl sceonendvitiiroonnsm. Tehnetasltcuodny-
                                 udtiitliiozneds. tThheeresgturedsysiuontilbizaesdelitnheemreogdrelssainodn fboausnedlinCeWmSovdaelluaens doff0o.u3n7danCdW0S.15vafoluredsifofef r0e.n3t7
                                 laenadf- 0a.n15d fcoarndoipffye-rlenvet llesacfa-leasn.dTchaenosptuyd-lyevfeulrsthcaelres.hTohweedstuthdayt ftuhrethreergrsehsoswioendbtahsaetlitnhee
                                 mreegtrheossdiofonrblaesaeflainnedmcaenthoopdy fsocralleesafcaanndprcoavniodpeysisgcnailfiescacnatnrpesruovltisdfeorsiagpnpifliiccaantitornesinulltosnfogr-
                                 taeprmplifcoarteiocansitninlgon(Fgi-gteurrme 2fo).reTchaestrienggre(Fssigiounreb2a)s.eTlihneermegordeessl icoannbbaesereliandeimlyoudseeldcatonpbreorveiadde-
                                 CilWy uSssetdattuos parnodvsidime pCliWfieSsstthaetuasnalnydsisiomfpclriofpiesvathrieetayn, asolyilsitsypoef,carnodp evnavrierotyn,msoeniltatyl pfaec,taonrsd.
                                 envirTohnims cernitiaclaflarcetvoiresw. examined the analysis of crop water stress using remote-sensing
                                 systems. Initially, the relationship of relative water content (RWC) with equivalent water

                                 thickness (EWT) and soil moisture crop water stress is determined. Evapotranspiration

                                 and sun-induced chlorophyll fluorescence are then analyzed in relation to crop water

                                 stress using remote-sensing systems. Finally, the study presents an overview of remote-

                                 sensing technologies used to detect crop water stress, including optical sensing systems,

                                 thermometric sensing systems, land-surface temperature-sensing systems, multispectral

                                 (spaceborne and airborne) sensing systems, hyperspectral sensing systems, and the LiDAR

                                 sensing system.
Remote Sens. 2021, 13, 4155                3 of 26
Remote Sens. 2021, 13, x FOR PEER REVIEW  3 of 28

Figure 2. Crop water stress assessment: (a) Normal stomatal conductance with no stress retrieved, (b) comparison of irri-
Figure 2. Crop water stress assessment: (a) Normal stomatal conductance with no stress retrieved, (b) comparison of
gation water resources and micro-environmental conditions near the plant source to evaluate the intensity of the crop
irrigation water resources and micro-environmental conditions near the plant source to evaluate the intensity of the crop
water stress content in real-time field conditions.
water stress content in real-time field conditions.

                                       This critical review examined the analysis of crop water stress using remote-sensing
                                        The aims of our study are to:
                                 systems. Initially, the relationship of relative water content (RWC) with equivalent water
                                 t(hi)icknSeusms (mEWariTz)eatnhde csuoirlremnot issctuopree corfocprowpawteratsetrresstsreisssddeetteercmtiionnedu.sEinvgapreomtraontes-psiernastiionng
                                        technology.
                                 and sun-induced chlorophyll fluorescence are then analyzed in relation to crop water
                                 (ii) Present real-world examples and relevant methods.
                                 stress using remote-sensing systems. Finally, the study presents an overview of remote-
                                 (iii) Classify common features of crop water stress used in detection to benefit the literature
                                 sensing technologies used to detect crop water stress, including optical sensing systems,
                                        on this topic.
                                 thermometric sensing systems, land-surface temperature-sensing systems, multispectral
                                 (2s.pRaceelabtoirvneeWaantderaCirobnotrennet) asnendsCinrgopsyWstaetmers,Shtryepsserspectral sensing systems, and the Li-
                                 DAR sensing system.
                                        Inoue et al. [14] defined the relative water content (RWC) as the ratio of the available
                                       The aims of our study are to:
                                 quantity of soil moisture and crop water. The study further specified the RWC as
                                 (i) Summarize the current scope of crop water stress detection using remote-sensing
                                      technolRoWgyC. = (fresh weight - dry weight)/(turgid weight - dry weight)
                                 (ii) Present real-world examples and relevant methods.
                                 (wiiih)erCel:assify common features of crop water stress used in detection to benefit the litera-
                                       tFuWre =onfrtehsihs wtoepiigch. t (%);
                                        DW = dry weight (%);

                                 2. RelTaWtiv=e tWuragteidr Cwoenigthent (t%an).d Crop Water Stress
                                        Crop RWC is an important parameter in acquiring a crop's physiological status [15,16],
                                       Inoue et al. [14] defined the relative water content (RWC) as the ratio of the available

                                 biochemical status [17-20], and irrigation use efficiency [21-24]. Thanks to remote-sensing
                                 quantity of soil moisture and crop water. The study further specified the RWC as
                                 systems, these conditions can be effectively tracked for leaf water potential and moisture

                                                                                           RWC = (fresh weight-dry weight)
                                 availability for effective and timely measures [25].

                                                                                               (turgid weight-dry weight)
                                        RWC can be determined with high accuracy using spectral remote-sensing systems,
                                 where:
                                 whereby spectral data are analyzed to provide simple readable information. Qi et al. [26],
                                 FW = fresh weight (%);
                                 for example, successfully used remote-sensing spectral systems to acquire accurate RWC
                                 DW = dry weight (%);
                                 data in a timely manner. The equivalent water thickness (EWT) of a leaf is used to assess
                                 TW = turgid weight (%).
                                 RWC, which provides the available water quantity per unit leaf area [27], with which
                                 reseaCrcrhoeprsRcWanCthiesnadnetiemrmpoinretatnhte pleavrealmofestetrresins thacaqt uthireinlegafaexcpreorpie'sncpehsyosriowloilgl iecxaplesrtieantucse
                                 [i1n5t,1h6e]f,ubtiuorceh.eTmhiicsarlesmtaottues-s[e1n7s-i2n0g],taenchdniirqruigeactiaonnpurseeciesfefliyciqenucaynt[i2fy1-c2r4o]p. Twhaatnerkssttroesrsembaosteed-
                                 soennsleinagf msyesatseumresm, tehnetsse, wcohnidchitiiosnvsitcaalninbme aekffiencgtivceerltyaitnradckeceidsiofonrs.leaf water potential and
                                 moistTuhree qavuaainlatibtyiliotyf sfoolraerfrfaedctiiavteioannrdectiemiveeldy amlseoasauffreecsts[2c5ro].p EWT. EWT is related to crop
                                 leaf mRWoisCtucraen. Ubenddeertehrimghinseodlawr ritahdihaitgiohna, cthcuerwacayteursrienqgusirpeemcternatl irsemhigohte,-ssoenashinigghsyamsteomuns,t
                                 wofhweraetbeyr isspaebcstroarlbdedataanadretraannaslpyizreedd t[o28p]r. oEvWidTe, saismdpelteerrmeaidnaebdlewiinthforremmaottioens.eQnsioertsa, cl.a[n26b]e,
                                 fuosreedxtaomapnlael,yszuecccreospsfuwlalyteursdeedmraenmdoaten-dsemnsoiinsgtusrpeeacvtaraillasbyilsitteym. Tshteoraecmquotiere-saecncsuinragtseeRnWsorCs
                                 dcaotnatiinnuaotuimslyelmy monaintonrerE.WThTeaesqsuesivsmaleenntt wvaaltueersth(liockwneasnsd(EhWighT)),owf hailceha,fiins euxsterdemtoeacsasseesss,
                                 RleWadCt,owchroicphdperaotvhi,dweshtehreeaasvaairlaapbilde winactreerasqeuaanndtitpyopseitrivuenvitalleuaefsarreevae[a2l7m],iwnoitrhcrwohpicwhartee-r
                                 ssetraerscsh.eDrsecJaonngtheetnald. e[2te9r]mprineseetnhteedleEvWel Tofvsatlrueesss dtheatetrtmheinleeadfuesxipnegraiesnpceecstroarlwreimll oetxep-seerniesninceg
Remote Sens. 2021, 13, 4155  4 of 26

                                       system at three locations, where a good correlation of 0.70 was found between leaf water
                                       content and spectral indices at the 970 nm wavelength band.

                                            The EWT approach [29] for determining water weight (FW - DW) per the leaf area
                                       index (LAI) is expressed as

                                                                               EWT = (FW - DW)/LAI

                                              For determining crop water stress at the RWC level, understanding the leaf water
                                       content is important. The correlation with leaf water content is determined using a remote-
                                       sensing system [30]. Ceccato et al. [31], Wang et al. [32], and Zhang et al. [33] stated that
                                       leaf water content stress and low water potential are created through an imbalance. The
                                       imbalance appears when the evaporated leaf water content and absorbed water level (by
                                       the root system) are not equal. Leaf water stress depends on the plant condition. Its
                                       transpiration rate and temperatures are indirectly related to each other. In conditions of
                                       higher transpiration, low crop water stress is due to the water availability of the leaves,
                                       while low transpiration leads to high crop water stress (Figure 3) [34]. The transpiration
                                       rate, temperature, cooling, and heating effects are detected by remote-sensing systems and
                                       further processed for crop water stress assessment [35]. However, the methods for leaf
                                       water content estimation are overly time-consuming and are not considered efficient for
Remote Sens. 2021, 13, x FOR PEER RElVarIEgWe-scale spatial analysis. For limited spatial analysis, modern remote-sensing me5thoof d2s8
                                       provide useful results [36]. Among them is a canopy temperature remote-sensing method
                                       that has attracted considerable attention for characterizing crop water stress [37].

Figure 3. Remote-sensing estimation of the crop water stress using leaf transpiration, temperature, cooling, and heating
Figure 3. Remote-sensing estimation of the crop water stress using leaf transpiration, temperature, cooling, and heating
effects, and comparing it with the air and soil moisture levels.
effects, and comparing it with the air and soil moisture levels.

                                       Leaves are not considered a real representative of the complete canopy but are the
                                 top portion of the plant that receives direct solar radiation. This quantity of absorbed solar
                                 radiation influences crop parameters, such as leaf area index (LAI) and upper and lower
                                 leaf features, which are significant characteristics in the remote determination of RWC.
                                 Tanner [38] developed a system for studying canopy temperature in order to continuously
                                 monitor RWC. His study provided an overview of leaf temperature and explains how a

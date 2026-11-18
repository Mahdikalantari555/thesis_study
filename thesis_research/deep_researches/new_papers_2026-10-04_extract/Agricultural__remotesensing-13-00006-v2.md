# Extract: remotesensing-13-00006-v2.pdf

*First ~4 pages, extracted with pdftotext on 2026-10-04. Source: D:\RS\Thesis\New_papers$f*

---

remote sensing

Review

A Review of Remote Sensing Challenges for Food Security with
Respect to Salinity and Drought Threats

Wen Wen 1,* , Joris Timmermans 1,2, Qi Chen 1 and Peter M. van Bodegom 1

                                               1 Institute of Environmental Sciences (CML), Leiden University, Box 9518, 2300 RA Leiden, The Netherlands;
                                                    j.timmermans@cml.leidenuniv.nl (J.T.); q.chen@cml.leidenuniv.nl (Q.C.);
                                                    p.m.van.bodegom@cml.leidenuniv.nl (P.M.v.B.)

                                               2 Institute for Biodiversity and Ecosystem Dynamics, University of Amsterdam,
                                                    1090 GE Amsterdam, The Netherlands

                                               * Correspondence: w.wen@cml.leidenuniv.nl

Citation: Wen, W.; Timmermans, J.;             Abstract: Drought and salinity stress are considered to be the two main factors limiting crop produc-
Chen, Q.; van Bodegom, P.M. A Re-              tivity. With climate change, these stresses are projected to increase, further exacerbating the risks
view of Remote Sensing Challenges              to global food security. Consequently, to tackle this problem, better agricultural management is
for Food Security with Respect to Salin-       required on the basis of improved drought and salinity stress monitoring capabilities. Remote sensing
ity and Drought Threats. Remote Sens.          makes it possible to monitor crop health at various spatiotemporal scales and extents. However,
2021, 13, 6. https://dx.doi.org/10.3390/       remote sensing has not yet been used to monitor both drought and salinity stresses simultaneously.
rs13010006                                     The aim of this paper is to review the current ability of remote sensing to detect the impact of these
                                               stresses on vegetation indices (VIs) and crop trait responses. We found that VIs are insufficiently
                                               accurate (0.02  R2  0.80) to characterize the crop health under drought and salinity stress. In
                                               contrast, we found that plant functional traits have a high potential to monitor the impacts of such
                                               stresses on crop health, as they are more in line with the vegetation processes. However, we also
                                               found that further investigations are needed to achieve this potential. Specifically, we found that
                                               the spectral signals concerning drought and salinity stress were inconsistent for the various crop
                                               traits. This inconsistency was present (a) between studies utilizing similar crops and (b) between
                                               investigations studying different crops. Moreover, the response signals for joint drought and salinity
                                               stress overlapped spectrally, thereby significantly limiting the application of remote sensing to monitor
                                               these separately. Therefore, to consistently monitor crop responses to drought and salinity, we need to
                                               resolve the current indeterminacy of the relationships between crop traits and spectrum and evaluate
                                               multiple traits simultaneously. Using radiative transfer models (RTMs) and multi-sensor frameworks
                                               allow monitoring multiple crop traits and may constitute a way forward toward evaluating drought
                                               and salinity impacts.

Received: 16 November 2020                     Keywords: drought; salinity; traits; crop; remote sensing; meta-analysis
Accepted: 18 December 2020
Published: 22 December 2020

Publisher's Note: MDPI stays neu-              1. Introduction
tral with regard to jurisdictional claims
in published maps and institutional                  Food security is a serious problem around the world with a significantly large number
affiliations.                                  of food production systems currently at risk [1]. It is predicted that by 2030, the population
                                               suffering from food insecurity will rise to more than 840 million. Meanwhile, it is projected
Copyright: © 2020 by the authors. Li-          that the ongoing COVID-19 could further worsen the number of undernourished people
censee MDPI, Basel, Switzerland. This          around the world [2]. Further exacerbating this food security problem, crop productivity
article is an open access article distributed  itself also suffers great threats from stresses, such as drought stress, nutrient stress, and
under the terms and conditions of the          salinity stress, which reduce the yield at various locations by more than 50% [3]. Moreover,
Creative Commons Attribution (CC BY)           crops frequently suffer from a combination of stress [4], which further causes challenges
license (https://creativecommons.org/          for food production. In order to allow for sustainable agricultural production and mitigate
licenses/by/4.0/).                             the threat of global food shortages, the impact of these stressors needs to be monitored and
                                               alleviated.

Remote Sens. 2021, 13, 6. https://dx.doi.org/10.3390/rs13010006  https://www.mdpi.com/journal/remotesensing
Remote Sens. 2021, 13, 6  2 of 14

Remote Sens. 2021, 13, x FOR PEER REVIWEWater stress, in the form of droughts, has been identified as the most seriou2sotfh1r6eat for

                                global agriculture, approximately affecting 40% of the world's land area [5]. Between 1980

                                and 2020, droughts have caused economic damages of around $6 billion per year in the

                                UnitedWStaatteerss,terexscse,einditnhge fdoarmaogfedsrofruogmhtso,thhaesrbweeenatihderntaifnieddcalismthaetemdoisstassetreirosu[s6t]h. rLeaikt ewise,
                                in fCohr ignloab, athl aegarviceurlatugree,aanpnpuroaxliemcaotneloymaifcfedctainmga4g0e%douf ethteowdororludg'shltanwdaasre$a12[5.8]. bBieltlwioenenduring
                                2001698-020a1n5d [270]2.0,Idnroaudgdhittsiohnavteocdauroseudgehcto,nsoamliincidtyamhaagseesmofearrgoeudndas$6abmilliaojnorpefarcyteoarr liinmiting
                                thethperUodniutecdtivStiatyteso,fecxrcoeepdsi.nSgoduatmhawgeesstfrUomnitoetdheSrtwateeasth, esrouanthdecrlinmAatseiadi(siansctelursd[i6n].gLIinked-ia and
                                Pakwiisstea,nin), Ceahsintear, nthAe saivae(rWageesatenrnnuaCl heicnoan)o,meaicstdearmnaAgeusdturaeltioa,darnodugnhotrwthaws $e1s2t.A8 bfriillciaonare the

                                       during 2006-2015 [7]. In addition to drought, salinity has emerged as a major factor limit-
                                most affected areas [8-10]. The United Nations Food and Agriculture Organization (FAO)

                                       ing the productivity of crops. Southwest United States, southern Asia (including India
                                has estimated that 11% of the global irrigated area (34 Mha) is currently affected by different

                                       and Pakistan), eastern Asia (Western China), eastern Australia, and northwest Africa are
                                levtehles mofosstalaifnfeitcyte. dTahreeraesin[8,-C10h]i.nTah,ethUenUitenditNedatiSotnasteFso,oPdakanisdtaAng,raicnudltuInrediOarhgaonldizamtioonre than
                                60%(FAofOt)hheastoetsatilmaaretead(t2h1atM11h%a)o. f the global irrigated area (34 Mha) is currently affected by

                                   difWferheinlte lpevreeslsenoftlsya, ldinriotyu.gThhtearenidn,sCalhiinniat,ytahlereUandiytedpoSstaetetrse, mPaeknisdtoanu,sacnhdalIlnedniagehsoflodr food
                                promdourcettihoann, 6it0%haosf btheeentotfaolraerceaas(t2e1dMthhaat).both stressors will increase both spatially and in

                                severityW. hCilleimpraetseencthlya,ndgreouwghiltl ainndcrseaalisneittyhaelrferaedqyuepnosceytarenmdesnedvoeursitcyhaollfedngroesufgohrtfoeovdents in

                                nupmroedrouuctsiorne,giitohnass [b1e1e-n1f4o]r,elceaasdteidngthtaot bdortahmstarteiscsoimrs pwaiclltsinocrneacsreopbogthroswpatthiaallnydanpdroinductiv-
                                itys[e1v2e]r.itSyp. Cecliimficaatellych, ahniggehewriltlemincpreearasetutrheesfarenqdueloncwyearnhdusmeviedriittyy hofavderobuegehnt esvheonwtsninto lead
                                to naunminercorueassrienggiownsa[t1e1r-1d4e]m, leaanddin(gintotdhreamfoartmic iomfpcarcotps oenvcarpooptrgaronwspthiraantidopnr)oadnudctiavirteyduced
                                wa[t1e2r].aSvpaeilcaifbicilailtlyy,frhoigmheerffteemctipveeraptruerceispaintadtiloonw,ewr hhuilme isdimityuhltaavneeboeuesnlys,haolwonwteorlaeanddtionafrnequent

                                       increasing water demand (in the form of crop evapotranspiration) and a reduced water
                                effective precipitation significantly reduces water availability, thereby negatively affecting

                                       availability from effective precipitation, while simultaneously, a lower and infrequent ef-
                                food production [15]. Similarly, it has been suggested that salinity will impact 50% of

                                       fective precipitation significantly reduces water availability, thereby negatively affecting
                                thefocoudltpivroadteudctiloannd[15b]y. S2im05il0ar[l1y6,]i.t hSaosilbseaelninsiutgygleesvteedlsthhaatvsealbineietynwshilloiwmnpatcot i5n0c%reoafstehein arid
                                lancdusltibveactaeduslaenfdrebsyh2w05a0te[1r6i]s. Snooitl asavlainiliatyblleevteolsdhraavine baececnusmhuowlantetdo isnaclrtesa[s1e7i]n, tahriudslaanctdisng as a
                                prabcetciacaulsleyfirrersehvwerastiebrleispnrootcaevsasi.laMbloerteoodvreari,nsoaiclcsuamliunliaztaetdiosnalthsa[s17b]e, ethnusshaocwtinngtaosiancprreaacs-e with
                                thetiecaxlplyanirsrieovnerosfibalegrpicroucletussr.eMtoorseeomveir-a, rsiodilasnaldinaizraidtiorneghiaosnbse[e1n7-s1h9o]w. nThtoerienfcorerea,sethweiitnhcrease
                                in dthreoeuxgphatnfsrioenquoef nagcryicaunltdurseotiol saemlini-iatryiduanndderarcildimreagtieoncsh[a1n7g-1e9f]u. Trthheererfeoxrea,ctehrebiantceretahsee threat

                                to cinrodpropurgohdtufrcetqiounen. cy and soil salinity under climate change further exacerbate the threat
                                   to Dcrroopupgrhotdaunctdiosna.linity cannot be seen independently of each other. As an aspect of water

                                quality,Dsraoluingihtyt ahnads bsaeleinnitpyrocavnennottobienscereenasienddeupreinndgednrtloyuogfhetapcehriootdhesr[.1A4s,2a0n,2a1s].peScpteocfifically,
                                it hwasatbeereqnuaslhitoyw, snaltihnaittydhuaes btoeelonwpreorvreinvetor lienvcreelas,sehyddurrionlgogdircoaulgdhrtopuegrihotdssig[1n4i,fi20c,a2n1t]l.ySpinec- reases
                                thecisfaiclainlliyt,yitinharsivbeeresn[1sh4,o2w2]n. tChoatndseuqeuteonltolwy,eirnrcirveearsleedvedlsr,ohuygdhrtofloregqicuael ndcryouagnhdt ssiegvneifrii-ty will

                                       cantly increases the salinity in rivers [14,22]. Consequently, increased drought frequency
                                exacerbate the accumulation of salinization and adversely affect crop yield and sustainable

                                       and severity will exacerbate the accumulation of salinization and adversely affect crop
                                agricultural development [23]. As such, there are already numerous areas in the world

                                       yield and sustainable agricultural development [23]. As such, there are already numerous
                                whaerreeasbionththderwouogrlhdtwanhedresablointhitydrsoturegshst caon-docsacluinri(tyFisgturerses 1c)o.-oFcucrutrhe(Frimguorree,1)d.uFeurttohesre-a level
                                risme ionret,hdeufeuttoursee,acluevlteilvraitseedinlatnhed f(uatnudrei,ncuplatirvtaitceudlalarncdoa(asntadl ilnowpalartnicdusla) rwciolal shtaalvleowa -higher
                                prolabnadbsi)liwtyiltlohsauveffearhfirgohmer bporothbadbriolituygthotsaunffdersafrloinmitbyostthredsrsou[2g4h-t2a7n]d. Tsahleinrietfyosrter,edssro[2u4g-ht and
                                sal2in7]i.tyThsehroefuolrde, ndorotubgehtvaienwd esadliinnitdyespheonudldenotltyb, eavnidewimedpiancdtespoefndjoeinnttlyd, raonudgimhtpacntds osfalinity

                                strejosisnttodraogurgichut latnudraslalpinroitdyustcrteisosntoshaogruilcdulbtuerainl vperosdtiugcattieodn.should be investigated.

Figure 1. Global distribution of drought and salinity. In panel (a), the global map of soil salinity change is shown [10],
while in panel (b) the global map of drought hazard [28] is shown. Global soil salinity map was extracted from [10] and
then transformed to the plate carrée projection by ArcGIS.
Remote Sens. 2021, 13, 6                                                                                                                                              3 of 14

                                Remote sensing (RS) is a key method for monitoring crop health due to its capability
                          to monitor and detect effective changes of large areas at relatively low-cost, in comparison
                          to traditional methods [29]. For this purpose, several vegetation indices (VIs) such as
                          the Normalized Difference Vegetation Index (NDVI) [30], the Perpendicular Vegetation
                          Index (PVI) [31] and the Soil Adjusted Vegetation Index (SAVI) [32] have been developed
                          in the past to monitor agricultural production. In addition, drought (impact) indicators
                          have been developed that account for seasonality effects (based on long-term standardized
                          observations), e.g., the Vegetation Condition Index (VCI) [33], the Vegetation Health Index
                          (VHI) [34], and the Normalized Difference Water Index (NDWI) anomalies [35]. However,
                          each of these drought indicators has specific limitations that limit its applicability as early
                          warning signals of drought [36]. As a consequence, results vary among different indices,
                          and most applications with these indicators focus on local scales and individual crop types.
                          As such, no comprehensive vegetation index has been developed that can be applied
                          globally to investigate drought impact consistently [36]. Similar to drought monitoring,
                          vegetation indices, used to monitor crop salinity stress, are also affected by limitations
                          regarding noise, halophyte presence, and spatial resolution [37,38]. In response, a more
                          comprehensive measurement of the reflectance spectrum representing crop traits is required
                          to monitor crop growth and health as affected by stress. In this regard, it has been shown
                          that hyperspectral data have a strong potential to detect biophysical and biochemical
                          parameters [39,40]. In addition, various studies highlighted that other (multi-spectral) RS
                          methods (e.g., microwave, thermal infrared (TIR), hyperspectral) show great promises to
                          characterize vegetation stress [41,42]. However, the number of studies focusing on this is
                          limited, and only part of these investigations focused on agricultural RS applications [43,44],
                          while studies on the relationship between crop traits and spectral properties in relation to
                          under drought or salinity stress is even more limited. Therefore, an in-depth analysis of the
                          reflectance spectrum of crop traits under stress is required to better identify plant drought
                          and salinity stress by remote sensing.

                                The main objective of the study is to evaluate the current state and shortcomings in the
                          RS monitoring of crops under drought and/or salinity stress. Based on a comprehensive
                          analysis, we evaluate the potential of remote sensing to identify and assess agricultural
                          ecosystems under drought and salinity stress through vegetation indices and plant traits.

                          2. Methodology

                                To evaluate the current state of monitoring drought and salinity stress by RS, we ap-
                          plied a thorough systematic review of recent scientific publications. For this, we (a) collected
                          a large representative set of scientific publications, and (b) analyzed their results to identify
                          the response patterns in vegetation indices and in plant traits. For the analysis of plant
                          traits, we classified them according to underlying plant functions (relating to primary
                          production, hydrological processes, and osmosis). This allows us to coherently investigate
                          the potential of remote sensing for monitoring the salinity/drought impact on biological
                          pathways/processes.

                          2.1. Creating Representative Database though a Systematic Review

                                In order to facilitate the analysis of a representative set of recent publications, we
                          adopted an optimized systematic review approach [45]. Specifically, we focused on sci-
                          entific peer-reviewed papers published between 2005 and 2020 through Web of Science
                          (WOS) and Google Scholar (GS) (Figure 2). This approach first requires the definition of
                          a representative set of keywords. For our study, these keywords were "remote sensing",
                          "drought", "salinity", "agriculture", and "traits", as well as their synonyms (such as RS,
                          food security, etc.). Afterwards, publications were selected from WOS and GS according to
                          the occurrence of combinations of these keywords in the title, abstract, author keywords,
                          and keywords plus, to create a first selection of publications, leading to 1184 selected
                          records. Then, this set of publications was screened to capture only papers that analyzed
                          (a) the impact of drought/salinity stress on VIs/traits of crops by remote sensing, and
Remote Sens. 2021, 13, 6  to the occurrence of combinations of these keywords in the title, abstract, author key-
                          words, and keywords plus, to create a first selection of publications, leading to 1184 se-
                          lected records. Then, this set of publications was screened to capture only papers that an-
                          alyzed (a) the impact of drought/salinity stress on VIs/traits of crops by remote sensing,
                          and (b) included information on the spectral wavelength on which the analysis was b4aosef 1d4.
                          This resulted in 78 unique records. Next, through snowballing these records (to capture
                          papers that were missed in the first step), an additional 49 publications were obtained. In
                          (b) included information on the spectral wavelength on which the analysis was based.
                          total, 115 publications (Table S1) fitting these criteria were identified after removing 12
                          This resulted in 78 unique records. Next, through snowballing these records (to capture
                          duplicates. More details on each step are provided in the supplementary information (Fig-
                          papers that were missed in the first step), an additional 49 publications were obtained.
                          ure S1). Maps of co-authors and co-occurrences based on the results of the systematic re-
                          In total, 115 publications (Table S1) fitting these criteria were identified after removing
                          view were created through VOSviewer (Figure S2).
                          12 duplicates. More details on each step are provided in the supplementary information
                          (Figure S1). Maps of co-authors and co-occurrences based on the results of the systematic
                          review were created through VOSviewer (Figure S2).

 · Searching                  Screening  ·78 records          Included
 from web of                               retained
 science and              ·1184 records                  ·115 records
google scholar                           ·49 records        included
                                         added from
  Identification                         snowballing

                                            Eligibility

                                        Figure 2. Flowchart of the systematic review.

                          2.2. ExtracFtiigounroef2D. Frloouwgchht/aSrat loinf itthyeSsytrsetsesmIantfiocrrmevaiteiown.

                                From the full set of publications on drought and salinity stress of agricultural crops,
                          w2.2e.eExxtrtaracctetidonthoef Dcorrorueglahtti/oSnalsitnrietnygStthrsesbseItnwfoeremnavtieognetation indices/crop traits responding to
                          drouFghrotmantdhesafluinllitsyetstorfespsuabnldicastpieocntsraolnbadnrodus/gwhtaavneldensagltihnsi.tyFisntarellsys, 3o4f8agcorircruelatutiroanlscrwoeprse,
                          wfoeunexdt,ramcteodngthwe hcoicrhre1la0t2iotrnasitsrewngertehswbaevtwelenengtvhecgoertaretiloantioinds,ic1e7s1/cwroepretrVaIists-wreasvpeolenndginthg
                          tcoordrerolautgiohntsa, nadndsa7l5intirtayitstwreesrseaVnIds scpoerrcetrlatliobnasn.dAs/lwl 1a7v1elVeinsg-wthasv. eFliennaglltyh, c3o4r8recloatriroenlastitohnast
                          werfeoufonudnfdo,caumseodngonwdhriocuhg1h0t2, atrnaditsnowreerveiewwaevdelsetnugdthy pcororrveildaetidoncso,rr1e7l1atwioenrse fVorIss-awlianvitey-
                          lsetnregstsh. correlations, and 75 traits were VIs correlations. All 171 Vis-wavelength correla-
                          tions that we found focused on drought, and no reviewed study provided correlations for
                          2.3. Classification of Plant Traits and Vegetation Indices
                          salinity stress.

                                After the creation of our representative set of publications, we clustered the traits into
                          2fo.3u.rCglarossuifpicsattoiorneolaftPeltahnet Timrapitascatnodf dVreoguetgahtito/nsIanlidniciteys stress to biological processes. Specifi-
                          cally, we classified the traits together on the basis of their definitions and the functional

                                After the creation of our representative set of publications, we clustered the traits into
                          processes involved [46,47]. This provided us with four clusters, namely biomass traits,
                          four groups to relate the impact of drought/salinity stress to biological processes. Specifi-
                          photosynthesis traits, water traits, and osmosis traits. Afterwards, each cluster was further
                          cally, we classified the traits together on the basis of their definitions and the functional
                          divided into RS (directly measurable by RS) and In-RS (indirectly derived by RS) (Table 1).
                          processes involved [46,47]. This provided us with four clusters, namely biomass traits,

                                In addition to individual plant functional traits, well-known RS vegetation indices
                          photosynthesis traits, water traits, and osmosis traits. Afterwards, each cluster was further
                          have been related to the responses to drought and/or salinity stress. For consistency, we
                          divided into RS (directly measurable by RS) and In-RS (indirectly derived by RS) (Table
                          clustered the results of these studies on the basis of a functional classification, resulting
                          1).
                          in xanthophyll indices, water content indices, carotenoid indices, and greenness indices
                          (Table 2).

                              Table 1. Classification of plant traits included in this study.

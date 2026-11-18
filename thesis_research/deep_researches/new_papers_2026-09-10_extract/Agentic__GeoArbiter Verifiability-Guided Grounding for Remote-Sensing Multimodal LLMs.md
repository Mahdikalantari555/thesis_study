# GeoArbiter Verifiability-Guided Grounding for Remote-Sensing Multimodal LLMs.pdf

- Category: Agentic
- Pages: 14
- Path: D:\RS\Thesis\New_papers\Agentic\GeoArbiter Verifiability-Guided Grounding for Remote-Sensing Multimodal LLMs.pdf

## Metadata

```json
{
  "/Author": "Xuechen Li",
  "/Creator": "arXiv GenPDF (tex2pdf:8def8d8)",
  "/DOI": "https://doi.org/10.48550/arXiv.2608.00877",
  "/License": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/Title": "GeoArbiter: Verifiability-Guided Grounding for Remote-Sensing Multimodal LLMs",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2608.00877v1"
}
```

## First pages


===== PAGE 1 =====
GeoArbiter: Verifiability-Guided Grounding for Remote-Sensing
Multimodal LLMs
Xuechen Li
University of Minnesota, Twin Cities
li003487@umn.edu
Abstract
Remote-sensing multimodal large language
models (MLLMs) often assert facts that im-
agery cannot establish, such as a facility’s iden-
tity or function. Coordinate-keyed geographic
retrieval can supply this missing knowledge,
improving fMoW land-use accuracy by 12.06–
17.19 points across three open MLLMs. How-
ever, retrieved records can also contradict vis-
ible evidence, and we find that models fre-
quently follow the records even when the im-
age is decisive. We argue that source trust
should therefore depend oncross-modal ver-
ifiability: geographic records are most useful
for attributes the image cannot verify and most
dangerous when they dispute visually verifi-
able attributes. We introduce GeoArbiter, a
training-free pipeline that operationalizes this
principle by injecting only image-unverifiable
geographic facts. Unlike arbitration prompts,
which leak across attribute types and bias
yes/no responses, content-level filtering pre-
serves 84.69–87.15% of the full-retrieval ac-
curacy gain, reduces claim-level hallucination
by 9.58–26.34% under a source-blinded judge,
and improves robustness to conflicting records
across all three models. These results identify
verifiability-guided content selection as a sim-
ple, effective mechanism for grounding remote-
sensing MLLMs in fallible geographic knowl-
edge.
1 Introduction
Multimodal large language models adapted to
remote-sensing (RS) imagery can describe satel-
lite scenes and answer open-ended questions flu-
ently (Qwen Team, 2025; Zhu et al., 2025; Li
et al., 2024). Yet many consequential errors are
not perceptual: a model may misname a facility,
invent its institutional role, or fabricate adminis-
trative context that pixels cannot establish. We
call theseknowledge hallucinations, distinguishing
them from errors about visible content (Li et al.,
60 65 70 75 80 85
land-use QA accuracy (%)  →  more useful
40
50
60
70
80
90
conflict robustness (%)  →  more trustworthy
Qwen2.5-VL
(76.8, 93.2)
(79.3, 72.0)
InternVL3
(73.5, 90.5)
(76.2, 62.2)
LLaVA-OV
(81.0, 91.2)
(82.6, 36.8)
prior retrieval baselines (accuracy only)
RS-RAG GeoNames Wiki
no knowledge
full injection (inject-all RAG)
GeoArbiter (ours)
Figure 1:GeoArbiter preserves accuracy and ro-
bustness.Full OSM injection improves land-use QA
but becomes brittle to a wrong record; verifiability-
stratified injection remains in the top-right across all
three MLLMs.
2023; Yin et al., 2023). They persist across RS
model families (Zhou et al., 2026; Liu et al., 2026)
and undermine applications in which an incorrect
facility identity can be more costly than a missed
object.
Geographic retrieval appears to offer a natu-
ral remedy. Every RS image has coordinates,
which provide an exact key into resources such as
OpenStreetMap (OSM; Haklay and Weber, 2008),
GeoNames, and land-cover maps. Prior work, how-
ever, mainly uses these resources during training
(Wang et al., 2024; Muhtar et al., 2024; Ailuro
et al., 2026; Bai et al., 2025; Anderson et al., 2025).
Inference-time RS retrieval instead relies on vi-
sual similarity to landmark descriptions (Wen et al.,
2025), which poorly covers ordinary schools, sub-
stations, and depots; coordinate-keyed text systems
(Manvi et al., 2024; Yu et al., 2025; Feng et al.,
2025) do not face conflicts between records and an
image.
Such conflicts make grounding a source-
arXiv:2608.00877v1  [cs.LG]  1 Aug 2026
===== PAGE 2 =====
selection problem. Geographic databases are in-
complete, stale, and potentially corrupted (Han
et al., 2026); a record can supply an invisible func-
tion but can also claim that a visibly absent runway
exists. Prior conflict studies examine perception,
context, and parametric memory (Jia et al., 2025;
Liu et al., 2024; Carragher et al., 2025; Ortu et al.,
2025; Lietzow et al., 2026), typically through syn-
thetic contradictions and instruction- or decoding-
level remedies (Liu et al., 2024; Shi et al., 2023).
They do not ask whichattributeseach modality is
qualified to resolve.
We proposecross-modal verifiabilityas that cri-
terion: records should dominate for attributes that
an image cannot verify (e.g., function or name),
whereas the image should dominate when a record
disputes visible structure. GeoArbiter enforces this
policy in the retrieved content rather than asking
a frozen model to follow it. A key-level filter re-
tains function and identity records and withholds
physical-structure records before prompting (Fig-
ure 2).
We make three contributions. First, coordinate-
keyed structured retrieval improves land-use QA by
12.06–17.19 points on all 28,087 functional fMoW
validation images. Second, retrieval’s benefit and
risk separate by verifiability: it reduces unsup-
ported function and name claims, whereas fabri-
cated visible-feature records cause 13.50–51.00-
point losses; none of six arbitration prompts re-
covers the image-only baseline. Third, GeoArbiter
preserves 84.69–87.15% of the retrieval gain, cuts
claim-level hallucination by 9.58–26.34% under a
source-blinded judge (19.28–45.19% with the stan-
dard judge), and outperforms every prompt-level
alternative. Historical OSM analysis further shows
that apparent map–image age gaps mostly reflect
mapping completion, not physical change.
2 Related Work
Hallucination in general and RS MLLMs.Ob-
ject hallucination in general-domain MLLMs is
well documented (Li et al., 2023), and post-hoc sys-
tems such as Woodpecker verify generated claims
after decoding (Yin et al., 2023). RS-specific stud-
ies broaden the taxonomy beyond object presence:
RSHallu characterizes domain-specific knowledge
errors (Zhou et al., 2026), while RADAR separates
factual and logical failures and steers attention dur-
ing decoding (Liu et al., 2026). These methods
improve how a model uses its existing visual and
parametric evidence, but cannot supply a facility
name or institutional function that the model never
learned. Our setting targets precisely this missing-
knowledge regime, while also measuring the new
failure mode created when external knowledge con-
tradicts perception.
Retrieval augmentation for remote sensing.
RS-RAG retrieves encyclopedia entries through
cross-modal embedding similarity and improves
captioning and VQA for recognizable landmarks
(Wen et al., 2025). Other systems retrieve ex-
emplars for SAR imagery (Ramirez et al., 2026),
image-derived context for aerial scenes (Xue et al.,
2026), or compose Earth-observation tools at in-
ference time (Zhao et al., 2026); CrisiSense-RAG
combines reports and post-event imagery across
evidence streams (Xiao et al., 2026). These ap-
proaches establish the value of inference-time con-
text, but visual-similarity retrieval favors distinc-
tive, documented sites and may return the wrong in-
stance of an ordinary-looking facility. GeoArbiter
instead uses coordinates as an exact retrieval key
and evaluates ordinary function-defined locations
at full fMoW scale. More importantly, we treat
retrieval as a trust problem: the retrieved block is
fallible evidence, not an oracle.
OSM in vision–language learning.OSM has
been distilled into RS captions (Wang et al., 2024),
instruction data and multimodal alignment cor-
pora (Muhtar et al., 2024; Bai et al., 2025), map-
based pre-training data (Anderson et al., 2025),
and rendered-tile domain adaptation (Ailuro et al.,
2026). All primarily consume OSM before deploy-
ment. SkyScript is especially related because it
classifies tags by whether overhead imagery can
visually ground them, retaining groundable tags to
improve caption fidelity (Wang et al., 2024). We
use the complementary inference-time selection:
image-verifiable records are the dangerous ones
when incorrect, so GeoArbiter withholds them and
injects facts the image cannot adjudicate. Text-only
coordinate-grounded systems (Manvi et al., 2024;
Yu et al., 2025; Feng et al., 2025) do not observe an
image and therefore do not face this source conflict.
Knowledge conflict and adaptive retrieval.
Multimodal conflict benchmarks construct contra-
dictions among context, images, and parametric
memory (Jia et al., 2025; Carragher et al., 2025);
mechanistic studies further identify modality-
specific preference patterns (Ortu et al., 2025; Li-
===== PAGE 3 =====
Figure 2:GeoArbiter pipeline.Image coordinates retrieve nearby OSM features, which may be stale or incomplete.
A deterministic verifiability filter withholds physical-structure keys that the image can check (red) and textualizes
image-unverifiable functional records (blue) into a knowledge block. The frozen MLLM answers from the image,
question, and filtered knowledge.
etzow et al., 2026). Focus-on-vision prompting is
often insufficient (Liu et al., 2024), and injected
text can override visual evidence (Khayatan et al.,
2026). In text RAG, incorrect or outdated passages
harm generation (Ouyang et al., 2025), motivat-
ing retrieval-quality estimation, query-complexity
routing, reflection, and answer-attribution filter-
ing (Asai et al., 2024; Yan et al., 2024; Jeong
et al., 2024; Chen et al., 2026). Those methods
ask whether retrieval is needed, relevant, or re-
liable. Verifiability is a different axis: an OSM
record may be relevant and usually correct, yet still
be the wrong evidence to expose when the image
can directly settle the disputed attribute. To our
knowledge, prior work has not used this property
to select multimodal context or directly compared
content-level with instruction-level arbitration.
3 GeoArbiter
3.1 Task formulation
Given an RS image I, coordinates (ϕ, λ), footprint
radius r, and instruction q, a frozen MLLM pre-
dicts ˆy= arg maxy pθ(y|I, q, K). The knowl-
edge block K=τ(S) deterministically textualizes
retrieved records S. Because no parameters are
updated, the central design choice is which records
to expose to the model.
3.2 Coordinate-keyed retrieval
Let c(f) be the centroid of OSM feature f and
κ(f) its primary tag key. We retrieve every feature
within ¯r= clamp(r,300,1500) m of (ϕ, λ), form-
ing R; full injection uses S=R . Dated Geofabrik
extracts and a spatial grid index make retrieval re-
producible without live API calls. On 461 images
available through both routes, local and API fea-
ture counts correlate at 0.97. Ablations add the
nearest GeoNames toponym and dominant ESA
WorldCover class (Zanaga et al., 2022). Unlike
embedding retrieval, coordinates identify ordinary
as well as landmark locations and cannot return a
visually similar but geographically unrelated site.
3.3 Cross-modal verifiability and stratified
injection
The pivotal property of a fact is whether the im-
age could in principle confirm or refute it. We as-
sign each OSM key a binary label v: keys express-
ing function or identity (amenity, shop, tourism,
military, office) take v= 0 , whereas keys ex-
pressing physical structure ( building, highway,
aeroway, natural, landuse) take v= 1 ; Ap-
pendix D gives the complete map and textualiza-
tion. Verifiability belongs to the attribute, not the
object: a building may be visible while its institu-
tional role is not.
===== PAGE 4 =====
For attribute class a, let G(a) be the accuracy
change from injecting K instead of no knowledge.
We test two predictions:
E[G|v=0]>E[G|v=1],
G(a|v=1,conflict)<0. (1)
Thus, correct records may still provide a useful
prior for visible attributes, but their marginal value
should be smaller; when such a record conflicts
with the image, its effect should be negative. A pol-
icy conditioned on v should therefore outperform a
fixed preference for either source.
Verifiability is distinct from both relevance and
source reliability. A nearby runway record is rele-
vant to a runway question, and OSM may be highly
accurate on average, but a false runway record
should not override an image in which the structure
is visibly absent. Conversely, a school-

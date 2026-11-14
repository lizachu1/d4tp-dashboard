# Connecting California's learner journey

**Linkage gap analysis and a 10-year strategy, prepared for Data 4 the People**
Research current as of November 14, 2026. Companion to the dashboard (`index.html`) and database (`data/`).

## The short version

California has built one of the most ambitious statewide longitudinal data systems in the country. The Cradle-to-Career Data System (C2C) grew from 8 data partners submitting data in 2023 to 16 in 2026, and it now links TK-12, community college, CSU, UC, financial aid, CalKIDS, developmental services, social services and wage records. The handoff from high school to college is now one of the strongest data links in the nation.

But the system is named "cradle to career" and does not yet start at the cradle, and it sees only part of a career.

1. **The first five years are a blind spot.** A child can pass through birth records, Medi-Cal, WIC, home visiting, Early Start, CDSS child care, state preschool, Head Start and First 5 without a single shared identifier. The first durable ID, the SSID, arrives at TK or kindergarten. Of the 19 early childhood and birth sources we cataloged, only two (CalKIDS and DDS) are C2C partners today.
2. **Careers are measured with a blunt tool.** Earnings come from UI wage records that carry no occupation, hours or location, leave out self-employed, gig, federal and out-of-state work, and depend on an SSN that many immigrant students do not have.
3. **The edges are missing.** Private colleges, adult schools, apprenticeship, justice-involved learners, students experiencing homelessness and students who leave the state are partly or wholly invisible.
4. **The barriers are mostly governance, not technology.** There is no lead agency or statute for an early childhood integrated data system (AB 2092 was held in 2026), no common definitions across agencies, and no durable funding for partner agencies to do the work.

The proposal: a three-phase, 10-year statewide linkage strategy (2027 to 2037) that begins with the D4TP 2027-2028 agenda and ends with every California child having a privacy-protected, lifelong learner record from first public contact to career.

## What exists today

The database catalogs **60 data sources** across seven segments, with **84 documented links** between them and **18 person identifiers**.

| Segment | Sources | In C2C (yes) | Partial | Planned | Not in C2C |
|---|---|---|---|---|---|
| Prenatal and birth | 4 | 1 | 0 | 0 | 3 |
| Early care and education | 15 | 1 | 1 | 3 | 10 |
| TK-12 | 10 | 3 | 3 | 0 | 4 |
| Postsecondary | 11 | 4 | 2 | 0 | 5 |
| Workforce and earnings | 12 | 3 | 3 | 1 | 5 |
| Health and human services | 5 | 0 | 3 | 0 | 2 |
| Linkage hubs | 3 | 1 (C2C itself) | 0 | 1 (ECIDS) | 1 (DxF) |

The strongest existing links are the ones built for operations: CALPADS to CaliforniaColleges.edu and CSAC for transcripts and Cal Grant GPAs, the weekly CDE and CDSS foster youth match, direct certification for school meals against CalFresh and Medi-Cal, and CDPH birth files opening CalKIDS accounts. These prove that California can match human services and education records routinely when there is a clear purpose and legal authority.

## Where the chain breaks

The dashboard's "Identifier relay" view shows the core problem. Each segment hands the next a different key, and in early childhood there is no key to hand.

| Age | IDs a typical child might have | Shared with the next stage? |
|---|---|---|
| Birth | Birth certificate number, Medi-Cal CIN, WIC ID, CalKIDS account | Only to CalKIDS |
| 0 to 3 | CIN, DDS UCI (Early Start), local child care case ID, home visiting ID | No |
| 3 to 5 | Local CSPP or Head Start ID, optional SSID in CAPSDAC | Rarely |
| TK to 12 | SSID, plus flags from CIN and CWS matches | Yes, to CCC, CSAC and CCGI |
| College | CCCID, CSU and UC campus IDs, SSN | Through C2C matching |
| Work | SSN and employer account number | Through C2C matching, if the person has an SSN |

C2C solves the later stages with probabilistic person matching on names, birth dates, SSNs and partner IDs. That approach can extend to early childhood only if early programs collect matchable information and are allowed to share it.

## Gap heatmap

Scores run from 0 (strong) to 4 (critical gap). The full table, with reasons, is in `data/heatmap.json`.

| Handoff | Shared ID | Individual records | In C2C | Legal authority | Definitions | Timeliness | Public use |
|---|---|---|---|---|---|---|---|
| Birth to early care | 4 | 3 | 4 | 3 | 3 | 3 | 4 |
| Health and home visiting to early care | 4 | 3 | 4 | 4 | 3 | 3 | 4 |
| Across ECE programs | 4 | 2 | 4 | 2 | 3 | 2 | 3 |
| Early care to TK and kindergarten | 3 | 2 | 4 | 2 | 3 | 2 | 4 |
| Human services to TK-12 | 2 | 1 | 2 | 2 | 2 | 1 | 3 |
| TK-12 to postsecondary | 1 | 0 | 0 | 1 | 2 | 2 | 2 |
| Community college to CSU and UC | 2 | 0 | 1 | 2 | 3 | 2 | 2 |
| Private, out-of-state and adult education | 3 | 3 | 3 | 2 | 3 | 3 | 3 |
| Postsecondary to UI-covered jobs | 2 | 1 | 0 | 1 | 2 | 2 | 2 |
| Apprenticeship and job training to earnings | 2 | 2 | 2 | 2 | 3 | 3 | 3 |
| Self-employed, gig, federal and out-of-state work | 2 | 4 | 4 | 3 | 3 | 3 | 4 |
| Educator pipeline (ECE and TK-12) | 3 | 2 | 3 | 2 | 3 | 3 | 3 |
| Justice, homelessness and reentry | 4 | 3 | 4 | 4 | 3 | 3 | 4 |

## The 13 gaps

| # | Gap | Severity | Type |
|---|---|---|---|
| G1 | No statewide child identifier before school | 5 | Identifier |
| G2 | Early learning and care is still outside C2C | 5 | Coverage |
| G3 | No legal home or lead agency for an ECIDS | 4 | Governance |
| G4 | Wage records lack occupation, hours and location | 4 | Content |
| G5 | SSN dependence leaves out immigrant students | 4 | Identifier |
| G6 | Earnings outside UI coverage are invisible | 3 | Coverage |
| G7 | Private, out-of-state and adult learners are partly missing | 3 | Coverage |
| G8 | FERPA interpretations block student debt and some segment data | 3 | Governance |
| G9 | Definitions differ across agencies | 3 | Standards |
| G10 | The ECE workforce cannot be followed | 3 | Coverage |
| G11 | Vulnerable populations drop between systems | 3 | Coverage |
| G12 | Funding and staff capacity at partner agencies | 3 | Capacity |
| G13 | Linked insights are slow to reach families and schools | 2 | Access |

Each gap's detail and evidence is in `data/gaps.json` and on the dashboard's Gaps tab.

## Recommendations: a 10-year linkage strategy

The strategy is organized in three phases. Phase 1 lines up with the D4TP 2027-2028 policy agenda so the coalition's near-term work becomes the first step of the long-term pitch.

### Phase 1: Foundations (2027-2028)

| # | Recommendation | D4TP priority | Vehicle |
|---|---|---|---|
| R1 | Stand up an Early Learning Data Task Force at C2C | P1, P5 | C2C Governing Board |
| R2 | Assign a matchable ID at first contact with any state-funded ECE program, starting with CAPSDAC and the new CDMIS monthly reports in July 2027 | P1 | Trailer bill or CDE/CDSS bulletin |
| R3 | Authorize and fund a phased ECIDS connected to C2C (AB 2092 follow-up with a tested cost estimate) | P1, P5 | Legislation and budget |
| R4 | Enhance UI wage records with occupation and hours (SB 1054 follow-up, phased by employer size) | P4 | Legislation |
| R5 | Return postsecondary outcomes to schools through the College/Career Indicator and extend Student Pathways to 13 years | P2, P5 | C2C and SBE |
| R6 | Adopt common definitions across agencies, starting with race and ethnicity (including MENA) and DLL status | P5, P3 | C2C Governance Manual, CEIC |
| R7 | Put student debt data into C2C | P3 | C2C advisory board proposal |

**Timing notes.** The July 2027 switch to CDMIS 2.0 is a once-in-a-decade chance to add an identifier field to early learning reporting at low cost (R2). AB 1534 (Workforce Pell oversight, signed September 2026) creates a near-term need for program outcomes data that strengthens the case for R4 and R8.

### Phase 2: Connect the edges (2029-2032)

| # | Recommendation | D4TP priority |
|---|---|---|
| R8 | Finish the workforce expansion (DAS, CalJOBS, ETP, DOR), bring in adult schools and BPPE student records, and publish a program-to-occupation crosswalk | P4 |
| R9 | Bridge early childhood health and human services data (Medi-Cal screening, WIC, home visiting, Early Start) through ECIDS and the CalHHS Data Exchange Framework | P1, P5 |
| R10 | Close the missing-outcomes gap with NSC, SWIS and FTB data, using matching that does not require an SSN | P4, P5 |
| R11 | Track the whole educator pipeline, ECE through grade 12 | P1, P2 |
| R12 | Follow students who cross systems: corrections, homelessness, foster care, juvenile justice | P5 |

### Phase 3: Whole learner, whole life (2033-2037)

| # | Recommendation | D4TP priority |
|---|---|---|
| R13 | Build a privacy-preserving California Learner Identifier: a C2C-issued token assigned at birth or first public contact, never based on SSN, never exposed outside the system | P5 |
| R14 | Make participation and funding durable: required participation for every publicly funded program, dedicated partner staff, an annual linkage scorecard | P5 |
| R15 | Put linked data to work for families: automatic eligibility, warm handoffs at each transition, family-facing tools under community oversight | P5, P1, P4 |

### How we would measure progress

- Share of children in state-funded ECE with a matchable ID (target: all by 2030)
- Unduplicated count of children 0 to 5 served by state programs, published every year (first release by 2029)
- Share of kindergartners whose early learning history is known in aggregate
- Share of UI wage records with occupation and hours
- Share of graduates with any known outcome (enrollment, wages, or other), overall and for students without SSNs
- Number of core data elements with one shared statewide definition
- An annual linkage scorecard that re-scores the heatmap above

## Framing the pitch

**The ask:** a 10-year, statewide commitment to connect every public data system that touches a Californian from birth to career, building on C2C rather than replacing it.

**Why now:** C2C has proven the model and doubled its partners in three years; the 2026-31 C2C Strategic Plan already commits to early learning data; CDMIS 2.0, Workforce Pell and the CalHHS Data Exchange Framework all change in 2026 and 2027; and a new administration brings a natural moment to set a long-term direction.

**Why D4TP:** the coalition already spans all three segments, has a record of sign-on letters that move the C2C board, and has five priorities that map one to one onto the phases above.

**What it is not:** a surveillance system or a new database of identities. Every recommendation keeps identity resolution inside C2C, uses de-identified data for public tools, and keeps C2C's existing bans on use for immigration or law enforcement.

## Sources and confidence

Every source entry carries a `confidence` field and a URL. Key 2025-2026 sources include the C2C 2026-31 Strategic Plan and 2026-27 Work Plan; C2C Governing Board resolutions 24-02 (DDS), 25-01 (ScholarShare) and the May 2025 and May 2026 workforce data actions; the Governor's July 27, 2026 release on C2C's five-year mark (16 partners); the Assembly analysis of AB 2092 and its May 2026 status; California EDGE Coalition updates on SB 1054; CDE CDMIS Update #41 (October 2026) and CAPSDAC guidance; the CalKIDS 2025 annual report; the CalHHS DxF roadmap and SB 660 fact sheet; PPIC's November 2026 report on C2C; and the D4TP 2026 Strategic Retreat Report.

Entries marked `needs_verification` (for example the exact Medi-Cal, CDSS and DMV data points in C2C) should be confirmed against the 2026 C2C Governance Manual and Data Elements by Provider list before external use.

#!/usr/bin/env python3
"""Build the California cradle-to-career data landscape database.

This file is the single source of truth. Running it writes:
  data/sources.json, data/sources.csv        one row per data source
  data/linkages.json, data/linkages.csv      one row per source-to-source link
  data/identifiers.json, data/identifiers.csv
  data/gaps.json, data/heatmap.json
  data/recommendations.json, data/timeline.json
  data/data.js                               everything above, for the dashboard

Usage:  python3 data-landscape/scripts/build_data.py
Research current as of November 2026. See data/DATA_DICTIONARY.md for field meanings.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")
AS_OF = "2026-11-14"

# ---------------------------------------------------------------------------
# Segments along the journey
# ---------------------------------------------------------------------------
SEGMENTS = [
    {"id": "birth", "name": "Prenatal and birth", "ages": "Before birth to 1"},
    {"id": "early", "name": "Early care and education", "ages": "0 to 5"},
    {"id": "k12", "name": "TK-12", "ages": "4 to 18"},
    {"id": "post", "name": "Postsecondary", "ages": "16 to 30+"},
    {"id": "work", "name": "Workforce and earnings", "ages": "16 to 65"},
    {"id": "hhs", "name": "Health and human services", "ages": "All ages"},
    {"id": "hub", "name": "Cross-system linkage hubs", "ages": "All ages"},
]

# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------
IDENTIFIERS = [
    # id, name, issuer, scope, age_min, age_max, notes
    ("birth_cert", "Birth certificate (state file) number", "CDPH Vital Records", "Statewide, every CA birth", -0.5, 0.5,
     "Assigned at birth registration. Used to seed CalKIDS newborn accounts. Not carried forward by any education system."),
    ("calkids_id", "CalKIDS account ID", "ScholarShare Investment Board", "Statewide, newborns since July 2022 and low-income public school students", 0, 26,
     "Created from CDPH birth data (newborns) and CALPADS SSID (students). One of the few identifiers created at birth that later meets an education record."),
    ("cin", "Medi-Cal Client Index Number (CIN)", "DHCS / county SAWS", "Statewide, anyone ever enrolled in Medi-Cal or CalFresh/CalWORKs", 0, 99,
     "Shared across Medi-Cal, CalFresh and CalWORKs through MEDS and CalSAWS. Covers roughly half of California children. Not shared with ECE or schools except through direct-certification matches."),
    ("wic_id", "WIC participant ID", "CDPH WIC", "Pregnant and postpartum people, infants and children under 5", -0.5, 5, "Program-specific."),
    ("cair_id", "CAIR immunization record ID", "CDPH (CAIR2 and regional registries)", "Children and adults with reported immunizations", 0, 99,
     "Schools and child care sites can look up records to verify entry immunizations, but no ID is stored in education data."),
    ("uci", "DDS Unique Client Identifier (UCI)", "Department of Developmental Services", "Early Start (0 to 3) and regional center consumers", 0, 99,
     "Program-specific. DDS joined C2C in 2024, so DDS records are now matched into the P20W data set by person-matching rather than a shared ID."),
    ("cws_id", "CWS/CMS client ID", "CDSS (moving to CWS-CARES)", "Children in child welfare and foster care", 0, 21,
     "Matched weekly to CALPADS by CDE to flag foster youth."),
    ("local_child_id", "Local child or family case ID", "Individual ECE contractors, Head Start grantees, First 5 commissions", "Program or agency only", 0, 5,
     "There is no statewide child identifier in early learning. Each contractor assigns its own. This is the single largest break in the chain."),
    ("ssid", "Statewide Student Identifier (SSID)", "CDE (CALPADS)", "Public TK-12 students, plus some LEA-run preschool and special education preschool", 3, 22,
     "10-digit ID assigned at first public school enrollment. Encouraged but not required in CAPSDAC (LEA-run state preschool). Collected by CCCApply and CaliforniaColleges.edu, which helps C2C matching."),
    ("seid", "Statewide Educator Identifier (SEID)", "CDE (CALPADS)", "Certificated and classified school staff", 18, 70,
     "Links staff assignments in CALPADS to CTC credential records for TAMO."),
    ("ctc_doc", "CTC credential / permit document records", "Commission on Teacher Credentialing", "Credential and Child Development Permit holders", 18, 70,
     "Child Development Permits for ECE staff live here, but ECE employment is not reported back, so the ECE workforce is invisible after the permit is issued."),
    ("cccid", "CCCID / college student ID", "California Community Colleges (CCCApply and each college)", "CCC applicants and students", 14, 99,
     "CCCID is statewide for applicants. Each college also assigns a local ID. SSN is collected but optional."),
    ("csu_id", "CSU campus ID (EmplID)", "California State University", "CSU applicants and students", 16, 99, "Campus-specific."),
    ("uc_id", "UC campus student ID", "University of California", "UC applicants and students", 16, 99, "Campus-specific."),
    ("ssn", "Social Security Number", "Federal (SSA)", "Most residents; missing for many immigrant students and young children in non-benefit programs", 0, 99,
     "The de facto workforce key (UI wages, FAFSA, CalJOBS). Absent or optional in most education records. Relying on it leaves out undocumented students and anyone who withholds it."),
    ("itin_cadaa", "CA Dream Act Application ID / ITIN", "CSAC / IRS", "Undocumented and mixed-status students applying for state aid", 16, 30,
     "Lets CSAC serve students without an SSN, but these students drop out of SSN-based wage matching."),
    ("employer_id", "EDD employer account number / FEIN", "EDD / IRS", "UI-covered employers", 16, 99,
     "Approved as a new C2C P20W data point from EDD in May 2026 (employer ID and name), which opens industry analysis."),
    ("c2c_pid", "C2C person ID (master data management)", "Office of Cradle-to-Career Data (GovOps)", "Everyone matched across C2C data partners", 0, 99,
     "Internal ID produced by probabilistic matching of name, birth date, SSN where present, and partner IDs. Never shared outward. This is the closest thing California has to a lifelong learner ID."),
]

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------
SOURCES = []


def S(id, name, segment, owner, owner_type, ages, population, unit, system_type, variables, identifiers,
      access, legal, c2c, c2c_note, url, notes="", confidence="agency_docs"):
    SOURCES.append({
        "id": id, "name": name, "segment": segment, "owner": owner, "owner_type": owner_type,
        "age_min": ages[0], "age_max": ages[1], "population": population, "unit": unit,
        "system_type": system_type, "key_variables": variables, "identifiers": identifiers,
        "access": access, "legal": legal, "c2c_status": c2c, "c2c_note": c2c_note,
        "url": url, "notes": notes, "confidence": confidence,
    })


# --- Prenatal and birth -----------------------------------------------------
S("cdph_birth", "Birth records (Birth Statistical Master File)", "birth", "CDPH Center for Health Statistics and Informatics", "state",
  (-0.5, 0), "Every birth in California", "individual", "Vital records",
  ["Date and county of birth", "Birthweight and gestational age", "Prenatal care start", "Principal payer (Medi-Cal or private)",
   "Parent age, education, race/ethnicity", "Plurality, delivery method"],
  ["birth_cert"], "restricted", ["Health and Safety Code 102100 et seq.", "CPHS review for research"], "no",
  "Not a C2C partner. Birth data reaches CalKIDS, which is a C2C partner, so a narrow indirect path exists.",
  "https://www.cdph.ca.gov/Programs/CHSI/Pages/default.aspx",
  "The only universal record of every child. Linking it forward would anchor a true cradle-to-career chain.", "agency_docs")

S("cdph_nbs", "Newborn Screening Program", "birth", "CDPH Genetic Disease Screening Program", "state",
  (0, 0.2), "Nearly all newborns", "individual", "Health screening",
  ["Screening results for metabolic, genetic and endocrine conditions", "Hearing screening referral", "Follow-up status"],
  ["birth_cert"], "restricted", ["Health and Safety Code 124975 et seq.", "HIPAA"], "no",
  "Not in C2C. Relevant for Early Start referral pathways.", "https://www.cdph.ca.gov/Programs/CFH/DGDS/Pages/nbs/default.aspx")

S("cdph_wic", "WIC (Women, Infants and Children)", "birth", "CDPH WIC Division", "state",
  (-0.5, 5), "Low-income pregnant and postpartum people, infants, and children under 5", "individual", "Benefit program",
  ["Enrollment and certification category", "Nutrition risk", "Breastfeeding status", "Height/weight", "Household income"],
  ["wic_id"], "restricted", ["7 CFR 246.26 (WIC confidentiality)"], "no",
  "Not in C2C. WIC participation could signal early need but is invisible to education data.", "https://www.cdph.ca.gov/Programs/CFH/DWICSN/Pages/Program-Landing1.aspx")

S("sib_calkids", "CalKIDS college savings accounts", "birth", "ScholarShare Investment Board (State Treasurer)", "state",
  (0, 26), "Every child born in CA since July 1, 2022, plus low-income public school students (over 5.6 million funded accounts by April 2026)",
  "individual", "Benefit program",
  ["Account seeded (newborn or school-based)", "Account claimed by family", "Family deposits", "Funds used for postsecondary"],
  ["calkids_id", "birth_cert", "ssid"], "restricted", ["Education Code 69996 et seq."], "yes",
  "Approved as a C2C data provider in February 2025 (Resolution 25-01) to study CalKIDS use and college access.",
  "https://calkids.org/",
  "Accounts are opened from CDPH birth data and CDE student data. SIB's own 2025 annual report flags those data linkages as a challenge to strengthen.",
  "verified")

# --- Early care and education ----------------------------------------------
S("cde_capsdac", "California Preschool Data Collection (CAPSDAC 2.0)", "early", "CDE Early Education Division", "state",
  (3, 5), "Children, classrooms and staff in LEA-operated California State Preschool Program (CSPP)", "individual", "Administrative (child-level)",
  ["Child enrollment and attendance", "Classroom assignment", "Staff and qualifications", "Child demographics", "Dual language learner status"],
  ["local_child_id", "ssid"], "internal", ["Education Code 60910", "FERPA (LEA programs)"], "planned",
  "Not yet imported to C2C. The 2026-27 C2C work plan sets initial milestones for importing early learning and care data.",
  "https://www.cde.ca.gov/sp/cd/ci/",
  "Required since July 2024 for LEA-run CSPP. SSID use is encouraged, not required, so many preschool records cannot be matched to later K-12 records.",
  "verified")

S("cde_cdmis", "CDE CDMIS and 801A monthly population report (CSPP)", "early", "CDE Early Education Division", "state",
  (0, 5), "Families and children in CDE-contracted CSPP (all operators, including non-LEA)", "individual", "Administrative (child-level, monthly)",
  ["Family size and income", "Reason for need and eligibility", "Child age, ethnicity, primary language", "Days of enrollment", "Co-enrollment in a CDSS child care program (added 2025)"],
  ["local_child_id"], "internal", ["Education Code 8200 et seq.", "Welfare and Institutions Code 10850"], "planned",
  "C2C planned early learning entry age, enrollment duration and family income from CDE since 2023 but had not received them.",
  "https://www.cde.ca.gov/sp/cd/ci/",
  "CDE announced CDMIS 2.0 in October 2026. A new CDMIS Monthly Report replaces the 801A starting with July 2027.",
  "verified")

S("cdss_ccdd", "CDSS child care subsidy data (CDD-801A in CDSS CDMIS)", "early", "CDSS Child Care and Development Division", "state",
  (0, 12), "Families in CDSS child care programs: general child care, migrant, family child care networks, alternative payment, CalWORKs Stages 2 and 3",
  "individual", "Administrative (child-level, monthly)",
  ["Family income and size", "Eligibility and need", "Provider type and setting", "Child age and demographics", "Subsidy amount and hours"],
  ["local_child_id"], "internal", ["Welfare and Institutions Code 10207 et seq.", "Welfare and Institutions Code 10850", "CCDF 45 CFR 98"], "planned",
  "CDSS is a C2C partner for social services data, but child care records are not yet in the P20W data set.",
  "https://www.cdss.ca.gov/inforesources/child-care-and-development",
  "Most child care programs moved from CDE to CDSS in July 2021 (AB 131). Since October 2024 all CDSS contract-type child data goes to the CDSS CDMIS.",
  "verified")

S("cdss_ccld", "Community Care Licensing (child care facilities)", "early", "CDSS Community Care Licensing Division", "state",
  (0, 12), "Every licensed child care center and family child care home", "facility", "Licensing",
  ["License number and type", "Licensed capacity by age group", "Address and county", "Inspection and citation history", "Status (open, closed, on probation)"],
  [], "public_detail", ["Health and Safety Code 1596.70 et seq."], "no",
  "Facility-level only. Useful for supply and desert analysis, not for following children.", "https://www.ccld.dss.ca.gov/carefacilitysearch/")

S("rr_network", "Child Care Resource and Referral data", "early", "Local R&R agencies and the CA Child Care Resource & Referral Network", "nonprofit",
  (0, 12), "Families seeking care and licensed providers in each county", "aggregate", "Supply and demand",
  ["Licensed slots by age and setting", "Referral requests and unmet need", "Provider vacancies", "Cost of care"],
  [], "public_aggregate", ["Contract terms with CDSS"], "no",
  "Not in C2C.", "https://rrnetwork.org/")

S("head_start", "Head Start and Early Head Start (Program Information Report)", "early", "Federal Office of Head Start (ACF); local grantees", "federal",
  (-0.5, 5), "Low-income pregnant people, infants, toddlers and preschoolers in federally funded programs", "aggregate", "Federal grantee reporting",
  ["Funded and cumulative enrollment", "Child health insurance and medical home", "Disability services", "Family services", "Staff qualifications"],
  ["local_child_id"], "public_aggregate", ["Head Start Act, 45 CFR 1303 (privacy)"], "no",
  "No state child-level data. Grantees keep records in their own systems. California's Head Start State Collaboration Office sits at CDE but holds no child records.",
  "https://eclkc.ohs.acf.hhs.gov/data-ongoing-monitoring/article/program-information-report-pir",
  "Head Start children can enroll in TK or kindergarten with no record of their preschool experience.")

S("first5", "First 5 California and county commissions", "early", "First 5 California and 58 county First 5 commissions", "state_local",
  (-0.5, 5), "Children 0 to 5 and families served by Prop 10 funded programs", "mixed", "Program and evaluation",
  ["Services delivered by result area", "Home visiting and family support participation", "Quality improvement participation", "Annual Prop 10 outcomes reporting"],
  ["local_child_id"], "public_aggregate", ["Health and Safety Code 130100 et seq. (Prop 10)"], "no",
  "Not in C2C. Each county uses its own data system.", "https://www.ccfc.ca.gov/")

S("qcc", "Quality Counts California (QRIS)", "early", "CDE, CDSS and First 5 California with county consortia", "state_local",
  (0, 5), "Participating ECE sites and educators", "facility", "Quality rating",
  ["Site quality tier and element ratings", "Educator qualifications and training", "CLASS and environment rating scores"],
  [], "public_aggregate", ["Program terms"], "no",
  "Not in C2C. Site data could link to children only if child records carried a site ID and a matchable child ID.", "https://qualitycountsca.net/")

S("drdp", "Desired Results Developmental Profile (DRDP)", "early", "CDE (Early Education and Special Education divisions)", "state",
  (0, 5), "Children in CSPP, CDSS-funded centers and preschool special education", "individual", "Child assessment",
  ["Developmental ratings across domains (language, literacy, math, social-emotional, physical)", "Assessment period", "IEP status"],
  ["local_child_id", "ssid"], "internal", ["FERPA", "IDEA (special education)"], "no",
  "Not in C2C. Special education DRDP uses SSID. General early learning DRDP mostly uses local IDs.", "https://www.desiredresults.us/")

S("dds_earlystart", "DDS Early Start and regional center services", "early", "Department of Developmental Services and 21 regional centers", "state",
  (0, 99), "Infants and toddlers with or at risk of delays (IDEA Part C), and people with developmental disabilities", "individual", "Service program",
  ["Eligibility and diagnosis category", "Early Start service receipt", "Regional center", "IFSP and transition at age 3", "Level of support"],
  ["uci"], "restricted", ["Welfare and Institutions Code 4514", "IDEA Part C"], "yes",
  "Approved as a C2C data provider in May 2024 (Resolution 24-02). Proposed points include eligibility, enrollment and receipt of Early Start services.",
  "https://www.dds.ca.gov/services/early-start/", "", "verified")

S("chvp", "California Home Visiting Program (MIECHV)", "early", "CDPH Maternal, Child and Adolescent Health", "state",
  (-0.5, 5), "Families enrolled in evidence-based home visiting in participating counties", "individual", "Service program",
  ["Enrollment and visit dosage", "Developmental and depression screening", "Child injury and ED visits", "Benchmarks required by HRSA"],
  ["local_child_id"], "restricted", ["HRSA MIECHV requirements", "HIPAA"], "no", "Not in C2C.",
  "https://www.cdph.ca.gov/Programs/CFH/DMCAH/CHVP/Pages/default.aspx")

S("cdss_hvp", "CalWORKs Home Visiting Program", "early", "CDSS with counties", "state_local",
  (-0.5, 2), "CalWORKs families who are pregnant or have a child under 24 months", "individual", "Service program",
  ["Enrollment and visit completion", "Family goals", "Program model"],
  ["cin"], "restricted", ["Welfare and Institutions Code 10850"], "no", "Not in C2C.",
  "https://www.cdss.ca.gov/inforesources/calworks-home-visiting-program")

S("ece_registry", "California ECE Workforce Registry", "early", "Child Care Resource Center (statewide operator)", "nonprofit",
  (18, 70), "Early educators who create a profile (voluntary; required in some local programs)", "individual", "Workforce registry",
  ["Employment history and site", "Education and permits", "Training hours", "Compensation (some sites)"],
  [], "restricted", ["Participant consent"], "no",
  "Not in C2C. Voluntary participation means the data does not represent the whole workforce.", "https://www.caregistry.org/")

S("cscce_study", "California ECE Workforce Study", "early", "UC Berkeley Center for the Study of Child Care Employment", "research",
  (18, 70), "Survey of more than 10,000 early educators (2025 round)", "survey", "Research survey",
  ["Wages and benefits", "Education and credentials", "Demographics and languages", "Turnover intent"],
  [], "public_aggregate", ["Research consent"], "no", "Research survey, not linkable.",
  "https://cscce.berkeley.edu/projects/california-early-care-and-education-workforce-study", "", "verified")

S("ctc_permits", "Child Development Permits", "early", "Commission on Teacher Credentialing", "state",
  (18, 70), "ECE teachers and directors holding a Child Development Permit (Associate Teacher to Program Director)", "individual", "Licensing",
  ["Permit type and level", "Issue and expiration dates", "Coursework and units"],
  ["ctc_doc"], "restricted", ["Education Code 44000 et seq."], "partial",
  "CTC is a C2C partner for credential data. Whether permit records are in P20W, and whether ECE employment is captured, needs confirmation.",
  "https://www.ctc.ca.gov/credentials/leaflets/child-development-permits", "", "needs_verification")

# --- TK-12 ------------------------------------------------------------------
S("cde_calpads", "CALPADS (student and staff records)", "k12", "CDE with CSIS (FCMAT)", "state",
  (4, 22), "About 5.8 million public TK-12 students and all school staff", "individual", "Administrative (longitudinal)",
  ["Enrollment, TK and grade level", "Race/ethnicity, gender, language and EL status", "Reclassification (RFEP) and State Seal of Biliteracy",
   "Special education and 504", "Socioeconomically disadvantaged, foster, homeless, migrant flags", "Attendance and chronic absence",
   "Courses, grades, A-G and CTE completion (grades 7-12)", "Dual enrollment courses", "Graduation and dropout", "Discipline"],
  ["ssid", "seid"], "restricted", ["FERPA", "Education Code 49076", "Education Code 60900"], "yes",
  "Core C2C data provider since the first data submissions in 2023.",
  "https://www.cde.ca.gov/ds/sp/cl/",
  "The backbone of state education data. No field records preschool or child care history at kindergarten entry.")

S("cde_assess", "CAASPP and ELPAC assessments", "k12", "CDE (ETS contractor)", "state",
  (7, 18), "Students in tested grades; English learners for ELPAC", "individual", "Assessment",
  ["Smarter Balanced ELA and math scale scores", "CAST science", "ELPAC summative and initial", "Alternate assessments"],
  ["ssid"], "restricted", ["FERPA", "Education Code 60640"], "partial",
  "Some assessment results are part of the K-12 data CDE provides. Item-level and early-grade measures are not.",
  "https://www.cde.ca.gov/ta/tg/ca/", "", "needs_verification")

S("cde_public", "California School Dashboard, DataQuest and College/Career Indicator", "k12", "CDE", "state",
  (4, 18), "Every public school, district and student group", "aggregate", "Public reporting",
  ["Dashboard indicators (academic, ELPI, graduation, chronic absence, suspension)", "College/Career Indicator (CCI)", "Enrollment and staffing downloads"],
  [], "public_aggregate", ["Education Code 52064.5"], "no",
  "D4TP is asking C2C to link postsecondary outcomes back to the CCI so schools see what happened to graduates.",
  "https://www.caschooldashboard.org/")

S("ctc_educator", "Educator preparation, credentials and TAMO", "k12", "Commission on Teacher Credentialing", "state",
  (18, 70), "Credential candidates, completers and credential holders; teacher assignments", "individual", "Licensing and workforce",
  ["Credentials and authorizations", "Preparation program and pathway", "Completer surveys", "Teaching Assignment Monitoring Outcomes (TAMO)", "Teacher supply report"],
  ["ctc_doc", "seid"], "restricted", ["Education Code 44230 et seq."], "yes",
  "CTC is a C2C partner. C2C is building a teacher training and retention dashboard in its 2026-27 work plan.",
  "https://www.ctc.ca.gov/commission/reports/data", "", "verified")

S("cde_dircert", "Direct Certification match (school meals)", "k12", "CDE Nutrition Services with CDSS and DHCS", "state",
  (4, 18), "Students in households enrolled in CalFresh, CalWORKs or Medi-Cal", "individual", "Operational match",
  ["Matched program participation", "Free or reduced-price meal eligibility", "Socioeconomically disadvantaged status"],
  ["ssid", "cin"], "internal", ["National School Lunch Act 42 USC 1758", "Welfare and Institutions Code 10850 exceptions"], "partial",
  "Results flow into CALPADS socioeconomic flags, which C2C receives. The underlying CIN link is not kept.",
  "https://www.cde.ca.gov/ls/nu/sn/dircert.asp",
  "A working proof that human services and education records can be matched routinely at scale.")

S("cde_foster", "Foster youth match (CDE and CDSS)", "k12", "CDE with CDSS", "state",
  (4, 21), "Students in foster care", "individual", "Operational match",
  ["Foster status", "County of jurisdiction", "Social worker contact (to LEAs)"],
  ["ssid", "cws_id"], "internal", ["Education Code 49085", "Welfare and Institutions Code 827"], "partial",
  "Foster flag appears in CALPADS data provided to C2C.", "https://www.cde.ca.gov/ls/pf/fy/")

S("cde_expanded", "Expanded learning (ELO-P, ASES, 21st CCLC)", "k12", "CDE Expanded Learning Division", "state",
  (4, 18), "Students in before, after and summer school programs", "aggregate", "Program reporting",
  ["Program attendance (site level)", "Funding and slots", "Outcome reports (federal 21st CCLC)"],
  [], "public_aggregate", ["Education Code 46120, 8482 et seq."], "no",
  "Participation is not reported by SSID, so it cannot be linked to outcomes. Raised as a TK-12 workgroup idea.", "https://www.cde.ca.gov/ls/ex/")

S("cde_private", "Private School Affidavit", "k12", "CDE", "state",
  (5, 18), "Private schools and homeschool filers", "aggregate", "Registration",
  ["School name and address", "Enrollment by grade (counts)", "Staff counts"],
  [], "public_aggregate", ["Education Code 33190"], "no",
  "No student-level data. Students who start in private school or homeschool have no SSID until they enter public school.",
  "https://www.cde.ca.gov/ds/si/ps/")

S("ccgi", "CaliforniaColleges.edu and eTranscript California", "k12", "California College Guidance Initiative (Foundation for CCC)", "state_nonprofit",
  (11, 20), "Students in participating districts (most public high school students)", "individual", "Operational tool",
  ["Student accounts and career exploration", "Verified transcripts and A-G progress", "Cal Grant and FAFSA/CADAA status", "College applications"],
  ["ssid"], "restricted", ["FERPA", "Education Code 10870 et seq."], "yes",
  "C2C's operational tools for college and career planning and electronic transcripts.", "https://www.californiacolleges.edu/")

S("calpass", "Cal-PASS Plus", "k12", "Educational Results Partnership and San Joaquin Delta College", "nonprofit",
  (12, 30), "Students in K-12 districts and colleges that sign data-sharing MOUs", "individual", "Voluntary data exchange",
  ["K-12 course and grade data", "College placement and course outcomes", "Regional pathway reports"],
  ["ssid", "cccid", "ssn"], "restricted", ["FERPA study exception", "Local MOUs"], "no",
  "Predates C2C. Voluntary coverage means gaps by district.", "https://www.calpassplus.org/")

# --- Postsecondary ----------------------------------------------------------
S("ccc_mis", "Community College MIS and CCCApply", "post", "California Community Colleges Chancellor's Office", "state",
  (14, 99), "About 2 million students a year at 116 colleges, including dual enrollment and noncredit", "individual", "Administrative (longitudinal)",
  ["Applications (CCCApply), including SSID when provided", "Course enrollment and grades", "Awards (degrees, certificates)", "Transfer-level milestones",
   "Financial aid (Promise, Pell, Cal Grant)", "Dual enrollment (CCAP)", "EOPS, DSPS, CalWORKs, veterans", "Program (TOP code)"],
  ["cccid", "ssn", "ssid"], "restricted", ["FERPA", "Education Code 70901, 72620"], "yes",
  "Core C2C data provider.", "https://datamart.cccco.edu/")

S("ccc_launchboard", "LaunchBoard, Student Success Metrics and Strong Workforce outcomes", "post", "CCCCO with Cal-PASS Plus and WestEd", "state",
  (16, 99), "CCC students and CTE program completers", "aggregate", "Public reporting",
  ["Program completion", "Employment and median earnings (EDD wage match)", "Living wage attainment", "CTE Outcomes Survey"],
  ["ssn"], "public_aggregate", ["FERPA", "Unemployment Insurance Code 1095"], "no",
  "Earnings outcomes depend on SSN-based EDD matching, so students without SSNs are missing.", "https://www.calpassplus.org/LaunchBoard/")

S("csu_ers", "CSU enrollment and degree reporting (ERS)", "post", "California State University Chancellor's Office", "state",
  (16, 99), "About 460,000 students at 23 campuses", "individual", "Administrative (longitudinal)",
  ["Applications and admissions", "Enrollment and units", "Degrees and majors (CIP)", "Transfer origin", "Financial aid"],
  ["csu_id", "ssn"], "restricted", ["FERPA", "Education Code 89000 et seq."], "yes",
  "Core C2C data provider. D4TP members report FERPA interpretations limit student debt data sharing.", "https://www.calstate.edu/data-center")

S("uc_ss", "UC student data (Corporate Student System)", "post", "University of California Office of the President", "state_constitutional",
  (16, 99), "About 300,000 students at 10 campuses", "individual", "Administrative (longitudinal)",
  ["Applications and admissions", "Enrollment", "Degrees and majors", "Transfer origin", "Financial aid and debt at graduation"],
  ["uc_id", "ssn"], "restricted", ["FERPA", "Constitutional autonomy (Art. IX, Sec. 9)"], "yes",
  "C2C data provider. Because of constitutional autonomy, statute requests rather than requires UC participation (restated in SB 135, 2026).",
  "https://www.universityofcalifornia.edu/about-us/information-center")

S("aiccu", "Independent nonprofit colleges (AICCU members)", "post", "Association of Independent California Colleges and Universities", "nonprofit",
  (16, 99), "Students at participating private nonprofit institutions", "individual", "Voluntary submission",
  ["Enrollment", "Degrees", "Cal Grant recipients"], ["ssn"], "restricted", ["FERPA", "Voluntary agreement"], "partial",
  "Represented on the C2C Governing Board. Participation is voluntary and institution by institution.", "https://aiccu.edu/", "", "needs_verification")

S("bppe", "Private postsecondary institutions (BPPE)", "post", "Bureau for Private Postsecondary Education (DCA)", "state",
  (16, 99), "Students at for-profit and private vocational schools approved by BPPE", "aggregate", "Regulatory reporting",
  ["Annual reports", "Student Performance Fact Sheets (completion, placement, licensure)", "Complaints and enforcement"],
  [], "public_aggregate", ["Education Code 94800 et seq."], "partial",
  "Listed as a C2C data partner, but BPPE collects institution-level reports, not student records, so students in these programs are largely invisible.",
  "https://www.bppe.ca.gov/", "", "needs_verification")

S("csac", "CSAC financial aid (Grant Delivery System, WebGrants)", "post", "California Student Aid Commission", "state",
  (16, 30), "FAFSA and CA Dream Act filers; Cal Grant, Middle Class Scholarship, Chafee and other awardees", "individual", "Administrative (aid)",
  ["FAFSA and CADAA completion", "High school GPA uploads", "Cal Grant eligibility and award", "Middle Class Scholarship", "Payment and renewal"],
  ["ssn", "itin_cadaa", "ssid"], "restricted", ["FERPA", "Education Code 69400 et seq.", "Higher Education Act (FAFSA data)"], "yes",
  "C2C data provider. Financial aid data points added to P20W in 2024.", "https://www.csac.ca.gov/")

S("fed_fsa", "Federal student aid and loans (FAFSA, NSLDS)", "post", "U.S. Department of Education", "federal",
  (16, 99), "Federal aid applicants and borrowers", "individual", "Federal administrative",
  ["FAFSA/ISIR data", "Pell receipt", "Federal loan balances and repayment status"],
  ["ssn"], "restricted", ["Higher Education Act 483", "Privacy Act"], "no",
  "Loan data is not available to C2C. Student debt is a priority gap for D4TP (TICAS, Public Advocates).", "https://studentaid.gov/data-center")

S("nsc", "National Student Clearinghouse", "post", "National Student Clearinghouse (nonprofit)", "nonprofit",
  (16, 99), "Enrollment and degrees at most U.S. colleges, including out of state", "individual", "Third-party verification",
  ["Enrollment by term at any participating college", "Degrees", "Institution type and state"],
  ["ssn"], "restricted", ["FERPA", "Contract"], "no",
  "Not in C2C, so students who leave California or attend most private colleges disappear from the state picture.", "https://www.studentclearinghouse.org/")

S("ipeds", "IPEDS and College Scorecard", "post", "U.S. Department of Education (NCES)", "federal",
  (16, 99), "Every Title IV institution", "aggregate", "Public reporting",
  ["Enrollment and completions by CIP", "Graduation rates", "Net price", "Earnings after entry (Scorecard, from IRS)", "Debt at completion"],
  [], "public_aggregate", ["Higher Education Act"], "no", "Institution-level public data.", "https://collegescorecard.ed.gov/")

S("caep", "Adult education (CAEP, TOPSpro Enterprise)", "post", "CDE and CCCCO (California Adult Education Program) with CASAS", "state",
  (16, 99), "Adult school and noncredit students: ESL, adult secondary, CTE, citizenship", "individual", "Program reporting",
  ["Enrollment and hours", "CASAS test gains", "High school equivalency", "Employment and wage outcomes (partial)"],
  ["ssn"], "restricted", ["WIOA Title II", "Education Code 84900 et seq."], "no",
  "Adult schools run by K-12 districts are not in C2C. Many adult learners have no SSN on file.", "https://caladulted.org/")

# --- Workforce --------------------------------------------------------------
S("edd_wages", "UI base wage records (DE 9C)", "work", "Employment Development Department", "state",
  (16, 99), "Workers in UI-covered jobs", "individual", "Administrative (quarterly)",
  ["Quarterly wages by employer", "Employer account and industry (NAICS)", "County of employer"],
  ["ssn", "employer_id"], "restricted", ["Unemployment Insurance Code 1094-1095", "20 CFR 603"], "yes",
  "C2C data provider. In May 2026 the Governing Board approved new EDD P20W points, including employer ID and name, and EDD became the first partner to transmit via Snowflake.",
  "https://edd.ca.gov/",
  "No occupation, hours or job title. Excludes self-employed, gig, federal, military and out-of-state work. SB 1054 (Cabaldon, 2026) would add these fields; it was held in Assembly Appropriations.",
  "verified")

S("edd_caljobs", "CalJOBS (WIOA participant records)", "work", "Employment Development Department", "state",
  (16, 99), "Job seekers and WIOA Title I and III participants at America's Job Centers", "individual", "Case management",
  ["Services and training received", "Credential attainment", "Employment and earnings (WIOA performance)", "Barriers to employment"],
  ["ssn"], "restricted", ["WIOA 116", "20 CFR 677"], "partial",
  "Part of the LWDA workforce data expansion approved by the C2C board in May 2025 and amended in late 2025.", "https://www.caljobs.ca.gov/", "", "needs_verification")

S("edd_lmi", "Labor Market Information (OES, QCEW, projections)", "work", "EDD Labor Market Information Division", "state",
  (16, 99), "Employers and occupations statewide", "aggregate", "Public statistics",
  ["Employment and wages by occupation (OES)", "Employment and wages by industry (QCEW)", "Occupational projections"],
  [], "public_aggregate", ["BLS cooperative agreements"], "no",
  "Aggregate context. Needed for a program-to-occupation crosswalk.", "https://labormarketinfo.edd.ca.gov/")

S("dir_das", "Registered apprenticeship records", "work", "Division of Apprenticeship Standards (DIR)", "state",
  (16, 99), "Registered apprentices and pre-apprentices", "individual", "Program registration",
  ["Apprenticeship program and occupation", "Registration, completion and cancellation", "Sponsor", "Related instruction provider"],
  ["ssn"], "restricted", ["Labor Code 3070 et seq."], "planned",
  "Included in the LWDA expansion the C2C board approved in May 2025 (described as its largest expansion). Import status should be confirmed.",
  "https://www.dir.ca.gov/das/", "", "agency_docs")

S("cwdb_caal", "CAAL-Skills workforce program data", "work", "California Workforce Development Board", "state",
  (16, 99), "Participants in 13 workforce programs across 7 state agencies", "individual", "Cross-program data system",
  ["Program participation", "Services received", "Employment and earnings outcomes", "Participant characteristics"],
  ["ssn"], "restricted", ["Unemployment Insurance Code 14013", "Interagency agreements"], "yes",
  "CWDB became a C2C data partner in May 2025.", "https://cwdb.ca.gov/caal-skills", "", "verified")

S("etp", "Employment Training Panel", "work", "Employment Training Panel", "state",
  (18, 99), "Incumbent and new workers trained under ETP contracts", "individual", "Program records",
  ["Employer contract", "Training hours", "Retention and wage after training"],
  ["ssn"], "restricted", ["Unemployment Insurance Code 10200 et seq."], "yes",
  "Became a C2C data partner in May 2025.", "https://etp.ca.gov/", "", "verified")

S("dor", "Vocational rehabilitation (WIOA Title IV)", "work", "Department of Rehabilitation", "state",
  (14, 99), "People with disabilities receiving VR and pre-employment transition services", "individual", "Case management",
  ["Eligibility and disability", "Services and pre-ETS for students", "Employment outcomes"],
  ["ssn"], "restricted", ["34 CFR 361.38"], "partial",
  "VR participant data reaches CWDB's CAAL-Skills. Direct C2C participation needs confirmation.", "https://www.dor.ca.gov/", "", "needs_verification")

S("cdcr", "Corrections education (CDCR, Rising Scholars)", "work", "CDCR Office of Correctional Education; CCC Rising Scholars", "state",
  (18, 99), "Incarcerated students and people on parole", "individual", "Administrative",
  ["Education program enrollment", "Credits and degrees in prison", "Release and parole"],
  [], "restricted", ["Penal Code 11105", "Penal Code 2053.1"], "no",
  "Not in C2C. CCC records capture Rising Scholars coursework, but release, reentry and employment are not linked.", "https://www.cdcr.ca.gov/rehabilitation/")

S("ftb", "State income tax records", "work", "Franchise Tax Board", "state",
  (16, 99), "State tax filers, including self-employed and CalEITC recipients", "individual", "Tax records",
  ["Self-employment income", "CalEITC and Young Child Tax Credit", "Household income"],
  ["ssn", "itin_cadaa"], "restricted", ["Revenue and Taxation Code 19542"], "no",
  "Not linked. The only state source that sees self-employment and gig income, and it covers ITIN filers.", "https://www.ftb.ca.gov/")

S("swis", "Out-of-state and federal wages (SWIS, FEDES)", "work", "U.S. DOL with state workforce agencies", "federal",
  (16, 99), "Workers employed in other states, federal civilian jobs and the military", "individual", "Wage exchange",
  ["Quarterly wages from other states", "Federal and military employment"],
  ["ssn"], "restricted", ["SWIS data sharing agreement (WIOA performance only)"], "no",
  "Use is limited to WIOA performance reporting. C2C cannot see Californians who work out of state.", "https://www.dol.gov/agencies/eta/performance/swis")

S("hcai_hw", "Health workforce data", "work", "Department of Health Care Access and Information (HCAI)", "state",
  (18, 99), "Licensed health professionals and health workforce program participants", "individual", "Licensing survey",
  ["License type", "Practice location", "Education and training", "Languages"],
  [], "public_aggregate", ["Health and Safety Code 128050"], "no",
  "A model for linking licensure to training, not connected to C2C.", "https://hcai.ca.gov/data/healthcare-workforce/")

S("dmv", "DMV identity records", "work", "Department of Motor Vehicles", "state",
  (15, 99), "Driver license and state ID holders", "individual", "Identity",
  ["Name and birth date history", "Address"], [], "restricted", ["Vehicle Code 1808 et seq."], "partial",
  "Reported as a C2C data partner added in August 2025, likely to improve identity matching. Needs confirmation.", "https://www.dmv.ca.gov/",
  "", "needs_verification")

# --- Health and human services ----------------------------------------------
S("dhcs_medi_cal", "Medi-Cal eligibility and claims (MEDS, encounters)", "hhs", "Department of Health Care Services", "state",
  (0, 99), "About 15 million members, roughly half of California's children", "individual", "Administrative (health)",
  ["Eligibility and aid code", "Well-child visits and developmental screening", "Dental and vision", "Behavioral health services", "Managed care plan"],
  ["cin", "ssn"], "restricted", ["Welfare and Institutions Code 14100.2", "HIPAA", "42 CFR 431.300"], "partial",
  "DHCS sits on the C2C Governing Board. Exactly which Medi-Cal points are in P20W needs confirmation.", "https://www.dhcs.ca.gov/dataandstats",
  "Developmental screening and well-child visit data could show which children enter school without early supports.", "needs_verification")

S("dhcs_cybhi", "School-linked behavioral health fee schedule (CYBHI)", "hhs", "DHCS with CDE", "state",
  (0, 25), "Students receiving behavioral health services at or near school", "individual", "Claims",
  ["Service type and provider", "Payer", "School/LEA"], ["cin", "ssid"], "restricted", ["HIPAA", "FERPA"], "no",
  "New since 2024. A potential bridge between school and health records.", "https://www.dhcs.ca.gov/CYBHI/")

S("calsaws", "CalSAWS (CalFresh, CalWORKs, Medi-Cal eligibility)", "hhs", "CalSAWS consortium of 58 counties, overseen by CDSS and DHCS", "state_local",
  (0, 99), "Households applying for or receiving CalFresh, CalWORKs, Stage 1 child care, General Assistance and Medi-Cal", "individual", "Eligibility system",
  ["Program enrollment and benefit", "Household composition", "Income and employment", "CalWORKs Welfare-to-Work and Stage 1 child care"],
  ["cin", "ssn"], "restricted", ["Welfare and Institutions Code 10850", "7 CFR 272.1"], "partial",
  "CDSS is a C2C data provider for selected social services participation indicators.", "https://www.calsaws.org/", "", "needs_verification")

S("cws", "Child welfare (CWS/CMS, CWS-CARES)", "hhs", "CDSS with county child welfare agencies", "state_local",
  (0, 21), "Children with abuse or neglect reports, in foster care, or in extended foster care", "individual", "Case management",
  ["Referrals and substantiations", "Placements and moves", "Exits to permanency", "Extended foster care (18 to 21)"],
  ["cws_id"], "restricted", ["Welfare and Institutions Code 827, 10850"], "partial",
  "Foster status reaches C2C through CALPADS. Public dashboards via the California Child Welfare Indicators Project (UC Berkeley).",
  "https://ccwip.berkeley.edu/")

S("hdis", "Homelessness data (HMIS, HDIS)", "hhs", "Continuums of Care; CA Interagency Council on Homelessness (HDIS)", "state_local",
  (0, 99), "People served by homeless services", "individual", "Service records",
  ["Program enrollment", "Household type", "Exits to housing"], [], "restricted", ["HUD HMIS standards"], "no",
  "Not linked. Schools separately identify McKinney-Vento students, and the two counts rarely meet.", "https://bcsh.ca.gov/calich/hdis.html")

# --- Hubs --------------------------------------------------------------------
S("c2c", "Cradle-to-Career Data System (P20W data set and tools)", "hub", "Office of Cradle-to-Career Data (Government Operations Agency)", "state",
  (0, 99), "People matched across 16 data partners (as of July 2026)", "individual", "Statewide longitudinal data system",
  ["Linked education, aid, social services and wage records", "Query Builder and Student Pathways Dashboard", "Expedited and comprehensive data requests",
   "Research library and secure data enclave", "Planned transfer outcomes and teacher dashboards"],
  ["c2c_pid"], "public_aggregate", ["Education Code 10850-10875 (AB 132, 2021)", "SB 135 (2026)"], "yes",
  "The hub. Partners grew from 8 submitting data in 2023 to 16 in 2026. Early learning and care is the largest remaining hole.",
  "https://c2c.ca.gov/",
  "Student Pathways Dashboard launched April 22, 2025. 2026-31 Strategic Plan adopted August 2026.", "verified")

S("ecids", "Early Childhood Integrated Data System (proposed)", "hub", "CDSS (lead, as proposed in AB 2092)", "state",
  (-0.5, 5), "Children 0 to 5 across child care, preschool, health, home visiting and early intervention", "individual", "Proposed linkage system",
  ["Unduplicated count of children served", "Program participation over time", "Workforce and supply", "Link to C2C at kindergarten entry"],
  [], "none", ["AB 2092 (Bonta, 2026) held in Assembly Appropriations"], "planned",
  "Designed to connect to C2C. Not yet authorized or funded. The 2020 Master Plan for Early Learning and Care called for it.",
  "https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202520260AB2092", "", "verified")

S("dxf", "CalHHS Data Exchange Framework", "hub", "HCAI (administrator under SB 660, 2026); CalHHS", "state",
  (0, 99), "Health plans, hospitals, providers, counties and social services organizations that sign the Data Sharing Agreement", "individual", "Health and social services exchange",
  ["Real-time exchange of health and social services information", "Consent management (in development)"],
  ["cin"], "restricted", ["Health and Safety Code 130290 (AB 133, 2021)", "SB 660 (2026)", "HIPAA"], "no",
  "Separate from C2C. Social services organizations began required exchange January 31, 2026. A future bridge for early childhood health data.",
  "https://dxf.chhs.ca.gov/", "", "verified")

# ---------------------------------------------------------------------------
# Linkages (source -> target)
#   status: routine  = recurring individual-level operational match
#           c2c      = matched inside the C2C P20W data set
#           periodic = research, voluntary or one-off matches
#           planned  = approved or proposed but not operating
#           missing  = needed link that does not exist
# ---------------------------------------------------------------------------
L = []


def link(a, b, status, mechanism, key, note=""):
    L.append({"source": a, "target": b, "status": status, "mechanism": mechanism, "identifier": key, "note": note})


C2C_MEMBERS = ["cde_calpads", "ccc_mis", "csu_ers", "uc_ss", "csac", "edd_wages", "ctc_educator", "sib_calkids",
               "dds_earlystart", "cwdb_caal", "etp", "ccgi", "calsaws"]
for m in C2C_MEMBERS:
    link(m, "c2c", "c2c", "Annual data submission matched into P20W", "Person matching (name, birth date, SSN or partner ID)")
for m in ["cde_assess", "aiccu", "bppe", "edd_caljobs", "dhcs_medi_cal", "dmv", "ctc_permits", "dor"]:
    link(m, "c2c", "periodic", "Partial or unconfirmed participation", "Person matching", "Scope needs confirmation")
for m in ["cde_capsdac", "cde_cdmis", "cdss_ccdd", "dir_das"]:
    link(m, "c2c", "planned", "Approved or in C2C work plan, not yet imported", "To be determined")
link("ecids", "c2c", "planned", "AB 2092 design: connect ECIDS to C2C at kindergarten entry", "Proposed")

link("cdph_birth", "sib_calkids", "routine", "Monthly birth file opens newborn CalKIDS accounts", "Birth record")
link("cde_calpads", "sib_calkids", "routine", "Student file opens school-based CalKIDS accounts", "SSID")
link("cdph_birth", "dhcs_medi_cal", "routine", "Newborns of Medi-Cal mothers are deemed eligible", "CIN")
link("cdph_birth", "cdph_nbs", "routine", "Screening tied to birth", "Birth record")
link("cdph_nbs", "dds_earlystart", "periodic", "Referral of flagged infants", "None shared")
link("cdph_wic", "dhcs_medi_cal", "periodic", "Adjunctive eligibility checks", "CIN")
link("calsaws", "dhcs_medi_cal", "routine", "Shared eligibility through MEDS", "CIN")
link("calsaws", "cdss_hvp", "routine", "CalWORKs families referred to home visiting", "CIN")
link("calsaws", "cdss_ccdd", "periodic", "CalWORKs Stage 1 to Stage 2 child care handoff", "Case number (no statewide child ID)")
link("cde_cdmis", "cdss_ccdd", "periodic", "Co-enrollment flag added to CSPP reporting in 2025", "Yes/no flag only")
link("cde_capsdac", "cde_calpads", "periodic", "SSID encouraged in CAPSDAC", "SSID (optional)")
link("cde_calpads", "cde_assess", "routine", "Assessments keyed to enrollment", "SSID")
link("cde_calpads", "cde_public", "routine", "Aggregates feed Dashboard and DataQuest", "SSID")
link("cde_calpads", "ctc_educator", "routine", "Staff assignments matched to credentials (TAMO)", "SEID")
link("cde_calpads", "cde_dircert", "routine", "Weekly or monthly benefits match", "Name, birth date, address")
link("calsaws", "cde_dircert", "routine", "CalFresh and CalWORKs rosters", "CIN")
link("dhcs_medi_cal", "cde_dircert", "routine", "Medi-Cal rosters", "CIN")
link("cws", "cde_foster", "routine", "Weekly foster youth match", "CWS client ID to SSID")
link("cde_foster", "cde_calpads", "routine", "Foster flag written to CALPADS", "SSID")
link("dds_earlystart", "cde_calpads", "periodic", "Part C to Part B transition at age 3 (local referral)", "UCI to SSID, local")
link("cde_calpads", "ccgi", "routine", "Transcript and A-G data for students", "SSID")
link("ccgi", "csac", "routine", "GPA and aid status exchange", "SSID")
link("cde_calpads", "csac", "routine", "Cal Grant GPA upload and FAFSA completion tracking", "SSID and name")
link("cde_calpads", "calpass", "periodic", "Voluntary MOU uploads", "SSID")
link("ccc_mis", "calpass", "periodic", "Voluntary MOU uploads", "CCCID and SSN")
link("ccc_mis", "ccc_launchboard", "routine", "Program outcomes reporting", "SSN")
link("edd_wages", "ccc_launchboard", "routine", "Wage match for CTE outcomes", "SSN")
link("ccc_mis", "csu_ers", "periodic", "Transfer verification", "SSN and name")
link("ccc_mis", "uc_ss", "periodic", "Transfer verification", "SSN and name")
link("csac", "ccc_mis", "routine", "Cal Grant and aid payment", "SSN or CADAA ID")
link("csac", "csu_ers", "routine", "Cal Grant and aid payment", "SSN or CADAA ID")
link("csac", "uc_ss", "routine", "Cal Grant and aid payment", "SSN or CADAA ID")
link("fed_fsa", "csac", "routine", "FAFSA ISIR records", "SSN")
link("edd_caljobs", "edd_wages", "routine", "WIOA performance wage match", "SSN")
link("cwdb_caal", "edd_wages", "routine", "Program outcome wage match", "SSN")
link("dor", "cwdb_caal", "routine", "VR participant data", "SSN")
link("etp", "cwdb_caal", "periodic", "Program data", "SSN")
link("caep", "edd_wages", "periodic", "Partial wage match for adult learners with SSN", "SSN")
link("swis", "edd_caljobs", "periodic", "Out-of-state wages for WIOA performance only", "SSN")
link("cde_calpads", "cde_expanded", "missing", "Expanded learning participation not reported by SSID", "None")
link("head_start", "cde_calpads", "missing", "No record of Head Start at kindergarten entry", "None")
link("first5", "cde_calpads", "missing", "No record of First 5 services at school entry", "None")
link("cdss_ccdd", "cde_calpads", "missing", "No record of subsidized child care at school entry", "None")
link("drdp", "cde_calpads", "missing", "Preschool developmental data not carried into TK/K", "Local ID")
link("chvp", "ecids", "missing", "Home visiting not part of any linked system", "None")
link("dhcs_medi_cal", "ecids", "missing", "Developmental screening not linked to early learning", "CIN")
link("ece_registry", "ctc_permits", "missing", "ECE employment not tied to permit records", "None")
link("ctc_permits", "edd_wages", "missing", "ECE workforce wages and retention not tracked", "SSN")
link("fed_fsa", "c2c", "missing", "Federal loan and debt data unavailable", "SSN")
link("nsc", "c2c", "missing", "Out-of-state and most private college enrollment unseen", "SSN")
link("swis", "c2c", "missing", "Out-of-state, federal and military wages unseen", "SSN")
link("ftb", "c2c", "missing", "Self-employment and gig income unseen", "SSN or ITIN")
link("cdcr", "c2c", "missing", "Justice-involved learners and reentry unseen", "None")
link("caep", "c2c", "missing", "K-12 adult schools not in C2C", "SSN (often missing)")
link("hdis", "cde_calpads", "missing", "Homeless services and McKinney-Vento counts not reconciled", "None")
link("dxf", "ecids", "missing", "No bridge between health exchange and early learning data", "None")
link("cdph_birth", "c2c", "missing", "No birth anchor for the lifelong record (beyond CalKIDS)", "Birth record")
link("bppe", "edd_wages", "missing", "Private vocational school outcomes not wage matched by the state", "SSN")

# ---------------------------------------------------------------------------
# Gap heatmap: handoffs x dimensions (0 = strong, 4 = critical gap)
# ---------------------------------------------------------------------------
DIMENSIONS = [
    {"id": "identifier", "name": "Shared identifier"},
    {"id": "individual", "name": "Individual-level records"},
    {"id": "c2c", "name": "In C2C today"},
    {"id": "legal", "name": "Legal authority to share"},
    {"id": "standards", "name": "Common definitions"},
    {"id": "timeliness", "name": "Timeliness"},
    {"id": "public", "name": "Public usability"},
]
HEATMAP = [
    {"id": "birth_ece", "name": "Birth to early care", "scores": [4, 3, 4, 3, 3, 3, 4],
     "why": "Birth records are universal but nothing carries them forward except CalKIDS. ECE programs assign local IDs."},
    {"id": "health_ece", "name": "Health and home visiting to early care", "scores": [4, 3, 4, 4, 3, 3, 4],
     "why": "Medi-Cal, WIC and home visiting use CIN or program IDs. HIPAA and W&I Code 10850 limit sharing with ECE without a framework."},
    {"id": "ece_internal", "name": "Across ECE programs (CDE, CDSS, Head Start, First 5)", "scores": [4, 2, 4, 2, 3, 2, 3],
     "why": "Child-level data exists in CDE and CDSS systems but cannot be unduplicated. Head Start and First 5 data stay local."},
    {"id": "ece_tk", "name": "Early care to TK and kindergarten", "scores": [3, 2, 4, 2, 3, 2, 4],
     "why": "SSID is optional in CAPSDAC and absent elsewhere. Kindergarten records carry no preschool history."},
    {"id": "hhs_k12", "name": "Human services to TK-12", "scores": [2, 1, 2, 2, 2, 1, 3],
     "why": "Direct certification and the foster match work routinely, but only as flags. The CIN link is not retained."},
    {"id": "k12_post", "name": "TK-12 to postsecondary", "scores": [1, 0, 0, 1, 2, 2, 2],
     "why": "Strongest handoff. SSID reaches CCCApply and CaliforniaColleges.edu. CCI still lacks C2C outcomes; course data definitions vary."},
    {"id": "transfer", "name": "Community college to CSU and UC", "scores": [2, 0, 1, 2, 3, 2, 2],
     "why": "All three are in C2C. Definitions differ across segments and the transfer dashboard is still being built."},
    {"id": "post_private", "name": "Private, out-of-state and adult education", "scores": [3, 3, 3, 2, 3, 3, 3],
     "why": "BPPE schools report aggregates, AICCU is voluntary, adult schools are outside C2C, NSC is unused."},
    {"id": "post_work", "name": "Postsecondary to UI-covered jobs", "scores": [2, 1, 0, 1, 2, 2, 2],
     "why": "EDD wages are in C2C, but students without SSNs fall out and there is no occupation or hours field."},
    {"id": "training_work", "name": "Apprenticeship and job training to earnings", "scores": [2, 2, 2, 2, 3, 3, 3],
     "why": "DAS, CalJOBS and ETP joined in 2025 and are still being imported. Program taxonomies differ."},
    {"id": "nonui_work", "name": "Self-employed, gig, federal and out-of-state work", "scores": [2, 4, 4, 3, 3, 3, 4],
     "why": "Outside UI wage records entirely. FTB and SWIS hold the data but are not available for C2C."},
    {"id": "workforce_pipeline", "name": "Educator pipeline (ECE and TK-12)", "scores": [3, 2, 3, 2, 3, 3, 3],
     "why": "TK-12 teachers link through SEID and CTC. ECE educators have permits but no employment records."},
    {"id": "justice", "name": "Justice, homelessness and reentry", "scores": [4, 3, 4, 4, 3, 3, 4],
     "why": "CDCR, HMIS/HDIS and juvenile justice data do not reach education or wage records."},
]

# ---------------------------------------------------------------------------
# Gaps (narrative)
# ---------------------------------------------------------------------------
GAPS = [
    {"id": "G1", "type": "identifier", "severity": 5, "segment": "early", "title": "No statewide child identifier before school",
     "detail": "From birth to TK, a child may appear in birth records, Medi-Cal, WIC, home visiting, Early Start, CDSS child care, CSPP, Head Start and First 5, each under a different ID or none. The SSID is the first durable ID, and it arrives at age 4 or 5.",
     "evidence": "CAPSDAC encourages but does not require SSID (CDE CAPSDAC Update #1, 2024). CDMIS and CDD-801A use local IDs.",
     "recs": ["R1", "R2", "R3"]},
    {"id": "G2", "type": "coverage", "severity": 5, "segment": "early", "title": "Early learning and care is still outside C2C",
     "detail": "C2C planned CDE early learning points (entry age, duration, family income) in 2023 but had not received them. The 2026-27 work plan only sets initial milestones for a future import. CDSS child care, Head Start and First 5 have no path at all.",
     "evidence": "C2C Data Elements by Provider (planned status); C2C 2026-27 Work Plan; AB 2092 held May 2026.",
     "recs": ["R1", "R3"]},
    {"id": "G3", "type": "governance", "severity": 4, "segment": "early", "title": "No legal home or lead agency for an ECIDS",
     "detail": "Early childhood data is split between CDE (CSPP), CDSS (child care, CalWORKs, licensing), CDPH (WIC, home visiting, births), DHCS (Medi-Cal), DDS (Early Start), First 5 and federal Head Start. AB 2092 would have named CDSS as lead but was held in Appropriations.",
     "evidence": "Assembly Human Services analysis of AB 2092 (March 2026); Master Plan for Early Learning and Care (2020).",
     "recs": ["R3", "R9"]},
    {"id": "G4", "type": "content", "severity": 4, "segment": "work", "title": "Wage records lack occupation, hours and location",
     "detail": "UI wage records show only quarterly earnings by employer. Without occupation or hours, the state cannot tell whether a nursing graduate works as a nurse, or whether low earnings mean low pay or part-time work.",
     "evidence": "SB 1054 (Cabaldon, 2026) would add occupation, hours, worker type and monthly wages; held in Assembly Appropriations.",
     "recs": ["R4", "R8"]},
    {"id": "G5", "type": "identifier", "severity": 4, "segment": "post", "title": "SSN dependence leaves out immigrant students",
     "detail": "Workforce outcomes depend on SSN matching. Undocumented and mixed-status students, CA Dream Act filers, and anyone who declines to give an SSN disappear from earnings outcomes, which biases every equity analysis.",
     "evidence": "CCC LaunchBoard and C2C wage matching rely on SSN; CADAA filers use non-SSN IDs.",
     "recs": ["R10", "R13"]},
    {"id": "G6", "type": "coverage", "severity": 3, "segment": "work", "title": "Earnings outside UI coverage are invisible",
     "detail": "Self-employed, gig, federal civilian, military and out-of-state workers have no UI wage record in California. FTB tax data and the federal SWIS exchange hold this information but are not available to C2C.",
     "evidence": "SWIS use limited to WIOA performance; FTB confidentiality under Revenue and Taxation Code 19542.",
     "recs": ["R10"]},
    {"id": "G7", "type": "coverage", "severity": 3, "segment": "post", "title": "Private, out-of-state and adult learners are partly missing",
     "detail": "BPPE institutions report aggregates, AICCU participation is voluntary, K-12 adult schools are outside C2C, and the National Student Clearinghouse is not used, so a student who leaves for Arizona State or a private trade school looks like a dropout.",
     "evidence": "C2C partner list; BPPE Student Performance Fact Sheets are institution-level.",
     "recs": ["R8", "R10"]},
    {"id": "G8", "type": "governance", "severity": 3, "segment": "post", "title": "FERPA interpretations block student debt and some segment data",
     "detail": "CSU and UC have cited FERPA in declining student-level debt data, and federal loan data (NSLDS) is not shared with states. The 2024 student debt proposal at C2C stalled.",
     "evidence": "D4TP 2026 Retreat Report, Priority 3; UC participation is requested, not required, under statute.",
     "recs": ["R7", "R14"]},
    {"id": "G9", "type": "standards", "severity": 3, "segment": "hub", "title": "Definitions differ across agencies",
     "detail": "Race and ethnicity categories (including the MENA category), dual language learner status, transfer, completion, and program codes (TOP, CIP, SOC) differ across CDE, CCC, CSU, UC and workforce agencies.",
     "evidence": "D4TP Priority 5 (standard definitions across CCC, CSU and UC); ECE workgroup on DLL definitions.",
     "recs": ["R6", "R8"]},
    {"id": "G10", "type": "coverage", "severity": 3, "segment": "early", "title": "The ECE workforce cannot be followed",
     "detail": "Child Development Permits live at CTC, the Workforce Registry is voluntary, and ECE employers do not report staff to any state system. Turnover, wages and pathways into TK teaching are unknown at the state level.",
     "evidence": "CSCCE 2025 workforce study notes its sample does not represent the whole workforce.",
     "recs": ["R11"]},
    {"id": "G11", "type": "coverage", "severity": 3, "segment": "hhs", "title": "Vulnerable populations drop between systems",
     "detail": "Justice-involved youth and adults, people experiencing homelessness, and youth aging out of foster care move across systems that do not link to education or wages.",
     "evidence": "CDCR and HDIS are not C2C partners; foster flag ends at K-12 exit.",
     "recs": ["R12"]},
    {"id": "G12", "type": "capacity", "severity": 3, "segment": "hub", "title": "Funding and staff capacity at partner agencies",
     "detail": "Each new data point needs agency staff, file specs and legal review. CDT flagged C2C's schedule for corrective action in 2025, and partners carry the work on top of operations.",
     "evidence": "CalMatters (March 2025) on CDT oversight; C2C budget change concept, August 2026.",
     "recs": ["R14"]},
    {"id": "G13", "type": "access", "severity": 2, "segment": "hub", "title": "Linked insights are slow to reach families and schools",
     "detail": "C2C is an analytical system with annual submissions. Schools still cannot see what happened to their graduates on the CCI, and families see little of the linked data.",
     "evidence": "D4TP TK-12 recommendation to connect C2C data to the CCI and extend Student Pathways from 9 to 13 years.",
     "recs": ["R5", "R15"]},
]

# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
RECS = [
    {"id": "R1", "horizon": "Phase 1: Foundations (2027-2028)", "title": "Stand up an Early Learning Data Task Force at C2C",
     "what": "Ask the C2C Governing Board to charter a task force that defines the first early learning data points (program, entry age, duration, family income, DLL status), adopts an ECE-to-TK crosswalk, and sets an import date for CDE and CDSS data.",
     "vehicle": "C2C Governing Board action", "bodies": "C2C Governing Board, CDE, CDSS, Early Childhood Policy Council",
     "priority": ["P1", "P5"], "gaps": ["G1", "G2"], "metric": "Early learning records present in P20W for the 2028 kindergarten cohort"},
    {"id": "R2", "horizon": "Phase 1: Foundations (2027-2028)", "title": "Assign a matchable ID at first contact with any state-funded ECE program",
     "what": "Require SSID (or a C2C-issued token) in CAPSDAC and in the new CDE and CDSS CDMIS monthly reports that start in July 2027, so preschool and child care records can match to kindergarten.",
     "vehicle": "Budget trailer bill or CDE/CDSS management bulletin", "bodies": "CDE, CDSS, CSIS",
     "priority": ["P1"], "gaps": ["G1"], "metric": "Share of CSPP and CDSS child records with a valid SSID or token"},
    {"id": "R3", "horizon": "Phase 1: Foundations (2027-2028)", "title": "Authorize and fund a phased ECIDS connected to C2C",
     "what": "Bring back the AB 2092 framework with a tested cost estimate and phasing: Phase A links CDE and CDSS child records; Phase B adds Early Start, home visiting and Medi-Cal screening; all phases connect to C2C at kindergarten entry.",
     "vehicle": "Legislation plus budget ask", "bodies": "CDSS (lead), CDE, CDPH, DHCS, DDS, First 5 California",
     "priority": ["P1", "P5"], "gaps": ["G2", "G3"], "metric": "Unduplicated count of children 0 to 5 served by state programs, published annually"},
    {"id": "R4", "horizon": "Phase 1: Foundations (2027-2028)", "title": "Enhance UI wage records with occupation and hours",
     "what": "Reintroduce SB 1054-style reporting with a lower-cost phase-in: large employers first, SOC occupation and hours before other fields, and alignment with CalSAWS work-requirement verification to share costs.",
     "vehicle": "Legislation", "bodies": "EDD, LWDA, CDSS, DHCS",
     "priority": ["P4"], "gaps": ["G4"], "metric": "Share of UI wage records with occupation and hours"},
    {"id": "R5", "horizon": "Phase 1: Foundations (2027-2028)", "title": "Return postsecondary outcomes to schools through the CCI",
     "what": "Link C2C postsecondary enrollment and completion back to the College/Career Indicator, and extend the Student Pathways Dashboard from 9 to 13 years of data.",
     "vehicle": "C2C Governing Board and State Board of Education", "bodies": "C2C, CDE, SBE",
     "priority": ["P2", "P5"], "gaps": ["G13"], "metric": "CCI reports include C2C-verified college enrollment"},
    {"id": "R6", "horizon": "Phase 1: Foundations (2027-2028)", "title": "Adopt common definitions across agencies",
     "what": "Publish a statewide data standards register starting with race and ethnicity (including MENA), dual language learner, transfer, completion and program codes, and require new C2C points to use it.",
     "vehicle": "C2C Governance Manual and CEIC coordination", "bodies": "C2C, CEIC, CCCCO, CSU, UC, CDE",
     "priority": ["P5", "P3"], "gaps": ["G9"], "metric": "Number of core elements with one shared definition"},
    {"id": "R7", "horizon": "Phase 1: Foundations (2027-2028)", "title": "Put student debt data into C2C",
     "what": "Revive the student debt proposal with CSAC, CSU and UC data points and a FERPA analysis, and pursue aggregate federal loan data agreements.",
     "vehicle": "C2C Data and Tools Advisory Board proposal", "bodies": "C2C, CSAC, CSU, UC",
     "priority": ["P3"], "gaps": ["G8"], "metric": "Debt at completion available by segment and program"},
    {"id": "R8", "horizon": "Phase 2: Connect the edges (2029-2032)", "title": "Finish the workforce expansion and build a program-to-occupation crosswalk",
     "what": "Complete import of DAS apprenticeship, CalJOBS, ETP and DOR data; bring K-12 adult schools and BPPE student records in; and publish a CIP/TOP-to-SOC crosswalk so Workforce Pell and short-term programs can be judged on outcomes.",
     "vehicle": "C2C work plan, AB 1534 Workforce Pell implementation", "bodies": "C2C, LWDA, CWDB, DIR, CSAC, BPPE, CDE",
     "priority": ["P4"], "gaps": ["G4", "G7", "G9"], "metric": "Outcomes published for every publicly funded short-term program"},
    {"id": "R9", "horizon": "Phase 2: Connect the edges (2029-2032)", "title": "Bridge early childhood health and human services data",
     "what": "Use the CalHHS Data Exchange Framework and a consent strategy to add Medi-Cal developmental screening, WIC, home visiting and Early Start participation to ECIDS, with only de-identified results flowing to C2C.",
     "vehicle": "Interagency agreement under CalHHS; ECIDS phase B", "bodies": "CalHHS, HCAI, DHCS, CDPH, DDS, CDSS",
     "priority": ["P1", "P5"], "gaps": ["G3"], "metric": "Share of kindergartners whose early screening history is known in aggregate"},
    {"id": "R10", "horizon": "Phase 2: Connect the edges (2029-2032)", "title": "Close the missing-outcomes gap",
     "what": "Negotiate NSC enrollment data, SWIS and federal wage access for C2C research, and an FTB match for self-employment income, using identity methods that do not require an SSN.",
     "vehicle": "Statute (FTB) and interagency or federal agreements", "bodies": "C2C, FTB, EDD, U.S. DOL",
     "priority": ["P4", "P5"], "gaps": ["G5", "G6", "G7"], "metric": "Share of graduates with any known outcome"},
    {"id": "R11", "horizon": "Phase 2: Connect the edges (2029-2032)", "title": "Track the whole educator pipeline, birth to grade 12",
     "what": "Link Child Development Permits, the ECE Workforce Registry and licensed-site staffing to CTC and SEID records so ECE and TK-12 workforce data appear together in the C2C teacher dashboard.",
     "vehicle": "CTC and CDSS licensing rules; C2C dashboard scope", "bodies": "CTC, CDSS, CDE, C2C",
     "priority": ["P1", "P2"], "gaps": ["G10"], "metric": "Annual ECE workforce turnover and wage report from administrative data"},
    {"id": "R12", "horizon": "Phase 2: Connect the edges (2029-2032)", "title": "Follow students who cross systems",
     "what": "Add CDCR and Rising Scholars, HDIS homelessness data, extended foster care and juvenile justice records as C2C partners with strict use limits.",
     "vehicle": "C2C Governing Board (Education Code 10866)", "bodies": "C2C, CDCR, Cal ICH, CDSS",
     "priority": ["P5"], "gaps": ["G11"], "metric": "Postsecondary and earnings outcomes reported for foster, homeless and justice-involved learners"},
    {"id": "R13", "horizon": "Phase 3: Whole learner, whole life (2033-2037)", "title": "Build a privacy-preserving California Learner Identifier",
     "what": "Turn C2C person matching into a statewide token service: issued at birth or first public contact, never based on SSN, used by every partner for matching, and never exposed outside the system.",
     "vehicle": "Statute and multi-year IT budget", "bodies": "C2C, GovOps, CDT, all partners",
     "priority": ["P5"], "gaps": ["G1", "G5"], "metric": "Match rate across partners, including for students without SSNs"},
    {"id": "R14", "horizon": "Phase 3: Whole learner, whole life (2033-2037)", "title": "Make participation and funding durable",
     "what": "Require participation by every public entity that receives state education, workforce or early learning funds; fund dedicated data staff at each partner; and publish an annual linkage scorecard.",
     "vehicle": "Statute and ongoing budget", "bodies": "Legislature, Governor, C2C, CEIC",
     "priority": ["P5"], "gaps": ["G8", "G12"], "metric": "Annual linkage scorecard, with every segment in this map rated"},
    {"id": "R15", "horizon": "Phase 3: Whole learner, whole life (2033-2037)", "title": "Put linked data to work for families",
     "what": "Use the linked system to automate eligibility (child care, Cal Grant, CalKIDS claims), warm handoffs at each transition, and family-facing pathway tools, under community oversight.",
     "vehicle": "Operational tools under C2C and CalHHS", "bodies": "C2C, CalHHS, CSAC, SIB, CCGI",
     "priority": ["P5", "P1", "P4"], "gaps": ["G13"], "metric": "Benefits and supports delivered automatically at each transition"},
]

# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------
TIMELINE = [
    {"date": "2019-06", "kind": "law", "title": "Budget Act funds C2C planning", "detail": "2019 Budget Act (SB 75) funds a planning process for a statewide longitudinal data system, facilitated by WestEd."},
    {"date": "2020-12", "kind": "plan", "title": "Master Plan for Early Learning and Care", "detail": "Calls for integrated early childhood data. Same month: first C2C legislative report."},
    {"date": "2021-07", "kind": "law", "title": "AB 132 establishes C2C", "detail": "Education Code 10850-10875 creates the system and the Office of Cradle-to-Career Data in GovOps. Child care programs move from CDE to CDSS (AB 131)."},
    {"date": "2021-07", "kind": "law", "title": "AB 133 creates the CalHHS Data Exchange Framework", "detail": "Health and Safety Code 130290."},
    {"date": "2022-07", "kind": "launch", "title": "CalKIDS newborn accounts begin", "detail": "Every child born on or after July 1, 2022 gets a seeded account. Universal TK rollout begins in 2022-23."},
    {"date": "2023-11", "kind": "milestone", "title": "First C2C data submissions", "detail": "Eight initial data partners submit data in 2023."},
    {"date": "2024-05", "kind": "c2c", "title": "DDS joins C2C", "detail": "Resolution 24-02 adds Developmental Services data, including Early Start."},
    {"date": "2024-07", "kind": "launch", "title": "CAPSDAC required for LEA-run state preschool", "detail": "Education Code 60910 child, classroom and staff data."},
    {"date": "2025-02", "kind": "c2c", "title": "ScholarShare (CalKIDS) joins C2C", "detail": "Resolution 25-01."},
    {"date": "2025-04", "kind": "launch", "title": "Student Pathways Dashboard launches", "detail": "First public C2C tool, announced April 22, 2025."},
    {"date": "2025-05", "kind": "c2c", "title": "Largest C2C expansion: workforce data", "detail": "Board approves LWDA labor and training data, with CWDB and ETP as new partners and apprenticeship data from DAS."},
    {"date": "2026-05", "kind": "bill", "title": "AB 2092 (ECIDS) held in Appropriations", "detail": "Would have created an ECIDS under CDSS linked to C2C."},
    {"date": "2026-05", "kind": "c2c", "title": "New EDD data points approved", "detail": "Employer ID and name among new P20W points; EDD moves to Snowflake transfer."},
    {"date": "2026-07", "kind": "law", "title": "SB 135 higher education trailer bill", "detail": "Chapter 79, Statutes of 2026. Requires partner MOUs for data sharing and requests UC participation."},
    {"date": "2026-07", "kind": "milestone", "title": "C2C five-year mark: 16 data partners", "detail": "Up from 8 partners submitting data in 2023."},
    {"date": "2026-08", "kind": "plan", "title": "C2C 2026-31 Strategic Plan and 2026-27 Work Plan", "detail": "Transfer outcomes and teacher dashboards; initial milestones for early learning and care data import."},
    {"date": "2026-08", "kind": "bill", "title": "SB 1054 (enhanced wage records) held", "detail": "Held in Assembly Appropriations."},
    {"date": "2026-09", "kind": "law", "title": "AB 1534 Workforce Pell oversight signed", "detail": "Reported chaptered September 27, 2026. Creates a state approval process for Workforce Pell programs."},
    {"date": "2026-10", "kind": "launch", "title": "CDE announces CDMIS 2.0", "detail": "CDMIS Monthly Report replaces the 801A beginning July 2027."},
    {"date": "2026-11", "kind": "milestone", "title": "D4TP letter on Early Learning Data Task Force", "detail": "Coalition letter considered for the November 13 C2C Governing Board meeting."},
]


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------
def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("; ".join(map(str, r[k])) if isinstance(r[k], list) else r[k]) for k in fields})


def main():
    os.makedirs(OUT, exist_ok=True)
    ids = {s["id"] for s in SOURCES}
    idents = [dict(zip(["id", "name", "issuer", "scope", "age_min", "age_max", "notes"], i)) for i in IDENTIFIERS]
    ident_ids = {i["id"] for i in idents}
    for s in SOURCES:
        for i in s["identifiers"]:
            assert i in ident_ids, (s["id"], i)
    for l in L:
        assert l["source"] in ids and l["target"] in ids, l
    for r in RECS:
        for g in r["gaps"]:
            assert any(x["id"] == g for x in GAPS), g

    # derived: links per source
    for s in SOURCES:
        s["linked_to"] = sorted({l["target"] if l["source"] == s["id"] else l["source"]
                                 for l in L if s["id"] in (l["source"], l["target"]) and l["status"] != "missing"})
        s["missing_links"] = sorted({l["target"] if l["source"] == s["id"] else l["source"]
                                     for l in L if s["id"] in (l["source"], l["target"]) and l["status"] == "missing"})

    data = {"as_of": AS_OF, "segments": SEGMENTS, "sources": SOURCES, "linkages": L, "identifiers": idents,
            "dimensions": DIMENSIONS, "heatmap": HEATMAP, "gaps": GAPS, "recommendations": RECS, "timeline": TIMELINE}

    for name in ["sources", "linkages", "identifiers", "gaps", "recommendations", "timeline"]:
        with open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(data[name], f, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT, "heatmap.json"), "w", encoding="utf-8") as f:
        json.dump({"dimensions": DIMENSIONS, "rows": HEATMAP}, f, indent=2, ensure_ascii=False)

    write_csv(os.path.join(OUT, "sources.csv"), SOURCES,
              ["id", "name", "segment", "owner", "owner_type", "age_min", "age_max", "population", "unit", "system_type",
               "key_variables", "identifiers", "access", "legal", "c2c_status", "c2c_note", "linked_to", "missing_links",
               "url", "notes", "confidence"])
    write_csv(os.path.join(OUT, "linkages.csv"), L, ["source", "target", "status", "mechanism", "identifier", "note"])
    write_csv(os.path.join(OUT, "identifiers.csv"), idents, ["id", "name", "issuer", "scope", "age_min", "age_max", "notes"])
    write_csv(os.path.join(OUT, "gaps.csv"), GAPS, ["id", "type", "severity", "segment", "title", "detail", "evidence", "recs"])
    write_csv(os.path.join(OUT, "recommendations.csv"), RECS,
              ["id", "horizon", "title", "what", "vehicle", "bodies", "priority", "gaps", "metric"])

    with open(os.path.join(OUT, "data.js"), "w", encoding="utf-8") as f:
        f.write("// Generated by scripts/build_data.py. Do not edit by hand.\n")
        f.write("window.D4TP_LANDSCAPE = ")
        json.dump(data, f, ensure_ascii=False)
        f.write(";\n")

    by = {}
    for s in SOURCES:
        by[s["c2c_status"]] = by.get(s["c2c_status"], 0) + 1
    print(f"{len(SOURCES)} sources, {len(L)} linkages, {len(idents)} identifiers, {len(GAPS)} gaps, {len(RECS)} recs")
    print("C2C status:", by)


if __name__ == "__main__":
    main()

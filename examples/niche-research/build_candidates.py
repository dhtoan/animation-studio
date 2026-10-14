"""Builds candidates.json: 20 documentary ideas with factor scores tied to evidence.json ids.

Factor scores are an editorial reading of the cited evidence (rationale stored per factor).
Topic-level audience age and RPM are NOT measurable from public data; audience fit cites
platform-level reach (Pew/Nielsen) and is marked as an agent assessment; revenue uses the
'ad-demand-proxy' category (capped at 5) and never a dollar figure.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

P = {  # pillar -> evidence ids used per factor
    "1": {"demand": ["e020", "e021", "e024", "e026"], "comp": ["e015", "e016", "e025"], "adv": ["e029", "e030"]},
    "2": {"demand": ["e036", "e038", "e040", "e042"], "comp": ["e031", "e032", "e041"], "adv": ["e045"]},
    "3": {"demand": ["e051", "e052", "e053", "e057"], "comp": ["e046", "e047"], "adv": ["e059"]},
    "4": {"demand": ["e064", "e068"], "comp": ["e060", "e061"], "adv": ["e070"]},
    "5": {"demand": ["e075", "e076", "e079"], "comp": ["e071", "e072"], "adv": ["e081"]},
    "6": {"demand": ["e086", "e090"], "comp": ["e082", "e083"], "adv": ["e091"]},
    "7": {"demand": ["e096", "e098", "e100"], "comp": ["e092", "e093"], "adv": ["e102"]},
    "8": {"demand": ["e107", "e108", "e109", "e112"], "comp": ["e103", "e104", "e110"], "adv": ["e114"]},
    "9": {"demand": ["e119", "e123"], "comp": ["e115", "e116"], "adv": ["e125"]},
    "10": {"demand": ["e130", "e134"], "comp": ["e126", "e127"], "adv": ["e136"]},
    "11": {"demand": ["e141", "e146"], "comp": ["e137", "e138"], "adv": ["e148"]},
    "12": {"demand": ["e153", "e157"], "comp": ["e149", "e150"], "adv": ["e159"]},
}
AUD = ["e001", "e003", "e005"]
# (demand, competition_gap, evergreen) per pillar: editorial reading of the cited evidence
PILLAR_SCORES = {"1": (9, 4, 9), "2": (7, 6, 8), "3": (8, 5, 7), "4": (3, 7, 6), "5": (6, 5, 8), "6": (3, 7, 7),
                 "7": (6, 6, 6), "8": (9, 4, 8), "9": (5, 6, 7), "10": (5, 5, 8), "11": (4, 6, 7), "12": (4, 6, 6)}
NOTES = {
    "1": "14M/7M-view recent WWII uploads (Yarnhub) show strong demand; large established channels make it crowded.",
    "2": "Cold War documentaries drew 0.3-2.3M views recently; many tiny faceless uploads compete but rarely break out.",
    "3": "Rise-and-fall brand stories drew 0.3-1.5M views in the last 30 days; competitors focus on modern brands.",
    "4": "New faceless channels on lost industries got 1-800 views in the sample: weak demand signal, low competition.",
    "5": "Steady evergreen interest; established competitors.",
    "6": "No large dedicated channel found; this-year searches show low views.",
    "7": "High demand for modern scandals (4.7M); no large channel focused on pre-1990 scandals (gap; historic demand unproven).",
    "8": "7.2M / 6.0M-view espionage stories (fern): very strong demand, strong competition.",
    "9": "Hit-driven: one 800K video beside uploads with 1-2K views.",
    "10": "Query dominated by non-history channels; mixed signal.",
    "11": "Tiny uploads with 3-1.3K views this year; advertiser sensitivity around casualties.",
    "12": "Generic biography format appears to be weakening (inferred from one channel grid).",
}
IDEAS = [
    ("The Ghost Army: America's secret unit of artists and illusions", "1", "Forgotten Battles of WWII", 9, 9, "artists + deception, documented by PL 117-85", "PL 117-85; National WWII Museum; Army", "archival + maps + handdrawn"),
    ("Operation Pastorius: the Nazi saboteurs who landed on American beaches (1942)", "8", "Hidden Chapters of WWII America", 9, 8, "home-front espionage on U.S. soil", "FBI history; court records", "maps + archival"),
    ("Project Azorian: how the CIA tried to raise a Soviet submarine", "2", "Cold War Files", 8, 9, "engineering + secrecy; declassified records", "CIA FOIA reading room", "motion + maps"),
    ("Camp Century: the city under the Greenland ice", "2", "Cold War Files", 8, 8, "engineering + Cold War secret", "Army technical reports", "whiteboard + maps"),
    ("The Greenbrier bunker: Congress's secret Cold War shelter", "2", "Cold War Files", 8, 7, "a U.S. landmark many 50+ viewers remember from 1992 reporting", "Senate and House history pages", "archival + motion"),
    ("The rise and fall of Studebaker", "3", "America's Lost Industrial Giants", 9, 8, "a car many viewers' families owned; factory-town story", "corporate history; museum", "motion + archival"),
    ("Polaroid: the instant camera empire that missed the digital turn", "3", "America's Lost Industrial Giants", 8, 8, "nostalgic product + strategic lesson", "SEC filings; museum", "motion + kinetic"),
    ("Montgomery Ward: how a catalog giant disappeared", "3", "America's Lost Industrial Giants", 9, 7, "catalog shopping memories", "corporate archives", "motion + archival"),
    ("Bethlehem Steel and the towns it built", "4", "America's Forgotten Towns", 8, 8, "industrial town decline", "Library of Congress; NPS", "maps + archival"),
    ("The SR-71 Blackbird: building a plane faster than missiles", "5", "The Men Behind the Machines", 8, 8, "engineering icon", "Air Force museum; CIA documents", "whiteboard + motion"),
    ("Philo Farnsworth: the farm boy who invented electronic television", "6", "The Men Behind the Machines", 7, 8, "forgotten inventor vs corporate giant", "Library of Congress; Smithsonian", "handdrawn + whiteboard"),
    ("The Great Salad Oil Swindle of 1963", "7", "Hidden Chapters of American Business", 8, 8, "pre-1990 scandal with a documented court record", "court records; newspapers", "motion + archival"),
    ("Ivar Kreuger, the Match King, and the crash of 1932", "7", "Hidden Chapters of American Business", 6, 8, "global fraud with U.S. investors", "SEC and historical reports", "motion + archival"),
    ("The Walker spy ring: a Navy family that sold secrets for 17 years", "8", "Cold War Files", 8, 8, "family espionage drama with court records", "FBI; court records", "handdrawn + motion"),
    ("Building the Interstate Highway System (1956)", "9", "Decisions That Changed America", 9, 7, "every viewer has used these roads", "FHWA history", "maps + motion"),
    ("D.B. Cooper: what the FBI file actually says", "10", "Unsolved Files", 8, 8, "enduring mystery; FBI Vault records", "FBI Vault", "archival + maps"),
    ("The Hyatt Regency walkway collapse (1981): an engineering lesson", "11", "Engineering Lessons", 7, 7, "engineering ethics; treat victims respectfully", "NIST/NBS report", "whiteboard"),
    ("The Johnstown Flood of 1889: a dam, a club and a disaster", "11", "Engineering Lessons", 6, 8, "evergreen; NPS memorial", "NPS", "maps + archival"),
    ("Hedy Lamarr: the actress who co-invented frequency hopping", "12", "The Men and Women Behind the Machines", 8, 8, "surprising inventor story", "patent records; Smithsonian", "handdrawn + whiteboard"),
    ("The Navajo Code Talkers: how the code was built", "1", "Forgotten Battles of WWII", 9, 8, "well documented; tell it with community-approved sources", "National WWII Museum; Navajo Nation", "handdrawn + maps"),
    ("The Battle of Los Angeles (1942): the air raid that wasn't", "10", "Unsolved Files", 8, 7, "wartime nerves, no enemy aircraft confirmed", "Army records; newspapers", "archival + motion"),
    ("Operation Paperclip: the scientists America brought home", "2", "Cold War Files", 8, 8, "moral complexity; declassified files", "National Archives", "archival + motion"),
    ("The Berlin Airlift: feeding a city from the air", "1", "Decisions That Changed America", 9, 7, "logistics triumph; many viewers' parents remember", "Air Force history", "maps + motion"),
    ("Sears Catalog Homes: houses delivered by train", "4", "America's Forgotten Towns", 8, 7, "nostalgia + DIY curiosity", "Smithsonian; NPS", "whiteboard + archival"),
    ("The Liberty Ships: building a freighter in days", "5", "The Men Behind the Machines", 8, 8, "home-front production record", "Maritime Administration; NPS", "whiteboard + motion"),
    ("The Pan Am story: rise and fall of America's airline", "3", "America's Lost Industrial Giants", 9, 8, "glamour era of flying", "corporate archives; museum", "motion + archival"),
    ("Tucker 48: the car and the trial", "7", "Hidden Chapters of American Business", 8, 8, "innovation vs. fraud trial; court record", "court records; museum", "motion + archival"),
    ("Project Mogul and the Roswell balloon files", "2", "Cold War Files", 8, 7, "separates record from legend; Air Force reports", "Air Force reports (1994-97)", "archival + whiteboard"),
    ("The 1977 New York blackout", "9", "Decisions That Changed America", 7, 7, "infrastructure failure with documented reports", "federal reports", "motion + maps"),
    ("The women 'computers' of NACA", "12", "The Men and Women Behind the Machines", 8, 8, "overlooked people; NASA history", "NASA history office", "handdrawn + whiteboard"),
]
PRIMARY = ("NASA", "Maritime", "National Archives", "federal", "FBI", "NPS", "Library", "CIA", "court", "SEC", "Museum", "Smithsonian", "FHWA", "NIST", "Air Force", "Army", "Senate", "PL ")

cands = []
for title, pil, series, aud, story, angle, sources, style in IDEAS:
    d, gap, ever = PILLAR_SCORES[pil]
    E = P[pil]
    sensitive = pil == "11"
    cands.append({
        "title": title, "niche": f"pillar {pil}", "series": series, "angle": angle, "sources": [sources],
        "visual_style": style, "runtime": "15-20 min",
        "audience_fit": "1940-1990 U.S. subject; YouTube reach and TV viewing among ages 50-64 / 65+ (e001, e003)",
        "competition": NOTES[pil], "shorts": ["surprising fact", "unanswered question", "overlooked person"],
        "factors": {
            "audience_fit_us50": {"score": aud, "evidence": AUD, "evidence_scope": "pillar", "assessed_by": "agent",
                                  "rationale": "platform reach is evidenced; topic-level age fit is an editorial judgement (no public per-video age data)"},
            "revenue_evidence": {"score": 3 if sensitive else 5, "category": "ad-demand-proxy", "evidence": E["adv"], "evidence_scope": "pillar",
                                 "rationale": "non-graphic educational long-form history is advertiser-eligible; no niche RPM claimed"},
            "demand": {"score": d, "evidence": E["demand"], "evidence_scope": "pillar", "rationale": NOTES[pil]},
            "competition_gap": {"score": gap, "evidence": E["comp"], "evidence_scope": "pillar"},
            "evergreen": {"score": ever, "evidence": E["demand"][-1:], "evidence_scope": "pillar"},
            "storytelling": {"score": story, "assessed_by": "agent", "rationale": angle},
            "feasibility": {"score": 8 if any(k in sources for k in PRIMARY) else 6, "assessed_by": "agent",
                            "rationale": "primary or public sources available: " + sources},
        }})

if __name__ == "__main__":
    (HERE / "candidates.json").write_text(json.dumps({"generated": "2026-10-14", "candidates": cands}, indent=1,
                                                     ensure_ascii=False), encoding="utf-8")
    print(len(cands), "candidates")

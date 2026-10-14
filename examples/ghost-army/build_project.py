"""Builds examples/ghost-army/project.json — V3 documentary demo.

"The Ghost Army: The Artists Who Fooled Hitler's Generals"? No — titles must not
overclaim. Working title: "The Ghost Army: America's Secret Unit of Artists and Illusions".
Every factual sentence cites claim ids from research/dossier.json (sources: PL 117-85,
National WWII Museum, army.mil, Library of Congress, Speaker press release, AP/CBS, U.S. Mint,
Luxembourg government, Fox Official History via the Ghost Army Legacy Project).
Contested figures are framed as contested; the bicycle story is labelled oral history.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
GEO = "assets/ne_110m_admin_0_countries.geojson"
GEO_ASSET = {"path": GEO, "license": "Public domain (Natural Earth)", "source": "naturalearthdata.com via nvkelso/natural-earth-vector v5.1.2"}

LOC = {"camp_forrest": (-86.21, 35.36), "pine_camp": (-75.75, 44.05), "omaha": (-0.87, 49.37), "brest": (-4.49, 48.39),
       "bettembourg": (6.10, 49.52), "lux_city": (6.13, 49.61), "bastogne": (5.72, 50.00), "bouzonville": (6.53, 49.29),
       "viersen": (6.39, 51.26), "rheinberg": (6.60, 51.55), "florence": (11.25, 43.77), "st_lo": (-1.09, 49.12)}


def T(text, pos, style="h2", at=0.0, **kw):
    return {"type": "text", "text": text, "pos": pos, "style": style, "at": at, **kw}


def I(name, pos, size=0.08, at=0.0, **kw):
    return {"type": "icon", "name": name, "pos": pos, "size": size, "at": at, **kw}


def M(key, label, at, **kw):
    lon, lat = LOC[key]
    return {"lon": lon, "lat": lat, "label": label, "at": at, **kw}


def MAP(bounds, at=0.2, highlight=None, markers=None, routes=None, labels=None, box=(0.04, 0.12, 0.92, 0.8)):
    return {"type": "map", "geojson": GEO, "bounds": bounds, "box": list(box), "at": at, "dur": 1.2,
            "highlight": highlight or [], "markers": markers or [], "routes": routes or [], "labels": labels or []}


# Natural Earth 1:110m is coarse: keep regional frames (≥ ~12° wide) so borders stay legible;
# the markers carry the local precision.
EUROPE = [-6.0, 42.5, 16.0, 55.0]
NW_EUROPE = [-6.5, 45.5, 11.0, 54.5]
LUX = [-1.0, 46.5, 13.0, 54.0]
RHINE = [-1.0, 47.0, 14.0, 55.0]
ITALY = [4.0, 39.0, 18.5, 48.5]
USA = [-92.0, 33.0, -70.0, 46.0]

chapters = [
    {"id": "open", "title": "Rubber tanks on the Rhine", "mood": "tension"},
    {"id": "artists", "title": "An army of artists", "mood": "wonder"},
    {"id": "toolkit", "title": "Sight, sound, radio and theater", "mood": "drive"},
    {"id": "normandy", "title": "Normandy to Brittany", "mood": "tension"},
    {"id": "lux", "title": "Luxembourg and the Bulge", "mood": "dark"},
    {"id": "viersen", "title": "The last show", "mood": "tension"},
    {"id": "silence", "title": "Fifty years of silence", "mood": "dark"},
    {"id": "myth", "title": "Myth versus record", "mood": "drive"},
    {"id": "medal", "title": "A gold medal at last", "mood": "resolve"},
]

S = []


def sc(id, ch, engine, purpose, narration, visual, elements=None, claims=(), **kw):
    s = {"id": id, "chapter": ch, "engine": engine, "purpose": purpose, "narration": narration, "visual": visual,
         "elements": elements or [], "claims": list(claims), "illustrative": True, "pad": {"lead": 0.5, "tail": 0.8}}
    s.update(kw)
    S.append(s)


# ---------------------------------------------------------------- opening
sc("g01", "open", "artistic", "hook",
   "March, nineteen forty-five. On the west bank of the Rhine River, American forces were preparing one of the great river "
   "crossings of the Second World War. On the other side, German commanders were watching and listening for any sign of where "
   "the blow would fall. This is not the story of a famous battle. It is the story of how, for most of a year, a small "
   "American unit made the enemy see and hear things that were not there.",
   "Night river, distant lights, slow push.",
   [T("March 1945 · The Rhine", [0.5, 0.18], "h2", 0.5, font="serif_bold", color="light")],
   claims=["C31"], params={"layers": ["hills", "city"], "sky": ["night", "night2"], "fog": True},
   camera={"move": "push_in", "amount": 0.07}, transition="fade_black", emotion="suspense")
sc("g02", "open", "motion", "hook",
   "Not far from the front, they could see it: the trucks, the tanks and the artillery of two American infantry divisions moving "
   "into position. They could hear engines at night. They could pick up the radio traffic.",
   "Map of the Rhine near Viersen; two division symbols appear.",
   [MAP(RHINE, highlight=[{"name": "Germany", "color": "muted"}],
        markers=[M("viersen", "Viersen", "cue:two")],
        labels=[{"lon": 6.2, "lat": 51.9, "text": "RHINE", "at": 0.6}])],
   claims=["C31"], assets=[GEO_ASSET])
sc("g03", "open", "kinetic", "reveal",
   "But those divisions were not there. The tanks were made of rubber. The engine noise was recorded. And the radio operators "
   "were impersonating units that were somewhere else entirely.",
   "Kinetic reveal.", claims=["C31", "C13", "C10", "C15"],
   params={"emphasis": ["not", "rubber.", "recorded.", "impersonating"]}, transition="flash_cut")
sc("g04", "open", "motion", "explain",
   "This is the story of the Ghost Army: about eleven hundred American soldiers, many of them artists, whose job was to deceive the "
   "enemy on the battlefields of Europe. Their work stayed classified for decades. In this documentary we'll follow them from "
   "Tennessee to the Rhine, separate the record from the legend, and look honestly at what we still don't know.",
   "Title card with unit count and roadmap.",
   [T("THE GHOST ARMY", [0.5, 0.3], "hero", 0.3, font="serif_bold", color="light"),
    T("23rd Headquarters Special Troops · 3133rd Signal Service Company", [0.5, 0.45], "body", 1.2, color="muted"),
    {"type": "counter", "from": 0, "to": 1100, "prefix": "≈ ", "pos": [0.5, 0.66], "at": "cue:eleven", "dur": 1.6,
     "style": "h1", "label": "soldiers", "color": "accent"}],
   claims=["C1", "C5", "C37"])

# ---------------------------------------------------------------- an army of artists
sc("g05", "artists", "handdrawn", "story",
   "The idea came from Ralph Ingersoll, an American officer who had worked with the British on deception planning for Operation "
   "Fortitude, the effort to mislead Germany about the D-Day landings. Ingersoll proposed something the U.S. Army did not yet have: "
   "a unit devoted entirely to deception.",
   "Sketch of an officer at a planning table with a map.",
   [{"type": "character", "pos": [0.24, 0.9], "height": 0.5, "pose": "point", "at": 0.3, "talk": True, "color": "cool"},
    {"type": "card", "box": [0.5, 0.22, 0.4, 0.34], "tag": "Proposal", "title": "A U.S. unit for deception",
     "body": "Ralph Ingersoll, after work on Operation Fortitude planning", "at": "cue:proposed", "tone": "light"},
    T("Ralph Ingersoll", [0.24, 0.12], "h3", 0.6)],
   claims=["C4"], characters=["ingersoll"], transition="fade_black")
sc("g06", "artists", "motion", "timeline",
   "On January twentieth, nineteen forty-four, the 23rd Headquarters Special Troops was activated at Camp Forrest, Tennessee, under "
   "Colonel Harry Reeder, who would command it for the rest of the war. From there, its men would train, ship out, and eventually "
   "cross the Atlantic to England and the battlefields of France.",
   "U.S. map with Camp Forrest marker and activation date.",
   [MAP(USA, highlight=[{"name": "United States of America", "color": "light"}],
        markers=[M("camp_forrest", "Camp Forrest, Tennessee", "cue:camp")], box=(0.04, 0.2, 0.55, 0.72)),
    T("January 20, 1944", [0.78, 0.32], "h2", "cue:january", color="accent"),
    T("Activated: 23rd HQ Special Troops", [0.78, 0.44], "body", "cue:activated"),
    T("Commander: Col. Harry L. Reeder", [0.78, 0.54], "body", "cue:colonel")],
   claims=["C2", "C3"], assets=[GEO_ASSET])
sc("g07", "artists", "motion", "data",
   "Its authorized strength was eighty-two officers and one thousand twenty-three enlisted men. About eleven hundred people, whose "
   "job was to look and sound like forces many times their size.",
   "Two counters and a crowd grid.",
   [{"type": "counter", "from": 0, "to": 82, "pos": [0.3, 0.3], "at": "cue:eighty-two", "dur": 1.2, "style": "h1", "label": "officers"},
    {"type": "counter", "from": 0, "to": 1023, "pos": [0.7, 0.3], "at": "cue:thousand", "dur": 1.6, "style": "h1", "label": "enlisted men"},
    {"type": "crowd", "box": [0.15, 0.52, 0.7, 0.36], "count": 44, "cols": 22, "at": "cue:eleven", "color": "cool"}],
   claims=["C5"])
sc("g08", "artists", "whiteboard", "process",
   "The 23rd was built from specialized parts. A camouflage battalion handled visual deception. A special signal company handled "
   "radio. A sonic company, the 3132nd, handled sound. And an engineer combat company guarded the perimeter and helped stage the illusions.",
   "Whiteboard org chart of four components.",
   [T("23rd Headquarters Special Troops", [0.5, 0.12], "h2", 0.2, underline=True),
    I("star", [0.14, 0.45], 0.07, "cue:camouflage", label="603rd Camouflage · visual"),
    I("server", [0.38, 0.45], 0.07, "cue:radio.", label="Signal Co. Special · radio"),
    I("cloud", [0.62, 0.45], 0.07, "cue:sound.", label="3132nd · sound"),
    I("truck", [0.86, 0.45], 0.07, "cue:engineer", label="406th Engineers · security"),
    T("small force → looks like a big one", [0.5, 0.82], "h3", "cue:illusions.", color="accent")],
   claims=["C6"], transition="crossfade")
sc("g09", "artists", "huashu_clip", "data",
   "The camouflage battalion, the 603rd Engineers, was the largest piece, with roughly three hundred eighty men. The radio company had "
   "about three hundred, the engineers about one hundred seventy, and the sound company about one hundred forty-five.",
   "Editorial bar chart of approximate component strengths.",
   params={"grammar": "t3_finance_chart", "theme": "paper",
           "data": {"title": "Approximate strength of the 23rd's components", "unit": "men (approximate)",
                    "source": "Source: National WWII Museum; Ghost Army Legacy Project (Fox history)", "chart": "bar", "decimals": 0,
                    "series": [{"label": "603rd camouflage", "value": 379}, {"label": "Signal Co. Special", "value": 296},
                               {"label": "406th engineers", "value": 168}, {"label": "3132nd sonic", "value": 145}],
                    "highlight": {"index": 0, "text": "≈ 380", "sub": "largest unit"}},
           "cues": [{"at": "cue:three", "kind": "bar", "data": {"index": 0}}, {"at": "cue:radio", "kind": "bar", "data": {"index": 1}},
                    {"at": "cue:engineers", "kind": "bar", "data": {"index": 2}}, {"at": "cue:sound", "kind": "bar", "data": {"index": 3}},
                    {"at": "end-1.5", "kind": "highlight"}]},
   claims=["C7"], camera={"move": "drift"})
sc("g10", "artists", "handdrawn", "character",
   "And here is the unusual part. Many of these soldiers, especially in the 603rd, came from art schools, advertising agencies and "
   "other creative or technical fields. The Army needed people who understood how the eye could be fooled.",
   "Sketched crowd of artists with brushes and drafting tools.",
   [{"type": "crowd", "box": [0.06, 0.25, 0.4, 0.5], "count": 12, "at": 0.3, "color": "accent"},
    I("lightbulb", [0.62, 0.4], 0.08, "cue:art", label="art schools"),
    I("document", [0.82, 0.4], 0.07, "cue:advertising", label="ad agencies"),
    T("How do you fool the eye?", [0.72, 0.75], "h3", "cue:eye", color="negative")],
   claims=["C18"], params={"fill": "hatch"})
sc("g11", "artists", "handdrawn", "character",
   "Some of their names became famous after the war. The painter Ellsworth Kelly served in the 603rd. So did fashion designer Bill Blass, "
   "wildlife artist Arthur Singer, and photographer Art Kane. Arthur Singer's wartime watercolors still survive.",
   "Four name cards pinned to a board.",
   [{"type": "card", "box": [0.05, 0.22, 0.21, 0.28], "title": "Ellsworth Kelly", "body": "painter", "at": "cue:ellsworth", "tone": "light"},
    {"type": "card", "box": [0.28, 0.22, 0.21, 0.28], "title": "Bill Blass", "body": "fashion designer", "at": "cue:blass,", "tone": "light"},
    {"type": "card", "box": [0.51, 0.22, 0.21, 0.28], "title": "Arthur Singer", "body": "wildlife artist", "at": "cue:arthur", "tone": "light"},
    {"type": "card", "box": [0.74, 0.22, 0.21, 0.28], "title": "Art Kane", "body": "photographer", "at": "cue:kane.", "tone": "light"},
    T("All served in the 603rd Engineer Camouflage Battalion", [0.5, 0.68], "body", "cue:watercolors")],
   claims=["C41", "C42", "C43", "C44"])

# ---------------------------------------------------------------- toolkit
sc("g12", "toolkit", "whiteboard", "explain",
   "So far we have an unusual unit of about eleven hundred men, many of them artists. Now, how did they actually fool an enemy army? "
   "The Ghost Army worked with four tools: things you could see, things you could hear, radio traffic, and a kind of theater. "
   "Used together, they could make a small force look and sound like a large one.",
   "Four tools drawn as icons.",
   [T("Four tools of deception", [0.5, 0.12], "h1", 0.2, underline=True),
    I("magnifier", [0.16, 0.48], 0.08, "cue:see,", label="sight"),
    I("cloud", [0.39, 0.48], 0.08, "cue:hear,", label="sound"),
    I("server", [0.62, 0.48], 0.08, "cue:radio", label="radio"),
    I("star", [0.85, 0.48], 0.08, "cue:theater.", label="theater")],
   claims=["C13", "C10", "C15", "C16", "C53"], transition="fade_black")
sc("g13", "toolkit", "image_whiteboard", "illustration",
   "Visual deception relied on inflatable rubber decoys: tanks, artillery, trucks and even aircraft. Some were manufactured by U.S. "
   "Rubber and Goodyear. From the air, or from a distance, a field of them could look like an armored force.",
   "An inflatable tank illustration is drawn stroke by stroke.",
   [T("inflatable decoys", [0.82, 0.16], "h2", "cue:inflatable", font="hand_bold", color="accent")],
   claims=["C13", "C14"], params={"src": "assets/decoy-tank.png", "order": "strokes", "draw_time": 10.0, "box": [0.03, 0.12, 0.66, 0.8]},
   assets=[{"path": "assets/decoy-tank.png", "license": "Original (generated by make_assets.py)", "source": "procedural illustration"}])
sc("g14", "toolkit", "archival", "recreation",
   "There's a well-known story, told by veterans, that two French civilians on bicycles once slipped past the perimeter and saw four "
   "American soldiers lifting what looked like a forty-ton Sherman tank. It comes from veterans' recollections, and one of them later "
   "painted the scene. We'll treat it as oral history, not documented fact.",
   "Archival-style recreation: four soldiers lift a tank shape; two bicycles; label ORAL HISTORY.",
   [{"type": "character", "pos": [0.18, 0.88], "height": 0.34, "pose": "shock", "at": "cue:bicycles", "color": "muted"},
    {"type": "character", "pos": [0.27, 0.88], "height": 0.34, "pose": "shock", "at": "cue:bicycles", "color": "muted"},
    {"type": "shape", "kind": "rect", "box": [0.48, 0.42, 0.34, 0.2], "fill": "muted", "at": "cue:lifting", "radius": 0.03},
    {"type": "character", "pos": [0.5, 0.88], "height": 0.32, "pose": "celebrate", "at": "cue:four"},
    {"type": "character", "pos": [0.6, 0.88], "height": 0.32, "pose": "celebrate", "at": "cue:four"},
    {"type": "character", "pos": [0.7, 0.88], "height": 0.32, "pose": "celebrate", "at": "cue:four"},
    {"type": "character", "pos": [0.8, 0.88], "height": 0.32, "pose": "celebrate", "at": "cue:four"},
    {"type": "stamp", "text": "Oral history", "pos": [0.5, 0.2], "at": "cue:oral", "color": "ink", "angle": -6, "scale": 0.06}],
   claims=["C45"], params={"label_text": "ILLUSTRATIVE RECREATION · ORAL HISTORY"})
sc("g15", "toolkit", "whiteboard", "explain",
   "Sound was the second tool. The sonic companies trained at the Army Experimental Station at Pine Camp, New York, today's Fort Drum. "
   "Their equipment was developed with Bell Labs. Recorded soundtracks were played from wire recorders through powerful speakers "
   "mounted on vehicles. Congress later described the two sonic companies as the only American sonic deception ground units of the war.",
   "Speaker vehicle with sound waves; Bell Labs + wire recorder labels.",
   [I("truck", [0.3, 0.55], 0.12, 0.3, label="speaker vehicle"),
    {"type": "arrow", "from": [0.42, 0.5], "to": [0.62, 0.42], "at": "cue:speakers", "curve": 0.1, "label": "recorded sound"},
    {"type": "arrow", "from": [0.42, 0.56], "to": [0.62, 0.56], "at": "cue:speakers", "curve": 0.0},
    {"type": "list", "box": [0.62, 0.28, 0.36, 0.4], "at": "cue:pine", "dur": 6.0, "marker": "dot",
     "items": ["Pine Camp, N.Y. (Fort Drum)", "Developed with Bell Labs", "Wire recorders", "Vehicle-mounted speakers"]}],
   claims=["C8", "C10", "C9"], transition="crossfade")
sc("g16", "toolkit", "motion", "evidence",
   "One museum account says the sound could carry up to about fifteen miles. That is an account, not a measured test, so treat it as "
   "an estimate. To aim the sound, the team even used a mobile weather station mounted on a jeep.",
   "Expanding sound rings labelled 'up to ~15 miles (estimate)'.",
   [{"type": "shape", "kind": "circle", "box": [0.35, 0.2, 0.3, 0.53], "color": "accent", "at": "cue:fifteen", "dur": 1.2},
    {"type": "shape", "kind": "circle", "box": [0.27, 0.06, 0.46, 0.82], "color": "muted", "at": "cue:miles", "dur": 1.2},
    I("truck", [0.5, 0.47], 0.05, 0.2),
    T("up to ~15 miles (one source; estimate)", [0.5, 0.92], "body", "cue:estimate.", color="accent"),
    I("cloud", [0.86, 0.3], 0.05, "cue:weather", label="jeep weather station")],
   claims=["C11", "C12"])
sc("g17", "toolkit", "motion", "explain",
   "The third tool was radio. Spoof radio operators created phony networks and imitated the operators of real units. Some could copy an "
   "individual operator's Morse code style, known as his fist, so listeners would believe a familiar unit was still on the air.",
   "Network of fake radio stations.",
   [T("Spoof radio", [0.5, 0.1], "h2", 0.2),
    {"type": "network", "at": "cue:phony", "dur": 3.0,
     "nodes": [{"id": "a", "label": "real unit (gone)", "pos": [0.2, 0.3], "color": "muted"},
               {"id": "b", "label": "spoof operator", "pos": [0.5, 0.55], "icon": "server", "size": 0.06, "color": "accent"},
               {"id": "c", "label": "phony net", "pos": [0.8, 0.3]}, {"id": "d", "label": "phony net", "pos": [0.8, 0.78]},
               {"id": "e", "label": "enemy listener", "pos": [0.2, 0.78], "color": "negative"}],
     "edges": [["b", "c"], ["b", "d"], ["b", "e"], ["a", "b"]]},
    T("copying an operator's 'fist'", [0.5, 0.94], "body", "cue:fist,", color="accent")],
   claims=["C15"])
sc("g18", "toolkit", "handdrawn", "explain",
   "The fourth tool was theater, which the unit called special effects: counterfeit shoulder patches, false vehicle markings, phony "
   "headquarters, and even officers posing as generals, all meant to feed false information to enemy agents who might be watching.",
   "Sketched patches, painted truck markings, an officer with fake stars.",
   [I("star", [0.18, 0.45], 0.07, "cue:patches,", label="fake patches"),
    I("truck", [0.4, 0.45], 0.07, "cue:markings,", label="false markings"),
    I("building", [0.62, 0.45], 0.07, "cue:headquarters,", label="phony HQ"),
    {"type": "character", "pos": [0.84, 0.86], "height": 0.42, "pose": "stand", "at": "cue:generals,", "color": "accent"},
    T("feed false information", [0.4, 0.82], "h3", "cue:false", color="negative")],
   claims=["C16"])
sc("g19", "toolkit", "whiteboard", "process",
   "And the 406th Engineer Combat Company did the heavy work. Its men guarded the perimeter, used bulldozers to create fake tank tracks "
   "and gun positions, and sometimes played the part of military police.",
   "Bulldozed fake tank tracks drawn across a field.",
   [{"type": "shape", "kind": "line", "from": [0.1, 0.7], "to": [0.9, 0.4], "at": "cue:bulldozers", "color": "ink", "weight": 0.012},
    {"type": "shape", "kind": "line", "from": [0.1, 0.76], "to": [0.9, 0.46], "at": "cue:tracks", "color": "ink", "weight": 0.012},
    I("box", [0.2, 0.35], 0.06, "cue:guarded", label="perimeter"),
    I("warning", [0.75, 0.78], 0.05, "cue:police.", label="'MPs'")],
   claims=["C17"])

# ---------------------------------------------------------------- Normandy to Brittany
sc("g20", "normandy", "motion", "story",
   "We've seen the tools. Now let's follow the unit across Europe, starting on the beaches of Normandy. The Ghost Army's war began there. Four of its members landed on D-Day itself, and two became casualties while building false "
   "beach landing sites. Seymour Nussenbaum, who had studied art at the Pratt Institute, landed on Omaha Beach about two weeks later.",
   "Map of Normandy with Omaha Beach marker.",
   [MAP(NW_EUROPE, highlight=[{"name": "France", "color": "light"}],
        markers=[M("omaha", "Omaha Beach", "cue:d-day")], labels=[{"lon": -2.5, "lat": 50.3, "text": "ENGLISH CHANNEL", "at": 0.6}])],
   claims=["C19", "C56"], assets=[GEO_ASSET], transition="fade_black")
sc("g21", "normandy", "archival", "recreation",
   "On June fourteenth, nineteen forty-four, a sixteen-man detachment called Task Force Mason set up dummy artillery to draw enemy fire "
   "away from a real American artillery battalion. It was the unit's first battlefield deception in France.",
   "Archival-style sketch of dummy guns in a field.",
   [I("flame", [0.3, 0.45], 0.08, "cue:fire", label="draws fire"),
    I("box", [0.55, 0.5], 0.07, "cue:dummy", label="dummy artillery"),
    T("June 14, 1944 · Task Force Mason", [0.5, 0.14], "h2", "cue:june", font="serif_bold")],
   claims=["C21"])
sc("g22", "normandy", "motion", "timeline",
   "Not every assignment was deception. Lieutenant Fred Fox's radio operators, whose planned operation had been cancelled, were attached "
   "to the Eighty-Second Airborne Division, which had lost ninety-five percent of its radio equipment. Then, in early July, Operation "
   "Elephant covered the Second Armored Division as it moved into the line. Congress later called it the first of twenty-one "
   "full-scale tactical deceptions.",
   "Timeline June–July 1944.",
   [{"type": "timeline", "box": [0.06, 0.32, 0.88, 0.36], "at": 0.3, "dur": 8.0, "horizontal": True,
     "events": [{"label": "June 6", "sub": "D-Day"}, {"label": "June 14", "sub": "Task Force Mason"},
                {"label": "June", "sub": "radio help to 82nd Airborne"}, {"label": "July 1–4", "sub": "Operation Elephant", "color": "negative"}]},
    {"type": "counter", "from": 0, "to": 95, "suffix": "%", "pos": [0.5, 0.82], "at": "cue:ninety-five", "dur": 1.0, "style": "h2",
     "label": "of the 82nd's radio equipment lost"}],
   claims=["C20", "C22"])
sc("g23", "normandy", "motion", "story",
   "In August, the unit moved to Brittany, supporting the Allied advance and the siege of the port city of Brest. According to one "
   "detailed nonprofit account, it was at Brest that the unit first combined visual, sonic and radio deception in a single operation.",
   "Map: route from Normandy to Brest.",
   [MAP(NW_EUROPE, highlight=[{"name": "France", "color": "light"}],
        markers=[M("omaha", "Normandy", 0.4), M("brest", "Brest", "cue:brest.")],
        routes=[{"path": [list(LOC["st_lo"]), [-2.0, 48.6], list(LOC["brest"])], "at": "cue:august", "dur": 3.0, "color": "accent"}])],
   claims=["C24", "C25"], assets=[GEO_ASSET])

# ---------------------------------------------------------------- Luxembourg and the Bulge
sc("g24", "lux", "motion", "story",
   "By the end of the summer of nineteen forty-four, the unit had worked in Normandy and in Brittany. Next came Luxembourg. "
   "In September came one of the boldest bluffs. Patton's Third Army had a thinly held stretch of line in Luxembourg. In Operation "
   "Bettembourg, about five hundred men impersonated the roughly eight thousand men of the Sixth Armored Division.",
   "Map of Luxembourg; Bettembourg marker; 500 vs 8,000.",
   [MAP(LUX, highlight=[{"name": "Luxembourg", "color": "accent"}], markers=[M("bettembourg", "Bettembourg", "cue:bettembourg,")],
        box=(0.03, 0.1, 0.55, 0.82)),
    {"type": "counter", "from": 0, "to": 500, "pos": [0.78, 0.32], "at": "cue:five", "dur": 1.0, "style": "h1", "label": "real men"},
    {"type": "counter", "from": 0, "to": 8000, "pos": [0.78, 0.66], "at": "cue:eight", "dur": 1.4, "style": "h1",
     "label": "men of the division they impersonated", "color": "accent"}],
   claims=["C26"], assets=[GEO_ASSET], transition="fade_black")
sc("g25", "lux", "archival", "recreation",
   "For three months, from late September to just before Christmas nineteen forty-four, most of the unit was housed in a building in "
   "the Limpertsberg district of Luxembourg City. Luxembourg's government says more than a third of the unit's missions took place in "
   "Luxembourg.",
   "Archival-style sketch of a city building and calendar.",
   [I("building", [0.32, 0.5], 0.14, 0.3, label="Limpertsberg, Luxembourg City"),
    T("Sept 25 – Dec 22, 1944", [0.72, 0.36], "h2", "cue:three", font="serif_bold"),
    T("> 1/3 of missions in Luxembourg (per Luxembourg government)", [0.72, 0.6], "body", "cue:third", max_width=0.4)],
   claims=["C27"])
sc("g26", "lux", "motion", "story",
   "During the Battle of the Bulge, the 23rd broadcast fake radio traffic suggesting that parts of Patton's Third Army were moving "
   "toward the besieged town of Bastogne.",
   "Map: radio waves pointing toward Bastogne.",
   [MAP(LUX, highlight=[{"name": "Belgium", "color": "light"}], markers=[M("bastogne", "Bastogne (besieged)", "cue:bastogne.")],
        routes=[{"path": [list(LOC["lux_city"]), list(LOC["bastogne"])], "at": "cue:fake", "dur": 2.5, "color": "accent", "dashed": True}])],
   claims=["C28"], assets=[GEO_ASSET])

# ---------------------------------------------------------------- the last show
sc("g27", "viersen", "artistic", "atmosphere",
   "Deception was not safe work. In March nineteen forty-five, during Operation Bouzonville, the unit simulated the Eightieth Infantry "
   "Division. It became its costliest operation: two men killed and fifteen wounded. In all, three soldiers of the 23rd were killed "
   "in the war, and dozens were wounded.",
   "Dark sky, silhouettes, a single line of text.",
   [T("Operation Bouzonville · March 1945", [0.5, 0.22], "h3", 0.6, font="serif_bold", color="light"),
    T("2 killed · 15 wounded", [0.5, 0.36], "h2", "cue:costliest", font="serif_bold", color="light")],
   claims=["C29", "C30"], params={"layers": ["hills", "city"], "sky": ["night", "night2"]}, transition="fade_black", emotion="melancholy")
sc("g28", "viersen", "motion", "reveal",
   "Then came Viersen, the last and largest deception, from March eighteenth to twenty-fourth, nineteen forty-five. The Ghost Army "
   "impersonated two infantry divisions, the Thirtieth and the Seventy-Ninth, to draw German attention away from the Ninth Army's real "
   "crossing point on the Rhine.",
   "Map: decoy position at Viersen vs. the real crossing to the north.",
   [MAP(RHINE, highlight=[{"name": "Germany", "color": "light"}],
        markers=[M("viersen", "decoy: 30th & 79th Inf. Div. (simulated)", "cue:impersonated", color="accent"),
                 M("rheinberg", "real crossing (approx.)", "cue:real", color="negative")],
        labels=[{"lon": 6.75, "lat": 51.85, "text": "RHINE", "at": 0.5}])],
   claims=["C31"], assets=[GEO_ASSET], transition="crash_zoom")
sc("g29", "viersen", "motion", "evidence",
   "Museum accounts say the operation simulated more than thirty thousand troops with about six hundred inflatable dummies. The law "
   "Congress passed in twenty twenty-two says only hundreds of vehicles, so the exact scale depends on the source. Afterward, Ninth Army "
   "commander Lieutenant General William Simpson commended the unit.",
   "Contested figures shown side by side.",
   [{"type": "card", "box": [0.06, 0.22, 0.42, 0.4], "tag": "Museum accounts", "title": "> 30,000 troops simulated",
     "body": "≈ 600 inflatable dummies", "at": "cue:museum", "tone": "night2"},
    {"type": "card", "box": [0.52, 0.22, 0.42, 0.4], "tag": "Public Law 117-85", "title": "\"hundreds\" of vehicles",
     "body": "no troop figure given", "at": "cue:law", "tone": "night2"},
    T("Commended by Lt. Gen. William H. Simpson, Ninth Army", [0.5, 0.8], "body", "cue:commended")],
   claims=["C32", "C33"])
sc("g30", "viersen", "handdrawn", "evidence",
   "Congress later quoted a postwar Army assessment praising how much influence such a small group had on a major operation.",
   "Sketched document with highlighted line.",
   [I("document", [0.5, 0.48], 0.16, 0.3, label="Postwar Army assessment (quoted in PL 117-85)")],
   claims=["C34"], min_duration=6.5)
sc("g31", "viersen", "motion", "story",
   "Meanwhile, in Italy, the 3133rd Signal Service Company carried out its own deceptions. In April nineteen forty-five, in Operation "
   "Craftsman, it supported an offensive against the German Gothic Line north of Florence, working alongside British deception units. "
   "About two hundred soldiers served in the 3133rd. They spent nineteen days in combat and lost almost seventy percent of their "
   "thirty-five dummy tanks to German fire.",
   "Map of Italy with Florence marker; counters.",
   [MAP(ITALY, highlight=[{"name": "Italy", "color": "light"}], markers=[M("florence", "Florence · Gothic Line to the north", "cue:florence,")],
        box=(0.03, 0.1, 0.55, 0.82)),
    {"type": "counter", "from": 0, "to": 19, "suffix": " days", "pos": [0.78, 0.3], "at": "cue:nineteen", "dur": 1.0, "style": "h2", "label": "in combat"},
    {"type": "counter", "from": 0, "to": 70, "prefix": "≈ ", "suffix": "%", "pos": [0.78, 0.62], "at": "cue:seventy", "dur": 1.0, "style": "h2",
     "label": "of 35 dummy tanks lost", "color": "negative"}],
   claims=["C35", "C36"], assets=[GEO_ASSET], transition="fade_black")

# ---------------------------------------------------------------- silence
sc("g32", "silence", "archival", "evidence",
   "The war in Europe ended in May nineteen forty-five. For the Ghost Army, a different kind of silence was about to begin. "
   "In September nineteen forty-five, Captain Fred Fox wrote the unit's official history. It is held today at the National Archives in "
   "College Park, Maryland.",
   "Typewritten report on a desk.",
   [I("document", [0.38, 0.5], 0.16, 0.3, label="Official History, Sept. 1945"),
    T("National Archives · Record Group 407", [0.72, 0.5], "h3", "cue:archives", font="serif_bold")],
   claims=["C38"], transition="fade_black")
sc("g33", "silence", "artistic", "atmosphere",
   "Then the story went quiet. The records were classified. A few newspaper articles appeared in August nineteen forty-five, and after "
   "that, very little, until a Smithsonian magazine article in April nineteen eighty-five.",
   "Night city; lights go out one by one.",
   [T("Classified", [0.5, 0.3], "h1", "cue:classified.", font="serif_bold", color="light")],
   claims=["C37"], params={"layers": ["towers", "city"], "sky": ["night", "night2"], "lights_out_at": "cue:classified."})
sc("g34", "silence", "motion", "evidence",
   "When were the records declassified? Most sources say nineteen ninety-six. An Army article says nineteen ninety-three. Others simply "
   "say the mid-nineteen-nineties. The sources disagree, and we could not locate the original declassification order.",
   "Timeline with two conflicting dates.",
   [{"type": "timeline", "box": [0.08, 0.34, 0.84, 0.34], "at": 0.3, "dur": 4.0, "horizontal": True,
     "events": [{"label": "1985", "sub": "Smithsonian article"}, {"label": "1993?", "sub": "army.mil", "color": "accent"},
                {"label": "1996?", "sub": "most sources", "color": "accent"}]},
    T("Sources disagree", [0.5, 0.84], "h2", "cue:disagree,", color="negative")],
   claims=["C39"])
sc("g35", "silence", "handdrawn", "story",
   "Many veterans stayed quiet for decades. The Associated Press reported that the son of one officer, Captain Oscar Seale, learned "
   "only after his father's death in two thousand one that he had served in the Ghost Army. Some of their voices survive: the Library of "
   "Congress Veterans History Project holds an interview with veteran Elmer Mellebrand about the decoys and the sound deception.",
   "Sketched family scene; a tape recorder icon for the oral history.",
   [{"type": "character", "pos": [0.22, 0.9], "height": 0.48, "pose": "think", "at": 0.3, "color": "muted"},
    I("document", [0.5, 0.4], 0.07, "cue:learned", label="a family discovers"),
    I("phone", [0.78, 0.4], 0.07, "cue:library", label="Veterans History Project")],
   claims=["C40", "C57"])
sc("g36", "silence", "whiteboard", "explain",
   "There was one more chapter. After Germany surrendered, the 23rd helped run camps for displaced persons. The unit's history cites up "
   "to about one hundred thousand people in thirteen camps.",
   "Whiteboard: 13 camps, ~100,000 people.",
   [{"type": "crowd", "box": [0.08, 0.25, 0.5, 0.55], "count": 39, "cols": 13, "at": "cue:camps", "color": "cool"},
    T("13 camps", [0.78, 0.4], "h1", "cue:thirteen", color="accent"),
    T("up to ~100,000 people", [0.78, 0.58], "h3", "cue:hundred")],
   claims=["C55"], transition="erase")

# ---------------------------------------------------------------- myth vs record
sc("g37", "myth", "motion", "comparison",
   "Because it stayed secret for so long, the Ghost Army's story has picked up some confusion. It's often mixed up with the fictional "
   "First U.S. Army Group created for Operation Fortitude before D-Day. They were different efforts. The Ghost Army's deceptions were "
   "tactical, staged near the front lines in France, Luxembourg and Germany.",
   "Two cards: FUSAG (strategic, before D-Day) vs 23rd (tactical, at the front).",
   [{"type": "card", "box": [0.06, 0.24, 0.42, 0.44], "tag": "Operation Fortitude", "title": "FUSAG (fictional army group)",
     "body": "strategic deception before D-Day", "at": "cue:fortitude", "tone": "night2"},
    {"type": "card", "box": [0.52, 0.24, 0.42, 0.44], "tag": "23rd HQ Special Troops", "title": "The Ghost Army",
     "body": "tactical deceptions near the front, 1944–45", "at": "cue:tactical,", "tone": "night2"},
    T("Different efforts", [0.5, 0.84], "h2", "cue:different", color="accent")],
   claims=["C54"], transition="fade_black")
sc("g38", "myth", "huashu_clip", "evidence",
   "Even the number of operations depends on who is counting. Different sources say about twenty, twenty-one, or twenty-two, depending "
   "on how rehearsals and cancelled missions are treated.",
   "Bar chart: operation counts by source.",
   params={"grammar": "t3_finance_chart", "theme": "paper",
           "data": {"title": "How many deception operations?", "unit": "count, by source", "chart": "bar", "decimals": 0,
                    "source": "AP; Public Law 117-85; National WWII Museum / Luxembourg government",
                    "series": [{"label": "AP", "value": 20}, {"label": "PL 117-85", "value": 21}, {"label": "Museum / Luxembourg", "value": 22}],
                    "highlight": {"index": 1, "text": "20–22", "sub": "depends on counting"}},
           "cues": [{"at": "cue:twenty,", "kind": "bar", "data": {"index": 0}}, {"at": "cue:twenty-one,", "kind": "bar", "data": {"index": 1}},
                    {"at": "cue:twenty-two,", "kind": "bar", "data": {"index": 2}}, {"at": "end-1.6", "kind": "highlight"}]},
   claims=["C23"])
sc("g39", "myth", "motion", "evidence",
   "And then there's the most quoted number: that the Ghost Army saved fifteen thousand to thirty thousand American lives. It's repeated "
   "often, including at the medal ceremony, but we could not find a primary study behind it. The honest answer is that we don't know how "
   "that estimate was calculated.",
   "A large number with a 'source unknown' marker.",
   [{"type": "counter", "from": 0, "to": 30000, "prefix": "15,000 – ", "pos": [0.5, 0.36], "at": "cue:fifteen", "dur": 1.6, "style": "hero"},
    T("estimate · no primary study found", [0.5, 0.58], "h3", "cue:study", color="negative"),
    T("lives saved (as quoted)", [0.5, 0.2], "body", "cue:saved", color="muted")],
   claims=["C52"])

# ---------------------------------------------------------------- medal
sc("g40", "medal", "motion", "timeline",
   "Recognition took a long time. Bills to award the Ghost Army a Congressional Gold Medal were introduced in Congress starting in twenty "
   "fifteen. The act became law on February first, twenty twenty-two. On March twenty-first, twenty twenty-four, the medal was presented "
   "in Emancipation Hall at the U.S. Capitol.",
   "Timeline 2015 → 2022 → 2024.",
   [{"type": "timeline", "box": [0.08, 0.34, 0.84, 0.34], "at": 0.3, "dur": 9.0, "horizontal": True,
     "events": [{"label": "2015", "sub": "first bill (H.R. 2170)"}, {"label": "Feb 1, 2022", "sub": "Public Law 117-85", "color": "positive"},
                {"label": "Mar 21, 2024", "sub": "medal presented", "color": "accent"}]}],
   claims=["C46", "C47", "C49"], transition="fade_black")
sc("g41", "medal", "handdrawn", "character",
   "Three of the seven then-known surviving veterans attended: Bernard Bluestein, John Christman and Seymour Nussenbaum. They were "
   "ninety-nine and one hundred years old.",
   "Three sketched veterans at the ceremony.",
   [{"type": "character", "pos": [0.28, 0.9], "height": 0.46, "pose": "stand", "at": "cue:bernard", "color": "cool"},
    {"type": "character", "pos": [0.5, 0.9], "height": 0.46, "pose": "stand", "at": "cue:john", "color": "cool"},
    {"type": "character", "pos": [0.72, 0.9], "height": 0.46, "pose": "stand", "at": "cue:seymour", "color": "cool"},
    T("Bluestein · Christman · Nussenbaum", [0.5, 0.14], "h3", "cue:attended:")],
   claims=["C50"])
sc("g42", "medal", "whiteboard", "explain",
   "The medal's design shows the four tools: a telegraph operator, a soldier applying a fake unit patch, a loudspeaker half-track, and "
   "soldiers carrying an inflatable tank. At the ceremony, the Secretary of the Army said many of the unit's techniques are still used today.",
   "Medal outline with four quadrants.",
   [{"type": "shape", "kind": "circle", "box": [0.32, 0.12, 0.36, 0.64], "color": "accent", "at": 0.2, "dur": 1.0},
    I("server", [0.42, 0.33], 0.05, "cue:telegraph"), I("star", [0.58, 0.33], 0.05, "cue:patch,"),
    I("truck", [0.42, 0.56], 0.05, "cue:loudspeaker"), I("box", [0.58, 0.56], 0.05, "cue:inflatable"),
    T("\"still used today\"", [0.5, 0.88], "h3", "cue:still", color="accent")],
   claims=["C53", "C51"])
sc("g43", "medal", "motion", "explain",
   "The law directs that the gold medal go to the Smithsonian Institution for display and research. The National World War Two Museum "
   "opened an exhibition about the unit in twenty twenty, and filmmaker Rick Beyer's twenty thirteen documentary, which aired on PBS, "
   "brought the story to a wide audience. In Luxembourg, there is a Ghost Army marker at Bettembourg, and a monument was unveiled in Limpertsberg "
   "in twenty twenty-three, where the unit had once been based.",
   "List of places the story lives on.",
   [{"type": "list", "box": [0.14, 0.22, 0.72, 0.6], "at": "cue:smithsonian", "dur": 12.0, "marker": "check", "scale": 1.2,
     "items": ["Medal: Smithsonian Institution", "Exhibition: National WWII Museum (2020)", "Documentary: Rick Beyer (2013, PBS)",
               "Monument: Limpertsberg, Luxembourg (2023)"]}],
   claims=["C48", "C60", "C58", "C59"])
sc("g44", "medal", "kinetic", "metaphor",
   "So what did the Ghost Army really accomplish? We know what they did, where, and at what cost. What we can't measure precisely is how "
   "many lives their illusions saved, and historians are still filling in parts of the record. Their story is also a reminder that "
   "creativity can be a form of service: painters, designers and sound engineers used their skills to protect other soldiers.",
   "Kinetic reflection with uncertainty stated.", params={"emphasis": ["accomplish?", "know", "can't", "still"]},
   claims=["C52", "C39"], transition="fade_black")
sc("g45", "medal", "kinetic", "cta",
   "If you have a family story connected to the 23rd Headquarters Special Troops, we would be glad to hear it in the comments. "
   "In our next documentary, we'll look at another group of Americans whose wartime work stayed secret for decades. Thanks for watching.",
   "End card.", params={"emphasis": ["secret", "decades."]}, claims=[], illustrative=False)

project = {
    "schema_version": 2, "slug": "ghost-army", "title": "The Ghost Army: America's Secret Unit of Artists and Illusions",
    "category": "history", "language": "en-US", "audience": "US 55+ (primary 55-64, secondary 65+)",
    "target_duration": 960, "tolerance": 0.10, "fps": 30, "theme": "history",
    "fictional": False, "badge": "ILLUSTRATIVE ANIMATION",
    "voice": {"mode": "edge-tts", "provider": "edge", "voice": "en-US-AndrewNeural", "edge_rate": "-10%", "allow_network": True,
              "languages": {"es": {"voice": "es-MX-JorgeNeural", "rate": "+4%"}}},
    "music": {"enabled": True, "volume": 0.12},
    "art_direction": {"style_id": "history-doc", "palette": "history",
                      "characters": {"ingersoll": "officer, blue uniform role 'cool'"},
                      "rules": ["dates and names on screen", "contested figures framed as contested",
                                "recreations labelled ILLUSTRATIVE RECREATION", "no graphic violence"]},
    "chapters": chapters, "scenes": S,
    "rights_issues": [{"item": "Natural Earth map data", "status": "resolved", "note": "public domain"}],
    "seo": {
        "title_options": ["The Ghost Army: America's Secret Unit of Artists and Illusions",
                          "Inflatable Tanks and Fake Radio: The True Story of the Ghost Army",
                          "The WWII Unit That Fought With Rubber Tanks (Full Documentary)"],
        "description": "In March 1945, German commanders watched two American divisions near the Rhine. They weren't there. This animated "
                       "documentary tells the documented story of the Ghost Army — the 23rd Headquarters Special Troops and the 3133rd "
                       "Signal Service Company — using Public Law 117-85, the National WWII Museum, Army and Library of Congress sources. "
                       "We separate the record from the legend: where the '15,000–30,000 lives saved' number comes from, why sources "
                       "disagree on the declassification date, and what remains unknown.",
        "sources_note": "Key sources: Public Law 117-85 (govinfo.gov); The National WWII Museum; army.mil; Library of Congress Veterans "
                        "History Project; U.S. Mint; Government of Luxembourg; Capt. Fred Fox, Official History (1945), National Archives RG 407. "
                        "Animated scenes are illustrative.",
        "tags": ["Ghost Army", "World War II", "WWII documentary", "23rd Headquarters Special Troops", "military deception",
                 "inflatable tanks", "Congressional Gold Medal", "history documentary", "Ellsworth Kelly", "Bill Blass"],
        "hashtags": ["#WWII", "#History", "#Documentary"],
        "pinned_comment": "Every claim in this video is listed with its source in the description. Where sources disagree (number of "
                          "operations, declassification year, lives saved) we say so. Did someone in your family serve in the 23rd?",
        "thumbnail_brief": "An inflatable Sherman tank silhouette being carried by four soldiers, sepia palette; 3 words max: 'RUBBER TANKS'. "
                           "No graphic war imagery.", "synthetic_disclosure": False},
    "thumbnail": {"engine": "archival", "params": {"label": False}, "elements": [
        T("RUBBER", [0.5, 0.3], "hero", 0, font="serif_bold", scale=1.4), T("TANKS", [0.5, 0.55], "hero", 0, font="serif_bold", scale=1.4, color="negative")]},
    "shorts": [
        {"id": "short-ga1", "funnel_type": "surprising fact", "title": "These WWII tanks were made of rubber", "chapter": "toolkit",
         "duration_range": [25, 50], "publish_order": 1,
         "segments": [
             {"engine": "kinetic", "narration": "In World War Two, some American tanks were made of rubber. On purpose.",
              "params": {"emphasis": ["rubber.", "purpose."]}},
             {"from": "g13", "narration": "Inflatable decoys of tanks, artillery and trucks, some made by U.S. Rubber and Goodyear, could look like an armored force from a distance.",
              "params": {"src": "assets/decoy-tank.png", "order": "strokes", "draw_time": 8.0, "box_v": [0.05, 0.18, 0.9, 0.5]}},
             {"from": "g12", "narration": "It was one of four tools used by a secret unit called the Ghost Army.",
              "elements": [{"type": "text", "text": "The Ghost Army", "style": "h1", "pos_v": [0.5, 0.2], "at": 0.2, "font": "hand_bold"},
                           {"type": "icon", "name": "magnifier", "pos_v": [0.3, 0.42], "size": 0.09, "at": "cue:four", "label": "sight"},
                           {"type": "icon", "name": "cloud", "pos_v": [0.7, 0.42], "size": 0.09, "at": "cue:tools", "label": "sound"},
                           {"type": "icon", "name": "server", "pos_v": [0.3, 0.62], "size": 0.09, "at": "cue:secret", "label": "radio"},
                           {"type": "icon", "name": "star", "pos_v": [0.7, 0.62], "size": 0.09, "at": "cue:ghost", "label": "theater"}]}],
         "description": "Inflatable decoys of WWII's Ghost Army. Full documentary in the related video. #WWII #History",
         "hashtags": ["#WWII", "#History", "#GhostArmy"], "pinned_comment": "The full story, with sources, is in the related video."},
        {"id": "short-ga2", "funnel_type": "overlooked person", "title": "A famous fashion designer served in a secret WWII unit",
         "chapter": "artists", "duration_range": [25, 50], "publish_order": 2,
         "segments": [{"engine": "kinetic", "narration": "Bill Blass, the fashion designer, served in a secret World War Two unit.", "params": {"emphasis": ["blass,", "secret"]}},
                      {"from": "g11", "narration": "So did painter Ellsworth Kelly, wildlife artist Arthur Singer and photographer Art Kane, all in the 603rd Engineer Camouflage Battalion. "
                                    "Many of its soldiers came from art schools and advertising agencies, because the Army needed people who understood how the eye could be fooled.",
                       "elements": [{"type": "card", "box_v": [0.08, 0.15, 0.84, 0.14], "title": "Ellsworth Kelly", "body": "painter", "at": "cue:ellsworth", "tone": "light"},
                                    {"type": "card", "box_v": [0.08, 0.32, 0.84, 0.14], "title": "Arthur Singer", "body": "wildlife artist", "at": "cue:arthur", "tone": "light"},
                                    {"type": "card", "box_v": [0.08, 0.49, 0.84, 0.14], "title": "Art Kane", "body": "photographer", "at": "cue:kane,", "tone": "light"}]}],
         "description": "Artists of the Ghost Army. #WWII #Art", "hashtags": ["#WWII", "#Art", "#History"],
         "pinned_comment": "Their full story is in the related documentary."},
        {"id": "short-ga3", "funnel_type": "unanswered question", "claims_note": "C52 (contested), C30", "title": "Did a rubber army save 30,000 lives?", "chapter": "myth",
         "duration_range": [25, 50], "publish_order": 3,
         "segments": [{"engine": "kinetic", "narration": "You may have heard the Ghost Army saved up to thirty thousand lives.", "params": {"emphasis": ["thirty", "thousand"]}},
                      {"from": "g39", "narration": "It's widely repeated, even at the medal ceremony. But we could not find a primary study behind that number. "
                                     "What the record does show is where the unit worked, what it did, and what it cost. How many lives it saved is still an open question.",
                       "elements": [{"type": "text", "text": "15,000–30,000?", "style": "hero", "pos_v": [0.5, 0.3], "at": 0.3},
                                    {"type": "text", "text": "no primary study found", "style": "h2", "pos_v": [0.5, 0.45], "at": "cue:study", "color": "negative"}]}],
         "description": "Separating record from legend. #WWII #History", "hashtags": ["#WWII", "#History", "#Documentary"],
         "pinned_comment": "We go through the sources in the full documentary (related video)."},
    ],
}

if __name__ == "__main__":
    (HERE / "project.json").write_text(json.dumps(project, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    words = sum(len(s["narration"].split()) for s in S)
    print(f"{len(S)} scenes · {words} words")

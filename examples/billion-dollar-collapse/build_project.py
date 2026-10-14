"""Builds examples/billion-dollar-collapse/project.json (the demo spec).

Corvane Logistics, Elliot Marsh, Halden Home and every figure in this story are
FICTIONAL. The mechanisms (float, covenants, customer concentration, negative
unit economics) are general business concepts, not claims about real firms.

Run:  python examples/billion-dollar-collapse/build_project.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent


def T(text, pos, style="h2", at=0.0, **kw):
    return {"type": "text", "text": text, "pos": pos, "style": style, "at": at, **kw}


def I(name, pos, size=0.08, at=0.0, **kw):
    return {"type": "icon", "name": name, "pos": pos, "size": size, "at": at, **kw}


chapters = [
    {"id": "cold", "title": "Seventy-two hours", "mood": "tension"},
    {"id": "promise", "title": "The promise", "mood": "wonder"},
    {"id": "machine", "title": "The hidden machine", "mood": "drive"},
    {"id": "cracks", "title": "The cracks", "mood": "tension"},
    {"id": "hours", "title": "The final 72 hours", "mood": "dark"},
    {"id": "lessons", "title": "What really happened", "mood": "resolve"},
]

S = []


def scene(id, chapter, engine, purpose, narration, visual, elements=None, **kw):
    s = {"id": id, "chapter": chapter, "engine": engine, "purpose": purpose, "narration": narration,
         "visual": visual, "elements": elements or [], "illustrative": True, "claims": kw.pop("claims", ["fic-story"])}
    s.update(kw)
    S.append(s)


# ---------------------------------------------------------------- cold open
scene("s01", "cold", "artistic", "hook",
      "On a Monday morning in March, Corvane Logistics was worth one point four billion dollars. "
      "Its purple vans were parked on almost every street in forty American cities, and its app was on millions of phones.",
      "Night skyline, every window lit; title fades in over the city.",
      [T("CORVANE LOGISTICS", [0.5, 0.3], "h1", 1.0, font="serif_bold", color="light", dur=1.6),
       T("Valuation: $1.4 billion", [0.5, 0.42], "h3", "cue:billion", color="accent", dur=1.0)],
      params={"layers": ["mountains", "towers", "city"], "sky": ["night", "night2"], "fog": True},
      camera={"move": "push_in", "amount": 0.08}, transition="fade_black", emotion="suspense",
      attention="Stakes in the first five seconds", shot={"type": "establishing", "angle": "high"})
scene("s02", "cold", "kinetic", "hook",
      "By Thursday night, the vans had stopped. Nine thousand drivers had not been paid. "
      "And two million packages were sitting in warehouses that nobody was allowed to open.",
      "Word-synced typography; key numbers in amber.",
      params={"emphasis": ["stopped.", "nine", "thousand", "two", "million", "nobody"]}, transition="cut",
      emotion="shock", shot={"type": "insert"})
scene("s03", "cold", "motion", "reveal",
      "Corvane filed for bankruptcy seventy-two hours after its last upbeat investor update. On paper, it collapsed overnight. "
      "But companies almost never die in a single night. They die slowly, and then all at once.",
      "A 72-hour countdown, then a BANKRUPT stamp slams onto the logo card.",
      [{"type": "counter", "from": 0, "to": 72, "suffix": " hours", "pos": [0.5, 0.36], "at": 0.3, "dur": 2.8,
        "label": "from investor update to bankruptcy filing"},
       {"type": "card", "box": [0.33, 0.58, 0.34, 0.2], "title": "Corvane Logistics", "body": "Est. 2019 · 40 cities",
        "tone": "night2", "at": 2.0},
       {"type": "stamp", "text": "Bankrupt", "pos": [0.5, 0.68], "at": "cue:overnight", "angle": -9}],
      transition="whip", emotion="shock")
scene("s04", "cold", "whiteboard", "explain",
      "In this video, we'll take the company apart piece by piece: how it grew, the hidden machine that kept it alive, "
      "the cracks nobody wanted to see, and the three days that ended it. "
      "Corvane is a fictional company, but every mechanism in this story is real, and you'll find it in real companies today.",
      "Whiteboard roadmap of the four parts of the video.",
      [T("The roadmap", [0.5, 0.12], "h1", 0.2, underline=True),
       I("rocket", [0.17, 0.45], 0.07, "cue:grew", label="1. The rise"),
       I("server", [0.39, 0.45], 0.07, "cue:machine", label="2. The machine"),
       I("warning", [0.61, 0.45], 0.07, "cue:cracks", label="3. The cracks"),
       I("clock", [0.83, 0.45], 0.07, "cue:three", label="4. The 72 hours"),
       {"type": "arrow", "from": [0.23, 0.45], "to": [0.32, 0.45], "at": "cue:machine", "curve": 0.1},
       {"type": "arrow", "from": [0.45, 0.45], "to": [0.54, 0.45], "at": "cue:cracks", "curve": 0.1},
       {"type": "arrow", "from": [0.67, 0.45], "to": [0.76, 0.45], "at": "cue:three", "curve": 0.1},
       T("Fictional company · real mechanisms", [0.5, 0.8], "h3", "cue:fictional", color="negative")],
      transition="erase", attention="Viewer promise: what you'll understand by the end")

# ---------------------------------------------------------------- the promise
scene("s05", "promise", "handdrawn", "story",
      "Corvane started in twenty nineteen with a simple frustration. Its founder, Elliot Marsh, ran a small furniture shop in Ohio. "
      "He was losing customers because the big retailers could deliver the same day, and he couldn't. "
      "He tried the national carriers, but their prices were built for companies a thousand times his size.",
      "Sketch of the founder in front of his small shop, a giant retailer's truck rolling past.",
      [{"type": "character", "pos": [0.25, 0.9], "height": 0.5, "pose": "stand", "at": 0.2, "talk": False,
        "poses": [{"at": "cue:losing", "pose": "slump"}]},
       I("house", [0.52, 0.55], 0.13, 1.2, label="Marsh Furniture, Ohio"),
       I("truck", [0.8, 0.6], 0.1, "cue:big", label="Same-day giants"),
       T("2019", [0.15, 0.15], "h1", 0.5)],
      camera={"move": "pan_right", "amount": 0.06}, transition="crossfade", shot={"type": "medium"},
      characters=["elliot_marsh"])
scene("s06", "promise", "handdrawn", "explain",
      "Marsh's idea was to give small shops the same superpower. One app. One flat price. "
      "And a fleet of independent drivers who would pick up a package in the morning and drop it off before dinner.",
      "Three sketched panels appear in sequence: app, price tag, driver.",
      [I("phone", [0.2, 0.45], 0.1, "cue:app", label="One app"),
       I("coin", [0.5, 0.45], 0.1, "cue:price", label="One flat price"),
       I("truck", [0.8, 0.45], 0.1, "cue:fleet", label="Independent drivers"),
       T("The superpower", [0.5, 0.14], "h1", 0.2)],
      params={"fill": "hatch"}, transition="cut")
scene("s07", "promise", "motion", "data",
      "Shops loved it. Within a year, Corvane was running in six cities. Within three years it was in forty, "
      "with regional hubs connected like the nodes of a giant nervous system. "
      "Each new city followed the same playbook: lease a warehouse, sign up a few hundred drivers, and sign up every small shop within thirty miles.",
      "Network of hubs lights up city by city.",
      [{"type": "network", "at": 0.5, "dur": 5.5,
        "nodes": [{"id": "a", "label": "Columbus", "pos": [0.3, 0.45], "icon": "warehouse"},
                  {"id": "b", "label": "Chicago", "pos": [0.18, 0.3]}, {"id": "c", "label": "Detroit", "pos": [0.42, 0.24]},
                  {"id": "d", "label": "Atlanta", "pos": [0.45, 0.72]}, {"id": "e", "label": "Dallas", "pos": [0.16, 0.7]},
                  {"id": "f", "label": "New York", "pos": [0.7, 0.3]}, {"id": "g", "label": "Phoenix", "pos": [0.06, 0.52]},
                  {"id": "h", "label": "Miami", "pos": [0.66, 0.8]}, {"id": "i", "label": "Boston", "pos": [0.86, 0.22]},
                  {"id": "j", "label": "Charlotte", "pos": [0.62, 0.55]}, {"id": "k", "label": "Denver", "pos": [0.02, 0.32]},
                  {"id": "l", "label": "Philadelphia", "pos": [0.84, 0.44]}],
        "edges": [["a", "b"], ["a", "c"], ["a", "d"], ["b", "e"], ["a", "f"], ["e", "g"], ["d", "h"], ["f", "i"],
                  ["d", "j"], ["b", "k"], ["f", "l"], ["j", "l"]]},
       {"type": "counter", "from": 1, "to": 40, "suffix": " cities", "pos": [0.83, 0.75], "at": "cue:forty", "dur": 1.6,
        "style": "h1"}],
      transition="push", camera={"move": "push_in", "amount": 0.05})
scene("s08", "promise", "huashu_clip", "data",
      "Revenue followed. Forty million dollars in the first full year. One hundred and ten million the next. "
      "Then two hundred sixty million. And four hundred thirty million by twenty twenty-three.",
      "Editorial bar chart (huashu-art-motion finance grammar) with each bar landing on the spoken number.",
      params={"grammar": "t3_finance_chart", "theme": "paper",
              "data": {"title": "Corvane revenue, 2020–2023", "unit": "Annual revenue, $ millions",
                       "source": "Fictional company · illustrative figures", "chart": "bar", "decimals": 0,
                       "series": [{"label": "2020", "value": 40}, {"label": "2021", "value": 110},
                                  {"label": "2022", "value": 260}, {"label": "2023", "value": 430}],
                       "highlight": {"index": 3, "text": "10.8×", "sub": "in three years"}},
              "cues": [{"at": "cue:forty", "kind": "bar", "data": {"index": 0}},
                       {"at": "cue:hundred", "kind": "bar", "data": {"index": 1}},
                       {"at": "cue:sixty", "kind": "bar", "data": {"index": 2}},
                       {"at": "cue:thirty", "kind": "bar", "data": {"index": 3}},
                       {"at": "end-1.6", "kind": "highlight"}]},
      transition="crossfade", emotion="awe")
scene("s09", "promise", "motion", "data",
      "Investors watched that curve and saw the next great American logistics company. "
      "Three funding rounds valued Corvane at one point four billion dollars. Marsh was on magazine covers. Everyone wanted a piece. "
      "The money came with expectations, of course. Investors wanted the growth curve to keep climbing, and Corvane promised it would.",
      "Valuation counter climbs while investor icons stack up.",
      [{"type": "counter", "from": 0, "to": 1.4, "decimals": 1, "prefix": "$", "suffix": "B", "pos": [0.5, 0.33],
        "at": "cue:valued", "dur": 2.0, "label": "valuation after three funding rounds"},
       I("bank", [0.25, 0.68], 0.07, "cue:three", label="Round A"),
       I("bank", [0.5, 0.68], 0.07, "cue:funding", label="Round B"),
       I("bank", [0.75, 0.68], 0.07, "cue:rounds", label="Round C"),
       {"type": "particles", "kind": "coins", "count": 26, "at": "cue:everyone"}],
      transition="cut", camera={"move": "pull_out", "amount": 0.06})
scene("s10", "promise", "kinetic", "metaphor",
      "But revenue is not profit. And a growth curve tells you how fast something is moving, not whether it can survive a crash.",
      "Typography: REVENUE IS NOT PROFIT.", params={"emphasis": ["not", "profit.", "survive", "crash."]},
      transition="cut")

# ---------------------------------------------------------------- the machine
scene("s11", "machine", "whiteboard", "process",
      "To understand the collapse, you have to understand the machine. Here is how a Corvane delivery worked. "
      "A shop paid Corvane the moment an order was booked. Corvane routed the package through a hub. A driver delivered it. "
      "And the driver got paid. Later.",
      "Four-step process drawn left to right; the last arrow is dashed and labelled 'later'.",
      [T("How one delivery worked", [0.5, 0.12], "h1", 0.3, underline=True),
       {"type": "process", "box": [0.05, 0.3, 0.9, 0.3], "at": "cue:shop", "dur": 9.0,
        "steps": [{"label": "Shop pays Corvane", "color": "positive"}, {"label": "Package routed to hub"},
                  {"label": "Driver delivers"}, {"label": "Driver is paid… later", "color": "accent"}]},
       T("cash IN on day 0", [0.17, 0.72], "h3", "cue:paid", color="positive"),
       T("cash OUT much later", [0.83, 0.72], "h3", "cue:later.", color="negative")],
      transition="erase", camera={"move": "drift"})
scene("s12", "machine", "whiteboard", "timeline",
      "How much later? Forty-five days. Customers paid on day zero. Drivers and hubs were paid on day forty-five. "
      "For six weeks, every dollar of revenue sat in Corvane's bank account.",
      "Timeline from day 0 to day 45, the gap shaded as a six-week cash window.",
      [{"type": "timeline", "box": [0.08, 0.3, 0.84, 0.32], "at": "cue:customers", "dur": 4.0,
        "events": [{"label": "Day 0", "sub": "Shop pays", "color": "positive"},
                   {"label": "Day 15", "sub": "cash piles up"}, {"label": "Day 30", "sub": "still piling up"},
                   {"label": "Day 45", "sub": "Drivers & hubs paid", "color": "negative"}]},
       {"type": "counter", "from": 0, "to": 45, "suffix": " days", "pos": [0.5, 0.18], "at": "cue:forty", "dur": 1.2,
        "style": "h1"},
       T("six weeks of other people's money", [0.5, 0.8], "h2", "cue:six", color="accent")],
      transition="cut")
scene("s13", "machine", "image_whiteboard", "illustration",
      "Accountants call this float. It's a well-known tool. Some retailers and insurers use float very successfully. "
      "As long as orders keep growing, the pile of other people's money in the account keeps growing too.",
      "A sketched hub illustration is drawn line by line (upstream stroke planner), then coloured.",
      [T("FLOAT", [0.82, 0.16], "h1", "cue:float.", color="accent", font="hand_bold")],
      params={"src": "assets/hub-illustration.png", "order": "strokes", "draw_time": 9.0, "line_share": 0.6,
              "box": [0.04, 0.08, 0.7, 0.86]},
      assets=[{"path": "assets/hub-illustration.png", "license": "Original (generated by make_assets.py in this repo)",
               "source": "procedural illustration rendered with the studio's handdrawn engine"}],
      transition="crossfade")
scene("s14", "machine", "handdrawn", "explain",
      "Corvane used that float to pay for its expansion. New hubs, new vans, new cities. On the dashboard, the company always "
      "looked flush with cash. But a large part of that cash was already owed to someone else. "
      "Nobody was hiding anything illegal. It was all in the contracts. It just wasn't on the dashboard.",
      "A sketched pile of coins; a second hand-drawn label reveals most of it belongs to drivers.",
      [{"type": "bar_chart", "box": [0.1, 0.22, 0.45, 0.62], "bars": [
          {"label": "Cash on hand", "value": 100, "color": "positive"},
          {"label": "Owed to drivers", "value": 71, "color": "negative"}], "suffix": "%", "at": "cue:dashboard", "dur": 3.5},
       I("warehouse", [0.72, 0.35], 0.07, "cue:hubs", label="new hubs"),
       I("truck", [0.86, 0.5], 0.06, "cue:vans", label="new vans"),
       I("globe", [0.72, 0.66], 0.06, "cue:cities.", label="new cities"),
       T("most of it wasn't theirs", [0.33, 0.12], "h2", "cue:owed", color="negative")],
      transition="cut", camera={"move": "push_in", "amount": 0.05})
scene("s15", "machine", "whiteboard", "explain",
      "And there was a second hidden engine: a revolving credit line from a single bank. Corvane could borrow up to three "
      "hundred million dollars, as long as it kept certain promises, called covenants, about its cash and its customers.",
      "Bank icon linked to Corvane by a lifeline; a covenant document hangs off the line.",
      [I("bank", [0.2, 0.45], 0.11, 0.3, label="One bank"),
       {"type": "arrow", "from": [0.3, 0.42], "to": [0.62, 0.42], "at": "cue:borrow", "label": "up to $300M", "curve": -0.15},
       I("building", [0.74, 0.45], 0.11, 0.8, label="Corvane"),
       I("document", [0.47, 0.72], 0.07, "cue:covenants,", label="Covenants"),
       T("the lifeline", [0.5, 0.12], "h1", "cue:revolving", underline=True)],
      transition="erase")

# ---------------------------------------------------------------- the cracks
scene("s16", "cracks", "motion", "data",
      "The first crack was the price. Corvane charged shops seven dollars and ten cents per delivery. "
      "But by its own internal numbers, each delivery cost about ten dollars to complete. It lost nearly three dollars on every single package.",
      "Two bars: price vs. cost per package; the gap is labelled -$2.90.",
      [T("Crack #1: the price", [0.5, 0.1], "h2", 0.2),
       {"type": "bar_chart", "box": [0.2, 0.2, 0.6, 0.62], "bars": [
           {"label": "Price charged", "value": 7.10, "color": "cool"},
           {"label": "Cost to deliver", "value": 10.0, "color": "negative"}], "prefix": "$", "decimals": 2,
        "at": "cue:charged", "dur": 4.0, "stagger": 0.6},
       T("−$2.90 per package", [0.5, 0.88], "h2", "cue:lost", color="negative")],
      transition="whip")
scene("s17", "cracks", "kinetic", "metaphor",
      "Why would anyone sell at a loss? Because growth hid it. More orders meant more float, and more float paid for the losses "
      "on the orders that came before.",
      "Typography loop: MORE ORDERS → MORE FLOAT → PAYS FOR LOSSES.",
      params={"emphasis": ["growth", "hid", "float,", "losses"]}, transition="cut")
scene("s18", "cracks", "motion", "data",
      "The second crack was concentration. One customer, a national home-goods chain called Halden Home, made up thirty-eight "
      "percent of Corvane's volume. Five other customers made up another twenty percent.",
      "Donut chart: 38% one customer, 20% five customers, 42% everyone else.",
      [T("Crack #2: one big customer", [0.5, 0.1], "h2", 0.2),
       {"type": "donut", "pos": [0.33, 0.55], "size": 0.26, "at": "cue:customer,", "dur": 2.5, "center": "38%",
        "segments": [{"value": 38, "color": "negative"}, {"value": 20, "color": "accent"}, {"value": 42, "color": "cool"}]},
       {"type": "list", "box": [0.58, 0.38, 0.38, 0.4], "at": "cue:halden", "dur": 4.5, "marker": "dot",
        "items": ["Halden Home: 38%", "Next five customers: 20%", "Thousands of small shops: 42%"]}],
      transition="cut")
scene("s19", "cracks", "motion", "explain",
      "The third crack was the network itself. Most hubs were leased on short contracts, and most drivers were independent "
      "contractors. That kept costs flexible. It also meant that nothing held the system together except the next payment. "
      "If the money stopped, the hubs could close and the drivers could leave, both within days.",
      "The hub network again, now with every link labelled 'next payment'.",
      [T("Crack #3: held together by the next payment", [0.5, 0.1], "h3", 0.2),
       {"type": "network", "at": 0.6, "dur": 4.0,
        "nodes": [{"id": "hq", "label": "Corvane", "pos": [0.5, 0.5], "icon": "building", "size": 0.06},
                  {"id": "h1", "label": "Leased hub", "pos": [0.25, 0.3]}, {"id": "h2", "label": "Leased hub", "pos": [0.75, 0.3]},
                  {"id": "d1", "label": "Contract drivers", "pos": [0.2, 0.72]},
                  {"id": "d2", "label": "Contract drivers", "pos": [0.8, 0.72]},
                  {"id": "d3", "label": "Contract drivers", "pos": [0.5, 0.85]}],
        "edges": [["hq", "h1"], ["hq", "h2"], ["hq", "d1"], ["hq", "d2"], ["hq", "d3"]]}],
      transition="cut", camera={"move": "push_in", "amount": 0.06})
scene("s20", "cracks", "handdrawn", "story",
      "Inside the company, some managers raised alarms. A finance analyst wrote a memo warning that if growth slowed for even "
      "one quarter, the float would start shrinking instead of growing. In our story, that memo was filed, and forgotten.",
      "A sketched analyst holds up a memo; it drifts into a filing cabinet.",
      [{"type": "character", "pos": [0.3, 0.9], "height": 0.5, "pose": "point", "at": 0.3, "talk": True,
        "poses": [{"at": "cue:forgotten.", "pose": "slump"}]},
       {"type": "card", "box": [0.52, 0.22, 0.38, 0.42], "tag": "Internal memo · fictional", "title": "If growth slows one quarter…",
        "body": "…the float shrinks instead of growing.", "at": "cue:memo", "tone": "light"},
       {"type": "stamp", "text": "Filed", "pos": [0.71, 0.5], "at": "cue:filed,", "color": "muted", "angle": 8, "scale": 0.06}],
      transition="crossfade", characters=["analyst"])
scene("s21", "cracks", "artistic", "atmosphere",
      "Then, in early March, growth didn't just slow down. It reversed.",
      "Dusk over the city; the sun sinks behind the towers.",
      [T("It reversed.", [0.5, 0.42], "h1", "cue:reversed.", font="serif_bold", color="light")],
      params={"layers": ["mountains", "towers", "city"], "sky": ["night2", "accent"], "sun": {"pos": [0.62, 0.42], "sink": 0.25},
              "mood_shift": "night"},
      min_duration=7, transition="fade_black", emotion="dread")

# ---------------------------------------------------------------- the 72 hours
scene("s22", "hours", "motion", "timeline",
      "Here is how the final seventy-two hours unfolded.",
      "Four-day timeline Monday → Thursday.",
      [{"type": "timeline", "box": [0.06, 0.32, 0.88, 0.34], "at": 0.3, "dur": 3.0, "horizontal": True,
        "events": [{"label": "Monday", "sub": "biggest customer leaves"}, {"label": "Tuesday", "sub": "credit line frozen", "color": "negative"},
                   {"label": "Wednesday", "sub": "drivers unpaid", "color": "negative"},
                   {"label": "Thursday", "sub": "bankruptcy filing", "color": "negative"}]}],
      min_duration=6.5, transition="push")
scene("s23", "hours", "kinetic", "reveal",
      "Monday, nine a.m. Halden Home announced it would bring its deliveries in-house. "
      "Thirty-eight percent of Corvane's volume would disappear over the next sixty days.",
      "MONDAY 9:00 AM — typography.", params={"emphasis": ["monday,", "in-house.", "thirty-eight", "disappear"]},
      transition="cut", emotion="urgency")
scene("s24", "hours", "motion", "data",
      "On its own, that was survivable. But it flipped the float. Fewer new orders meant less cash coming in, while forty-five "
      "days of driver bills were still coming due. The pile of other people's money started to shrink, fast. "
      "Within forty-eight hours, the company's cash projections went from comfortable to critical.",
      "Line chart of cash on hand: rising for years, then turning sharply down (red).",
      [T("Cash on hand (fictional)", [0.5, 0.1], "h3", 0.2),
       {"type": "line_chart", "box": [0.08, 0.18, 0.84, 0.66], "at": 0.5, "dur": 9.0, "color": "positive",
        "values": [40, 55, 70, 92, 110, 135, 160, 180, 196, 205, 150, 88, 30], "drop_index": 9,
        "labels": ["2021", "", "", "", "2022", "", "", "", "2023", "", "Mar", "", "Thu"],
        "mark": {"index": 12, "text": "nearly empty", "color": "negative"}}],
      transition="cut")
scene("s25", "hours", "whiteboard", "evidence",
      "Monday afternoon, the bank looked at the covenants. One of them required notice if any single customer relationship "
      "changed materially. Another required a minimum cash balance. Corvane was about to break both.",
      "The covenant document is redrawn; two clauses get crossed out in red.",
      [I("document", [0.3, 0.5], 0.2, 0.3, label="Credit agreement"),
       {"type": "list", "box": [0.52, 0.3, 0.42, 0.4], "at": "cue:one", "dur": 6.0, "marker": "cross", "scale": 1.0,
        "items": ["Notify bank if a major customer leaves", "Keep a minimum cash balance"]},
       T("both at risk", [0.73, 0.78], "h2", "cue:both.", color="negative", underline=True)],
      transition="erase")
scene("s26", "hours", "artistic", "atmosphere",
      "Tuesday evening, the bank froze the credit line. The three hundred million dollar safety net was gone in a single email.",
      "Night city; office windows go dark building by building.",
      [T("Tuesday, 6:40 PM", [0.5, 0.2], "h3", 0.4, font="serif_bold", color="light"),
       T("Credit line: FROZEN", [0.5, 0.32], "h2", "cue:froze", font="serif_bold", color="negative")],
      params={"layers": ["towers", "city"], "sky": ["night", "night2"], "lights_out_at": "cue:froze", "fog": True},
      transition="fade_black", emotion="dread", camera={"move": "pull_out", "amount": 0.07})
scene("s27", "hours", "motion", "reveal",
      "Wednesday morning, the driver payment run failed. Drivers talk to each other. By noon, group chats in a dozen cities "
      "were telling people to stop picking up packages. By evening, most of the fleet had parked.",
      "The hub network: links snap and turn red one by one.",
      [T("Wednesday: payment run failed", [0.5, 0.08], "h3", 0.2, color="negative"),
       {"type": "network", "at": 0.3, "dur": 2.5, "break_at": "cue:noon,",
        "nodes": [{"id": "hq", "label": "Corvane", "pos": [0.5, 0.5], "icon": "building", "size": 0.06, "fails": True},
                  {"id": "a", "label": "Chicago drivers", "pos": [0.2, 0.25], "fails": True},
                  {"id": "b", "label": "Atlanta drivers", "pos": [0.8, 0.25], "fails": True},
                  {"id": "c", "label": "Dallas drivers", "pos": [0.15, 0.7], "fails": True},
                  {"id": "d", "label": "Boston drivers", "pos": [0.85, 0.7], "fails": True},
                  {"id": "e", "label": "Columbus drivers", "pos": [0.5, 0.86], "fails": True}],
        "edges": [["hq", "a"], ["hq", "b"], ["hq", "c"], ["hq", "d"], ["hq", "e"]],
        "broken": [["hq", "a"], ["hq", "b"], ["hq", "c"], ["hq", "d"], ["hq", "e"]]}],
      transition="cut", emotion="urgency")
scene("s28", "hours", "handdrawn", "story",
      "Shops started calling. Customers started posting photos of stuck orders. Hubs filled up with packages that had nowhere "
      "to go. Every hour without deliveries meant more refunds, and every refund pulled more cash out. "
      "Some shops even hired their own couriers to rescue packages from Corvane's hubs.",
      "Sketch of a hub overflowing with boxes, phones ringing.",
      [I("warehouse", [0.5, 0.48], 0.18, 0.3, label="Columbus hub"),
       {"type": "crowd", "box": [0.07, 0.2, 0.25, 0.5], "count": 12, "at": "cue:customers", "color": "muted",
        "highlight": 12, "highlight_color": "negative"},
       I("phone", [0.82, 0.3], 0.06, "cue:calling.", label="ringing"),
       I("box", [0.74, 0.66], 0.05, "cue:packages"), I("box", [0.84, 0.7], 0.05, "cue:nowhere"),
       I("box", [0.79, 0.58], 0.05, "cue:refunds,"),
       T("refunds → less cash", [0.5, 0.88], "h3", "cue:refund", color="negative")],
      transition="crossfade", camera={"move": "push_in", "amount": 0.07})
scene("s29", "hours", "motion", "reveal",
      "Thursday night, Corvane filed for Chapter Eleven bankruptcy protection. Seventy-two hours earlier, it had been worth "
      "one point four billion dollars.",
      "Valuation counter runs down from $1.4B; CHAPTER 11 stamp.",
      [{"type": "counter", "from": 1.4, "to": 0.0, "decimals": 2, "prefix": "$", "suffix": "B", "pos": [0.5, 0.34],
        "at": "cue:seventy-two", "dur": 2.5, "label": "equity value (fictional)", "color": "negative"},
       {"type": "stamp", "text": "Chapter 11", "pos": [0.5, 0.72], "at": "cue:filed", "angle": -8}],
      transition="whip", emotion="shock", camera={"move": "static"})

# ---------------------------------------------------------------- lessons
scene("s30", "lessons", "whiteboard", "explain",
      "So was it really overnight? Not at all. The collapse took three days. The conditions for it took four years. "
      "Losing money on every package. Depending on one customer. Funding growth with cash that belonged to drivers. "
      "And a lifeline that could be cut with one email.",
      "Whiteboard checklist: four conditions, each ticked as it is named.",
      [T("3 days to collapse · 4 years to build the conditions", [0.5, 0.12], "h2", "cue:conditions", underline=True),
       {"type": "list", "box": [0.18, 0.28, 0.66, 0.6], "at": "cue:losing", "dur": 9.5, "marker": "cross", "scale": 1.2,
        "items": ["Losing money on every package", "Depending on one customer",
                  "Funding growth with drivers' money", "A lifeline that one email could cut"]}],
      transition="erase")
scene("s31", "lessons", "handdrawn", "metaphor",
      "Each of those choices made sense on its own. Selling at a loss can win a market. A big customer can be a great anchor. "
      "Float can be a superpower. The danger was that all of them depended on the same thing: growth never stopping.",
      "Four sketched blocks stacked on one narrow pillar labelled GROWTH.",
      [{"type": "shape", "kind": "rect", "box": [0.46, 0.5, 0.08, 0.38], "fill": "accent", "at": "cue:danger", "dur": 1.2},
       T("GROWTH", [0.5, 0.92], "h3", "cue:growth", color="accent"),
       {"type": "card", "box": [0.18, 0.3, 0.16, 0.14], "title": "Sell at a loss", "at": "cue:selling", "tone": "light"},
       {"type": "card", "box": [0.36, 0.22, 0.16, 0.14], "title": "Big customer", "at": "cue:anchor.", "tone": "light"},
       {"type": "card", "box": [0.54, 0.22, 0.16, 0.14], "title": "Float", "at": "cue:superpower.", "tone": "light"},
       {"type": "card", "box": [0.72, 0.3, 0.16, 0.14], "title": "Credit line", "at": "cue:all", "tone": "light"},
       {"type": "character", "pos": [0.12, 0.92], "height": 0.36, "pose": "think", "at": 0.3}],
      transition="cut")
scene("s32", "lessons", "motion", "explain",
      "If you want to spot the next Corvane, ask three questions. Does the company make money on each unit it sells? "
      "How much of its business depends on one customer? And whose money is actually in the bank account? "
      "None of these questions require insider access. You can usually find the answers in annual reports, investor letters, or even job postings.",
      "Three question cards slide in.",
      [T("Three questions to ask", [0.5, 0.12], "h2", 0.2),
       {"type": "card", "box": [0.06, 0.3, 0.27, 0.42], "tag": "1", "title": "Unit economics",
        "body": "Does it make money on each unit it sells?", "at": "cue:does", "tone": "night2", "anim": "slide"},
       {"type": "card", "box": [0.365, 0.3, 0.27, 0.42], "tag": "2", "title": "Concentration",
        "body": "How much depends on one customer?", "at": "cue:how", "tone": "night2", "anim": "slide"},
       {"type": "card", "box": [0.67, 0.3, 0.27, 0.42], "tag": "3", "title": "Whose cash?",
        "body": "Whose money is actually in the bank account?", "at": "cue:whose", "tone": "night2", "anim": "slide"}],
      transition="push")
scene("s33", "lessons", "artistic", "atmosphere",
      "Real companies have run into these same traps, and more will. The good news is that the warning signs are almost "
      "always visible long before the final seventy-two hours, if you know where to look.",
      "Dawn over the skyline; lights come back on.",
      [T("The signs are visible early.", [0.5, 0.3], "h2", "cue:warning", font="serif_bold", color="light")],
      params={"layers": ["mountains", "towers", "city"], "sky": ["night2", "accent"], "sun": {"pos": [0.3, 0.62], "sink": -0.2},
              "flicker": True}, claims=["gen-traps"], transition="crossfade", emotion="awe")
scene("s34", "lessons", "kinetic", "cta",
      "Next time, we'll look at a company that faced its own seventy-two hours and survived, and exactly what it did differently. "
      "Thanks for watching.",
      "End card typography.", params={"emphasis": ["survived,", "differently."]}, transition="cut", illustrative=False,
      claims=[])

project = {
    "schema_version": 2,
    "slug": "billion-dollar-collapse",
    "title": "The Billion-Dollar Business That Collapsed Overnight",
    "category": "business",
    "language": "en-US",
    "audience": "US",
    "target_duration": 600,
    "tolerance": 0.05,
    "fps": 30,
    "theme": "documentary",
    "fictional": True,
    "disclaimer": "Corvane Logistics, its people, customers and figures are fictional. The business mechanisms are real.",
    "voice": {"provider": "sapi", "voice": "Microsoft David Desktop", "rate": -1},
    "music": {"enabled": True, "volume": 0.14},
    "art_direction": {"style_id": "doc-mixed-media", "palette": "documentary",
                      "characters": {"elliot_marsh": "Founder: blue shirt, simple bean figure",
                                     "analyst": "Finance analyst: blue shirt, holds memo"},
                      "rules": ["amber = attention", "red = loss / failure", "green = growth / cash in",
                                "every chart labelled fictional"]},
    "chapters": chapters,
    "scenes": S,
    "rights_issues": [{"item": "Narration voice (Windows SAPI 'David')", "status": "resolved",
                       "note": "local system voice used for the demo; replace with licensed voice talent for publication"}],
    "shorts": [
        {"id": "short-01", "title": "It lost $2.90 on every package — and grew anyway", "chapter": "cracks",
         "duration_range": [15, 45], "publish_order": 1,
         "segments": [
             {"engine": "kinetic", "narration": "This company lost money on every single delivery. And investors loved it.",
              "params": {"emphasis": ["every", "loved"]}},
             {"from": "s16", "narration": "It charged seven dollars and ten cents. Each delivery cost about ten. "
                                          "Almost three dollars lost, every package.",
              "elements": [{"type": "bar_chart", "box_v": [0.1, 0.2, 0.8, 0.42], "bars": [
                  {"label": "Price", "value": 7.10, "color": "cool"}, {"label": "Cost", "value": 10.0, "color": "negative"}],
                  "prefix": "$", "decimals": 2, "at": 0.2, "dur": 3.0},
                  {"type": "text", "text": "−$2.90", "style": "hero", "pos_v": [0.5, 0.12], "color": "negative",
                   "at": "cue:almost"}]},
             {"from": "s17", "narration": "Growth hid it. More orders brought in more cash, and that cash covered the losses. Until growth stopped."}],
         "description": "How a fictional billion-dollar delivery company hid a loss on every package. #business #startups",
         "hashtags": ["#business", "#startups", "#finance"],
         "pinned_comment": "The full breakdown, including the 72 hours that ended it, is in the related video."},
        {"id": "short-02", "title": "The accounting trick that kept it alive", "chapter": "machine",
         "duration_range": [15, 50], "publish_order": 2,
         "segments": [
             {"engine": "kinetic", "narration": "Customers paid on day zero. Drivers got paid on day forty-five.",
              "params": {"emphasis": ["zero.", "forty-five."]}},
             {"from": "s12", "narration": "For six weeks, every dollar sat in the company's bank account. Accountants call it float.",
              "elements": [{"type": "timeline", "box_v": [0.12, 0.18, 0.76, 0.5], "at": 0.2, "dur": 3.0,
                            "events": [{"label": "Day 0", "sub": "Shop pays", "color": "positive"},
                                       {"label": "Day 45", "sub": "Drivers paid", "color": "negative"}]},
                           {"type": "text", "text": "FLOAT", "style": "hero", "pos_v": [0.5, 0.12], "color": "accent",
                            "at": "cue:float.", "font": "hand_bold"}]},
             {"from": "s14", "narration": "It looked like a mountain of cash. Most of it was already owed to someone else.",
              "elements": [{"type": "bar_chart", "box_v": [0.12, 0.2, 0.76, 0.44], "bars": [
                  {"label": "Cash", "value": 100, "color": "positive"}, {"label": "Owed", "value": 71, "color": "negative"}],
                  "suffix": "%", "at": 0.2, "dur": 2.5}]}],
         "description": "Float: the cash-flow trick behind a fictional billion-dollar collapse. #business #accounting",
         "hashtags": ["#business", "#accounting", "#money"],
         "pinned_comment": "Watch how the float flipped in the related video."},
        {"id": "short-03", "title": "Worth $1.4 billion on Monday. Bankrupt by Thursday.", "chapter": "hours",
         "duration_range": [15, 50], "publish_order": 3,
         "segments": [
             {"from": "s29", "narration": "Monday: worth one point four billion dollars. Thursday: bankrupt.",
              "elements": [{"type": "counter", "from": 1.4, "to": 0.0, "decimals": 2, "prefix": "$", "suffix": "B",
                            "pos_v": [0.5, 0.3], "at": "cue:thursday:", "dur": 1.5, "color": "negative"},
                           {"type": "stamp", "text": "Chapter 11", "pos_v": [0.5, 0.32], "at": "cue:bankrupt.", "angle": -8,
                            "scale": 0.13}]},
             {"from": "s27", "narration": "The bank froze its credit line. The driver payment run failed. By evening, the fleet had parked.",
              "elements": [{"type": "network", "at": 0.2, "dur": 2.0, "break_at": "cue:failed.",
                            "nodes": [{"id": "hq", "label": "Corvane", "pos_v": [0.5, 0.36], "pos": [0.5, 0.5], "size": 0.08, "fails": True},
                                      {"id": "a", "label": "Drivers", "pos_v": [0.2, 0.18], "pos": [0.2, 0.2], "fails": True},
                                      {"id": "b", "label": "Drivers", "pos_v": [0.8, 0.18], "pos": [0.8, 0.2], "fails": True},
                                      {"id": "c", "label": "Hubs", "pos_v": [0.2, 0.54], "pos": [0.2, 0.8], "fails": True},
                                      {"id": "d", "label": "Shops", "pos_v": [0.8, 0.54], "pos": [0.8, 0.8], "fails": True}],
                            "edges": [["hq", "a"], ["hq", "b"], ["hq", "c"], ["hq", "d"]],
                            "broken": [["hq", "a"], ["hq", "b"], ["hq", "c"], ["hq", "d"]]}]},
             {"engine": "kinetic", "narration": "It didn't really collapse overnight. The cracks took four years.",
              "params": {"emphasis": ["overnight.", "four", "years."]}}],
         "description": "The final 72 hours of a fictional billion-dollar company. #business #documentary",
         "hashtags": ["#business", "#documentary", "#startups"],
         "pinned_comment": "The four-year story behind those 72 hours is in the related video."},
    ],
    "seo": {
        "title_options": ["The Billion-Dollar Business That Collapsed Overnight",
                          "How a $1.4 Billion Company Died in 72 Hours",
                          "It Lost Money on Every Package. Then It Lost Everything."],
        "description": "Corvane Logistics was worth $1.4 billion on Monday and bankrupt by Thursday. In this animated business "
                       "documentary we take the company apart: the same-day delivery promise, the cash-flow float that "
                       "funded its growth, the three cracks nobody fixed, and the 72 hours that ended it. Then: three "
                       "questions you can ask to spot the same warning signs in real companies.",
        "tags": ["business documentary", "company collapse", "bankruptcy explained", "startup failure",
                 "cash flow explained", "float accounting", "unit economics", "customer concentration",
                 "debt covenants", "animated explainer", "logistics startup", "business case study"],
        "hashtags": ["#business", "#documentary", "#finance"],
        "pinned_comment": "Corvane is fictional, but the three questions at 9:20 work on real companies. Which company should we "
                          "break down next?",
        "thumbnail_brief": "Left: purple delivery van in silhouette. Right: huge '$1.4B → $0' in amber/red. 3 words max on "
                           "the image ('72 HOURS'). High contrast, readable at phone size; no fake news-logo styling.",
        "sources_note": "This is a fictional case study. Concepts: float, covenants, unit economics and customer "
                        "concentration are standard finance terms.",
    },
    "thumbnail": {"engine": "motion", "elements": [
        T("$1.4B", [0.3, 0.42], "hero", 0, color="accent", scale=1.5, font="display"),
        T("→ $0", [0.72, 0.42], "hero", 0, color="negative", scale=1.5, font="display"),
        T("IN 72 HOURS", [0.5, 0.78], "h1", 0, color="light", font="display"),
        I("truck", [0.12, 0.2], 0.08, 0)]},
}

if __name__ == "__main__":
    out = HERE / "project.json"
    out.write_text(json.dumps(project, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    words = sum(len(s["narration"].split()) for s in S)
    print(f"wrote {out} · {len(S)} scenes · {words} narration words")

#!/usr/bin/env python3
"""Build scenarios/slow-boat-to-china.json for Eldritch Portal.

Content is condensed from Pulp Cthulhu, chapter 13 "A Slow Boat to
China" so the scenario can be run from the app without the book at hand.
"""
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "slow-boat-to-china.json")

# --------------------------------------------------------------- meta

data = {
    "id": "slow-boat-to-china",
    "title": "A Slow Boat to China",
    "system": "Pulp Cthulhu / Call of Cthulhu 7e",
    "source": "Pulp Cthulhu, Chapter 13 (Chaosium)",
    "author_note": "Data entered for play in Eldritch Portal. Human NPC "
                   "characteristics not printed in the scenario text are "
                   "marked as Keeper-ready standins - swap in Appendix A "
                   "values if you have the book.",
    "tagline": "A luxury liner, eleven days at sea, and something in the "
               "hold that is learning to play.",
    "player_pitch":
        "December 1931. The SS President Coolidge sails from San Francisco "
        "for Shanghai with 678 passengers, 315 crew, and a fifteen-day "
        "crossing ahead. There is jazz in the Grand Salon, skeet off the "
        "stern, and a seven-course dinner every night. On the second "
        "morning a millionaire's empty clothes are found folded in a chair "
        "as if the man inside had simply melted away.",
    "keeper_summary":
        "A crawling one - the vermin-swarm remnant of the sorcerer Luis "
        "Fernando de la Montoyo - is shipping the Pipes of Leng, a "
        "mechanical pipe organ built to summon and trap Mythos entities, "
        "to a test firing in the middle of the Pacific. It travels as the "
        "reclusive Spanish nobleman Senor Diego Guiterrez de Almacan, "
        "murders and wears the faces of anyone inconvenient, and needs the "
        "blood of five sacrifices to charge the device. On 19 December it "
        "plays the pipes. The device works exactly wrong: it enrages what "
        "it summons. A flying polyp comes up out of the ocean to destroy "
        "the machine, and the ship with it.",
    "run_time": "3-5 sessions",
    "player_count": "3-6 heroes",
    "setting": "SS President Coolidge, San Francisco to Shanghai, "
               "5-20 December 1931",
    "notes": "",
    "sessions": [],
}

# ------------------------------------------------------- keeper brief

data["keeper_brief"] = [
    {
        "title": "The one-paragraph version",
        "body":
            "A crawling one has built a machine that summons Mythos "
            "entities. It is testing the machine on a passenger liner in "
            "the middle of the Pacific. It needs five blood sacrifices to "
            "charge it, and it takes the faces of the people it kills. The "
            "heroes are passengers. When the machine finally plays, it "
            "summons something that tears the ship apart.",
    },
    {
        "title": "How the heroes get involved",
        "body":
            "They are simply aboard - a rest cure to Shanghai, or an "
            "invitation to the opening of 'Le Monde Mysterieux de "
            "l'Indo-Chine' at the Institut Orientale in the French "
            "Concession, an exhibit said to include rare occult scrolls "
            "and a black toad-icon called Cahoqua. New parties should all "
            "book the same class. Do not let a player be ship's crew.",
    },
    {
        "title": "Pacing - the thing most likely to go wrong",
        "body":
            "Fifteen days is a lot of days. Players will want to use every "
            "hour of every one of them. Force the pace: red-line the "
            "story, say out loud that you are fast-forwarding to the "
            "important part, and throw a scene at them whenever the "
            "investigation stalls. Let them explore and gossip, but keep "
            "the days moving.",
    },
    {
        "title": "The cat-and-mouse rule",
        "body":
            "Finding the crawling one should be a hunt, not a reveal. It "
            "can be any of five faces, it can switch between them in a "
            "single combat round, and if cornered it collapses into a pile "
            "of insects and pours away through the floorboards. Never let "
            "it be caught early - let it be *nearly* caught often.",
    },
    {
        "title": "Dialling the pulp up or down",
        "body":
            "As written: a shipboard murder mystery with a monster at the "
            "end. Dialled up: zombies rising below decks, crazed tcho-tcho, "
            "a hunting horror in the corridors, and warship guns called in "
            "on the polyp. Both are supported below - see the optional "
            "entries in Reference.",
    },
    {
        "title": "Where it ends",
        "body":
            "The Coolidge almost certainly sinks. Survivors are picked up "
            "within hours; the papers report a freak wave. If the crawling "
            "one completes its Gate to Shanghai it joins the Eight "
            "Fortunes Mutual Aid Society and becomes a returning villain "
            "with a grudge.",
    },
]

# ----------------------------------------------------------- timeline


def ev(day, when, title, desc, refs=None, tag=""):
    e = {"id": "tl-" + title.lower().replace(" ", "-")[:40],
         "day": day, "when": when, "title": title, "description": desc,
         "triggered": False}
    if refs:
        e["connects_to"] = refs
    if tag:
        e["tag"] = tag
    return e


data["timeline"] = [
    ev("Sat 5 Dec", "11:00 a.m.", "Depart San Francisco",
       "The Coolidge sails from Pier 42 into fog and foghorns, passing "
       "Alcatraz on the way out. Boarding is by class: First and Special "
       "forward under First Officer Schramm, Third amidships, Steerage aft "
       "under their own power. The heroes meet a drunk Chad Peterson and "
       "his fiancee Virginia Ridley on the gangway.",
       ["beat-up-the-gangway"], "voyage"),
    ev("Sat 5 Dec", "evening",
       "Peterson is consumed",
       "The crawling one boards in vermin form inside the aetheric energy "
       "device in Hold 7, takes an unlisted cabin as Senor Almacan, and is "
       "confronted by Chief Purser Martin Dungass - who is killed and "
       "consumed. Realising it cannot murder the whole crew, it instead "
       "finds and consumes Chad Peterson. Virginia dined with the real "
       "Peterson around 7:00 p.m.; the figure she glimpses in the corridor "
       "at 9:30 p.m. is already the crawling one.",
       ["npc-crawling-one", "beat-cabin-mates"], "villain"),
    ev("Sun 6 Dec", "~9:45 a.m.", "The empty suit is found",
       "Albert Hallander picks the lock on Peterson's cabin to rob it and "
       "finds a mass of cockroaches. Minutes later Virginia Ridley opens "
       "the unlocked door and screams. The clothes are slumped in a chair, "
       "nested inside one another like a Russian doll.",
       ["beat-the-empty-suit", "handout-suicide-note"], "event"),
    ev("Sun 6 Dec", "through the day", "Anyone seen the purser?",
       "Crew gossip spreads that Chief Purser Martin Dungass has not been "
       "seen since his rounds last evening.",
       ["beat-anyone-seen-the-purser"], "event"),
    ev("Sun 6 Dec", "morning / evening",
       "Sunday Mass and St. Nicholas Night",
       "Father Alvarez celebrates Mass in the chapel. St. Nicholas Night "
       "for all First, Special and Third Class children in the ballroom.",
       ["npc-father-alvarez"], "social"),
    ev("Mon 7 Dec", "after midnight", "The Tome of Red Jade is stolen",
       "The crawling one, having overheard Dr. Soong and Wang Ma, resumes "
       "Peterson's form, steals a crewman's uniform, and takes the book "
       "from Soong's cabin while the doctor walks the deck. Wang Ma is "
       "killed. The thief leaps from the Boat Deck to the Promenade Deck "
       "and vanishes.",
       ["beat-the-stolen-book", "handout-book-of-red-jade"], "villain"),
    ev("Mon 7 Dec", "daytime", "Bunny Bates is dominated",
       "The crawling one casts Dominate on the gangster Stuart 'Bunny' "
       "Bates and begins using him as its hands. The spell must be recast "
       "every night, requiring an opposed POW roll.",
       ["npc-bunny-bates"], "villain"),
    ev("Mon 7 Dec", "evening", "Casino Night",
       "Casino Night for First and Special Class. Four hired dealers, "
       "including the Po brothers from Third Class working Pai Gow.",
       None, "social"),
    ev("Tue 8 Dec", "11:00 a.m.", "Peterson memorial service",
       "Father Alvarez holds a memorial service in the ship's chapel. "
       "Charles Astor stomps about insisting something must be done; a few "
       "First Class women take Virginia under their wing in barely "
       "suppressed panic.",
       ["beat-passenger-reactions"], "social"),
    ev("Tue 8 Dec", "3:00 p.m.", "Wang Ma is buried at sea",
       "A short ceremony at the stern. Lo Mai steps into Wang Ma's place "
       "at Dr. Soong's side.",
       ["npc-wang-ma"], "event"),
    ev("Wed 9 Dec", "daytime", "Virginia shoots skeet",
       "Virginia Ridley shoots skeet off the stern deck to work off her "
       "nerves. Stewards eventually ask her to stop - the gunshots are "
       "upsetting the other passengers.",
       ["npc-virginia-ridley"], "social"),
    ev("Wed 9 Dec", "evening", "Tahitian Ball",
       "Tahitian Ball for First and Special Class passengers.",
       None, "social"),
    ev("Thu 10 Dec", "daytime", "Phyllis Barnes performs",
       "Phyllis Barnes gives a performance in the Music Room on B Deck.",
       ["npc-phyllis-barnes"], "social"),
    ev("Thu 10 Dec", "early morning", "Arrive Honolulu - quarantine",
       "The ship is held under quarantine. No one disembarks, no tenders "
       "come alongside. Honolulu police board to investigate Peterson's "
       "apparent suicide and the purser's disappearance, interview Soong, "
       "Aimesworthy and Ridley, search Steerage, and leave after two "
       "hours.",
       ["beat-honolulu-and-beyond"], "event"),
    ev("Thu 10 Dec", "after dinner", "SACRIFICE 1: Takishi Suroda",
       "Bates finds Suroda wandering after dinner, overpowers him, and "
       "takes him to Cargo Hold 7. Drained, then tipped out of a porthole. "
       "A hero sharing his cabin finds the bed not slept in.",
       ["beat-missing-people", "npc-takishi-suroda"], "villain"),
    ev("Fri 11 Dec", "daytime", "Suicide ruling - depart Honolulu",
       "Detective William Ranta declares the note genuine and Peterson a "
       "jumper; the empty clothes are 'a coincidence'. Dungass is ruled an "
       "accidental drowning. Wang Ma's killer supposedly jumped ship. "
       "Heroes who insist they have seen Peterson since his death are "
       "dismissed. After Honolulu, Charles Astor offers $1,000 cash for "
       "useful information.",
       ["beat-honolulu-and-beyond", "npc-charles-astor"], "event"),
    ev("Sat 12 Dec", "-", "Cross the International Date Line",
       "A day is gained. Scenario dates are kept to US dates throughout "
       "for ease of reference.",
       None, "voyage"),
    ev("Sat 12 Dec", "night", "SACRIFICE 2: Miles Hardaway",
       "The Chronicle reporter is lured to Senor Almacan's cabin. Bates "
       "strikes him from behind. Drained, then out a porthole.",
       ["beat-missing-people", "npc-miles-hardaway"], "villain"),
    ev("Sun 13 Dec", "morning", "Sunday Mass",
       "Father Alvarez celebrates Mass in the chapel.",
       ["npc-father-alvarez"], "social"),
    ev("Sun 13 Dec", "night", "SACRIFICES 3 & 4: Barnes and a crewman",
       "Phyllis Barnes hears the pipes through the ventilation shafts and "
       "goes to investigate, finding her way to the cargo hatches - where "
       "she walks in on Bates knocking out a sailor on his rounds. Bates "
       "clubs her too and takes both below. The crewman goes over the "
       "side; Barnes cannot be dumped unseen, so her body is put in a "
       "ballast tank in Hold 4. It will be found in about a week, by "
       "smell.",
       ["beat-missing-people", "loc-hold-4", "npc-phyllis-barnes"],
       "villain"),
    ev("Sun 13 Dec", "night onwards", "Rumours of strange music",
       "Passengers begin talking about music heard in the dead of night. "
       "No two accounts agree - 'a haunting opera', 'a dirge from hell'.",
       ["beat-distant-music"], "event"),
    ev("Mon 14 Dec", "night", "The music is heard clearly",
       "The music is now heard around the ship. A Listen roll at night "
       "catches it; a Hard Listen places it below decks. The music room is "
       "empty.",
       ["beat-distant-music"], "event"),
    ev("Tue 15 - Wed 16 Dec", "night", "SACRIFICE 5: Keeper's choice",
       "One more death fully charges the pipes. Who it is, is yours: a "
       "nameless passenger, or - better - someone the heroes have come to "
       "know. Dr. Soong, Virginia Ridley and Father Alvarez are all "
       "candidates. A hero is a legitimate target.",
       ["beat-missing-people"], "villain"),
    ev("Thu 17 Dec", "-", "Bunny Bates confesses",
       "Bates briefly breaks the domination and seeks out Father Alvarez - "
       "or a hero, if one is a priest - to confess. He admits the theft of "
       "the book and the murder of Wang Ma, and anything else he can think "
       "of. He speaks of voices that made him do it. His stories do not "
       "hold together. Within an hour his mind snaps; the crawling one "
       "retakes him permanently.",
       ["npc-bunny-bates", "npc-father-alvarez"], "event"),
    ev("Fri 18 Dec", "all day", "Foul weather",
       "CON roll or seasick.",
       None, "voyage"),
    ev("Sat 19 Dec", "morning", "Heavy seas",
       "Big waves and rain all morning - CON roll or seasick. Clear in the "
       "afternoon.",
       None, "voyage"),
    ev("Sat 19 Dec", "evening", "CLIMAX: Bunny takes a hostage",
       "Bates walks into the First Class dining hall and takes the first "
       "person he sees hostage, ranting about the voices. He must be taken "
       "down by force or by clever talk (Extreme Persuade or Fast Talk, or "
       "Hard Psychoanalysis).",
       ["beat-bunny-takes-a-hostage"], "climax"),
    ev("Sat 19 Dec", "evening", "CLIMAX: The final test",
       "While everyone is distracted, the crawling one plays the Pipes of "
       "Leng in Hold 7. A whirlpool opens in the ocean and a flying polyp "
       "rises to destroy the machine - and the ship around it.",
       ["beat-the-final-test", "npc-flying-polyp"], "climax"),
    ev("Sun 20 Dec", "6:00 a.m.", "Due in Shanghai",
       "The scheduled arrival - which the Coolidge will probably never "
       "make.",
       ["beat-conclusion"], "voyage"),
]

# -------------------------------------------------------------- beats


def beat(bid, title, act, body, refs=None):
    b = {"id": bid, "title": title, "act": act, "description": body,
         "done": False}
    if refs:
        b["connects_to"] = refs
    return b


data["beats"] = [
    beat("beat-up-the-gangway", "Up the Gangway", "Act 1 - Boarding",
         "Saturday 5 December, Pier 42.\n\n"
         "The heroes check their baggage and are greeted by a Dollar Line "
         "steward and the ship's officers. Passengers board by class: "
         "First and Special forward with First Officer Hugo Schramm "
         "welcoming them; Third amidships with able-bodied seamen "
         "helping; Steerage aft, under their own power.\n\n"
         "MEET THE DOOMED MAN. The heroes should bump into Chad Peterson "
         "and Virginia Ridley on the gangway. Peterson is impeccably "
         "dressed and thoroughly drunk, demanding champagne be sent to his "
         "room and greeting everyone he collides with: 'Chad Peterson from "
         "New York, delighted to make your acquaintance.' Stewards fawn "
         "over him and steer him firmly to First Class on A Deck. Virginia "
         "is annoyed but tight-lipped; addressed, she gives a forced smile "
         "and excuses herself - 'Please excuse me. I must get ready for "
         "dinner.'\n\n"
         "Dr. Soong boards in a dark Western suit and bowler with a small "
         "doctor's bag, his manservant Wang Ma at his shoulder. Soong "
         "introduces himself but not Wang Ma; spoken to, Wang Ma grunts, "
         "and Soong explains that the man is 'a little reserved'.\n\n"
         "STEERAGE PASSENGERS meet the dockworkers and Lo Mai, one of "
         "Soong's tcho-tcho labourers, overseeing fifty barrels labelled "
         "'Hawaiian Botanical Specimens'.\n\n"
         "WHAT IS BEING LOADED (all of this is visible from the dock):\n"
         "- Three new 1931 Packard sedans, a 1930 Hudson tourer, a Bugatti "
         "racer\n"
         "- Twenty dairy cows, a dozen Oliver tractors\n"
         "- A dozen barrels of French cognac, a truckload of mail bags\n"
         "- A massive crate: a complete 50-pipe organ from the 'Wm. Wood "
         "Pipe Organ Co., Inc. of Portland, Oregon'\n"
         "- A six-foot green metal box, delivered with an armed guard\n"
         "- Hundreds of trunks, sea chests, gun cases, instruments, and a "
         "parrot\n\n"
         "SPOT HIDDEN: also notices a large crate marked 'Funeral "
         "Supplies' - the body of a tcho-tcho who died in San Francisco, "
         "being repatriated to Burma at Dr. Soong's expense.\n\n"
         "The ship sails just after 11:00 a.m., passing Alcatraz on the "
         "way out.",
         ["clue-organ-crate", "clue-green-metal-box",
          "clue-funeral-supplies", "npc-chad-peterson"]),

    beat("beat-cabin-mates", "Cabin Mates", "Act 1 - Boarding",
         "Saturday 5 December. Give the heroes time to settle in, and use "
         "cabin mates to hand out relationships for free.\n\n"
         "STEERAGE dormitory: a family of seven Hawaiian missionaries (the "
         "Castors), four young Irishmen contracted to the Shanghai "
         "Municipal Police, thirteen Americans hoping to strike it rich in "
         "China, three Japanese brewers returning to Tokyo, a group of "
         "Filipino jazz musicians who did not make it big in San "
         "Francisco, three nannies whose employers travel First Class, six "
         "of Dr. Soong's tcho-tcho labourers under Lo Mai, and ten Chinese "
         "rail workers and shopkeepers going home.\n\n"
         "THIRD CLASS: an 8-bed cabin shared with the brothers Po Liang "
         "and Po Hau, Pai Gow dealers hired for Casino Night, and US Navy "
         "crewman Olaf Gustavsen of the minesweeper Abilene, returning to "
         "Pearl Harbor from family leave.\n\n"
         "SPECIAL CLASS: male heroes likely share with Takishi Suroda, "
         "female heroes with Phyllis Barnes.\n\n"
         "FIRST CLASS on A Deck: Senor Diego Guiterrez de Almacan is one "
         "cabin down. Virginia Ridley and Chad Peterson are close by. On "
         "the Boat Deck, Dr. Soong and Wang Ma are the neighbours. The "
         "heroes may share an elevator with the young couple on the way to "
         "dinner, or catch them holding hands at the bow on the "
         "Promenade.\n\n"
         "Nothing unusual happens the first night - not to the heroes. In "
         "his cabin, Chad Peterson is devoured.",
         ["npc-almacan", "npc-takishi-suroda", "npc-phyllis-barnes"]),

    beat("beat-the-empty-suit", "The Empty Suit", "Act 2 - The Mystery",
         "Sunday 6 December, just after 9:45 a.m., First Class hallway on "
         "A Deck towards the stern, near the barber shop and tailors.\n\n"
         "LISTEN roll for early risers: they hear the disturbance from an "
         "upper deck.\n\n"
         "Virginia Ridley, changing for a late breakfast, goes to "
         "Peterson's room, finds the door unlocked, and screams. Inside: "
         "an empty suit of clothes and a strange, bad smell. Socks and "
         "shoes on the floor in front of a suit, vest, shirt and "
         "undershirt - all placed inside one another like a Russian doll, "
         "as if the body within had simply melted away.\n\n"
         "WHO IS IN THE HALLWAY. Only Hallander and Ridley must be "
         "present:\n"
         "- Albert Hallander, sailor, who picked the lock minutes earlier "
         "to rob the place and found thousands of cockroaches skittering "
         "off the chair. He yelled. He is still shaken.\n"
         "- Virginia Ridley, distraught.\n"
         "- Charles Astor, obnoxiously present.\n\n"
         "BREAKING HALLANDER. He claims he heard a noise and came in "
         "through an unlocked door. He is lying - there was no noise and "
         "the door was locked. Psychology notices he is shocked; "
         "Intimidate or Persuade gets him talking; a second Psychology "
         "detects the lies. He would rather muddy the water and slip away "
         "than admit attempted theft, but a concerted effort makes him "
         "confess - and be arrested by the ship's officers.\n\n"
         "Rumours that Peterson was 'a jumper' start immediately. Seaman "
         "Hank Henson holds the door until Dr. Hartman and First Officer "
         "Schramm have seen the scene.\n\n"
         "SEARCHING THE CABIN. The crew want it quiet and keep their "
         "findings to themselves. Heroes get in by bribe, bluff, First "
         "Class standing, or a fuss from Virginia; later, once Henson is "
         "back on normal duties, by Locksmith or Mechanical Repair. "
         "Nothing looks out of place except the clothes - and a suicide "
         "note on the desk, which Steward Aimesworthy removes as evidence "
         "that evening.",
         ["handout-suicide-note", "clue-empty-clothes",
          "clue-hallanders-lie", "npc-albert-hallander"]),

    beat("beat-anyone-seen-the-purser", "Anyone Seen the Purser?",
         "Act 2 - The Mystery",
         "Sunday 6 December, anywhere aboard.\n\n"
         "LISTEN roll to overhear crew talking about Chief Purser Martin "
         "Dungass, not seen since last evening when he was 'doing his "
         "rounds'. The same conversation recurs all day until the general "
         "opinion is that Dungass, like Peterson, has gone missing.\n\n"
         "THE TRUTH: Dungass noticed a passenger who was not on the "
         "manifest and went to ask about it. He was killed and consumed.\n\n"
         "THE MANIFEST. A Hard Persuade roll gets a hero a look at the "
         "passenger manifest. Senor Guiterrez de Almacan is not listed "
         "anywhere - not First Class, not anywhere. This is the single "
         "hardest fact in the scenario and it points straight at the "
         "villain.\n\n"
         "CREW GOSSIP. Heroes who befriend a crewman learn the consensus: "
         "Dungass hit the bottle and is sleeping it off below decks - "
         "there are rumours of trouble with his wife. He will turn up, and "
         "the Captain will have words for him when he does.",
         ["clue-manifest-gap", "npc-martin-dungass"]),

    beat("beat-passenger-reactions", "Passenger Reactions",
         "Act 2 - The Mystery",
         "Miles Hardaway of the San Francisco Chronicle makes a meal of "
         "the case, emphasising its 'locked room' nature and wiring "
         "speculation ashore as 'a real-life Sherlock Holmes mystery!' The "
         "shipboard newspaper, the Pacific Current, mentions neither "
         "disappearance.\n\n"
         "Some First Class women take Virginia under their wing in barely "
         "suppressed panic. Charles Astor stomps about demanding "
         "'something must be done'. Telegrams of condolence arrive over "
         "the next 24 hours from New York, Chicago, San Francisco and Los "
         "Angeles. Father Alvarez arranges a memorial service.\n\n"
         "First Officer Schramm is mystified and under orders to keep the "
         "disappearances quiet.",
         ["npc-miles-hardaway", "npc-charles-astor"]),

    beat("beat-the-stolen-book", "The Stolen Book", "Act 2 - The Mystery",
         "Monday 7 December, after midnight, Boat Deck.\n\n"
         "During the morning of the 7th the crawling one - as Almacan - "
         "overhears Dr. Soong and Wang Ma discussing the doctor's copy of "
         "the Tome of Red Jade, taken from a gang of San Francisco "
         "cultists. The crawling one believes it is the very copy it once "
         "owned, and it wants it back.\n\n"
         "After midnight it reassumes Peterson's form, steals a crewman's "
         "uniform, and enters Soong's cabin while the doctor walks the "
         "deck. Wang Ma dies defending it.\n\n"
         "IF THE HEROES ARE NEARBY (especially on the Boat Deck):\n"
         "- LISTEN: the doctor's cry for help, and running feet.\n"
         "- They see a steward burst through a doorway and run for the "
         "ship's side, between the lifeboats, carrying a book.\n"
         "- It is night. Little light, many dark corners.\n\n"
         "THE CHASE. The crawling one vaults the Boat Deck railing down to "
         "the Promenade Deck and keeps running without breaking stride. "
         "Pursuers must make a Jump roll or take 1D6+3 from the fall onto "
         "hard decking.\n\n"
         "MINDBLAST. Anyone directly in its path may be hit: opposed POW "
         "roll against POW 100. If the crawling one wins, the target sees "
         "it for a moment as a hollow, eyeless thing with dark energies "
         "frothing inside - 5 Sanity points and an immediate bout of "
         "madness. If the hero wins, no effect.\n\n"
         "IT ALWAYS ESCAPES. However the chase goes, it gets away: cornered, "
         "it leaps into a dark recess and falls apart into a mass of "
         "insects that scatter and are gone. The book may be dropped in "
         "the process - your call.\n\n"
         "OPTIONAL DIFFICULTY: have the dominated Bunny Bates, in a stolen "
         "crew uniform, cover the escape from a dark vantage point. He has "
         "a .32 revolver, or a Tommy gun if you want real pressure. "
         "Captured alive here he refuses to say a word. Killed or brigged, "
         "the crawling one dominates Steward Martin Aimesworthy instead - "
         "substitute him for Bates in every later scene.",
         ["handout-book-of-red-jade", "npc-dr-soong", "npc-wang-ma",
          "npc-bunny-bates", "clue-blood-on-the-crate"]),

    beat("beat-looking-for-bunny", "Looking for Bunny Bates",
         "Act 2 - The Mystery",
         "Bates lies low in the crawling one's cabin or in the cargo "
         "holds. Whether the heroes find him is down to how resourceful "
         "they are.\n\n"
         "Cornered, he fights desperately and runs at the first "
         "opportunity. Captured, he babbles about 'the voice within' and "
         "how 'the choir of angels has commanded me'. While the Dominate "
         "spell holds, there is nothing useful to get out of him.\n\n"
         "BREAKING THE DOMINATION. The crawling one must recast Dominate "
         "every night, requiring an opposed POW roll. If the heroes can "
         "bolster Bates' willpower - a Hard Persuade or Hard "
         "Psychoanalysis roll - give him a bonus die to resist.\n\n"
         "TROUBLESOME HEROES. If the heroes are making life difficult, or "
         "the action needs a shove, Bates springs an ambush: at a hero's "
         "cabin door, or out of the dark in the hold. Especially if they "
         "are getting close to Almacan's cabin or nosing at the cargo "
         "hatches. For a seriously hard time, the crawling one summons a "
         "hunting horror instead - though it will time such an attack to "
         "minimise witnesses.",
         ["npc-bunny-bates", "npc-hunting-horror"]),

    beat("beat-honolulu-and-beyond", "Honolulu and Beyond",
         "Act 2 - The Mystery",
         "Thursday 10 December, early.\n\n"
         "The Coolidge arrives at Honolulu and is immediately held under "
         "quarantine. No one disembarks. No tenders come alongside. A team "
         "of policemen comes aboard to investigate Peterson's apparent "
         "suicide, the purser's disappearance, and Wang Ma's murder if it "
         "was ever reported.\n\n"
         "They interview Dr. Soong, Martin Aimesworthy and Virginia "
         "Ridley, search Steerage for Wang Ma's killer, take statements on "
         "Suroda if his absence is known, search his cabin, find nothing, "
         "and leave after about two hours.\n\n"
         "DETECTIVE WILLIAM RANTA'S CONCLUSIONS (Friday 11th):\n"
         "- The suicide note is genuine. Peterson jumped from his suite's "
         "small balcony. The empty clothes are a coincidence, and Ranta "
         "would rather set such details aside and close the case.\n"
         "- Peterson drank too much and suffered from 'dark thoughts'.\n"
         "- Dungass got drunk and was swept overboard - accidental "
         "death.\n"
         "- Wang Ma's killer jumped ship at Honolulu.\n"
         "- Suroda also jumped ship, and may be connected to Wang Ma's "
         "murder. Ranta assures everyone he will track him down.\n\n"
         "Heroes explaining that they have seen Peterson walking about "
         "since his death are quickly dismissed.\n\n"
         "AFTER HONOLULU. The ship departs on the 11th. Charles Astor, "
         "unconvinced, backs his protests with $1,000 cash for anyone with "
         "useful information - a strong lever if the heroes need money or "
         "motivation.",
         ["npc-charles-astor", "npc-takishi-suroda"]),

    beat("beat-missing-people", "Missing People", "Act 3 - The Pattern",
         "The crawling one must energise the Pipes of Leng with five "
         "sacrifices, letting the blood run into the organ. It does not "
         "matter who they are. Bates collects them; they are taken to "
         "Cargo Hold 7, killed, and drained. There are no witnesses - "
         "though if the heroes are floundering, a bleary-eyed passenger "
         "may report having seen something strange.\n\n"
         "THE FIVE:\n"
         "1. Takishi Suroda, 10 Dec - taken after dinner, out a "
         "porthole.\n"
         "2. Miles Hardaway, 12 Dec - lured to Almacan's cabin, struck "
         "from behind, out a porthole.\n"
         "3-4. Phyllis Barnes and a crewman, 13 Dec - she followed the "
         "music to the cargo hatches and found Bates knocking out a sailor "
         "on his rounds. The crewman goes over the side; Barnes goes into "
         "a ballast tank in Hold 4, and will be found in about a week by "
         "smell.\n"
         "5. 15th or 16th Dec - your choice. A nameless passenger works, "
         "but someone the heroes know works far better: Dr. Soong, "
         "Virginia Ridley, Father Alvarez. A hero is a legitimate "
         "target.\n\n"
         "HOW THE HEROES NOTICE:\n"
         "- They go looking for someone and find an empty cabin and nobody "
         "who has seen them for a while.\n"
         "- A crying child says her music lesson with Ms. Barnes was "
         "cancelled and the teacher is nowhere to be found.\n"
         "- Another passenger asks the heroes whether they have seen "
         "so-and-so lately.\n\n"
         "THE CREW'S RESPONSE. Brought to the senior crew's attention, "
         "they investigate and conclude the person is simply elsewhere "
         "aboard and will turn up at dinner. It is down to the heroes.",
         ["loc-hold-7", "loc-hold-4", "npc-bunny-bates"]),

    beat("beat-soong-requests-help", "Dr. Soong Requests Help",
         "Act 3 - The Pattern",
         "If the heroes need motivating and Soong has not already "
         "approached them about his book, he does so soon after Honolulu - "
         "requesting their company in a smoking room or the First Class "
         "Library.\n\n"
         "Soong is worried that something evil is afoot, something beyond "
         "a simple suicide or murder. He believes the missing people, the "
         "deaths and his stolen book are all connected, and he may raise "
         "the strange music himself.\n\n"
         "THE OFFER. He is too old and frail to search. He will send his "
         "tcho-tcho through Steerage if the heroes will take the engine "
         "room and the holds.\n\n"
         "KEEPER NOTE. Soong is an ally and a source of Mythos "
         "information, not an oracle. Do not let him answer every question "
         "or save the day. Use him to point, and - when the heroes are "
         "floundering - to hand over one useful piece of information that "
         "gets them moving again.",
         ["npc-dr-soong", "npc-tcho-tcho"]),

    beat("beat-distant-music", "Distant Music", "Act 3 - The Pattern",
         "13 December onwards.\n\n"
         "Rumours circulate of strange music heard in the dead of night. "
         "No two passengers agree on what it sounds like: 'a haunting "
         "opera', 'a dirge from hell'. Nobody can place where it comes "
         "from. Crew asked about it admit they have heard it too. One "
         "crewman may offer that it is the siren's song of myth, drawing "
         "sailors to their doom.\n\n"
         "THE ROLLS. A hero wandering the ship late at night: LISTEN to "
         "catch a distant, muffled music - church-like, haunting, "
         "downright melancholy. The music room is empty. HARD LISTEN "
         "places the sound below decks.\n\n"
         "IT GETS LOUDER. The crawling one is testing the machine in Cargo "
         "Hold 7, and with each new sacrifice the sound grows louder and "
         "clearer. Build it: start with second-hand hints and dream "
         "reports ('I had a strange dream, filled with unearthly music'), "
         "and let the accounts thicken day by day until the heroes hear it "
         "themselves.",
         ["loc-hold-7", "clue-music-below-decks"]),

    beat("beat-meeting-the-captain", "Meeting the Captain",
         "Act 3 - The Pattern",
         "Sooner or later anyone making a nuisance of themselves is "
         "confronted by Captain Henry Nelson - the heroes have, after all, "
         "been seen hanging around most of the crime scenes. He questions "
         "them individually or in small groups. Keep the interviews quick "
         "and direct.\n\n"
         "Nelson has no reason to trust them and a darkening situation "
         "aboard his ship. He has Psychology 70% and Fast Talk 95%: heroes "
         "trying to fool him with shady facts may find themselves "
         "discreetly followed by stewards.\n\n"
         "CONSEQUENCES. Anyone already under suspicion - brandishing "
         "weapons, fighting, lurking where they should not be - may find "
         "their cabin searched while they are being questioned. Heroes who "
         "attack people without cause can be confined to their cabins "
         "unless they give a good account of themselves.\n\n"
         "THE PRIZE. Convince him of their good intentions - Charm or "
         "Persuade at Hard difficulty - and they gain his trust. "
         "Particularly insightful and honourable heroes may be deputised "
         "to help solve the mystery before Shanghai, which unlocks the "
         "holds and the engine room legitimately.",
         ["npc-captain-nelson"]),

    beat("beat-searching-the-ship", "Searching the Ship",
         "Act 3 - The Pattern",
         "Clues lead below the Third Class deck: the engine compartment "
         "amidships, or the cargo holds in the lowest decks, reached from "
         "a passageway along the keel and from four sealed cargo hatches "
         "on the Third Class deck.\n\n"
         "GETTING DOWN THERE. Without the Captain's permission this is "
         "trespass and can land the heroes in serious trouble. Passengers "
         "may not wander the holds without good reason and are flatly "
         "forbidden the engine rooms unescorted. Past the crew on duty - "
         "Second Mate Gustav Knutsen by day, Junior Engineer Barry "
         "O'Rourke by night - takes Stealth, bribery (Charm, Psychology or "
         "Persuade), or Fast Talk.\n\n"
         "THE HATCHES. Watertight, meant to stop flooding, and all but "
         "impossible to force: Extreme STR, or Hard STR with a crowbar. "
         "Picking the locks takes Locksmith.\n\n"
         "THE RAT PELT. SPOT HIDDEN in the holds: a rat pelt, entirely "
         "intact and pliable. All flesh and organs gone from inside the "
         "skin, which is perfectly tanned and soft. No holes or wounds "
         "other than the natural ones. Small bones rattle inside. Science "
         "(Biology or Zoology) or Art/Craft (Leatherwork) knows that it is "
         "impossible to skin an animal this way, and that a rotted animal "
         "would leave stiff or rotten leather. It looks eaten from the "
         "inside out.\n\n"
         "ESCALATE IT. This is the crawling one feeding - the insect form "
         "leaves only skin, hair and bone fragments. Plant progressively "
         "larger finds as the voyage goes on: a pet dog, then a stowaway. "
         "Call for Sanity rolls as appropriate.\n\n"
         "AMBUSH COUNTRY. The holds and bilges are ideal for Bates, a "
         "summoned monster, or a spell out of the dark.",
         ["clue-rat-pelt", "loc-bilges", "loc-boilers", "loc-hold-1",
          "loc-hold-7"]),

    beat("beat-the-tcho-tcho", "The Tcho-Tcho", "Act 3 - The Pattern",
         "THEIR JOB IS TO BE THE WRONG ANSWER. The tcho-tcho and their "
         "debt to Dr. Soong are a red herring, there to lead suspicious "
         "heroes to the wrong conclusion. Played straight they are neutral "
         "to events and may even help via Soong.\n\n"
         "IF YOU WANT THEM NASTY, they change allegiance from Soong to the "
         "crawling one during the voyage, giving it a team of henchmen for "
         "misdirection, theft or murder.\n\n"
         "THE BARRELS. The tcho-tcho are said to be cannibals, and the "
         "fifty barrels in Hold 6 labelled 'Hawaiian Botanical Specimens' "
         "may in fact hold human corpses. Heroes who stake out Hold 6 or "
         "follow the tcho-tcho to a secret meeting see a barrel opened and "
         "its contents cooked and eaten: Sanity roll (1/1D4).\n\n"
         "THE DEAL. The heroes may witness 'Chad Peterson' meeting the "
         "tcho-tcho in Hold 6, offering them terms - 'protection, and all "
         "the meat you can eat'. It can go either way:\n\n"
         "- THEY ACCEPT and the heroes intervene: Peterson runs at the "
         "first sign of trouble while his new allies attack. Cornered, he "
         "disintegrates into a thousand insects and escapes in a wave of "
         "crawling things that washes over the heroes for 1D4 damage. "
         "Witnessing the change: Sanity roll (1D3/2D6).\n\n"
         "- THEY REFUSE: the crawling one immediately summons a hunting "
         "horror to kill them all. If the heroes stay out of it, the "
         "tcho-tcho die. If they drive off or kill the monster, the "
         "survivors are grateful - and if only one is left he bows and "
         "declares 'Sheng Tsin, your servant now and always', believing he "
         "owes a life debt. Sheng Tsin serves as assistant, cook and "
         "translator, and could become a replacement character.",
         ["npc-tcho-tcho", "npc-hunting-horror", "loc-hold-6"]),

    beat("beat-bunny-takes-a-hostage", "Bunny Takes a Hostage",
         "Act 4 - Climax",
         "Saturday 19 December, First Class dining hall.\n\n"
         "Bates walks in and takes the first person he sees hostage - a "
         "background NPC, someone the heroes know, or one of the heroes "
         "themselves. He rants about the voices in his head and how they "
         "made him do it. He demands to be let off the boat immediately or "
         "he kills the hostage. He is clearly homicidal and deranged.\n\n"
         "RESOLUTION: force, or clever negotiation - an Extreme Persuade "
         "or Fast Talk roll, or a Hard Psychoanalysis roll.\n\n"
         "Play the scene to its conclusion, with Bates dead or captured. "
         "This is a distraction, and it is working: if the heroes stay "
         "occupied here long enough, the first they know of the final test "
         "is a vast whirlpool opening in the ocean.\n\n"
         "SANITY AWARD: preventing Bates from killing the hostage, +1D6.",
         ["npc-bunny-bates", "beat-the-final-test"]),

    beat("beat-the-final-test", "The Final Test", "Act 4 - Climax",
         "Saturday 19 December, Cargo Hold 7.\n\n"
         "The machine combines the blood of the sacrifices with the "
         "inhuman harmonics of Mythos-enchanted pipes tuned to "
         "otherworldly frequencies. Once the crawling one starts to play, "
         "the harmonics immediately begin drawing Mythos entities - and "
         "affect everyone within 100 feet as per the Pipes of Madness "
         "spell. After a few moments the machine plays itself.\n\n"
         "IT DOES NOT WORK. The device sends out waves of energy and music "
         "that draw nearby Mythos entities, but it does not contain or "
         "hold them. Instead of a well of siphoned power, all the crawling "
         "one has built is a machine that enrages whatever hears it and "
         "tells it exactly where to come.\n\n"
         "THE POLYP. Not long after the playing begins, a flying polyp is "
         "summoned from the bottom of the ocean. Rising, it opens a vast "
         "whirlpool; the ship veers, and passengers and crew panic. Then "
         "it launches itself at the hull. It takes TEN ROUNDS to tear its "
         "way through to Cargo Hold 7 unless the heroes stop it.\n\n"
         "THE VILLAIN RUNS. Realising the danger, the crawling one "
         "attempts a Gate spell to Shanghai unless stopped. In its hurry "
         "it leaves the machine running.\n\n"
         "IF THE POLYP REACHES HOLD 7 it uses its wind blast to blow the "
         "pipes apart - along with the crawling one and anyone else nearby "
         "(5D6 damage). With the music stopped it may sink back into the "
         "ocean, throwing a mighty wave against the ship. Or keep it "
         "around a few rounds if the heroes want a fight.\n\n"
         "THE SHIP IS DYING. The damage is tremendous. The hole in the "
         "hull means the Coolidge is taking on water and listing. It will "
         "not be long. Ask the heroes plainly: do they run for the "
         "lifeboats thinking only of themselves, or do they organise, find "
         "trapped passengers, and get women and children into the boats? "
         "Play that out - the Sanity awards at the end depend on it.",
         ["npc-flying-polyp", "npc-crawling-one", "loc-hold-7",
          "ref-dealing-with-the-polyp"]),

    beat("beat-conclusion", "Conclusion", "Act 4 - Climax",
         "The scenario most likely ends with the SS President Coolidge "
         "sinking somewhere off the coast of Japan or China, the crawling "
         "one and its faulty Pipes of Leng destroyed - probably by the "
         "polyp, possibly by the heroes.\n\n"
         "Survivors are rescued within a few hours and a great many "
         "questions are asked. In time the newspapers report a freak wave "
         "that sank the ship. Those who survived know better.\n\n"
         "IF THE CRAWLING ONE GATES OUT it arrives in Shanghai and joins "
         "the Eight Fortunes Mutual Aid Society, a Mythos cult with "
         "tendrils across China. Over the following months or years it "
         "plots revenge on everyone who had a hand in its downfall - a "
         "ready-made recurring villain who comes looking for the heroes.\n\n"
         "SANITY AWARDS:\n"
         "+1D6  Prevent Bates from killing the hostage\n"
         "+1D4  Destroy the aetheric energy device\n"
         "+2D6  Capture or kill the crawling one\n"
         "-1D6  Allow the crawling one to escape\n"
         "+1D20 Defeat the flying polyp\n"
         "+1D10 Try to save as many people from drowning as possible\n"
         "-1D10+2 Leave the ship without regard for others",
         ["ref-sanity-awards"]),
]

# -------------------------------------------------------------- clues


def clue(cid, title, where, desc, roll="", refs=None):
    c = {"id": cid, "title": title, "where": where, "description": desc,
         "found": False}
    if roll:
        c["roll"] = roll
    if refs:
        c["connects_to"] = refs
    return c


data["clues"] = [
    clue("clue-organ-grate-crate", "A 50-pipe organ from Portland",
         "Pier 42, loading / Cargo Hold 7",
         "A massive crate labelled 'Wm. Wood Pipe Organ Co., Inc. of "
         "Portland, Oregon'. Nobody aboard has ordered an organ; the ship "
         "already has instruments in the Music Room. It is bound for Hold "
         "7, which is double-locked.",
         "", ["loc-hold-7"]),
    clue("clue-organ-crate", "The organ crate has been opened repeatedly",
         "Cargo Hold 7",
         "The screws holding the left-hand side panel have been unscrewed "
         "and refitted many times over. Something is being got at inside, "
         "often.",
         "Spot Hidden", ["loc-hold-7", "clue-blood-on-the-crate"]),
    clue("clue-blood-on-the-crate", "Blood on the panel",
         "Cargo Hold 7",
         "Bloodstains on the wooden panel at the left-hand side of the "
         "organ crate - spillage from the sacrifices poured into the "
         "pipes. Dried or fresh depending on how late the heroes get "
         "here.",
         "Hard Spot Hidden without a light source; Regular with one",
         ["loc-hold-7"]),
    clue("clue-green-metal-box", "The green metal box",
         "Pier 42, loading / Cargo Hold 7",
         "A six-foot tall green metal box, delivered to the dock under "
         "armed guard and stowed in Hold 7. Locked: Hard Locksmith, or "
         "Hard STR to force. Inside are engineering diagrams for the "
         "aetheric energy device, plus notes on assembly, materials, costs "
         "and construction, covered in hand-written occult symbols.",
         "Mechanical Repair or Science (Engineering) to recognise "
         "blueprints; Cthulhu Mythos plus two hours' study to grasp that "
         "the device summons entities from beyond the stars in order to "
         "capture their essence",
         ["loc-hold-7"]),
    clue("clue-funeral-supplies", "The 'Funeral Supplies' crate",
         "Pier 42, loading / Cargo Hold 6",
         "A large crate marked 'Funeral Supplies'. It holds the body of a "
         "tcho-tcho who died in San Francisco, being repatriated at Dr. "
         "Soong's expense. A red herring - but a good one.",
         "Spot Hidden", ["loc-hold-6", "npc-tcho-tcho"]),
    clue("clue-empty-clothes", "The empty clothes",
         "Peterson's cabin, A Deck",
         "Socks and shoes on the floor before a chair; suit, vest, shirt "
         "and undershirt nested inside one another like a Russian doll. A "
         "strange bad smell. As though the body inside melted away without "
         "disturbing a fold.",
         "", ["beat-the-empty-suit"]),
    clue("clue-suicide-note-wrong", "The note is wrong",
         "Peterson's cabin (removed as evidence that evening)",
         "The note is at odds with Peterson's happy-go-lucky public face "
         "and his rough-and-tumble life. The handwriting matches "
         "reasonably well - but he always signed himself 'Charles Chadwick "
         "Peterson', 'Charles Peterson', or 'C. C. P.'. Never simply "
         "'Chad'. The 'hollow millionaire' line refers to scions ruined in "
         "the Crash of 1929; Peterson's family came through it largely "
         "intact, so it is not even true.",
         "Art/Craft (Calligraphy or similar) or Hard Spot Hidden to spot "
         "differences against a known sample - obtainable from Virginia "
         "Ridley, or by showing the note to Charles Astor",
         ["handout-suicide-note", "npc-virginia-ridley"]),
    clue("clue-hallanders-lie", "Hallander's story does not hold",
         "First Class hallway, A Deck",
         "He says he heard a noise and came in through an unlocked door. "
         "There was no noise and the door was locked - he picked it, "
         "intending to rob the cabin, and found the chair boiling with "
         "cockroaches.",
         "Psychology to see he is shocked; Intimidate or Persuade to get "
         "him talking; a second Psychology to detect the lies",
         ["npc-albert-hallander"]),
    clue("clue-manifest-gap", "Almacan is not on the manifest",
         "Purser's office",
         "Senor Guiterrez de Almacan appears nowhere among the paying "
         "passengers - not First Class, not anywhere. This is what got "
         "Chief Purser Dungass killed.",
         "Hard Persuade to get a look at the manifest",
         ["npc-almacan", "npc-martin-dungass"]),
    clue("clue-peterson-walking", "Peterson has been seen since he died",
         "Anywhere aboard",
         "Dr. Soong saw Chad Peterson leaving his cabin around 6:00 a.m. "
         "on Sunday 6 December - after the supposed suicide. Phyllis "
         "Barnes has seen him several times and calls the suicide "
         "'hogwash'. She also notes that he got on well with her and "
         "Virginia on the first night out, yet the next morning had no "
         "idea who she was.",
         "", ["npc-dr-soong", "npc-phyllis-barnes"]),
    clue("clue-virginias-unease", "Virginia's woman's intuition",
         "Virginia Ridley, First Class",
         "She saw Chad in the hall around 9:30 p.m. on 5 December, after "
         "dinner. Something about him bothered her - his walk, or his "
         "clothes; he seemed distraught or unhappy. She dismisses it as "
         "intuition and is eager to tell anyone who asks. She has also got "
         "a genuine note from him that morning: 'Virginia, every day I "
         "know I made the right choice. Come sail with me! Your Loving "
         "Chad.'",
         "", ["npc-virginia-ridley", "clue-suicide-note-wrong"]),
    clue("clue-rat-pelt", "The hollow rat",
         "Cargo holds",
         "A rat pelt, entirely intact and pliable, perfectly tanned and "
         "soft, with no holes or wounds except the natural ones. All flesh "
         "and organs gone; small bones rattle inside. It looks eaten from "
         "the inside out.",
         "Spot Hidden to find; Science (Biology or Zoology) or Art/Craft "
         "(Leatherwork) to know that skinning an animal this way is "
         "impossible",
         ["beat-searching-the-ship", "npc-crawling-one"]),
    clue("clue-music-below-decks", "The music comes from below",
         "Anywhere aboard, late at night",
         "Distant, muffled, church-like music - haunting and downright "
         "melancholy. The Music Room is empty. It grows louder and clearer "
         "with every sacrifice.",
         "Listen to hear it; Hard Listen to place it on the lower decks",
         ["beat-distant-music", "loc-hold-7"]),
    clue("clue-kennel-boy", "The kennel boy has seen something",
         "Cargo Hold 5",
         "James Hawthorne, 17, is skittish, mumbling, eyes constantly "
         "searching the floor. He shrieks and bolts into his den at the "
         "sight of a spider or cockroach. Calmed, he talks about the "
         "'creepy crawlies' - he has seen them coming and going, marching "
         "like an army, and can hear them scurrying about the ship. He is "
         "certain they are coming to eat him. He saw the crawling one "
         "dissolve, and it has driven him indefinitely insane.",
         "Psychology to see he is terrified and probably insane; time "
         "spent calming him, or Psychoanalysis, to understand him",
         ["loc-hold-5", "npc-james-hawthorne"]),
    clue("clue-ballast-tank", "The body in the ballast tank",
         "Cargo Hold 4",
         "Phyllis Barnes, decomposing in a ballast tank. Opening the upper "
         "hatch releases a cloud of vile gas.",
         "CON roll or vomit from the reek; Sanity roll 0/1D2 on "
         "discovering the body",
         ["loc-hold-4", "npc-phyllis-barnes"]),
    clue("clue-cold-fire", "The cold fire in the bow hold",
         "Cargo Hold 1",
         "The remains of a small fire made from broken crates, at least 24 "
         "hours old. The ashes are cold and contain charred bits of bone - "
         "the remnants of an impromptu tcho-tcho meal. Nearby, the spent "
         "ashes of an opium pipe.",
         "Spot Hidden to find both; Know or Science (Chemistry or "
         "Pharmacy) to identify the opium",
         ["loc-hold-1", "npc-tcho-tcho"]),
    clue("clue-bates-confession", "Bates' confession",
         "The chapel, 17 December",
         "Bates confesses to Father Alvarez - or to a hero who is a priest "
         "- to the theft of Soong's book, the murder of Wang Ma, and any "
         "other shipboard crime he can think of. He believes he is going "
         "mad and speaks of 'voices' that 'made him do it'. His stories do "
         "not agree with one another and his condition visibly "
         "deteriorates. Afterwards he flees and is dominated again.",
         "", ["npc-bunny-bates", "npc-father-alvarez"]),
    clue("clue-consume-likeness-pattern", "The pattern of the faces",
         "Keeper's clue - for heroes who put it together",
         "Every impossible sighting is a person who has recently died or "
         "vanished. Dungass vanishes and is never found. Peterson dies and "
         "keeps being seen. An unlisted nobleman appears out of nowhere. "
         "One entity is wearing them all, and it needs 48 hours in a new "
         "form before it can speak - which is why 'Peterson' could not "
         "answer his own fiancee, and had to abandon the shape.",
         "Cthulhu Mythos, or simply good detective work",
         ["npc-crawling-one"]),
]

# --------------------------------------------------------------- NPCs


def npc(nid, name, category, role, desc, **kw):
    n = {"id": nid, "name": name, "category": category, "role": role,
         "description": desc}
    n.update(kw)
    return n


STANDIN = ("Keeper-ready standin - the printed scenario keeps these in "
           "Appendix A. Adjust freely.")

data["npcs"] = [
    # ---------------------------------------------------- antagonists
    npc("npc-crawling-one", "The Crawling One", "Antagonist",
        "Luis Fernando de la Montoyo - the villain",
        "A man-shaped mass of living worms, roaches, scorpions and "
        "grave-vermin in a robe and hood. In life a master of a cult "
        "devoted to Azathoth, magically extended into the Spanish "
        "conquest, hanged by the governor of Sonora - after which his "
        "consciousness passed into the vermin that devoured his corpse. "
        "It is not undead: the things that make up its body are alive, so "
        "wounds that kill individual roaches merely inconvenience it while "
        "the swarm breeds replacements.",
        stats={"STR": "65", "CON": "80", "SIZ": "60", "DEX": "50",
               "INT": "90", "POW": "100", "HP": "14", "MP": "20",
               "DB": "0", "Build": "0", "Move": "6",
               "Armor": "see Special"},
        combat=["Bite or grasp 30%, damage 1D4 plus writhing vermin",
                "Weak in a physical fight - it prefers spells and lets "
                "its minions handle mundane matters",
                "Can switch between any of its human forms in a single "
                "combat round"],
        skills="Occult 90%, Cthulhu Mythos 80%, Stealth 60%, "
               "Psychology 55%. Languages: Navaho, courtly archaic "
               "Spanish, Mandarin Chinese, modern Wu Chinese, modern "
               "American English",
        spells="Consume Likeness, Dominate, Mindblast (as used in The "
               "Stolen Book), Mental Suggestion, Gate, Graveyard Kiss "
               "(pulp option), Summon/Bind Hunting Horror, Pipes of "
               "Madness (via the device)",
        special="DISINTEGRATION: if gravely threatened it falls apart "
                "into individual insects that slither away through "
                "floorboards - effectively unkillable by conventional "
                "means unless cornered somewhere it cannot drain away "
                "from.\n\n"
                "CONSUME LIKENESS: it can take the form of any human it "
                "kills and eats. A new form takes 48 HOURS to develop "
                "vocal capability - the reason it had to abandon "
                "Peterson's shape when Virginia expected him to speak.\n\n"
                "TRUE FORM: cannot speak or make any sound at all, and "
                "must communicate in writing. Telegrams are typical.\n\n"
                "FEEDING: leaves only skin, hair and bone fragments - "
                "hence the hollow rat pelt.",
        sanity_loss="1D3/2D6 to see it change or to see its true form",
        stats_note=STANDIN + " POW 100 is fixed by the text (the "
                             "Mindblast opposed roll).",
        forms="Senor Diego Guiterrez de Almacan (primary cover) | Chad "
              "Peterson | Martin Dungass, Chief Purser | Haseye Adikai, a "
              "Navaho teenage girl | Du Zeming, a scarred elderly Chinese "
              "woman | anyone else it kills aboard",
        notes="Finding it should be cat and mouse. Its plan: test the "
              "Pipes of Leng far from prying eyes, then Gate itself and "
              "the device to Shanghai to join the Eight Fortunes Mutual "
              "Aid Society."),

    npc("npc-almacan", "Senor Diego Guiterrez de Almacan", "Antagonist",
        "The crawling one's cover identity",
        "A reclusive Spanish nobleman in an unlisted First Class cabin on "
        "A Deck, one door down from the heroes if they are quartered "
        "there. Keeps to his cabin; can be seen promenading the deck some "
        "evenings. Speaks an antiquated, courtly Spanish.",
        special="He is not on the passenger manifest. Chief Purser "
                "Dungass noticed, went to ask, and died for it.",
        notes="Use him as a face, not a fight. He is the crawling one - "
              "see that entry for stats.",
        stats_note="See The Crawling One."),

    npc("npc-bunny-bates", "Stuart 'Bunny' Bates", "Antagonist",
        "Dominated gangster - the crawling one's hands",
        "Chestnut hair, big hands, a nose broken a few times. Three years "
        "with the Capone Gang in Chicago, then a year hiding in the "
        "Wabasha Street Caves in St. Paul, paying off the police chief to "
        "be left alone. The caves drove him a little crazy and he is "
        "spoiling for action. With Prohibition over he is looking to "
        "maximise profits - or at least find a good supply of opium in "
        "Shanghai.",
        stats={"STR": "70", "CON": "65", "SIZ": "70", "DEX": "60",
               "INT": "55", "APP": "45", "POW": "50", "EDU": "45",
               "HP": "13", "MP": "10", "SAN": "25", "DB": "+1D4",
               "Build": "1", "Move": "8"},
        combat=["Fighting (Brawl) 60%, damage 1D3+1D4",
                ".32 revolver 50%, damage 1D8",
                "Thompson SMG 45%, damage 1D10+2, burst 1/2/5 (if the "
                "Keeper wants real pressure)"],
        skills="Intimidate 65%, Stealth 50%, Locksmith 45%, "
               "Psychology 30%",
        possessions=".32 revolver, a Tommy gun stashed below, stolen crew "
                    "uniform",
        traits="Determined, ambitious, cynical",
        quotes=["\"Why am I goin' ta Japan? Mind yer own business.\"",
                "\"God Almighty, whaddaya take me for, a snitch? Mind yer "
                "own business.\"",
                "\"The choir of angels has commanded me.\""],
        special="DOMINATED from 7 December. The crawling one must recast "
                "Dominate every night (opposed POW roll). Heroes who "
                "bolster his willpower - Hard Persuade or Hard "
                "Psychoanalysis - give him a bonus die to resist.\n\n"
                "The strain drives him into paranoid insanity. On 17 "
                "December he breaks free long enough to confess, then his "
                "mind snaps within the hour and he can no longer resist "
                "the spell at all.",
        stats_note=STANDIN,
        notes="If Bates is killed or brigged early, the crawling one "
              "dominates Steward Martin Aimesworthy instead and he takes "
              "Bates' place in every later scene."),

    npc("npc-flying-polyp", "Flying Polyp", "Monster",
        "The thing the machine calls up",
        "A half-visible horror of impossible geometry that moves on winds "
        "of its own making. Summoned from the bottom of the ocean by the "
        "Pipes of Leng, and enraged rather than controlled by them. Its "
        "rising opens a vast whirlpool that makes the ship veer.",
        stats={"STR": "180", "CON": "125", "SIZ": "180", "DEX": "90",
               "INT": "80", "POW": "80", "HP": "30", "MP": "16",
               "DB": "+4D6", "Build": "5", "Move": "12 flying",
               "Armor": "4"},
        combat=["Tentacle brush - damage resembling desiccation or "
                "extreme windburn",
                "Wind blast 5D6 - shatters glass and hurls furniture "
                "across rooms",
                "Takes 10 rounds to tear through the hull to Hold 7"],
        armor="4 points. Suffers only MINIMUM damage from physical "
              "weapons. Enchanted weapons, fire and electrical attacks do "
              "full damage.",
        special="Because of its absolute rage it remains VISIBLE - which "
                "means everyone aboard sees it.\n\n"
                "If the pipes stop playing it turns around and returns "
                "whence it came, leaving a trail of destruction. If they "
                "keep playing it lays waste to the ship.",
        sanity_loss="1D3/1D20 - rolled by everyone aboard",
        stats_note="POW 80 and Armor 4 are fixed by the text (the Bind "
                   "Flying Polyp opposed roll and the damage rules). "
                   "Remaining characteristics are standard creature "
                   "values.",
        notes="See Reference: Dealing with the Polyp for the three ways "
              "out - destroy the pipes, bind it, or fight it."),

    npc("npc-hunting-horror", "Hunting Horror", "Monster",
        "Optional - summoned to kill the heroes",
        "A ropy black thing that whips through the air, hurting to look "
        "at. Summoned by the crawling one when it wants heroes or "
        "tcho-tcho dead and is willing to accept the attention it draws.",
        stats={"STR": "85", "CON": "70", "SIZ": "90", "DEX": "85",
               "INT": "50", "POW": "70", "HP": "16", "MP": "14",
               "DB": "+1D6", "Build": "2", "Move": "8 / 18 flying",
               "Armor": "2"},
        combat=["Bite 65%, damage 1D8",
                "Crush 40%, damage 2D6 - a coiled attack on a grappled "
                "target"],
        special="Destroyed by direct sunlight. Aboard ship, that means it "
                "must be dealt with before dawn, or driven onto an open "
                "deck.",
        sanity_loss="1D3/1D20",
        stats_note="Standard creature values - check against your "
                   "Malleus Monstrorum if you have it.",
        notes="A heavy hammer. The scenario suggests it for Keepers who "
              "want to give the heroes a seriously hard time, or to wipe "
              "out the tcho-tcho if they refuse the crawling one's "
              "offer."),

    npc("npc-pipes-of-leng", "The Pipes of Leng", "Device",
        "The aetheric energy device - the object of the whole plot",
        "Ostensibly a church pipe organ, covered in additional wires, "
        "fuse-valves, tubes and weird nodules, and largely covered in "
        "blood. Standing close, you can hear an ominous whispery humming. "
        "The pipes themselves were bought, stolen and plundered from "
        "Tibetan, Nepalese and other Himalayan sources and brought to San "
        "Francisco two years ago, where they were combined and tuned to "
        "otherworldly harmonics. A Portland pipe organ company and a small "
        "electrical firm built the mechanism that plays them, in isolation "
        "and complete ignorance of its purpose.",
        stats={"HP": "50", "Armor": "3"},
        special="POWERING IT: five human sacrifices, blood run down into "
                "the pipes.\n\n"
                "PLAYING IT: draws Mythos entities, and affects everyone "
                "within 100 feet as per the Pipes of Madness spell. After "
                "a few moments it plays itself.\n\n"
                "THE FLAW: it summons but does not contain. Everything it "
                "calls arrives enraged and looking for the source of the "
                "noise.\n\n"
                "DESTROYING IT: 50 points of damage against armor 3. "
                "There are no explosives aboard.",
        stats_note="HP 50 and Armor 3 are stated in the text.",
        notes="Stowed in a huge crate in Cargo Hold 7."),

    # ----------------------------------------------------------- crew
    npc("npc-captain-nelson", "Captain Henry Nelson", "Crew",
        "Master of the SS President Coolidge",
        "Stark white hair, a well-groomed mustache, a very firm "
        "handshake. Relentless and efficient. Norwegian, raised in the "
        "French colony of Martinique, so his warm voice carries a strange "
        "accent and his colonial French is excellent. An avid poker "
        "player who knows how to bluff and knows when he is being "
        "bluffed.",
        stats={"STR": "60", "CON": "65", "SIZ": "65", "DEX": "55",
               "INT": "75", "APP": "60", "POW": "70", "EDU": "70",
               "HP": "13", "MP": "14", "SAN": "70", "DB": "0",
               "Build": "0", "Move": "7"},
        skills="Psychology 70%, Fast Talk 95%, Navigate 75%, Persuade "
               "60%, Law 40%, Language (French) 80%",
        combat=["Fighting (Brawl) 45%, damage 1D3",
                "Revolver 55%, damage 1D10 - kept locked in his cabin"],
        traits="Cunning, shrewd, well mannered",
        quotes=["\"Good evening. I trust you are enjoying the voyage?\"",
                "\"What the devil is going on here!\""],
        stats_note=STANDIN + " Psychology 70% and Fast Talk 95% are "
                             "stated in the text.",
        notes="Very little escapes his attention. Heroes who try to fool "
              "him with shady facts get discreetly followed by stewards. "
              "Win his trust with a Hard Charm or Persuade and he may "
              "deputise the heroes - which opens the holds legitimately."),

    npc("npc-hugo-schramm", "Hugo Schramm", "Crew", "First Officer",
        "Light brown hair, a thin face, a pencil-thin mustache. Kept busy "
        "with passenger issues and standing in for the Captain at ship's "
        "functions. When it all gets too much he retreats to his office "
        "and pretends he is not there.",
        traits="Smiles and nods his head a lot",
        quotes=["\"Of course, I'll see to it at once.\"",
                "\"Sorry, didn't hear you out there!\""],
        stats_note=STANDIN,
        notes="Mystified by the disappearances, and under orders to keep "
              "them quiet. Greets First and Special Class at the gangway "
              "on boarding day, and examines Peterson's cabin with Dr. "
              "Hartman."),

    npc("npc-albert-hallander", "Albert Hallander", "Crew",
        "Seaman First Class - thief",
        "Blond and strong, with green eyes. Indonesian-born of Dutch "
        "parentage, with a penchant for petty thievery. He picked the lock "
        "on Chad Peterson's cabin to rob it and found a mass of "
        "cockroaches pouring off the chair.",
        skills="Locksmith 45%, Stealth 50%, Fast Talk 45%, "
               "Persuade 30%",
        traits="Sneaky, pompous, a pretty good liar",
        quotes=["\"I vas passing by, I should have ignored it.\"",
                "\"I don't know anything, I swear to you.\""],
        stats_note=STANDIN,
        notes="He will muddy the water rather than admit attempted theft. "
              "A concerted effort makes him confess - and then the "
              "officers arrest him, which removes a witness."),

    npc("npc-martin-aimesworthy", "Martin Aimesworthy", "Crew",
        "First Class Steward",
        "Tall, blond, clean-shaven. Attends to First Class needs. "
        "Reliable, honest and dutiful. Befriended, he will share whatever "
        "suspicions he has picked up.",
        traits="Loyal and attentive",
        quotes=["\"It's no bother at all. Let me take care of that.\"",
                "\"Well, it's a right palaver!\""],
        stats_note=STANDIN,
        notes="He takes the suicide note as evidence on the evening of 6 "
              "December. IMPORTANT: if Bates is captured or killed, the "
              "crawling one casts Dominate on Aimesworthy and uses him in "
              "Bates' place from then on."),

    npc("npc-martin-dungass", "Martin Dungass", "Victim",
        "Chief Purser - dead before the scenario starts",
        "Consumed by the crawling one on the night of 5-6 December after "
        "he went to ask an unlisted passenger some questions. His body is "
        "never found.",
        stats_note="No stats needed - he is dead on page one.",
        notes="The crew's consensus is that he hit the bottle and is "
              "sleeping it off below decks; there are rumours of trouble "
              "with his wife. Honolulu police rule it accidental "
              "drowning."),

    npc("npc-erik-hartman", "Dr. Erik Hartman", "Crew", "Ship's Doctor",
        "Examines the scene in Peterson's cabin with First Officer "
        "Schramm, and keeps his findings to himself as ordered.",
        skills="Medicine 60%, First Aid 70%, Science (Biology) 45%",
        stats_note=STANDIN,
        notes="A useful gate for heroes with medical skills - a "
              "professional courtesy is an easy way into the cabin."),

    npc("npc-other-crew", "The rest of the crew", "Crew",
        "Names to drop as needed",
        "Chief Radioman Marco Borrely (nine radio and telegraph operators "
        "under him) | Chief Engineer Oliver Grossmann | Engineer's Mate "
        "Wilhelm Schubert | Fireman Robert Reid, one of twenty junior "
        "engineers | Head Chef Anthony Deplace | Wine Steward Phillipe "
        "d'Alsace | Seaman First Class Hank Henson, who guards Peterson's "
        "door | Arthur Benedict Carmel, head of fifty-four waiters | "
        "Ephraim 'Fizzy' Walters, wisecracking head bartender | Second "
        "Mate Gustav Knutsen, on the cargo hatches by day | Junior "
        "Engineer Barry O'Rourke, on them by night | Raymond Hickler, "
        "conductor of the Pacific Jazz Orchestra | Arthur Pendury, groom "
        "to the horses in Hold 5",
        stats_note="Background - use ordinary sailor or professional "
                   "profiles as needed.",
        notes="315-350 crew all told. Repeat familiar faces so the "
              "players get to know a few regulars."),

    # ----------------------------------------------- first class pax
    npc("npc-chad-peterson", "Chad Peterson", "Victim",
        "Wealthy fiance - consumed on the first night",
        "Charles Chadwick Peterson of New York. Impeccably dressed, "
        "thoroughly drunk on the gangway, greeting everyone he collides "
        "with. Devoured in his cabin on the night of 5 December; from then "
        "on, everyone who sees 'Peterson' is seeing the crawling one.",
        quotes=["\"Chad Peterson from New York, delighted to make your "
                "acquaintance.\""],
        special="He signed himself Charles Chadwick Peterson, Charles "
                "Peterson, or C. C. P. - never 'Chad'. The suicide note is "
                "signed 'Chad'.",
        stats_note="No stats needed - dead by the end of the first "
                   "night.",
        notes="The genuine note he left Virginia on the morning of the "
              "6th reads: 'Virginia, every day I know I made the right "
              "choice. Come sail with me! Your Loving Chad.' Compare it "
              "with the suicide note."),

    npc("npc-virginia-ridley", "Virginia Ridley", "Passenger - First Class",
        "Dilettante and flapper - Peterson's fiancee",
        "Chestnut hair, curvy, a dangerous strut. Born in Shanghai and "
        "raised by an amah, in the States since her fifteenth birthday. A "
        "notorious New York flapper whose family lost a great deal in the "
        "Crash. She talked Chad Peterson into coming to China with her and "
        "is eager to arrive for Chinese New Year and show him the city of "
        "her childhood.",
        stats={"STR": "45", "CON": "55", "SIZ": "50", "DEX": "70",
               "INT": "60", "APP": "80", "POW": "60", "EDU": "60",
               "HP": "10", "MP": "12", "SAN": "60", "DB": "0",
               "Build": "0", "Move": "9"},
        combat=["Shotgun (skeet, over-and-under) 55%, damage 4D6/2D6/1D6"],
        skills="Charm 70%, Dance 65%, Firearms (Shotgun) 55%, Language "
               "(Wu Chinese) 30%",
        traits="Flirty, enjoys guns and thrills, a great dancer",
        quotes=["\"I finally got the big lug to come to China and he skips "
                "out on me!\"",
                "\"You'll find him, won't you? You've got to find him.\""],
        stats_note=STANDIN,
        notes="Separate cabins from Peterson on the Presidential Deck. "
              "She has not spoken to him since dinner around 7:00 p.m. on "
              "5 December - the figure at 9:30 p.m. was already the "
              "crawling one, and something about him bothered her. From 9 "
              "December she shoots skeet off the stern to work off her "
              "nerves until the stewards ask her to stop. A candidate for "
              "the fifth sacrifice."),

    npc("npc-charles-astor", "Charles Winston Astor", "Passenger - First Class",
        "Rich businessman - Peterson's friend",
        "Good teeth, a sharp chin, greying hair. One of the New York "
        "Astors, and he rarely lets anyone forget it. Made his money the "
        "old-fashioned way - he inherited it. Graduated solidly mid-class "
        "from Yale in 1895 and has run the family manufacturing concerns "
        "in Massachusetts and along the Hudson ever since. Travelling in "
        "the President's Suite, the finest cabin aboard, with his son "
        "James (25), his butler Walker (38), and his daughter Elizabeth "
        "Anne (19).",
        stats={"STR": "55", "CON": "55", "SIZ": "70", "DEX": "50",
               "INT": "60", "APP": "55", "POW": "55", "EDU": "70",
               "HP": "12", "MP": "11", "SAN": "55", "DB": "+1D4",
               "Build": "1", "Move": "6"},
        combat=["Rifle/Shotgun 55% - shoots skeet off the stern deck"],
        skills="Credit Rating 95%, Persuade 55%, Intimidate 50%, "
               "Accounting 50%",
        traits="Assertive, phony, tells a fine dirty joke, can shoot and "
               "hunt",
        quotes=["\"Chip was a great friend of mine, a close friend, and he "
                "would never do something like this.\"",
                "\"I don't understand it. I just don't.\""],
        stats_note=STANDIN,
        notes="Perfectly friendly, and not especially fond of making "
              "friends below Special Class. Befriended, he can put in a "
              "good word with the Captain if the heroes land in trouble. "
              "He confirms Peterson's engagement to Virginia and insists "
              "'Chip' was not the type to throw himself out a porthole. "
              "After Honolulu he backs that with $1,000 cash for useful "
              "information."),

    npc("npc-alex-hubbard", "Alex Hubbard", "Passenger - First Class",
        "Big game hunter",
        "Overweight, balding, muscular. Renowned for tracking down and "
        "killing anything worth crossing an ocean for. His current target "
        "is the black pygmy rhino of Siam, which few Westerners have seen "
        "and fewer have mounted in their smoking rooms. Travelling with no "
        "plan beyond stops at Yokohama, Shanghai and Macao before Bangkok "
        "- the 'fleshpots of Asia' tour, as he calls it.",
        stats={"STR": "70", "CON": "65", "SIZ": "80", "DEX": "55",
               "INT": "55", "APP": "45", "POW": "55", "EDU": "55",
               "HP": "14", "MP": "11", "SAN": "55", "DB": "+1D4",
               "Build": "1", "Move": "6"},
        combat=["Winchester rifle with scope 70%, damage 2D6+4",
                "Over-and-under shotgun 60% (birdshot)"],
        skills="Track 65%, Natural World 55%, Survival 50%, "
               "Intimidate 45%",
        possessions="Winchester rifle and scope, a skeet-shooting "
                    "over-and-under shotgun with birdshot, and a copy of "
                    "Baedeker's Guide to Siam and Indochina",
        traits="Ruthless, raconteur, chatty, territorial",
        quotes=["\"A man who doesn't hunt isn't much of a man.\"",
                "(after a few drinks) \"Sure, I'd like to mount her in my "
                "trophy case.\""],
        stats_note=STANDIN,
        notes="Besides the rhino, he has his sights on Virginia Ridley "
              "and consoles her in hopes of drawing her affections. His "
              "luggage is the most convenient source of firepower aboard "
              "for heroes who need a gun."),

    npc("npc-dr-soong", "Dr. Soong", "Ally",
        "Occult and Mythos researcher",
        "White hair and beard, frail, slightly stooped, over 70. "
        "Comfortable in traditional or Western dress and happy to discuss "
        "herbal remedies, Taoism or religion with equal pleasure. An "
        "ardent communist until recently, serving the workers of Shanghai "
        "as a traditional doctor, a confidant and a collaborator - though "
        "he has decided to travel in style, First Class on the Boat Deck. "
        "Born in Shanghai; his native language is Wu Chinese, his Mandarin "
        "broken, his English much better.",
        stats={"STR": "35", "CON": "45", "SIZ": "50", "DEX": "40",
               "INT": "85", "APP": "55", "POW": "75", "EDU": "85",
               "HP": "9", "MP": "15", "SAN": "45", "DB": "-1",
               "Build": "-1", "Move": "4"},
        skills="Occult 80%, Cthulhu Mythos 25%, Medicine 70%, Science "
               "(Pharmacy) 65%, History 60%, Language (Mandarin) 40%, "
               "Language (English) 70%",
        traits="Serious, scholarly, morbid, and very, very smart",
        quotes=["\"This is my servant, Wang Ma. He will answer your "
                "questions. Please excuse me.\"",
                "\"The incident is most unfortunate. Regrettable and "
                "unfortunate.\""],
        possessions="A chest of herbal medicines, a small doctor's bag, "
                    "and (until 7 December) a copy of the Book of Red "
                    "Jade",
        stats_note=STANDIN,
        notes="BACKGROUND: he struggled for years against the opium "
              "trade, Western exploitation and Nationalist propaganda, "
              "made unsavoury friends and acquired a taste for opium "
              "himself without falling into deep addiction. In 1927 "
              "Nationalist thugs murdered his wife and two of his three "
              "sons; he left for the United States with his surviving son "
              "and daughter and took up Mythos research full time.\n\n"
              "AFTER 7 DECEMBER he mentions that he saw Chad Peterson "
              "leaving his cabin around 6:00 a.m. on Sunday the 6th - "
              "after the supposed suicide.\n\n"
              "KEEPER NOTE: do not let him answer everything or save the "
              "day. He is old and frail. Use him to point the heroes in "
              "the right direction, and to unstick them when they "
              "flounder. He is also a candidate for the fifth sacrifice."),

    npc("npc-wang-ma", "Wang Ma", "Ally",
        "Dr. Soong's manservant - murdered 7 December",
        "Short and ugly, with a broad chest, pallid skin and a wicked "
        "grin. He takes care of the doctor's clothes, his chest of herbal "
        "medicines, and his personal safety. He is a tcho-tcho, and the "
        "leader of a small band of them booked in Steerage who serve "
        "Soong to discharge a debt - the details of which are yours to "
        "invent. Something along the lines of Soong having saved a number "
        "of tcho-tcho lives.",
        stats={"STR": "65", "CON": "70", "SIZ": "45", "DEX": "60",
               "INT": "60", "APP": "30", "POW": "55", "EDU": "30",
               "HP": "11", "MP": "11", "SAN": "45", "DB": "0",
               "Build": "0", "Move": "8"},
        combat=["Fighting (Brawl) 55%, damage 1D3",
                "Knife 60%, damage 1D4+2"],
        skills="Stealth 60%, Spot Hidden 50%, Survival 55%",
        traits="Steady, brave, suspicious",
        quotes=["\"Master Soong say, no.\"", "\"Master Soong not say.\""],
        stats_note=STANDIN,
        notes="Killed on 7 December defending the Book of Red Jade, and "
              "buried at sea at 3:00 p.m. on the 8th. He is replaced at "
              "Soong's side by Lo Mai, using the same statistics; if Lo "
              "Mai dies too, further tcho-tcho step up in turn."),

    # ---------------------------------------------- special class pax
    npc("npc-phyllis-barnes", "Phyllis Barnes", "Passenger - Special Class",
        "Music teacher and good egg - sacrifice 3",
        "Heavyset, hair in a bun, a twinkle in her eyes, short "
        "fingernails. Reddish hair and a bright smile are her best "
        "features. She plays piano, organ, harp and flute and sings a "
        "smooth alto, gives impromptu performances almost daily at lunch "
        "or dinner, and teaches music to the wealthier children aboard - "
        "including the Astor children. She also does charity work in "
        "Steerage, teaching music, mathematics and rudimentary German to "
        "young children. An old maid, young at heart, robustly built but "
        "not in the best of health, and a bit of a nosy parker.",
        stats={"STR": "45", "CON": "45", "SIZ": "65", "DEX": "45",
               "INT": "60", "APP": "45", "POW": "60", "EDU": "65",
               "HP": "11", "MP": "12", "SAN": "60", "DB": "0",
               "Build": "0", "Move": "5"},
        skills="Art/Craft (Music) 75%, Listen 55%, Charm 50%, "
               "Psychology 40%",
        traits="Racist and xenophobic, especially around Chinese people, "
               "as well as a devout Christian",
        quotes=["\"I'll be in the music room if anyone needs me.\"",
                "\"Well, I'm happy to help but I'm not sure there's much I "
                "can do.\""],
        stats_note=STANDIN,
        notes="She claims to have seen 'violent fights among the "
              "Chinamen' more than once - a lie she tells to make herself "
              "more interesting. Asked about Peterson she says he behaved "
              "strangely: they got on well the first night out, yet the "
              "next morning he had no idea who she was. She calls the "
              "suicide 'hogwash' because she has seen him several times "
              "since.\n\nShe dies on 13 December, following the music to "
              "the cargo hatches. Her body goes into a ballast tank in "
              "Hold 4."),

    npc("npc-takishi-suroda", "Takishi Suroda", "Passenger - Special Class",
        "Nosey businessman - sacrifice 1",
        "A muscular yet slight frame, a wide smile, excited eyes. A "
        "jewellery dealer who has just concluded a business venture in San "
        "Francisco that appears to have gone well, and is on his way to a "
        "Honolulu vacation. Making the most of his time aboard to relax "
        "and enjoy the trip.",
        skills="Appraise 60%, Charm 45%, Persuade 45%",
        traits="Likes to know everyone else's business, a bit of a gossip",
        quotes=["\"Hey, what's that you've got there?\"",
                "\"Hey, I've been looking for you! Where you been "
                "hiding?\""],
        stats_note=STANDIN,
        notes="Likely a male hero's cabin mate in Special Class. "
              "Deliberately a blank slate - use him to help, to hinder, to "
              "hand out red herrings, or to be a nuisance. He is due to "
              "disembark at Honolulu on 10 December; instead he is the "
              "first sacrifice, and his cabin mate finds the bed not "
              "slept in."),

    # ------------------------------------------------ third class pax
    npc("npc-father-alvarez", "Father Raphael Alvarez", "Ally",
        "Jesuit missionary priest",
        "Black hair and mustache, rough skin, hands callused from years in "
        "the church gardens. A Jesuit originally from Mexico with a good "
        "track record of investigating the paranormal on behalf of Rome. "
        "Reassigned to Peking to report on the status of Christians in the "
        "Chinese capital - and secretly to search for information on the "
        "ancient fertility cults of the Mongolian deserts. He knows enough "
        "of the Cthulhu Mythos to have nightmares.",
        stats={"STR": "55", "CON": "60", "SIZ": "60", "DEX": "55",
               "INT": "70", "APP": "55", "POW": "75", "EDU": "80",
               "HP": "12", "MP": "15", "SAN": "70", "DB": "0",
               "Build": "0", "Move": "7"},
        skills="Occult 55%, Cthulhu Mythos 10%, Psychology 60%, Persuade "
               "55%, History 50%, Library Use 60%, Language (Latin) 70%, "
               "Language (Chinese) 40% and improving fast",
        traits="Kind, logical, curious, perceptive, haunted",
        quotes=["\"I would investigate the sailors; if the suicide is, in "
                "fact, a murder, they might be responsible.\"",
                "\"Bless you, my child. Bless us all.\""],
        stats_note=STANDIN,
        notes="He prefers to say very little unless directly confronted "
              "with proof of Mythos activity, and asks more questions "
              "than he answers. Happy to give confession, lead Mass and "
              "minister to anyone aboard; unwilling to talk about himself "
              "or his orders from Rome. He has spent recent weeks "
              "teaching himself Chinese from a book, with hands-on "
              "tutoring from the stewards.\n\nHe hears Bates' confession "
              "on 17 December and takes it to the Captain. A strong "
              "candidate for a replacement player character - and for the "
              "fifth sacrifice."),

    npc("npc-miles-hardaway", "Miles Hardaway", "Passenger - Third Class",
        "Pushy reporter - sacrifice 2",
        "Greased-back hair, slight stature, piercing eyes. A San Francisco "
        "Chronicle reporter aboard to write up the voyage and cover "
        "business and trade opportunities between the U.S. and China.",
        skills="Fast Talk 65%, Persuade 55%, Library Use 55%, "
               "Spot Hidden 50%",
        traits="Nosey, a gossip, and rather pushy",
        quotes=["\"Say, tell me about yourself.\"", "\"Can I get a "
                "quote?\""],
        stats_note=STANDIN,
        notes="He makes a meal of the Peterson case, playing up the "
              "'locked room' angle as a real-life Sherlock Holmes mystery "
              "and wiring speculation ashore. Either a running nuisance or "
              "pure background, as you prefer. He is lured to Almacan's "
              "cabin and killed on 12 December."),

    npc("npc-james-hawthorne", "James Hawthorne", "Passenger - Crew",
        "Kennel boy, 17 - the witness who broke",
        "Skittish, mumbling, eyes constantly searching the floor around "
        "him. Shrieks and bolts into his little den at the sight of a "
        "spider or a cockroach. He looks after more than 30 dogs, 14 cats, "
        "20 seasick cattle and five thoroughbred horses in Hold 5.",
        stats_note=STANDIN,
        notes="He saw the crawling one dissolve into a mass of wriggling "
              "horrors in the hold, and it has driven him indefinitely "
              "insane. Calmed - or reached with Psychoanalysis - he talks "
              "about the 'creepy crawlies' he has seen coming and going, "
              "marching like an army, and how he can hear them scurrying "
              "about the ship, certain they are coming to eat him.\n\n"
              "If the heroes do not get down to the holds until late in "
              "the voyage, he will be gone - taken and sacrificed."),

    npc("npc-tcho-tcho", "The Tcho-Tcho", "Red herring",
        "Lo Mai and six labourers, booked in Steerage",
        "A small clan in Dr. Soong's retinue, discharging a debt to him. "
        "They oversee fifty barrels labelled 'Hawaiian Botanical "
        "Specimens' and gather privately in the bow hold, away from the "
        "noise of Steerage. Sinister, insular, and - in this scenario - "
        "not the villains.",
        stats={"STR": "60", "CON": "65", "SIZ": "45", "DEX": "65",
               "INT": "55", "APP": "30", "POW": "50", "EDU": "30",
               "HP": "11", "MP": "10", "SAN": "40", "DB": "0",
               "Build": "0", "Move": "8"},
        combat=["Fighting (Brawl) 50%, damage 1D3",
                "Knife 55%, damage 1D4+2"],
        skills="Stealth 65%, Survival 60%, Spot Hidden 45%",
        stats_note=STANDIN,
        notes="THEIR PURPOSE IS TO BE THE WRONG ANSWER. Played straight "
              "they are neutral and may help through Soong. Played nasty "
              "they can switch allegiance to the crawling one mid-voyage. "
              "Heroes searching Hold 1 at night meet them, and they do "
              "not take kindly to it unless the heroes can show they work "
              "with Dr. Soong.\n\nLo Mai steps into Wang Ma's place after "
              "the murder. If the tcho-tcho refuse the crawling one's "
              "offer and the heroes save them, the sole survivor Sheng "
              "Tsin declares himself their servant for life."),

    npc("npc-background-passengers", "Background passengers", "Background",
        "Names to drop as required",
        "FIRST CLASS: Xin Yu, Yan Zou, Sissy McPatrick, Neal Westner, "
        "Deliah Conningway, Rupert Cocksure.\n\n"
        "SPECIAL CLASS: Ru Li, Shen Liu, Arthur Sellkirk, Maud Rendox, "
        "Jasper Conway, Lottie Unser.\n\n"
        "THIRD CLASS: Peng Chen, Fu Wang, Lan Wu, Daiyu Tang, Billy "
        "Royston, Ethel Rind, Paul Scott.\n\n"
        "THIRD CLASS CABIN MATES: the brothers Po Liang and Po Hau, Pai "
        "Gow dealers hired for Casino Night, and US Navy crewman Olaf "
        "Gustavsen of the minesweeper Abilene.\n\n"
        "ENTERTAINERS: jazz and cabaret singers Rebecca McCormick and "
        "Antonio Portaluppi.",
        stats_note="Background - no stats needed.",
        notes="678 passengers aboard. The other passengers have almost "
              "nothing better to do than gossip and speculate, and most "
              "won't mind doing it at length with the heroes."),
]

# ----------------------------------------------------------- handouts

data["handouts"] = [
    {
        "id": "handout-suicide-note",
        "title": "Handout 1: Chad Peterson's suicide note",
        "found": False,
        "description":
            "Found on the desk in Peterson's cabin, and removed as "
            "evidence by Steward Aimesworthy that evening.\n\n"
            "READ TO THE PLAYERS:\n\n"
            "  MY LIFE HAS BEEN A LIE BUILT ON MY FATHER'S MONEY.\n"
            "  DESPITE MY OUTWARD SEEMING, I AM A HOLLOW MILLIONAIRE.\n"
            "  WITHOUT MONEY, I KNOW MYSELF INADEQUATE TO MAKE WHAT I\n"
            "  WANTED OF MY LIFE. FAREWELL, WORLD, I GO TO A BETTER\n"
            "  PLACE.\n"
            "                                              CHAD\n\n"
            "WHAT IS WRONG WITH IT: the signature. He signed himself "
            "Charles Chadwick Peterson, Charles Peterson, or C. C. P. - "
            "never simply 'Chad'. The handwriting matches reasonably "
            "well; spotting the differences takes an Art/Craft "
            "(Calligraphy or similar) roll, or a Hard Spot Hidden, "
            "against a known sample from Virginia Ridley or Charles "
            "Astor. And 'hollow millionaire' means a scion ruined in the "
            "Crash of 1929 - which Peterson was not.",
        "connects_to": ["clue-suicide-note-wrong", "beat-the-empty-suit"],
    },
    {
        "id": "handout-book-of-red-jade",
        "title": "Handout 2: The Book of Red Jade",
        "found": False,
        "description":
            "A debauched work of Mythos knowledge that provokes shudders "
            "among all good Confucians and students of the Classics. It "
            "blasphemes not just the work of Lao Tzu but Taoism, the "
            "Emperor, and the entire divine status of the Manchu "
            "dynasty.\n\n"
            "DESCRIPTION: long and narrow - 344 woodblock-printed pages, "
            "6 inches wide and 12 tall, in courtly Mandarin Chinese. The "
            "ink is a bright ox-blood red, with marginal notes and "
            "woodcut illustrations in black. Blue silk endpapers with a "
            "disquieting shimmer under light, and three intricately "
            "knotted red silk bookmarks. Calfskin over thin but extremely "
            "hard wooden boards, the leather coated in a slightly gritty "
            "waterproof varnish said to resemble tarnished copper or dark "
            "green soapstone. A brass three-clawed dragon with a single "
            "eye decorates each cover, affixed beneath the varnish.\n\n"
            "RARITY: only thirty-three copies are believed to have been "
            "made; the Chinese authorities destroyed most in the 1830s. "
            "Several went to the Philippines and the United States with "
            "immigrant Chinese cultists. One is believed to be in the "
            "British Museum.\n\n"
            "HISTORY: written in prison or under duress during the Manchu "
            "dynasty, attributed to Zhou Lo Wei, the Warlord of One "
            "Hundred Masteries. Zhou first appears in Chinese records as "
            "an alchemist from the Mongolian provinces in the 1830s, and "
            "is better known after arriving in Peking in 1847, where he "
            "became an opium addict and a scholar of the Classics, "
            "attracting a sect of sycophants and reformers who called "
            "themselves the Sevenfold Hidden Path Clan - anti-religious "
            "zealots, extortionists and educated criminals who terrified "
            "the capital for years. Zhou attained a position at the "
            "Imperial Court in 1850 and abused it grossly until 1861, "
            "when he was seized and tried for trespass against the "
            "Imperial city, witchcraft, and crimes against public order. "
            "He was beheaded in Peking in 1862. Accounts of his burial "
            "are confused - another body may have been substituted, or he "
            "dissolved into insects at the execution ground.\n\n"
            "IT IS ENTIRELY POSSIBLE, EVEN LIKELY, THAT ZHOU AND THE "
            "CRAWLING ONE ARE THE SAME.\n\n"
            "MYTHOS KNOWLEDGE: the process of ghoul transformation; "
            "summoning and binding a flying polyp; the history of the "
            "Mongols and Manchus with respect to star vampires and mi-go; "
            "and a dream sequence referring directly to Azathoth and "
            "Nyarlathotep. It also paraphrases material from the Seven "
            "Cryptical Books of Hsan.\n\n"
            "GAME STATISTICS: Mandarin Chinese. Sanity loss 1D10. Cthulhu "
            "Mythos +4/+8. Mythos Rating 36. Eleven weeks for full study; "
            "an initial skim reading takes 6 hours.\n\n"
            "SUGGESTED SPELLS: Cause/Cure Blindness, Consume Likeness, "
            "Dominate, Flesh Ward, Powder of Ibn-Ghazi, Summon/Bind "
            "Flying Polyp, Words of Power.\n\n"
            "NOTE: heroes without Mandarin Chinese might, on recovering "
            "the book for Dr. Soong, persuade the good doctor to "
            "translate sections - or teach them a spell as a reward. Bind "
            "Flying Polyp is the one that matters on 19 December.",
        "connects_to": ["beat-the-stolen-book", "npc-dr-soong",
                        "ref-dealing-with-the-polyp"],
    },
    {
        "id": "handout-genuine-note",
        "title": "Handout 3: The genuine note to Virginia",
        "found": False,
        "description":
            "Left for Virginia Ridley on the morning of 6 December, in "
            "Peterson's real hand.\n\n"
            "READ TO THE PLAYERS:\n\n"
            "  Virginia, every day I know I made the right choice.\n"
            "  Come sail with me!\n"
            "                                    Your Loving Chad\n\n"
            "Use it as the known sample against which the suicide note is "
            "compared - and as the small heartbreak that makes the "
            "suicide ruling ring false.",
        "connects_to": ["clue-suicide-note-wrong", "npc-virginia-ridley"],
    },
]

# ---------------------------------------------------------- locations


def loc(lid, title, deck, desc, refs=None):
    d = {"id": lid, "title": title, "deck": deck, "description": desc,
         "visited": False}
    if refs:
        d["connects_to"] = refs
    return d


data["locations"] = [
    loc("loc-first-class", "First Class",
        "Boat Deck, A, B and C Decks",
        "214-307 passengers in outside cabins and suites along the upper "
        "decks and forward. Four suites have their own bath and toilet; 32 "
        "staterooms share a bath; most of the rest are single cabins with "
        "private baths, and the cheapest First Class tickets are twin "
        "cabins with a shared shower. All have private heaters, full "
        "carpeting and lavish light fixtures, paintings and furnishings. "
        "No bunk beds.\n\n"
        "The First Class Dining Room is on C Deck amidships, reached down "
        "an ornate grand stairwell past a large mural of the countries "
        "served by Dollar Line ships, with a private dining room off the "
        "main hall.\n\n"
        "First Class has its own crewmen who guard their passengers' "
        "privileges jealously."),
    loc("loc-special-class", "Special Class", "B Deck",
        "133 rooms just behind the First Class accommodation - smaller, "
        "with shared bathrooms, but used as First Class cabins when demand "
        "warrants. 23 staterooms sleep three, 16 sleep four; twin singles "
        "with fold-out bunks over one or both. The Special Class dining "
        "room is on C Deck, a little further aft than the First Class "
        "hall."),
    loc("loc-third-class", "Third Class", "C Deck, aft",
        "170 accommodations, none of them exterior cabins. Spartan 3- and "
        "4-bunk cabins sleeping six or eight, with fixed rather than "
        "folding bunks. Each cabin has a mirror, toilet and washbasin, and "
        "shares a communal bathroom. The Third Class dining room is right "
        "at the stern on C Deck.\n\n"
        "The four sealed cargo hatches are on this deck - which is why "
        "heroes end up down here."),
    loc("loc-steerage", "Steerage", "D Deck, aft",
        "Up to 380 people in six large rooms of 60 berths each, with no "
        "privacy, by the noisy rudder engines and the turbo-electric "
        "engines that drive the propellers. Doubles as cargo space from "
        "time to time. Steerage uses the Third Class dining room after "
        "Third Class has eaten.\n\n"
        "Furthest from the ship's centre of balance, so every wave tosses "
        "it further than anywhere else aboard."),
    loc("loc-amenities", "Amenities and entertainment", "Upper decks",
        "MUSIC ROOM (B Deck): pianos, harp and other instruments. Phyllis "
        "Barnes performs and teaches here.\n"
        "SMOKING ROOMS (A and B Decks): poker, canasta and bridge. The "
        "First Class room has a Rip Van Winkle tapestry, walnut "
        "armchairs, green settees, game tables, green and reddish rubber "
        "tiles, a green marble fireplace with an electric fire, and a "
        "stained-glass 'Lady and the Unicorn' above it. The Special Class "
        "room on B Deck has a Sierra Nevada painting, a portrait of "
        "President Coolidge, maroon chairs and wooden card tables with "
        "recessed drink holders and built-in glass ashtrays.\n"
        "GRAND SALON: Raymond Hickler and His Pacific Jazz Orchestra "
        "every night. The Presidential Dance Orchestra plays the ballroom "
        "at 9:00 p.m. sharp.\n"
        "CONTINENTAL LOUNGE (First Class, A Deck): a dome of 3,000 pieces "
        "of glass and blue velvet seats. Films and newsreels Friday and "
        "Saturday - The Persian Pasha and Chaplin's City Lights before "
        "Honolulu; At the Kentucky Derby and It Pays to Advertise, "
        "starring Louise Brooks, after. Also the finer of the ship's two "
        "bars.\n"
        "HAWAIIAN SALOON (C Deck): the coarser bar. Both are well stocked "
        "with liquor, champagne, wines including sake, and San Francisco "
        "and Yokohama beer.\n"
        "FIRST CLASS LIBRARY AND WRITING ROOM (A Deck): a mural of "
        "deep-sea marine life and roughly 4,000 volumes - fiction, "
        "history, business, humanities reference and periodicals.\n"
        "POOLS: two, open 10:00 a.m. to 6:00 p.m. with lifeguards. The "
        "Special and Third Class pool over Hold 6 opens only in warmer "
        "water near Hawaii.\n"
        "ALSO: a gymnasium, a barbershop, a soda fountain, two electric "
        "lifts, a darkroom for photographers, a chapel, and an onboard "
        "printing press that announces events and prints invitations. The "
        "entire ship is air-conditioned, which is unusual for 1931."),
    loc("loc-bilges", "The bilges", "Below the holds",
        "Ballast water, huge fuel tanks full of diesel oil, and little "
        "else. Rats and shipboard vermin are the extent of the creepiness "
        "available - unless the crawling one has been forced into its "
        "vermin form, in which case this is where it hides out.",
        ["npc-crawling-one"]),
    loc("loc-boilers", "Engine room and boilers", "Amidships, below",
        "An inferno worked by 45 men in 24-hour shifts of 15. They "
        "regulate the engines, repair turbines and boilers, and manually "
        "work the complex piping feeding diesel oil to the boilers and "
        "electricity to the turbo-electric engines.\n\n"
        "Heroes entering are confronted unless they have made successful "
        "Stealth rolls or talked a crewman into giving them a tour. The "
        "engine crew removes anyone who should not be there, notifies the "
        "senior crew, and holds interlopers until the Captain can attend "
        "to them. Only an Extreme Fast Talk or Persuade convinces the "
        "engineers that the heroes have permission to be down here "
        "alone."),
    loc("loc-hold-1", "Cargo Hold 1 - the bow hold", "Lowest deck, forward",
        "ALWAYS UNLOCKED. The meeting place of the tcho-tcho for their "
        "private gatherings, away from the noise of Steerage.\n\n"
        "SPOT HIDDEN finds two things: the remains of a small fire made "
        "from broken crates, at least 24 hours cold, with charred bits of "
        "bone in the ashes; and the spent ashes of an opium pipe (Know or "
        "Science (Chemistry or Pharmacy) to identify).\n\n"
        "Heroes searching here at night meet the tcho-tcho, who do not "
        "take kindly to the intrusion unless the heroes can demonstrate "
        "that they work with Dr. Soong.",
        ["clue-cold-fire", "npc-tcho-tcho"]),
    loc("loc-hold-2", "Cargo Hold 2 - passenger luggage", "Lowest deck",
        "LOCKED. Well over 2,700 articles: steamer trunks, lockers, "
        "safes, heavy satchels, boxes wrapped in brown paper and twine, "
        "hat cases, carefully crated urns and glassware, two dozen cases "
        "of French wine, and enough musical instruments for a small "
        "symphony orchestra.\n\n"
        "Passenger weapons and guns are stored here - including Alex "
        "Hubbard's Winchester and shotgun.",
        ["npc-alex-hubbard"]),
    loc("loc-hold-3", "Cargo Hold 3 - refrigerated", "Lowest deck",
        "Locked by a handle that turns easily. Perishables - meat, fruit, "
        "milk and other foodstuffs - plus flowers, scientific samples and "
        "medical supplies. The cooks visit often to resupply their "
        "pantries, which makes this the easiest hold to be seen in "
        "legitimately."),
    loc("loc-hold-4", "Cargo Hold 4 - crates and ballast tanks",
        "Lowest deck",
        "UNLOCKED. More than 2,000 wooden crates, footlockers and "
        "shipping trunks, and a number of ballast tanks.\n\n"
        "IF THE TANKS ARE OPENED: the decomposing remains of Phyllis "
        "Barnes. Opening the upper hatch releases a cloud of incredibly "
        "vile gas - CON roll or vomit from the reek. Discovering the body "
        "calls for a Sanity roll (0/1D2).",
        ["clue-ballast-tank", "npc-phyllis-barnes"]),
    loc("loc-hold-5", "Cargo Hold 5 - kennels and livestock",
        "Lowest deck",
        "Always heated, staffed and unlocked, and the whole hold smells "
        "of animals. 20 seasick cattle, five thoroughbred horses with "
        "their groom Arthur Pendury (who visits three times a day and "
        "sometimes sleeps here rather than in Steerage), more than 30 "
        "dogs and 14 cats - all watched over by the kennel boy James "
        "Hawthorne, aged 17.\n\n"
        "Hawthorne is the best witness aboard, and he is falling apart.",
        ["npc-james-hawthorne", "clue-kennel-boy"]),
    loc("loc-hold-6", "Cargo Hold 6 - vehicles and cargo", "Lowest deck",
        "UNLOCKED. Three brand-new Packard sedans, a Hudson tourer, a "
        "Bugatti racer and a dozen Oliver tractors strapped to the deck. "
        "Large containers of mailbags - hundreds if not thousands. A dozen "
        "barrels of French cognac. Fifty barrels labelled 'Hawaiian "
        "Botanical Specimens'. A large crate marked 'Funeral Supplies' "
        "holding the body of a tcho-tcho who died in San Francisco, being "
        "repatriated at Dr. Soong's expense.\n\n"
        "The Special and Third Class pool is rigged as a removable canvas "
        "over this hold.\n\n"
        "WHAT IS REALLY IN THE BARRELS is yours to decide - botanicals, "
        "something illegal stowed by the tcho-tcho, or human corpses. If "
        "the heroes stake out the hold they may watch a barrel opened, its "
        "contents cooked and eaten (Sanity 1/1D4), or witness 'Chad "
        "Peterson' offering the tcho-tcho a deal.",
        ["beat-the-tcho-tcho", "clue-funeral-supplies"]),
    loc("loc-hold-7", "Cargo Hold 7 - THE VALUABLES HOLD", "Lowest deck",
        "DOUBLE LOCKED: a padlock (Locksmith) and a deadbolt in the "
        "hatchway (Hard Locksmith). This is where everything is.\n\n"
        "CONTENTS: twenty-two crated oil paintings, four bronze and four "
        "marble statues (also crated), an enormous shipment of redwood "
        "planks and timbers, sixteen large glass carboys of hazardous "
        "chemicals such as ether and hydrochloric acid, a locker holding "
        "the ship's supply of small arms, rifles and skeet shotguns - and "
        "two things that matter:\n\n"
        "THE GREEN METAL BOX. Six feet tall, locked (Hard Locksmith or "
        "Hard STR to force). Engineering diagrams for the aetheric energy "
        "device, with notes on assembly, materials, costs and "
        "construction, covered in hand-written occult symbols. "
        "Recognising them as blueprints is easy (Mechanical Repair or "
        "Science (Engineering)); understanding that the device is meant "
        "to summon eldritch horrors through mechanical means in order to "
        "capture their essences takes a Cthulhu Mythos roll and at least "
        "two hours of study.\n\n"
        "THE ORGAN CRATE. Huge, labelled 'Wm. Wood Pipe Organ Co., Inc. "
        "of Portland, Oregon'. Spot Hidden (Hard without a light source) "
        "sees bloodstains on the left-hand panel, and that its screws "
        "have been unscrewed and refitted many times. Opening or smashing "
        "it is easy, and reveals the Pipes of Leng.\n\n"
        "THE CRAWLING ONE DOES NOT TAKE KINDLY to its artifact being "
        "found. A single hero may catch a spell - Mindblast, Dominate, "
        "Mental Suggestion. A group may get a hunting horror. Try to "
        "distract the heroes away rather than confront them too early - "
        "unless you are near a suitable climax, in which case dive in.\n\n"
        "THE ACID in the carboys does 1D10 per round to the flying polyp, "
        "ignoring its armor. Remember it is here.",
        ["clue-green-metal-box", "clue-blood-on-the-crate",
         "npc-pipes-of-leng", "beat-the-final-test"]),
]

# --------------------------------------------------------- reference

data["reference"] = [
    {
        "id": "ref-ship-stats",
        "title": "SS President Coolidge - full specifications",
        "description":
            "Built August 1931 at the Newport News shipyard for the Dollar "
            "Line - four months old, and the largest passenger ship ever "
            "built in the United States (though not large by European "
            "standards).\n\n"
            "SIZE\n"
            "Length 654 feet | Beam 81 feet | Draft 34 feet\n"
            "Gross tonnage 21,936 tons | Displacement 30,924 tons\n"
            "Levels: three above the deck, five below\n\n"
            "CARGO\n"
            "Capacity 608,850 cubic feet | Seven holds, four reachable "
            "from deck\n"
            "Car space for 100 vehicles in Hold 4 | Refrigerated 70,000 "
            "cubic feet in Hold 6\n"
            "18 cargo winches of 35 hp, lifting 3,000 lbs direct at 340 "
            "feet of rope per minute\n"
            "Six Welin McLachlan gravity davits for lifeboats; two 25 hp "
            "boat winches for tenders; six American Engineering Company "
            "capstan winches\n\n"
            "WEAPONS ABOARD\n"
            "A supply of small arms, rifles and shotguns (for skeet) "
            "locked in Cargo Hold 7. The Captain keeps a revolver locked "
            "in his cabin. There are no explosives aboard.\n\n"
            "ENGINES\n"
            "Two 13,250 hp Westinghouse turbo-electric | 12 Babcock and "
            "Wilcox high-pressure fuel oil boilers\n"
            "Steam pressure 300 psi | Boiler temperature 620 F | Two "
            "14,000 bhp turbines | Two propellers\n"
            "Prop speed 133 rpm at 22.2 knots | Top speed 22.2 knots | "
            "Cruising 20 knots\n"
            "Fuel storage 6,240 tons | Range 19,500 nautical miles "
            "cruising, 14,500 at full speed\n\n"
            "AMENITIES\n"
            "Maximum passengers 990 | Required crew 324 | Maximum aboard "
            "1,314\n"
            "Fresh water 2,320 tons | Lighting from four 500 kw 240/120 "
            "volt auxiliary turbine-generators\n"
            "Two swimming pools, one First Class and one a removable "
            "canvas over Hold 6\n\n"
            "THIS VOYAGE: 678 passengers and 315 crew, San Francisco to "
            "Shanghai via Honolulu. Five days to Honolulu (5-10 Dec), "
            "nine more to Shanghai (11-19 Dec), due in at 6:00 a.m. on "
            "the 20th.",
    },
    {
        "id": "ref-segregation",
        "title": "Moving between classes",
        "description":
            "The ship is very publicly and thoroughly divided. First, "
            "Special, Third and Steerage hardly ever mix, and this is a "
            "real obstacle for a party split across decks.\n\n"
            "GOING DOWN a class is possible, though stewards discourage "
            "'slumming'.\n\n"
            "GOING UP is much harder. Stairwells are watched by stewards "
            "and the three electric lifts have crew operators (one lift "
            "is cargo-only, into the kitchen). A passenger needs an "
            "invitation, a bribe to a corrupt crewmember, or a successful "
            "INTIMIDATE, CHARM, PERSUADE or FAST TALK roll to walk up a "
            "deck.\n\n"
            "CLIMBING is the dangerous course: a HARD CLIMB roll without "
            "a rope, Regular with one. Failure means falling overboard - "
            "or, on certain sections of hull up to First Class, falling "
            "30 feet onto the deck for 3D6 damage. A kind Keeper may "
            "allow a successful Jump to halve it.\n\n"
            "IF CAUGHT: First and Special Class passengers are politely "
            "removed and firmly discouraged from returning. Third Class "
            "are handled more roughly. Steerage passengers may be "
            "shackled to their beds if they keep sneaking off.\n\n"
            "CREW can move between classes without much difficulty - "
            "which is why a stolen uniform is worth so much, and why the "
            "crawling one uses one.",
    },
    {
        "id": "ref-key-rolls",
        "title": "Every roll in the scenario, in one place",
        "description":
            "INVESTIGATION\n"
            "Listen - hear the disturbance on 6 Dec; overhear crew about "
            "the purser; hear Soong's cry during the theft; hear the "
            "distant music at night. HARD LISTEN places the music below "
            "decks.\n"
            "Spot Hidden - the 'Funeral Supplies' crate on the dock; the "
            "rat pelt in the holds; the cold fire and opium ashes in Hold "
            "1; the reopened screws on the organ crate. HARD SPOT HIDDEN "
            "- blood on the crate panel without a light source (Regular "
            "with one); differences in the suicide-note handwriting.\n"
            "Psychology - Hallander is shocked; a second roll detects his "
            "lies; Hawthorne is terrified and probably insane.\n"
            "Art/Craft (Calligraphy) - the forged signature.\n"
            "Cthulhu Mythos - what the blueprints are actually for (plus "
            "two hours' study); the correct magic point investment to "
            "bind the polyp.\n"
            "Mechanical Repair or Science (Engineering) - recognise the "
            "blueprints.\n"
            "Science (Biology/Zoology) or Art/Craft (Leatherwork) - the "
            "rat pelt cannot have been skinned.\n"
            "Know or Science (Chemistry/Pharmacy) - identify opium "
            "ashes.\n\n"
            "SOCIAL\n"
            "Hard Persuade - see the passenger manifest.\n"
            "Intimidate or Persuade - get Hallander talking.\n"
            "Hard Charm or Persuade - win the Captain's trust.\n"
            "Extreme Fast Talk or Persuade - convince the engineers you "
            "have permission below.\n"
            "Extreme Persuade or Fast Talk, or Hard Psychoanalysis - talk "
            "Bates down from the hostage-taking.\n"
            "Hard Persuade or Hard Psychoanalysis - bolster Bates against "
            "Dominate (grants him a bonus die).\n"
            "Intimidate/Charm/Persuade/Fast Talk - walk up a deck.\n\n"
            "PHYSICAL\n"
            "Jump - follow the crawling one's leap to the Promenade Deck, "
            "or take 1D6+3. Also halves the 3D6 fall damage when climbing "
            "the hull.\n"
            "Hard Climb - climb between decks without a rope (Regular "
            "with one).\n"
            "Locksmith - the cargo hatches; the padlock on Hold 7; "
            "breaking into Peterson's cabin (or Mechanical Repair). HARD "
            "LOCKSMITH - the Hold 7 deadbolt and the green metal box.\n"
            "Extreme STR - force a watertight hatch. HARD STR with a "
            "crowbar, or to force the green box.\n"
            "Stealth - get past the crew on the hatches and in the engine "
            "room.\n"
            "CON - avoid seasickness on 18-19 Dec; avoid vomiting at the "
            "ballast tank.\n\n"
            "OPPOSED POW\n"
            "vs POW 100 - the crawling one's Mindblast and Dominate.\n"
            "vs POW 80 - Bind Flying Polyp (this roll cannot be pushed).",
    },
    {
        "id": "ref-sanity",
        "title": "Sanity losses during play",
        "description":
            "Mindblast from the crawling one - 5 points and an immediate "
            "bout of madness (opposed POW roll against POW 100; no effect "
            "if the hero wins).\n"
            "Seeing the crawling one change form, or its true form - "
            "1D3/2D6.\n"
            "Watching the tcho-tcho cook and eat the contents of a barrel "
            "- 1/1D4.\n"
            "Finding Phyllis Barnes in the ballast tank - 0/1D2.\n"
            "The flying polyp - 1D3/1D20, rolled by everyone aboard, "
            "because its rage keeps it visible.\n"
            "The hunting horror - 1D3/1D20.\n"
            "Reading the Book of Red Jade - 1D10 (Cthulhu Mythos "
            "+4/+8).\n"
            "Casting Bind Flying Polyp - 1 point.\n"
            "Progressively larger skinned animals in the holds - call for "
            "rolls as appropriate.",
    },
    {
        "id": "ref-sanity-awards",
        "title": "Sanity awards at the end",
        "description":
            "+1D6   The heroes prevent Bunny Bates from killing the "
            "hostage\n"
            "+1D4   The heroes destroy the aetheric energy device\n"
            "+2D6   The heroes capture or kill the crawling one\n"
            "-1D6   Allowing the crawling one to escape\n"
            "+1D20  The heroes defeat the flying polyp\n"
            "+1D10  The heroes attempt to save as many people as they can "
            "from drowning\n"
            "-1D10+2 The heroes leave the ship without regard for "
            "others",
    },
    {
        "id": "ref-dealing-with-the-polyp",
        "title": "Dealing with the polyp - the three ways out",
        "description":
            "1. DESTROY THE PIPES. 50 points of damage against armor 3 "
            "stops the machine playing and lets the polyp depart. "
            "Explosives would help; there are none aboard. When the music "
            "stops the polyp may take a few rounds to notice - keep it "
            "attacking for as long as you like, then have it suddenly "
            "stop, turn, fly upwards and shoot down into the depths.\n\n"
            "2. BIND IT. Heroes holding the Book of Red Jade can attempt "
            "Bind Flying Polyp. The caster cannot be in combat with the "
            "creature and must be within 100 yards, and must win an "
            "opposed POW roll against POW 80 - this roll CANNOT BE "
            "PUSHED. The spell costs 1 Sanity point. The caster may "
            "invest magic points equal to one-fifth of the monster's POW "
            "(16 MP) to gain a bonus die on the roll - but will not know "
            "the creature's POW, so it is a gamble; a successful Cthulhu "
            "Mythos roll deduces the correct number. Bound, the polyp "
            "falls under the caster's command and can be ordered back "
            "into the depths.\n\n"
            "3. FIGHT IT. Probably the hardest option. 4-point armor, and "
            "it suffers only MINIMUM damage from physical weapons - but "
            "enchanted weapons, fire and electrical attacks deliver full "
            "damage. The hydrochloric acid in the Hold 7 carboys does "
            "1D10 per round and negates its armor. For high pulp, "
            "military-minded heroes may call in nearby British, American "
            "or Japanese warships: a battery of warship guns does 10D10, "
            "and a salvo or two should destroy it or wound it grievously "
            "enough to drive it into the ocean.\n\n"
            "IF IT DIES its body smashes onto the ship with a heavy "
            "crunch and begins to decay almost immediately. Within "
            "minutes there is nothing left but greasy liquid and a bad "
            "smell.\n\n"
            "EITHER WAY THE SHIP IS LOST. The hole in the hull means the "
            "Coolidge is taking on water and listing. Ask the heroes what "
            "they want to do.",
    },
    {
        "id": "ref-optional-mayhem",
        "title": "Optional: additional mayhem and horror (high pulp)",
        "description":
            "For Keepers running this at full pulp, the crawling one uses "
            "its Graveyard Kiss spell to create zombies.\n\n"
            "In this version, rather than throwing the sacrificed bodies "
            "overboard, the crawling one has Bates hide them around Cargo "
            "Hold 7 as insurance. At the first sign of trouble it wakes "
            "them and sends them after the nearest living humans - which "
            "means zombies climbing up from below decks to endanger "
            "everyone aboard.\n\n"
            "As written that is only five zombies, which is little "
            "challenge for Pulp Cthulhu heroes. To scale it up, let each "
            "zombie make more: the crawling one's variant spell requires "
            "placing part of its insect mass in a corpse's mouth to "
            "awaken it, and awakened zombies can do the same - insects "
            "leaping from their mouths into the mouths of passengers they "
            "have killed. In theory a full zombie apocalypse can take "
            "over the ship while the heroes face the polyp.\n\n"
            "The zombies also make a fine replacement for Bunny Bates in "
            "the hostage scene if Bates has already been dealt with.",
    },
    {
        "id": "ref-troublesome-heroes",
        "title": "Optional: when the heroes get ahead of you",
        "description":
            "IF THEY ARE MAKING LIFE DIFFICULT for the crawling one, or "
            "the action needs a shove, Bunny Bates springs a surprise "
            "attack - especially if they are getting close to Almacan's "
            "cabin or nosing around the cargo hatches. He might appear at "
            "a hero's cabin door, or jump out at them in the hold.\n\n"
            "FOR A SERIOUSLY HARD TIME the crawling one summons a hunting "
            "horror to hunt them down. This draws a great deal of "
            "attention, so it will time the attack to minimise "
            "witnesses.\n\n"
            "IF THEY REACH THE PIPES TOO EARLY, distract rather than "
            "confront: a single hero catches a spell (Mindblast, "
            "Dominate, Mental Suggestion), or a group draws a hunting "
            "horror. If things go badly for the crawling one it "
            "discorporates and returns to the machine later. If the "
            "heroes destroy the Pipes of Leng, it sets its sights firmly "
            "on revenge.\n\n"
            "IF BATES IS LOST EARLY - killed, brigged, captured - the "
            "crawling one dominates Steward Martin Aimesworthy and "
            "substitutes him in every later scene. Alternatively, to keep "
            "things simple, have it dominate some other NPC to hinder the "
            "heroes so that Bates survives to play his part in the "
            "climax.",
    },
    {
        "id": "ref-dining",
        "title": "Colour: meals, entertainment and shipboard life",
        "description":
            "A typical dinner seats at least 200 at a time, and "
            "reservations are expected. Lobster, pheasant and veal are "
            "First Class only - but even Third Class eats better than "
            "many would ashore.\n\n"
            "FIRST CLASS - seven courses. Hors d'oeuvres and oysters; "
            "consomme Olga or cream of barley; salmon with mousseline "
            "sauce and cucumber; filet mignon, sauteed chicken Lyonnaise "
            "or fresh vegetables; then lamb in mint sauce, roast duckling "
            "in apple sauce or medallions of beef with green peas, boiled "
            "rice, creamed carrots, boiled new potatoes and potatoes "
            "Parmentier; then punch romaine, roast squab and crepes, cold "
            "asparagus vinaigrette, pate de foie gras and celery; and for "
            "dessert Waldorf pudding, peaches in Chartreuse jelly, "
            "chocolate and vanilla eclairs, or French ice cream. The "
            "Presidential Dance Orchestra plays the First Class Saloon "
            "6:00-9:00 p.m. nightly and takes requests.\n\n"
            "SPECIAL CLASS - consomme, baked haddock in a spicy sauce, "
            "then curried chicken, spring lamb in mint sauce or roast "
            "turkey with cranberry, with green peas, pureed turnips, "
            "boiled rice, boiled and roast potatoes. Desserts: plum "
            "pudding, wine jelly, a coconut sandwich or American ice "
            "cream, plus nuts, fresh fruit, cheese, biscuits and coffee. "
            "The Pacific Jazz Orchestra plays 7:00-9:00 p.m. on alternate "
            "nights.\n\n"
            "THIRD CLASS - rice soup, corned beef and cabbage, boiled "
            "potatoes, biscuits, fresh bread and butter, stewed apples "
            "and rice for dessert, coffee with dessert. Menus change "
            "daily but the meal is fixed for the day, served 6:00-8:00 "
            "p.m.\n\n"
            "STEERAGE - watery corned beef and cabbage, boiled carrots, "
            "boiled potatoes, rice pudding. The menu rarely changes; "
            "sometimes green beans, or bacon in a potato salad, or rice "
            "instead of potatoes. Served 8:00-9:00 p.m., after Third "
            "Class is done.\n\n"
            "SMOKING: not prohibited indoors generally, but Third Class "
            "and Steerage are expected to smoke outside on C Deck under "
            "the eye of stewards who fear cigarettes, pipes and cigars as "
            "fire hazards.\n\n"
            "THE PRINTING PRESS announces events, parties, special "
            "dinners and occasions. First and Special Class heroes get "
            "telegrams from shore stations and freshly printed invitations "
            "to St. Nicholas Night (6 Dec), Casino Night (7 Dec), the "
            "Tahitian Ball (9 Dec), and Sunday Mass (mornings of 6, 13 "
            "and 20 Dec).",
    },
    {
        "id": "ref-pacing",
        "title": "A word about pacing",
        "description":
            "This scenario unfolds over a number of days, which lets you "
            "build to the climax - and means you must hustle the time "
            "along to get there.\n\n"
            "Players often want to use every hour of every day in their "
            "investigations. Discourage this by forcing the pace. Focus "
            "on the action, maintain momentum, and red-line the story: "
            "simply tell the players you are fast-forwarding to the "
            "important stuff.\n\n"
            "Allow them time to explore and talk to NPCs, but be prepared "
            "to throw situations, questions and scenes at them to keep "
            "the game moving. The timeline is your friend here - when in "
            "doubt, jump to the next dated event.",
    },
]

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2)

n = {k: len(v) for k, v in data.items() if isinstance(v, list)}
print("wrote", OUT)
print("sections:", n)
print("size:", os.path.getsize(OUT), "bytes")

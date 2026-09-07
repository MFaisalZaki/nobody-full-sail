;; ====================================================================
;; Wine-Dark — the storyworld.
;;
;; Homer's Iliad and Odyssey merged into one continuous, fully editable
;; timeline. Nothing here is a scene. Every action is a SCHEMA, and the
;; storylines are whatever the schemas compose into — which is why one
;; template, one silhouette and one row of the accusation dropdown are
;; all authored here, beside the schema they belong to, and never per
;; episode.
;;
;; Three decisions are visible in the shape of this file, and each was
;; an open question in CLAUDE.md before it was written:
;;
;; 1. THE METERS ARE SPLIT. The symbolic LADDER is planner state and may
;;    be gated on (`(crew ?b)` with `(rung-down ?lo ?hi)`); the 0-100
;;    NUMBER is a display projection, declared per beat with `@meter`
;;    and carried by the player's path rather than by the world. So the
;;    reachable state space stays finite and enumerable, and two roads
;;    into one state still show different numbers.
;;
;; 2. ONE ACTION IS ONE DECISIVE BEAT — roughly a scene. Not a day, not
;;    an episode. A storyline is fifteen to forty beats, which is the
;;    right size for a card game and the right size for testimony: a
;;    witness says "I was there when you did that", and a beat you can
;;    point at is a beat somebody can have been present for.
;;
;; 3. TIME RIDES THE BEAT. `years` is a meter like the others, declared
;;    per schema. There is no filler `time-passes` action, because a
;;    beat that supports nothing is a beat the novelty machinery would
;;    discard anyway — so the clock is carried by beats that earn it.
;;
;; The register throughout is Emily Wilson's, not Alexander Pope's:
;; plain, fast, contemporary English. Never archaic.
;; ====================================================================

;; @title Wine-Dark
;; @note The score to beat is the canonical one: Odysseus reaches Ithaca
;; @note alone, twenty years late, having lost every man. That is a
;; @note benchmark, not a spoiler — the audience already knows it.

;; --- what the player can read off the world (state residue) ---------
;; CLAUDE.md's worked example turns on two facts, and the first draft of
;; this list had both backwards: "residue shows provisions were consumed
;; and the ship was wrecked", and "NOTHING observes the becalming".
;; `becalmed` is therefore not visible — an empty sea is not evidence of
;; who emptied it — and `provisions-spent` is.
;; @visible blinded wreckage mast-broken cattle-eaten sacrilege
;; @visible troy-fallen city-sacked bag-open swine scar-shown
;; @visible shade grave-raised temple-spared blown-back provisions-spent
;; @visible cave-shut conveyed
;; @visible heard-sirens strait-passed town-raided
;; A crossing is the commonest beat in the world and it used to
;; leave nothing at all: its parameters are the silent hero and
;; two places, so no witness and no provenance, and `at` names
;; only where you are now. `called-at` accumulates and is never
;; retracted, so every elided landfall leaves its own mark — the
;; cheap, plentiful residue the design wants, and the only
;; evidence a voyage of sailing leaves behind.
;; @visible called-at drifted was-kept
;; ...and the marks that read as an ABSENCE. `(dead eurylochus)`
;; is the design's own example of residue, and in a world that
;; models `(alive ?x)` that is a deletion: the man is not there.
;; Same for the ship no longer whole, and for every leaving beat —
;; out of the cave, up from the dead — whose entire contribution is
;; to stop something being true.
;; @visible alive ship-whole in-cave among-the-dead

;; --- what the player carries back through a rewind -------------------
;; The meters reset, the clock resets, the world resets. What happened
;; to you does not un-happen: a man who has stood on Thrinacia and
;; watched his crew eat the sun's cattle knows what is on that island,
;; and unpicking the shroud does not unknow it. So an episode LIVED is
;; the one thing a rewind does not take back, and `@foreknown` on a
;; schema is the lock it opens.
;; @episode troy The wooden horse, and what came after
;; @episode lotus The island where the food makes men forget
;; @episode cyclops The cave on the high shore
;; @episode aeolus The king of the winds, and the bag he gave you
;; @episode laestrygonians The narrow harbour and the cliffs above it
;; @episode circe The witch's hall, and the year in it
;; @episode underworld The country of the dead
;; @episode strait The rock and the whirlpool
;; @episode thrinacia The island where the sun keeps cattle
;; @episode ogygia The nymph's island, and the offer she makes
;; @episode scheria The court that will carry you home
;; @episode ithaca Your own hall, full of other men

;; --- who can testify, and for how long -------------------------------
;; @agent mortal god monster
;; @testify-while alive shade
;; @living alive
;; ...and reachable. A living witness is questioned, not remembered, so
;; he can only be asked while he is still with you. Without this the
;; cyclops answers questions about his own blinding from an island
;; twenty beats astern — and since he was a parameter of every beat of
;; that episode, he alone names the whole chain, so clause 2 of the
;; solvability guarantee refuses every landing point on every storyline
;; that passes his cave. Sailing away has to end testimony.
;; @testify-near with
;; A shade answers only where the dead answer. Without the gate
;; killing a witness would cost nothing, and the design's second
;; cost of a death would not exist.
;; @testify-gate among-the-dead
;; A god acting alone leaves no witness — that is the whole of why the
;; becalming is unrecoverable except by inference.
;; @silent poseidon athena zeus helios aeolus circe calypso
;; @carries thing

;; --- what the scenario planner needs, and the PDDL cannot say ---------
;; polyscene gates what MAY be told and picks among the admissible by
;; structure. To do either it needs three things a domain file has
;; nowhere to put: who the protagonist is, which fluents count as a
;; standing relation between people, and what he is playing for.
;; (The per-beat half — `@intensity`, `@sign`, `@directed` — sits beside
;; each schema, where it belongs.)
;; @hero odysseus
;; @ties with favours wrathful
;; @wants recognised-by penelope 10
;; @wants home 8
;; @wants suitors-dead 3
;; @wants blinded polyphemus -2
;; @wants heard-sirens 2

;; --- the arity fence -------------------------------------------------
;; The scenario planner (polyscene) reifies a beat by arity, event1 to
;; event4, and refuses to tell a story containing a beat it cannot see.
;; So no schema here takes more than FOUR parameters. Where a fifth was
;; wanted it became an `exists` in the precondition — which is the right
;; answer anyway, since a parameter nobody testifies about and nothing
;; distinguishes was never load-bearing.

;; --- what the meters read (display only; the ladders do the planning)
;; @meter-bar crew 0 100 100
;; @meter-bar divine 0 100 50
;; @meter-bar ithaca 0 100 90
;; @meter-bar kleos 0 100 20
;; @meter-bar years 0 30 0

;; --- the ladders the planner actually gates on -----------------------
;; A rung carries the number it reads as, so the strip and the ladder can
;; never disagree — a bar reading 48 beside an ending that reads "crew
;; alone" is two answers to one question.
;; @ladder crew alone=0 remnant=20 thinned=55 full=100
;; @ladder ithaca on=ithaca-hold lost=0 besieged=25 pressed=55 secure=90
;; @ladder kleos unsung=20 named=55 renowned=95

;; --- how a terminal state reads --------------------------------------
;; One ending is one knot, however many roads reach it. These name the
;; readings the world can end on; anything unnamed falls back to the
;; generator's own reading (goal / failure / dead end / stuck).
;; @ending reunited Home, and known
;; @ending home Home
;; @ending took-immortality The god's bargain
;; @ending suitors-spared The hall, left standing
;; @ending suitors-dead The hall, washed down
;; @ending cattle-eaten The sun's cattle
;; @ending held-by Seven years on the shore
;; @ending sacrilege The temple, and what followed
;; @ending becalmed Becalmed
;; @ending troy-fallen Troy, and no further

;; --- how the world is spelled in prose ---------------------------------
;; Instance vocabulary, not narrator vocabulary: the narrator still
;; authors one template per schema; these only say how a name is set.
;; @name odysseus Odysseus
;; @name eurylochus Eurylochus
;; @name perimedes Perimedes
;; @name elpenor Elpenor
;; @name polyphemus Polyphemus
;; @name poseidon Poseidon
;; @name athena Athena
;; @name zeus Zeus
;; @name helios Helios
;; @name aeolus Aeolus
;; @name circe Circe
;; @name calypso Calypso
;; @name scylla Scylla
;; @name penelope Penelope
;; @name telemachus Telemachus
;; @name antinous Antinous
;; @name teiresias Teiresias
;; @name ajax Ajax
;; @name agamemnon Agamemnon
;; @name troy Troy
;; @name ismaros Ismaros
;; @name lotus-land the land of the lotus-eaters
;; @name cyclops-island the cyclops' island
;; @name aeolia Aeolia
;; @name telepylos Telepylos
;; @name aiaia Aiaia
;; @name the-dead the country of the dead
;; @name strait the strait
;; @name thrinacia Thrinacia
;; @name ogygia Ogygia
;; @name scheria Scheria
;; @name ithaca Ithaca
;; @name ship the ship
;; @name cattle the sun's cattle
;; @name wind-bag the bag of winds
;; @name moly the black-rooted herb
;; @name bow the great bow
;; @name old-scar the scar
;; @name stake the olive stake

;; --- how a place reads, and how a fluent reads ------------------------
;; @place at 1
;; @where cyclops-island A high shore, and a cave above the beach.
;; @where thrinacia The sun's cattle graze the headland.
;; @where ogygia An island with one person on it.
;; @where aeolia A floating island with a bronze wall round it.
;; @where telepylos Deep water inside a mouth of rock.
;; @where aiaia Woodsmoke, and a woman singing.
;; @where the-dead A trench, and a queue.
;; @where strait Two rocks, a mile apart, and no third way through.
;; @where scheria A court that has heard of nobody.
;; @where ithaca Home, or what is left of it.
;; @where troy Ten years of this.
;; @reads blinded the cyclops is blind — {0}
;; @reads wreckage wreckage on the beach — {0}
;; @reads mast-broken the mast is broken — {0}
;; @reads cattle-eaten the sacred cattle have been eaten
;; @reads sacrilege the temple was violated
;; @reads provisions-spent the stores are empty
;; @reads heard-sirens someone here has heard the Sirens
;; @reads bag-open the bag of winds is open
;; @reads shade {0} is dead
;; @reads scar-shown the scar has been seen

(define (domain wine-dark)

 (:requirements :strips :typing :negative-preconditions :equality
                :disjunctive-preconditions :conditional-effects
                :universal-preconditions)

 (:types
    agent thing place band - object
    mortal god monster - agent
    hero companion noble - mortal)

 (:constants
    ;; the crew ladder, worst rung first
    alone remnant thinned full - band
    ;; how Ithaca is holding
    lost besieged pressed secure - band
    ;; the name that outlives you
    unsung named renowned - band)

 (:predicates
    ;; --- the ladders, and the static rungs that order them -----------
    (crew ?b - band)
    (ithaca-hold ?b - band)
    (kleos ?b - band)
    (rung-down ?lower - band ?higher - band)
    (rung-down2 ?lower - band ?higher - band)
    (rung-up ?higher - band ?lower - band)

    ;; --- where things are --------------------------------------------
    (at ?m - mortal ?p - place)
    (leg ?from - place ?to - place)
    (ship-whole)
    (raft-built)
    ;; ANY agent can be alive, not only a mortal: a monster who is
    ;; alive is a monster who can be asked, and testimony falls out of
    ;; being a parameter. Gods are alive too and say nothing — see
    ;; `@silent` — which is the design's own line: "Poseidon does not
    ;; testify".
    (alive ?a - agent)
    (shade ?m - mortal)
    (with ?c - companion)
    (grave-raised ?m - mortal)

    ;; --- Troy ---------------------------------------------------------
    (troy-standing)
    (troy-fallen)
    (horse-built)
    (inside-horse)
    (city-sacked)
    (sacrilege)
    (temple-spared)
    (armour-claimed)

    ;; --- the gods ------------------------------------------------------
    (wrathful ?g - god)
    (favours ?g - god)
    (sacrificed-to ?g - god)
    (owns-the-sun ?g - god)
    (owns-the-sea ?g - god)
    (owns-the-sky ?g - god)

    ;; --- the cyclops ----------------------------------------------------
    (in-cave)
    (cave-shut)
    ;; you go up to the cave once. Without this the beat that leaves it
    ;; re-enables the beat that entered it, and a planner rewarded for
    ;; long causal chains will walk in and out of it all day.
    (cave-visited)
    (blinded ?m - monster)
    (false-name-given ?m - monster)
    (named-to ?m - monster)
    (curse-laid ?m - monster)

    ;; --- Aeolus --------------------------------------------------------
    (has-bag ?t - thing)
    (bag-open)
    (blown-back)

    ;; --- Circe ----------------------------------------------------------
    (swine ?c - companion)
    (has-moly ?t - thing)
    (bedded ?g - god)
    (released-by ?g - god)

    ;; --- the underworld ---------------------------------------------------
    (prophecy-heard)
    (questioned ?m - mortal)

    ;; --- the strait -------------------------------------------------------
    (ears-stopped)
    (bound-to-mast)
    (heard-sirens)

    ;; --- Thrinacia ---------------------------------------------------------
    (sacred-cattle ?t - thing)
    (becalmed)
    (provisions)
    (cattle-eaten)
    (wreckage ?t - thing)
    (mast-broken ?t - thing)

    ;; --- Ogygia -------------------------------------------------------------
    (held-by ?g - god)
    (offered-immortality)
    (took-immortality)

    ;; --- Scheria -------------------------------------------------------------
    (supplicated ?m - mortal)
    (story-told)
    (conveyed)

    ;; --- Ithaca ---------------------------------------------------------------
    (disguised)
    (scar ?t - thing)
    (scar-shown)
    (recognised-by ?m - mortal)
    (bow-strung)
    (suitors-dead)
    (suitors-spared)
    (reunited)
    (home)

    ;; --- what the crew have learned ----------------------------------------
    ;; The single longest causal link in the domain: pull them off a beach
    ;; early, drag them out of the lotus, moor outside the harbour — and
    ;; ten beats later they are the crew who do NOT touch the cattle.
    (disciplined)
    (lotus-eaten ?c - companion)
    (town-raided)
    (watch-kept)
    (provisions-spent)
    (strait-passed)
    (among-the-dead)
    (been-below)
    ;; a port you have already called at. A voyage does not go back
    ;; the way it came, and without this the sea is a corridor the
    ;; planner can pace up and down to fill a horizon.
    (called-at ?p - place)
    ;; you drift once and she keeps you once. Both were re-enabled by
    ;; their own sequels — the raft clears `held-by`, sailing it clears
    ;; `raft-built` — so the planner ran the whole Calypso episode
    ;; twice to fill a horizon.
    (drifted)
    (was-kept)

    ;; --- what is where: the static board -------------------------------------
    ;; Each episode fires only where its episode is. Without these a schema
    ;; is applicable everywhere, the graph fills with beats that mean
    ;; nothing, and the storylines stop being about anywhere.
    (troy-here ?p - place)
    ;; a shrine is to SOMEBODY. Without the god in the fact, a shrine
    ;; offers a sacrifice to every god on the board and the card fills
    ;; with beats that differ only in a name.
    (shrine-to ?p - place ?g - god)
    ;; where news from the other homecomings can actually reach you
    (news-here ?p - place)
    (town-here ?p - place)
    (lotus-here ?p - place)
    (cave-here ?p - place)
    (winds-here ?p - place)
    (narrow-harbour ?p - place)
    (witch-here ?p - place)
    (dead-here ?p - place)
    (strait-here ?p - place)
    (cattle-here ?p - place)
    (nymph-here ?p - place)
    (court-here ?p - place)
    (home-here ?p - place)
    (keeper-of-winds ?g - god)
    ;; which god is which: without these, every schema that takes a god
    ;; grounds once per god on the board, and the cards fill with beats
    ;; that are only nominally different.
    (nymph ?g - god)
    (witch ?g - god)
    ;; which monster is which. Unguarded, Scylla lives in the cyclops'
    ;; cave and Polyphemus is the rock in the strait.
    (cyclops ?m - monster)
    (rock ?m - monster)
    ;; ...and which noble. Unguarded, the endgame binds ANY of them: you
    ;; can shoot Penelope as a suitor and come home to Antinous.
    (wife ?m - mortal)
    (kin ?m - mortal)
    (suitor ?m - mortal)
    (rival-for-the-armour ?m - mortal)
    (host ?m - mortal)
    (king ?m - mortal)
    (gives-the-herb ?g - god)
    (prophet ?m - mortal)
    ;; which thing is which, for the same reason: an unconstrained thing
    ;; parameter grounds a schema once per object on the board
    (is-ship ?t - thing)
    (is-bag ?t - thing)
    (is-herb ?t - thing)
    (is-bow ?t - thing)

    ;; --- the Nostoi, the free background consequence layer -----------------
    (agamemnon-murdered)
    (menelaus-lost)
    (ajax-drowned))


 ;; Acting slots are typed by who could PHYSICALLY do the thing, and
 ;; generously: any placed mortal may sacrifice, string the bow, kill
 ;; the suitors, sack a city. Whose story gets told — who the
 ;; protagonist is, which of these deeds is worth a telling — is the
 ;; scenario planner's business, decided by its objectives, never by
 ;; narrowing a type. The expedition's own beats (sailing, the cave,
 ;; the raft) stay hero-slotted because their state — the ship, the
 ;; party, the voyage's zero-arity fluents — is the expedition's.

 ;; ==================================================================
 ;; TROY — the ten years the player can also edit
 ;; ==================================================================

 ;; @gloss propose the horse
 ;; @tell {?who} puts the idea to them: a horse, hollow, left on the sand.
 ;; @span You proposed the horse.
 ;; @meter kleos+8 years+1
 ;; @tag troy
 (:action propose-the-horse
  :parameters (?who - mortal ?where - place)
  :precondition (and (at ?who ?where) (troy-here ?where) (troy-standing)
                     (not (horse-built)))
  :effect (and (horse-built)))

 ;; @gloss take the walls by storm
 ;; @tell They go at the walls in the open, and the walls take their price.
 ;; @span You stormed the walls.
 ;; @meter kleos+12 crew-25 years+1
 ;; @tag troy
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?who ?where
 (:action storm-the-walls
  :parameters (?who - mortal ?where - place)
  :precondition (and (at ?who ?where) (troy-here ?where) (troy-standing)
                     (not (crew alone)))
  :effect (and (troy-fallen) (not (troy-standing))
               (forall (?lo - band ?hi - band)
                 (when (and (crew ?hi) (rung-down ?lo ?hi))
                       (and (crew ?lo) (not (crew ?hi)))))))

 ;; @gloss get inside the horse
 ;; @tell They climb in and wait in the dark.
 ;; @span You waited inside the horse.
 ;; @meter years+1
 ;; @tag troy
 (:action enter-the-horse
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (troy-here ?where) (horse-built)
                     (troy-standing) (not (inside-horse))
                     (exists (?c - companion) (with ?c)))
  :effect (and (inside-horse)))

 ;; @gloss open the horse at night
 ;; @tell The bolt goes back, and they come down the rope one at a time.
 ;; @span You opened the horse.
 ;; @meter kleos+14
 ;; @tag troy
 (:action open-the-horse
  :parameters (?who - hero)
  :precondition (and (inside-horse) (troy-standing)
                     (exists (?c - companion) (with ?c)))
  :effect (and (troy-fallen) (not (troy-standing)) (not (inside-horse))))

 ;; @gloss sack the city
 ;; @tell They take the city apart. It takes all night and most of the morning.
 ;; @span You sacked the city.
 ;; @meter kleos+6 divine-12
 ;; @tag troy
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?who ?where
 (:action sack-the-city
  :parameters (?who - mortal ?where - place)
  :precondition (and (at ?who ?where) (troy-here ?where) (troy-fallen)
                     (not (city-sacked)))
  :effect (and (city-sacked)))

 ;; @gloss leave the temple alone
 ;; @tell {?who} puts a guard on the temple door and keeps him there.
 ;; @span You spared the temple.
 ;; @meter divine+18
 ;; @tag troy
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whose
 (:action spare-the-temple
  :parameters (?who - mortal ?whose - god ?where - place)
  :precondition (and (at ?who ?where) (troy-here ?where) (troy-fallen)
                     (not (sacrilege)) (not (temple-spared)))
  :effect (and (temple-spared) (favours ?whose) (not (wrathful ?whose))))

 ;; The sacrilege that costs the whole Greek fleet its homecoming. It
 ;; happens inside a temple, at night, in a city on fire: nobody sees it
 ;; and nobody will admit to it. DELIBERATELY UNOBSERVABLE — the player
 ;; can only ever infer it from what the sea does afterwards.
 ;; @gloss (the temple is violated)
 ;; @tell Something happens in the temple that nobody will admit to.
 ;; @span The temple was violated.
 ;; @observe unwitnessed
 ;; @meter divine-30
 ;; @tag troy divine
 ;; @kind event
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?whom ?whose
 (:action violate-the-temple
  :parameters (?whom - noble ?whose - god ?where - place)
  :precondition (and (troy-here ?where) (troy-fallen) (alive ?whom)
                     (not (temple-spared)) (not (sacrilege)))
  :effect (and (sacrilege) (wrathful ?whose) (not (favours ?whose))))

 ;; @gloss raise a grave
 ;; @tell They pile the stones and put his oar upright in them.
 ;; @span You raised a grave for {?whom}.
 ;; @meter divine+8
 ;; @tag rites
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whom
 (:action raise-a-grave
  :parameters (?who - mortal ?whom - mortal ?where - place)
  :precondition (and (at ?who ?where) (shade ?whom) (questioned ?whom)
                     (not (grave-raised ?whom)))
  :effect (and (grave-raised ?whom)))

 ;; @gloss claim the armour
 ;; @tell {?who} argues for the armour, and wins the argument.
 ;; @span You claimed the armour.
 ;; @meter kleos+10 divine-6
 ;; @tag troy
 (:action claim-the-armour
  :parameters (?who - mortal ?where - place)
  :precondition (and (at ?who ?where) (troy-here ?where) (troy-fallen)
                     (not (armour-claimed)))
  :effect (and (armour-claimed)))

 ;; The argument's bill. Winning the armour is a deed with a body in
 ;; it: the man who lost the argument does not survive losing it.
 ;; Nobody is in the pen when it happens — the player infers it from
 ;; the shade where a witness used to be.
 ;; @gloss (Ajax and the sword)
 ;; @tell They find him at first light in a pen of slaughtered sheep,
 ;; @tell the sword set in the ground at the hilt.
 ;; @span Ajax died by his own hand.
 ;; @observe unwitnessed
 ;; @meter divine-6 kleos-4
 ;; @tag troy
 ;; @kind event
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?whom ?who
 (:action ajax-falls-on-his-sword
  :parameters (?whom - noble ?where - place ?who - hero)
  :precondition (and (at ?who ?where) (troy-here ?where) (at ?whom ?where)
                     (armour-claimed) (rival-for-the-armour ?whom)
                     (alive ?whom))
  :effect (and (not (alive ?whom)) (shade ?whom)))

 ;; @gloss burn something for the god
 ;; @tell A thigh-bone wrapped in fat, and the smoke goes the right way.
 ;; @span You sacrificed to {?whose}.
 ;; @meter divine+10 years+1
 ;; @tag rites divine
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whose
 (:action sacrifice-to
  :parameters (?who - mortal ?whose - god ?where - place)
  :precondition (and (at ?who ?where) (shrine-to ?where ?whose)
                     (not (sacrificed-to ?whose)))
  ;; ...but no altar buys back a cursed sea: once the cyclops has
  ;; prayed over your NAME, the sea god is past appeasing.
  :effect (and (sacrificed-to ?whose)
               (when (or (not (owns-the-sea ?whose))
                         (forall (?m - monster) (not (curse-laid ?m))))
                     (and (favours ?whose) (not (wrathful ?whose))))))

 ;; ==================================================================
 ;; THE SEA — the leg that joins every episode to the next
 ;;
 ;; THE SPINE. Three gates, and between them they are why the second
 ;; half of the poem exists at all. Without them every episode is
 ;; optional: `sail-on` needs a ship and a lane, nothing homecoming
 ;; requires is produced by any episode, and episodes only ever COST —
 ;; so the storyline that wins is the one that sails past everything,
 ;; and both the enumerator and the planner find it, correctly and
 ;; boringly.
 ;;
 ;;   1. YOU CANNOT SAIL HOME. No `sail-on` into the place you are
 ;;      trying to reach: Odysseus arrives on someone else's ship, and
 ;;      the Phaeacians are the only ones who give him one — which
 ;;      means losing his own, which means Thrinacia or Charybdis or
 ;;      the Laestrygonian harbour.
 ;;   2. YOU CANNOT FIND THE WAY. Being carried home needs the
 ;;      prophecy, which needs the dead, which needs Circe to send you.
 ;;   3. THE SEA REFUSES YOU. Nobody carries you home while the god who
 ;;      owns the water is angry — so a curse laid on a beach ten beats
 ;;      ago has to be paid for before the last leg.
 ;;
 ;; What is left is not a choice of ROUTE — there is one route — but a
 ;; choice of PRICE at every stop on it. Which is the game.
 ;; ==================================================================

 ;; @gloss put to sea
 ;; @tell They put out from {?from} and the coast goes down behind them.
 ;; @span You sailed to {?to}.
 ;; @meter years+1 ithaca-4
 ;; @tag sea
 (:action sail-on
  :parameters (?who - hero ?from - place ?to - place)
  :precondition (and (at ?who ?from) (leg ?from ?to) (ship-whole)
                     (not (home-here ?to))
                     ;; a `leg` is a SAILABLE PASSAGE, not adjacency: the
                     ;; problem lists every forward crossing, however
                     ;; many ports it passes, so one beat is one
                     ;; LANDFALL — a decisive act — and a storyline that
                     ;; skips three islands spends one card doing it,
                     ;; not three. Forward only; the one road back is up
                     ;; from the country of the dead. Without that the
                     ;; planner paces a two-port stretch to fill its
                     ;; horizon and the storyline reads as a man who
                     ;; cannot make up his mind.
                     (or (not (called-at ?to)) (dead-here ?from))
                     (not (becalmed)) (not (in-cave)) (not (inside-horse))
                     (not (among-the-dead)) (not (= ?from ?to)))
  :effect (and (not (at ?who ?from)) (at ?who ?to) (called-at ?to)))

 ;; ==================================================================
 ;; THE VOYAGE — Ismaros to Ogygia
 ;; ==================================================================

 ;; @gloss raid the town
 ;; @tell They take the town in an hour and will not leave for three days.
 ;; @span You raided the town.
 ;; @meter kleos+6 crew-15 years+1
 ;; @tag voyage
 ;; @intensity 3
 ;; @sign pos
 ;; @directed ?who ?where
 (:action raid-the-town
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (town-here ?where)
                     (not (crew alone)) (not (town-raided))
                     (not (disciplined)))
  :effect (and (town-raided) (forall (?lo - band ?hi - band)
                 (when (and (crew ?hi) (rung-down ?lo ?hi))
                       (and (crew ?lo) (not (crew ?hi)))))))

 ;; @gloss get them back aboard before dark
 ;; @tell {?who} counts them onto the ship while there is still light.
 ;; @span You pulled them out early.
 ;; @meter kleos-4 divine+4
 ;; @tag voyage
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?where
 (:action withdraw-at-once
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (town-here ?where)
                     (exists (?c - companion) (and (with ?c) (alive ?c)))
                     (not (town-raided)) (not (disciplined)))
  :effect (and (town-raided) (disciplined)))

 ;; @gloss (they taste the lotus)
 ;; @tell The people here are friendly and give them something to eat, and
 ;; @tell after that {?whom} does not want to leave.
 ;; @span They ate the lotus.
 ;; @meter kleos-4 years+1
 ;; @tag lotus
 ;; @kind event
 (:action taste-the-lotus
  :parameters (?whom - companion ?where - place ?who - hero)
  :precondition (and (at ?who ?where) (lotus-here ?where) (with ?whom)
                     (alive ?whom) (not (lotus-eaten ?whom)))
  :effect (and (lotus-eaten ?whom)))

 ;; @gloss drag them off the beach
 ;; @tell They are weeping when he ties them under the benches.
 ;; @span You dragged {?withwhom} back to the ship.
 ;; @meter kleos+4
 ;; @tag lotus
 (:action drag-them-back
  :parameters (?who - hero ?withwhom - companion ?where - place)
  :precondition (and (at ?who ?where) (lotus-here ?where) (with ?withwhom)
                     (lotus-eaten ?withwhom) (not (disciplined)))
  :effect (and (not (lotus-eaten ?withwhom)) (disciplined)))

 ;; @gloss go up to the cave
 ;; @tell There is cheese in baskets and no one at home. {?who} waits to
 ;; @tell see who owns it.
 ;; @span You went into the cave.
 ;; @meter years+1
 ;; @tag cyclops
 (:action enter-the-cave
  :parameters (?who - hero ?where - place ?whose - monster)
  :precondition (and (at ?who ?where) (cave-here ?where) (cyclops ?whose)
                     (exists (?c - companion) (and (with ?c) (alive ?c)))
                     (not (in-cave)) (not (cave-visited))
                     (not (blinded ?whose)))
  :effect (and (in-cave) (cave-visited) (cave-shut)))

 ;; @gloss take the cheese and go
 ;; @tell They load what they can carry and are back at the oars by dusk.
 ;; @span You took the cheese and left.
 ;; @meter kleos-6 divine+6
 ;; @tag cyclops
 (:action take-the-cheese
  :parameters (?who - hero ?where - place ?whom - monster)
  :precondition (and (at ?who ?where) (in-cave) (cyclops ?whom)
                     (not (blinded ?whom))
                     (exists (?c - companion) (with ?c)))
  :effect (and (not (in-cave)) (not (cave-shut)) (disciplined)))

 ;; @gloss put out his eye
 ;; @tell The stake goes in hissing. The sound he makes brings the whole
 ;; @tell island to the mouth of the cave.
 ;; @span You blinded {?whom}.
 ;; @meter kleos+10 crew-12 divine-10
 ;; @tag cyclops
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?who ?whom
 ;; Blinding the sea god's son is what angers the sea god — the poem's
 ;; own cause, and it does not wait for your name. The SHOUT is what
 ;; makes the wrath incurable (see lay-the-curse and sacrifice-to):
 ;; without it, a sacrifice can still buy the sea back.
 (:action blind-the-cyclops
  :parameters (?who - hero ?whom - monster ?withwhom - companion)
  :precondition (and (in-cave) (cyclops ?whom) (not (blinded ?whom))
                     (with ?withwhom) (alive ?withwhom))
  :effect (and (blinded ?whom) (forall (?lo - band ?hi - band)
                 (when (and (crew ?hi) (rung-down ?lo ?hi))
                       (and (crew ?lo) (not (crew ?hi))))
               (forall (?g - god)
                 (when (owns-the-sea ?g)
                       (and (wrathful ?g) (not (favours ?g))))))))

 ;; @gloss go out under the sheep
 ;; @tell They go out under the rams' bellies, one man to a fleece, and he
 ;; @tell counts the backs of his own flock as they pass.
 ;; @span You got out of the cave.
 ;; @meter kleos+6
 ;; @tag cyclops
 (:action escape-the-cave
  :parameters (?who - hero ?whom - monster)
  :precondition (and (in-cave) (cyclops ?whom) (blinded ?whom)
                     (exists (?c - companion) (with ?c)))
  :effect (and (not (in-cave)) (not (cave-shut))))

 ;; @gloss tell him your name is Nobody
 ;; @tell "Nobody," {?who} says, and lets him have it.
 ;; @span You told him you were Nobody.
 ;; @meter kleos-2
 ;; @tag cyclops
 ;; @intensity 1
 ;; @sign neutral
 ;; @directed ?who ?whom
 (:action give-a-false-name
  :parameters (?who - hero ?whom - monster)
  :precondition (and (in-cave) (not (named-to ?whom))
                     (not (false-name-given ?whom)))
  :effect (and (false-name-given ?whom)))

 ;; The canonical piece of hubris in the whole poem, and the one the
 ;; design names as the thematic core: +kleos, and a decade of -divine.
 ;; @gloss shout your real name across the water
 ;; @tell {?who} cannot leave it. He shouts his name across the water, and
 ;; @tell his father's name, and the name of the island he is from.
 ;; @span You shouted your name at {?whom}.
 ;; @meter kleos+20 divine-10
 ;; @tag cyclops hubris
 ;; @intensity 3
 ;; @sign pos
 ;; @directed ?who ?whom
 (:action shout-your-name
  :parameters (?who - hero ?whom - monster ?where - place)
  :precondition (and (at ?who ?where) (cave-here ?where) (cyclops ?whom)
                     (blinded ?whom) (not (in-cave)) (not (named-to ?whom)))
  :effect (and (named-to ?whom)))

 ;; The beat that nobody sees. A blind giant on an empty beach, praying
 ;; to his father — no witness, no residue, and the fleet is gone by
 ;; morning. Its consequence is the entire second half of the poem, and
 ;; the player can only ever get at it by inference. This is where the
 ;; puzzle lives.
 ;; @gloss (a curse is laid)
 ;; @tell Somewhere behind them, someone is talking to the sea.
 ;; @span A curse was laid.
 ;; @observe unwitnessed
 ;; @meter divine-30
 ;; @tag cyclops divine
 ;; @kind event
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?whom ?against
 (:action lay-the-curse
  :parameters (?whom - monster ?whose - god ?against - hero)
  :precondition (and (blinded ?whom) (cyclops ?whom) (named-to ?whom)
                     (owns-the-sea ?whose) (not (curse-laid ?whom)))
  :effect (and (curse-laid ?whom) (wrathful ?whose) (not (favours ?whose))))

 ;; @gloss take the bag of winds
 ;; @tell The king gives him an ox-hide bag, tied with silver wire, and
 ;; @tell tells him not to open it.
 ;; @span You were given the bag of winds.
 ;; @meter divine+6 years+1
 ;; @tag aeolus
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whose
 (:action take-the-bag
  :parameters (?who - hero ?whose - god ?what - thing ?where - place)
  :precondition (and (at ?who ?where) (winds-here ?where)
                     (keeper-of-winds ?whose) (is-bag ?what)
                     (not (has-bag ?what)) (not (bag-open)))
  :effect (and (has-bag ?what) (favours ?whose) (not (wrathful ?whose))))

 ;; @gloss stay awake and steer
 ;; @tell Nine days at the tiller. On the tenth, Ithaca is a smudge on the
 ;; @tell water and {?who} is still awake.
 ;; @span You kept watch over the bag.
 ;; @meter kleos+4 years+1
 ;; @tag aeolus
 ;; Nine days awake at the tiller is what you do the SECOND time somebody hands you a bag of winds.
 ;; [deferred] @foreknown aeolus
 (:action keep-watch
  :parameters (?who - hero ?what - thing)
  :precondition (and (has-bag ?what) (is-bag ?what) (not (bag-open))
                     (not (watch-kept)))
  :effect (and (watch-kept)))

 ;; @gloss (they open the bag)
 ;; @tell They are certain it is gold. They cut the wire while he sleeps.
 ;; @span They opened the bag of winds.
 ;; @meter ithaca-10 years+1
 ;; @tag aeolus
 ;; @kind event
 ;; @intensity 2
 ;; @sign pos
 ;; @directed ?whom ?what
 (:action open-the-bag
  :parameters (?whom - companion ?what - thing)
  :precondition (and (has-bag ?what) (is-bag ?what) (with ?whom)
                     (alive ?whom) (not (bag-open)) (not (watch-kept)))
  :effect (and (bag-open) (blown-back) (not (has-bag ?what))
               (forall (?lo - band ?hi - band)
                 (when (and (ithaca-hold ?hi) (rung-down ?lo ?hi))
                       (and (ithaca-hold ?lo) (not (ithaca-hold ?hi)))))))

 ;; @gloss moor inside the harbour
 ;; @tell Deep water, high cliffs, a mouth like a gate. Every ship goes in
 ;; @tell but his.
 ;; @span You moored inside the harbour.
 ;; @meter crew-40 years+1
 ;; @tag laestrygonians
 ;; @kind event
 (:action moor-inside
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (narrow-harbour ?where) (ship-whole)
                     (not (crew alone))
                     (exists (?c - companion) (with ?c)))
  :effect (and (not (ship-whole))
               (forall (?c - companion)
                 (when (with ?c)
                       (and (not (alive ?c)) (not (with ?c)) (shade ?c))))
               (forall (?lo - band ?hi - band)
                 (when (and (crew ?hi) (rung-down2 ?lo ?hi))
                       (and (crew ?lo) (not (crew ?hi)))))))

 ;; @gloss moor outside, under the rock
 ;; @tell {?who} ties up outside the harbour mouth, the way a man does who
 ;; @tell has stopped trusting good anchorages.
 ;; @span You moored outside the harbour.
 ;; @meter divine+4 years+1
 ;; @tag laestrygonians
 ;; Mooring outside a good anchorage is not a thing a man does until he has seen what is inside one.
 ;; [deferred] @foreknown laestrygonians
 (:action moor-outside
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (narrow-harbour ?where) (ship-whole)
                     (not (disciplined)))
  :effect (and (disciplined)))

 ;; @gloss (they drink what she pours)
 ;; @tell {?whom} drinks first, and stops being able to answer.
 ;; @span They drank what she poured.
 ;; @meter crew-8 years+1
 ;; @tag circe
 ;; @kind event
 ;; @intensity 3
 ;; @sign pos
 ;; @directed ?whose ?whom
 (:action drink-the-cup
  :parameters (?whom - companion ?whose - god ?where - place ?who - hero)
  :precondition (and (at ?who ?where) (witch-here ?where) (witch ?whose)
                     (with ?whom) (alive ?whom) (not (swine ?whom))
                     (not (released-by ?whose)))
  :effect (and (swine ?whom)))

 ;; @gloss take the herb before you go up
 ;; @tell Black root, white flower. Hard for mortals to dig up; not for the
 ;; @tell one who hands it over.
 ;; @span You were given the herb.
 ;; @meter divine+8
 ;; @tag circe
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?whose ?who
 ;; Taking the herb before you go up the path means knowing what is at the top of it.
 ;; [deferred] @foreknown circe
 (:action take-the-herb
  :parameters (?who - hero ?whose - god ?what - thing ?where - place)
  :precondition (and (at ?who ?where) (witch-here ?where) (is-herb ?what)
                     (gives-the-herb ?whose) (not (has-moly ?what)))
  :effect (and (has-moly ?what)))

 ;; @gloss make her swear and free them
 ;; @tell She swears the great oath, and the bristles go back into their skin.
 ;; @span You made her free them.
 ;; @meter kleos+6
 ;; @tag circe
 ;; @intensity 2
 ;; @sign pos
 ;; @directed ?who ?whose
 (:action free-the-crew
  :parameters (?who - hero ?whose - god ?what - thing ?whom - companion)
  :precondition (and (has-moly ?what) (is-herb ?what) (witch ?whose)
                     (swine ?whom) (not (released-by ?whose)))
  :effect (and (released-by ?whose) (not (swine ?whom))))

 ;; @gloss stay the year
 ;; @tell A year goes by the way a year does when nobody is counting it.
 ;; @span You stayed a year with {?whose}.
 ;; @meter years+1 ithaca-14 kleos-6
 ;; @tag circe
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whose
 (:action stay-the-year
  :parameters (?who - hero ?whose - god ?where - place)
  :precondition (and (at ?who ?where) (witch-here ?where) (witch ?whose)
                     (released-by ?whose) (not (bedded ?whose)))
  :effect (and (bedded ?whose) (forall (?lo - band ?hi - band)
                 (when (and (ithaca-hold ?hi) (rung-down ?lo ?hi))
                       (and (ithaca-hold ?lo) (not (ithaca-hold ?hi)))))))

 ;; @gloss (he falls from the roof)
 ;; @tell {?whom} sleeps on the roof for the cool of it, forgets the
 ;; @tell ladder, and breaks his neck in the yard.
 ;; @span {?whom} fell from the roof.
 ;; @kind event
 ;; @meter divine-4
 ;; @tag circe
 (:action fall-from-the-roof
  :parameters (?whom - companion ?where - place ?who - hero)
  :precondition (and (at ?who ?where) (witch-here ?where) (with ?whom)
                     (alive ?whom))
  :effect (and (not (alive ?whom)) (not (with ?whom)) (shade ?whom)))

 ;; ==================================================================
 ;; THE DEAD — where testimony is literal
 ;; ==================================================================

 ;; @gloss go down and ask
 ;; @tell A trench, black blood, and a queue of people who used to be alive.
 ;; @span You went down to the dead.
 ;; @meter divine-6 years+1 kleos+8
 ;; @tag underworld
 (:action go-down-to-the-dead
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (dead-here ?where)
                     (not (among-the-dead)) (not (been-below)))
  :effect (and (among-the-dead) (been-below)))

 ;; Testimony, in fiction as well as in mechanism: an agent who was a
 ;; parameter of a beat can be asked about it, and death is not always
 ;; the end of that — which is why `@testify-while` names `shade` as
 ;; well as `alive`.
 ;; @gloss question the shade
 ;; @tell {?whom} drinks, and remembers who he is, and answers.
 ;; @span You questioned {?whom}.
 ;; @kind investigate
 ;; @tag underworld evidence
 ;; @intensity 1
 ;; @sign neutral
 ;; @directed ?who ?whom
 (:action question-the-shade
  :parameters (?who - mortal ?whom - mortal ?where - place)
  :precondition (and (at ?who ?where) (among-the-dead) (shade ?whom)
                     (not (questioned ?whom)))
  :effect (and (questioned ?whom)))

 ;; @gloss hear the prophecy
 ;; @tell Leave the cattle alone, he says. Leave them alone and you may all
 ;; @tell get home. Touch them and you come home late, alone, on someone
 ;; @tell else's ship.
 ;; @span You heard the prophecy.
 ;; @kind investigate
 ;; @meter divine+6
 ;; @tag underworld
 (:action hear-the-prophecy
  :parameters (?who - mortal ?whom - mortal ?where - place)
  :precondition (and (at ?who ?where) (among-the-dead) (shade ?whom)
                     (prophet ?whom) (questioned ?whom)
                     (not (prophecy-heard)))
  :effect (and (prophecy-heard)))

 ;; @gloss come back up
 ;; @tell He goes back up the same way, and does not look behind him.
 ;; @span You came back from the dead.
 ;; @meter years+1
 ;; @tag underworld
 (:action come-back-from-the-dead
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (among-the-dead))
  :effect (and (not (among-the-dead))))

 ;; ==================================================================
 ;; THE STRAIT — every option here is a price
 ;; ==================================================================

 ;; @gloss wax in every ear
 ;; @tell He goes down the benches with the wax and does not miss anyone.
 ;; @span You stopped their ears.
 ;; @meter kleos-4
 ;; @tag strait
 ;; Wax in every ear presupposes knowing there is something in the water worth not hearing.
 ;; [deferred] @foreknown strait
 (:action stop-their-ears
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (strait-here ?where)
                     (exists (?c - companion) (with ?c))
                     (not (ears-stopped)))
  :effect (and (ears-stopped)))

 ;; @gloss have them tie you to the mast
 ;; @tell He wants to hear it. That is the whole of the reason.
 ;; @span You had yourself tied to the mast.
 ;; @meter kleos+10
 ;; @tag strait
 (:action bind-me-to-the-mast
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (strait-here ?where) (ears-stopped)
                     (not (bound-to-mast))
                     (exists (?c - companion) (with ?c)))
  :effect (and (bound-to-mast) (heard-sirens)))

 ;; @gloss ithaca the course past the rock
 ;; @tell Six of them, one for each head, still calling his name.
 ;; @span You went past the rock and lost six men.
 ;; @meter crew-14 kleos+4
 ;; @tag strait
 ;; @intensity 3
 ;; @sign pos
 ;; @directed ?who ?what
 (:action pass-the-rock
  :parameters (?who - hero ?what - monster ?where - place
               ?whom - companion)
  :precondition (and (at ?who ?where) (strait-here ?where) (rock ?what)
                     (ship-whole) (with ?whom) (alive ?whom)
                     (not (becalmed)) (not (strait-passed)))
  :effect (and (strait-passed)
               (not (alive ?whom)) (not (with ?whom)) (shade ?whom) (forall (?lo - band ?hi - band)
                 (when (and (crew ?hi) (rung-down ?lo ?hi))
                       (and (crew ?lo) (not (crew ?hi)))))))

 ;; @gloss steer for the whirlpool instead
 ;; @tell He puts the bow at the other side, where the water goes down
 ;; @tell instead of where the teeth are.
 ;; @span You steered for the whirlpool.
 ;; @meter crew-40 divine-4
 ;; @tag strait
 ;; @intensity 3
 ;; @sign pos
 ;; @directed ?who ?what
 (:action steer-for-the-whirlpool
  :parameters (?who - hero ?what - monster ?where - place)
  :precondition (and (at ?who ?where) (strait-here ?where) (rock ?what)
                     (ship-whole) (not (strait-passed)))
  :effect (and (strait-passed) (not (ship-whole))
               (forall (?c - companion)
                 (when (with ?c)
                       (and (not (alive ?c)) (not (with ?c)) (shade ?c)))) (forall (?lo - band ?hi - band)
                 (when (and (crew ?hi) (rung-down2 ?lo ?hi))
                       (and (crew ?lo) (not (crew ?hi)))))))

 ;; ==================================================================
 ;; THRINACIA — the design's own worked example
 ;; ==================================================================

 ;; @gloss put in at the island
 ;; @tell The cattle are on the headland, and they are not anyone's.
 ;; @span You landed on {?where}.
 ;; @meter years+1
 ;; @tag thrinacia
 (:action land-at
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (cattle-here ?where) (ship-whole)
                     (exists (?c - companion) (with ?c))
                     (not (provisions)) (not (provisions-spent)))
  :effect (and (provisions)))

 ;; @gloss sail past without landing
 ;; @tell They can see the cattle from the water. He does not put in.
 ;; @span You sailed past the island.
 ;; @meter kleos+4 divine+10
 ;; @tag thrinacia
 (:action sail-past
  :parameters (?who - hero ?where - place ?whose - god)
  :precondition (and (at ?who ?where) (cattle-here ?where) (ship-whole)
                     (prophecy-heard) (owns-the-sun ?whose)
                     (not (favours ?whose))
                     (not (becalmed)) (not (provisions)))
  :effect (and (favours ?whose) (not (wrathful ?whose))))

 ;; The becalming. A god holds the wind, alone, over open water. Nobody
 ;; is a witness to weather. DELIBERATELY UNOBSERVABLE — and it is the
 ;; hinge of the design's worked example: *"a brief landing cannot
 ;; exhaust provisions, so something held them there."*
 ;; @gloss (the wind stops)
 ;; @tell The wind stops. It does not start again.
 ;; @span The wind died.
 ;; @observe unwitnessed
 ;; @meter years+1 ithaca-6
 ;; @tag thrinacia divine
 ;; @kind event
 ;; @intensity 3
 ;; @sign pos
 ;; @directed ?whose ?who
 (:action becalm
  :parameters (?whose - god ?where - place ?who - hero)
  :precondition (and (at ?who ?where) (wrathful ?whose) (owns-the-sea ?whose)
                     (provisions) (not (becalmed)))
  :effect (and (becalmed)))

 ;; Residue: the empty sack. Cheap, plentiful, and rarely conclusive —
 ;; it tells you what, not why.
 ;; The way out of a becalming that is not eating the sun's cattle. It
 ;; needs the discipline the player bought somewhere earlier — which is
 ;; the longest causal link in the domain paying off — and without it a
 ;; crew that would not touch the cattle simply starves where it stands.
 ;; @gloss wait it out
 ;; @tell Nobody touches the cattle. They sit on the beach and wait, and
 ;; @tell on the eighth day there is a little wind out of the north.
 ;; @span You waited out the calm.
 ;; @meter years+1 ithaca-8 kleos+6
 ;; @tag thrinacia
 (:action endure-the-calm
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (becalmed) (disciplined)
                     (not (cattle-eaten)))
  :effect (and (not (becalmed))))

 ;; @gloss (the stores run out)
 ;; @tell The corn goes, then the wine, then the last of the salt meat.
 ;; @span The provisions ran out.
 ;; @meter years+1
 ;; @tag thrinacia
 ;; @kind event
 (:action consume-provisions
  :parameters (?whom - companion ?where - place ?who - hero)
  :precondition (and (at ?who ?where) (with ?whom) (alive ?whom)
                     (becalmed) (provisions))
  :effect (and (not (provisions)) (provisions-spent)))

 ;; @gloss (they take the cattle)
 ;; @tell {?whom} makes the argument about starving, and it is a good
 ;; @tell argument, and they do it while he is asleep.
 ;; @span They killed the sun's cattle.
 ;; @meter divine-25 kleos-8
 ;; @tag thrinacia
 ;; @kind event
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?whom ?whose
 (:action slaughter-the-cattle
  :parameters (?whom - companion ?what - thing ?whose - god ?where - place)
  :precondition (and (cattle-here ?where) (with ?whom) (alive ?whom)
                     (provisions-spent) (sacred-cattle ?what)
                     (owns-the-sun ?whose)
                     (exists (?h - hero) (at ?h ?where))
                     (not (disciplined)) (not (cattle-eaten)))
  :effect (and (cattle-eaten) (wrathful ?whose) (not (favours ?whose))))

 ;; @gloss (the ship is broken)
 ;; @tell One bolt, from a clear sky, into the mast-step.
 ;; @span The ship broke up.
 ;; @meter crew-40 years+1
 ;; @tag thrinacia divine
 ;; @kind event
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?whose ?who
 (:action break-the-ship
  :parameters (?whose - god ?what - thing ?who - hero)
  :precondition (and (cattle-eaten) (owns-the-sky ?whose) (ship-whole)
                     (is-ship ?what))
  :effect (and (not (ship-whole)) (wreckage ?what) (mast-broken ?what)
               (forall (?c - companion)
                 (when (with ?c)
                       (and (not (alive ?c)) (not (with ?c)) (shade ?c))))
               (forall (?lo - band ?hi - band)
                 (when (and (crew ?hi) (rung-down2 ?lo ?hi))
                       (and (crew ?lo) (not (crew ?hi)))))))

 ;; Residue expires. The tide takes the wreckage, and with it the only
 ;; physical evidence that there was ever a ship.
 ;; @gloss (the tide takes the wreckage)
 ;; @tell By the second tide there is nothing on the sand but sand.
 ;; @span The tide took the wreckage.
 ;; @tag thrinacia
 ;; @kind event
 (:action the-tide-takes-it
  :parameters (?what - thing ?where - place ?who - hero)
  :precondition (and (at ?who ?where) (wreckage ?what) (is-ship ?what))
  :effect (and (not (wreckage ?what))))

 ;; ==================================================================
 ;; OGYGIA — where the clock does the damage
 ;; ==================================================================

 ;; The drift, and it happens ONCE and it ends in one place. Written as
 ;; an ordinary leg it became a ship-free `sail-on` — the planner used it
 ;; as free traversal and told storylines with eleven consecutive days of
 ;; drifting in them. A man on a keel does not choose a heading: the sea
 ;; takes him where the sea takes him, which in this poem is the nymph's
 ;; island, and everything he has not done by then he will not do.
 ;; @gloss drift
 ;; @tell Nine days on the keel of his own ship, and on the tenth a beach.
 ;; @tell He comes up it on his hands and knees and sleeps under the leaves.
 ;; @span You drifted to {?to}.
 ;; @meter years+1 ithaca-6 crew-100
 ;; @tag ogygia
 (:action wash-ashore
  :parameters (?who - hero ?from - place ?to - place)
  :precondition (and (at ?who ?from) (nymph-here ?to) (not (ship-whole))
                     (not (raft-built)) (not (drifted))
                     (not (among-the-dead)) (not (= ?from ?to)))
  :effect (and (not (at ?who ?from)) (at ?who ?to) (drifted)
               (forall (?c - companion)
                 (when (with ?c)
                       (and (not (alive ?c)) (not (with ?c)) (shade ?c))))
               (forall (?lo - band ?hi - band)
                 (when (and (crew ?hi) (rung-down2 ?lo ?hi))
                       (and (crew ?lo) (not (crew ?hi)))))))

 ;; @gloss (she keeps him)
 ;; @tell Seven years. He sits on the shore most days and looks at the water.
 ;; @span She kept you seven years.
 ;; @meter years+7 ithaca-30 kleos-10
 ;; @tag ogygia
 ;; @kind event
 ;; @intensity 2
 ;; @sign pos
 ;; @directed ?whose ?who
 (:action be-kept
  :parameters (?whose - god ?who - hero ?where - place)
  :precondition (and (at ?who ?where) (nymph-here ?where) (nymph ?whose)
                     (not (ship-whole)) (not (was-kept))
                     (not (held-by ?whose)))
  :effect (and (held-by ?whose) (was-kept) (offered-immortality)
               (forall (?lo - band ?hi - band)
                 (when (and (ithaca-hold ?hi) (rung-down2 ?lo ?hi))
                       (and (ithaca-hold ?lo) (not (ithaca-hold ?hi)))))))

 ;; @gloss refuse to be a god
 ;; @tell She offers him the one thing nobody gets. He says he wants to
 ;; @tell see his wife, who will die.
 ;; @span You refused to become immortal.
 ;; @meter kleos+16 divine+8
 ;; @tag ogygia
 ;; @intensity 2
 ;; @sign neg
 ;; @directed ?who ?whose
 (:action refuse-immortality
  :parameters (?who - hero ?whose - god)
  :precondition (and (offered-immortality) (held-by ?whose) (nymph ?whose)
                     (not (took-immortality)))
  :effect (and (not (offered-immortality)) (forall (?up - band ?have - band)
                 (when (and (kleos ?have) (rung-up ?up ?have))
                       (and (kleos ?up) (not (kleos ?have)))))))

 ;; @gloss take it
 ;; @tell He takes it. The years stop counting and so does everything else.
 ;; @span You became immortal.
 ;; @meter kleos-20 ithaca-40
 ;; @tag ogygia ending
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whose
 (:action take-immortality
  :parameters (?who - hero ?whose - god)
  :precondition (and (offered-immortality) (held-by ?whose) (nymph ?whose)
                     (not (took-immortality)))
  :effect (and (took-immortality) (not (offered-immortality))))

 ;; @gloss build a raft
 ;; @tell Twenty trees, an auger, and a sail she cuts herself.
 ;; @span You built a raft.
 ;; @meter years+1 kleos+4
 ;; @tag ogygia
 (:action build-a-raft
  :parameters (?who - hero ?whose - god ?where - place)
  :precondition (and (at ?who ?where) (nymph-here ?where) (held-by ?whose)
                     (not (ship-whole)) (not (raft-built))
                     (not (took-immortality)))
  :effect (and (raft-built) (not (held-by ?whose))))

 ;; @gloss put the raft in the water
 ;; @tell Seventeen days on his own timber, and on the eighteenth the storm
 ;; @tell takes the raft apart under him.
 ;; @span You sailed the raft to {?to}.
 ;; @meter years+1 kleos+4
 ;; @tag ogygia
 (:action sail-the-raft
  :parameters (?who - hero ?from - place ?to - place)
  :precondition (and (at ?who ?from) (leg ?from ?to) (raft-built)
                     (not (home-here ?to)) (not (= ?from ?to)))
  :effect (and (not (at ?who ?from)) (at ?who ?to) (not (raft-built))))

 ;; ==================================================================
 ;; SCHERIA — the last court before home
 ;; ==================================================================

 ;; @gloss go to her with nothing on
 ;; @tell He comes out of the bushes covered in salt and asks her, very
 ;; @tell carefully, whether she is a goddess.
 ;; @span You supplicated {?whom}.
 ;; @meter kleos+4 divine+6
 ;; @tag scheria
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whom
 (:action supplicate
  :parameters (?who - mortal ?whom - noble ?where - place)
  :precondition (and (at ?who ?where) (court-here ?where) (host ?whom)
                     (alive ?whom) (not (supplicated ?whom))
                     (not (ship-whole)))
  :effect (and (supplicated ?whom)))

 ;; The one place in the poem where kleos is manufactured rather than
 ;; earned: the story of the voyage, told well, in a hall that will
 ;; repeat it.
 ;; @gloss tell them the whole thing
 ;; @tell He tells it from the horse to the raft, and they do not
 ;; @tell interrupt him once.
 ;; @span You told them your story.
 ;; @meter kleos+18 years+1
 ;; @tag scheria
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whom
 (:action tell-your-story
  :parameters (?who - mortal ?whom - noble ?where - place)
  :precondition (and (at ?who ?where) (court-here ?where)
                     (supplicated ?whom) (not (story-told)))
  :effect (and (story-told) (forall (?up - band ?have - band)
                 (when (and (kleos ?have) (rung-up ?up ?have))
                       (and (kleos ?up) (not (kleos ?have)))))))

 ;; @gloss let them take you home
 ;; @tell He is asleep when they carry him ashore, and asleep when they
 ;; @tell leave.
 ;; @span They carried you home.
 ;; @meter years+1
 ;; @tag scheria
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?whom ?who
 (:action be-conveyed-home
  :parameters (?who - hero ?whom - noble ?from - place ?to - place)
  :precondition (and (at ?who ?from) (court-here ?from) (host ?whom)
                     (story-told) (supplicated ?whom) (leg ?from ?to)
                     (home-here ?to) (prophecy-heard)
                     (forall (?g - god)
                             (or (not (owns-the-sea ?g))
                                 (not (wrathful ?g))))
                     (not (ship-whole)) (not (= ?from ?to)))
  :effect (and (not (at ?who ?from)) (at ?who ?to) (conveyed)))

 ;; ==================================================================
 ;; ITHACA
 ;; ==================================================================

 ;; The hall does not just wait. When the hold slips, the suitors stop
 ;; pretending to court and start clearing the succession — a betrayal
 ;; with a body in it, plotted where nobody testifies to it, and every
 ;; year the master is away makes it easier.
 ;; @gloss (the suitors move against the prince)
 ;; @tell The young man goes out to the farms one morning and does not
 ;; @tell come back from them.
 ;; @span The suitors killed {?whom}.
 ;; @observe unwitnessed
 ;; @meter ithaca-20 divine-10
 ;; @tag ithaca
 ;; @kind event
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?who ?whom
 (:action ambush-the-prince
  :parameters (?who - noble ?whom - mortal ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (at ?whom ?where)
                     (suitor ?who) (alive ?who) (kin ?whom) (alive ?whom)
                     (not (wife ?whom)) (not (suitors-dead))
                     (not (suitors-spared)) (not (home))
                     (not (ithaca-hold secure)))
  :effect (and (not (alive ?whom)) (shade ?whom)
               (forall (?lo - band ?hi - band)
                 (when (and (ithaca-hold ?hi) (rung-down ?lo ?hi))
                       (and (ithaca-hold ?lo) (not (ithaca-hold ?hi)))))))

 ;; @gloss come ashore as a beggar
 ;; @tell She puts twenty years on him in about four seconds.
 ;; @span You landed disguised.
 ;; @meter divine+6
 ;; @tag ithaca
 ;; @intensity 1
 ;; @sign neutral
 ;; @directed ?who ?whose
 ;; Coming ashore as a beggar is not caution, it is knowledge: you
 ;; only put twenty years on your own face if you already know what
 ;; is sitting in your hall. A first life has to walk in openly and
 ;; pay for it; the second one knows better.
 ;; [deferred] @foreknown ithaca
 (:action land-disguised
  :parameters (?who - hero ?whose - god ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (favours ?whose) (not (disguised))
                     (not (suitors-dead)) (not (home)))
  :effect (and (disguised)))

 ;; @gloss walk in as yourself
 ;; @tell He walks up the road to his own house with his own face on.
 ;; @span You walked in openly.
 ;; @meter kleos+8 ithaca-20
 ;; @tag ithaca
 (:action land-openly
  :parameters (?who - hero ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (not (disguised))
                     (not (home)))
  :effect (and (forall (?lo - band ?hi - band)
                 (when (and (ithaca-hold ?hi) (rung-down ?lo ?hi))
                       (and (ithaca-hold ?lo) (not (ithaca-hold ?hi)))))))

 ;; Object provenance, in fiction: a thing carries the beats it was a
 ;; parameter of, and this one has carried its beat for forty years.
 ;; @gloss let the old woman wash your feet
 ;; @tell She has his foot in her hands when she finds the ridge above the
 ;; @tell knee, and the basin goes over.
 ;; @span The scar was recognised.
 ;; @kind investigate
 ;; @tag ithaca evidence
 ;; @intensity 1
 ;; @sign neutral
 ;; @directed ?whom ?who
 (:action be-known-by-the-scar
  :parameters (?who - mortal ?whom - mortal ?what - thing ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (disguised)
                     (scar ?what) (kin ?whom) (alive ?whom)
                     (not (recognised-by ?whom)))
  :effect (and (recognised-by ?whom) (scar-shown)))

 ;; @gloss tell your son
 ;; @tell The beggar straightens up in the swineherd's hut and stops
 ;; @tell being a beggar.
 ;; @span You revealed yourself to {?whom}.
 ;; @meter kleos+4
 ;; @tag ithaca
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whom
 (:action reveal-yourself
  :parameters (?who - hero ?whom - mortal ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (disguised)
                     (kin ?whom) (alive ?whom) (not (recognised-by ?whom)))
  :effect (and (recognised-by ?whom)))

 ;; @gloss string the bow
 ;; @tell He turns it over twice, the way a man checks an instrument, and
 ;; @tell strings it sitting down.
 ;; @span You strung the bow.
 ;; @meter kleos+10
 ;; @tag ithaca
 (:action string-the-bow
  :parameters (?who - mortal ?what - thing ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (disguised)
                     (is-bow ?what) (not (bow-strung))
                     (not (suitors-dead)))
  :effect (and (bow-strung)))

 ;; @gloss kill them all
 ;; @tell It takes the rest of the afternoon and the hall has to be
 ;; @tell washed down afterwards.
 ;; @span You killed the suitors.
 ;; @meter kleos+14 divine-10
 ;; @tag ithaca
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?who ?whom
 (:action kill-the-suitors
  :parameters (?who - mortal ?whom - noble ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (bow-strung)
                     (suitor ?whom) (alive ?whom) (not (suitors-dead))
                     (not (suitors-spared)))
  :effect (and (suitors-dead) (not (alive ?whom)) (shade ?whom)
               (forall (?up - band ?have - band)
                 (when (and (ithaca-hold ?have) (rung-up ?up ?have))
                       (and (ithaca-hold ?up) (not (ithaca-hold ?have)))))))

 ;; @gloss let them go
 ;; @tell He puts the bow down. It is the strangest thing he has ever done.
 ;; @span You spared the suitors.
 ;; @meter divine+16 kleos-12
 ;; @tag ithaca
 ;; @intensity 2
 ;; @sign neg
 ;; @directed ?who ?whom
 (:action spare-the-suitors
  :parameters (?who - mortal ?whom - noble ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (bow-strung)
                     (suitor ?whom) (alive ?whom)
                     (not (suitors-dead)) (not (suitors-spared)))
  :effect (and (suitors-spared)))

 ;; @gloss make peace
 ;; @tell She stops the fighting in the road with one sentence.
 ;; @span {?whose} made the peace.
 ;; @meter divine+10 ithaca+10
 ;; @tag ithaca
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?whose ?who
 (:action make-the-peace
  :parameters (?who - mortal ?whose - god ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (favours ?whose)
                     (or (suitors-dead) (suitors-spared)) (not (home))
                     (not (ithaca-hold secure)))
  :effect (and (forall (?up - band ?have - band)
                 (when (and (ithaca-hold ?have) (rung-up ?up ?have))
                       (and (ithaca-hold ?up) (not (ithaca-hold ?have)))))))

 ;; The goal, and the thing the whole apparatus is pointed at.
 ;; @gloss go up to her
 ;; @tell She asks him to move the bed. He tells her why he cannot, and
 ;; @tell that is the end of the argument.
 ;; @span You came home.
 ;; @meter ithaca+20 years+1
 ;; @tag ithaca
 ;; @intensity 1
 ;; @sign neg
 ;; @directed ?who ?whom
 (:action come-home
  :parameters (?who - hero ?whom - noble ?where - place)
  :precondition (and (at ?who ?where) (home-here ?where) (wife ?whom)
                     (alive ?whom) (recognised-by ?whom)
                     (or (suitors-dead) (suitors-spared)) (not (home)))
  :effect (and (home) (reunited)))

 ;; ==================================================================
 ;; THE NOSTOI — changing Troy changes their homecomings too
 ;; ==================================================================

 ;; @gloss (news of Agamemnon)
 ;; @tell Word comes that he got home, and that getting home was the
 ;; @tell dangerous part.
 ;; @span Agamemnon was murdered at his own door.
 ;; @observe unwitnessed
 ;; @meter divine-6
 ;; @tag nostoi
 ;; @kind event
 ;; @intensity 4
 ;; @sign pos
 ;; @directed ?whom ?who
 (:action agamemnon-comes-home
  :parameters (?whom - noble ?where - place ?who - hero)
  :precondition (and (at ?who ?where) (news-here ?where) (city-sacked)
                     (king ?whom) (alive ?whom) (not (agamemnon-murdered)))
  :effect (and (agamemnon-murdered)))

 ;; @gloss (news of Menelaus)
 ;; @tell Word comes that he is in Egypt, and has been for some years.
 ;; @span Menelaus was blown to Egypt.
 ;; @observe unwitnessed
 ;; @tag nostoi
 ;; @kind event
 (:action menelaus-is-blown-south
  :parameters (?whose - god ?where - place ?who - hero)
  :precondition (and (at ?who ?where) (news-here ?where) (city-sacked)
                     (wrathful ?whose) (owns-the-sea ?whose)
                     (not (menelaus-lost)))
  :effect (and (menelaus-lost)))

 ;; The sacrilege's own bill, and the clearest worked example of the
 ;; Nostoi layer: violate the temple at Troy and a man drowns off Gyrae
 ;; ten years later. Nobody witnesses either beat.
 ;; @gloss (news of Ajax)
 ;; @tell Word comes that he made it onto the rock, said he had survived
 ;; @tell without the gods, and then the rock came apart.
 ;; @span Ajax drowned off the rocks.
 ;; @observe unwitnessed
 ;; @meter divine-8
 ;; @tag nostoi
 ;; @kind event
 ;; (One Ajax stands in for both of the tradition's: a man who died on
 ;; his own sword at Troy cannot also drown off Gyrae, so the news
 ;; requires him living.)
 (:action ajax-drowns
  :parameters (?whose - god ?where - place ?who - hero ?whom - noble)
  :precondition (and (at ?who ?where) (news-here ?where) (sacrilege)
                     (owns-the-sea ?whose) (rival-for-the-armour ?whom)
                     (alive ?whom) (not (ajax-drowned)))
  :effect (and (ajax-drowned) (not (alive ?whom)) (shade ?whom)
               (wrathful ?whose) (not (favours ?whose)))))
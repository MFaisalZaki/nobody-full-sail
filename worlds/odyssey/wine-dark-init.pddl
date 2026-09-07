;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; THE INSTANCE — one board for the physics above, in the same file.
;;
;; unified_planning's reader wants the two defines separately; split at
;; the line the instance starts on when loading:
;;
;;     import re
;;     from unified_planning.io import PDDLReader
;;     text = open('wine-dark.pddl').read()
;;     i = [m.start() for m in re.finditer(r'^\(define', text, re.M)][-1]
;;     task = PDDLReader().parse_problem_string(text[:i], text[i:])
;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; The arc: Troy to Ithaca, one editable timeline, one instance.
;;
;; The Iliad and the Odyssey as ONE continuous world, so that a decision
;; at Troy is a decision the player can go back and change, and the
;; Nostoi layer (Agamemnon, Menelaus, Ajax) answers to it. This is the
;; merge of the three former instances (thrinacia, voyage, nostos) —
;; the slice was a subset of the voyage, and the voyage a suffix of
;; this.
;;
;; There is NO GOAL HERE, deliberately: what a storyline is FOR belongs
;; to the scenario planner — the hero's motives are the `@wants`
;; directives in the domain, and the engine's own tiers decide what is
;; worth telling. The empty conjunction below is PDDL grammar's
;; required minimum, and it constrains nothing.
(define (problem odyssey) (:domain wine-dark)

 (:objects
    odysseus - hero
    eurylochus perimedes elpenor - companion
    poseidon athena zeus helios aeolus circe calypso - god
    polyphemus scylla - monster
    penelope telemachus antinous teiresias alcinous ajax agamemnon - noble
    troy ismaros lotus-land cyclops-island aeolia telepylos aiaia
    the-dead strait thrinacia ogygia scheria ithaca - place
    ship cattle wind-bag moly bow old-scar - thing)

 (:init
  ;; the ladders, as static facts. `rung-down` is one rung, `rung-down2`
  ;; is two — a schema says how far a beat costs by which relation it
  ;; binds, so the domain never needs arithmetic to lose a crew.
  (crew full) (ithaca-hold secure) (kleos unsung)
  (rung-down thinned full) (rung-down remnant thinned) (rung-down alone remnant)
  (rung-down2 remnant full) (rung-down2 alone thinned)
  (rung-up full thinned) (rung-up thinned remnant) (rung-up remnant alone)
  (rung-down pressed secure) (rung-down besieged pressed) (rung-down lost besieged)
  (rung-down2 besieged secure) (rung-down2 lost pressed)
  (rung-up secure pressed) (rung-up pressed besieged) (rung-up besieged lost)
  (rung-down unsung named) (rung-down named renowned)
  (rung-up named unsung) (rung-up renowned named)

  ;; who owns what
  (cyclops polyphemus) (rock scylla)
  (wife penelope) (kin penelope) (kin telemachus)
  (suitor antinous) (host alcinous) (king agamemnon)
  (rival-for-the-armour ajax)
  (owns-the-sea poseidon) (owns-the-sun helios) (owns-the-sky zeus)
  (keeper-of-winds aeolus) (witch circe) (nymph calypso)
  (gives-the-herb athena) (prophet teiresias)
  (is-ship ship) (sacred-cattle cattle) (scar old-scar)
  (is-bag wind-bag) (is-herb moly) (is-bow bow)

  ;; the board: the war's last act, Troy still standing. The horse is
  ;; not yet proposed, the temple not yet spared or violated, the
  ;; armour not yet argued over — the ten Troy beats are live, and how
  ;; the city falls (or whether the fleet just sails from under its
  ;; walls) is the telling's first business. The old poem-start board
  ;; (troy-fallen, city-sacked, the fleet leaving) is any state one
  ;; storm-the-walls or open-the-horse beat downstream of this one.
  (at odysseus troy) (called-at troy) (ship-whole) (troy-standing)
  ;; the cast, placed. Agents act where they stand: Agamemnon can sack
  ;; the city, Telemachus can string the bow, Antinous is in the hall.
  (at agamemnon troy) (at ajax troy)
  (at penelope ithaca) (at telemachus ithaca) (at antinous ithaca)
  (at alcinous scheria)
  (alive polyphemus) (alive scylla)
  (alive eurylochus) (with eurylochus)
  (alive perimedes) (with perimedes)
  (alive penelope) (alive telemachus) (alive antinous)
  (alive alcinous)
  (favours athena)
  (alive ajax) (alive agamemnon)
  (shade teiresias) (shade elpenor)

  ;; what is where
  (troy-here troy)
  (shrine-to troy athena) (shrine-to troy poseidon)
  (shrine-to aiaia circe) (shrine-to the-dead poseidon)
  (news-here troy) (news-here aiaia) (news-here scheria)
  (news-here ithaca)
  (town-here ismaros) (lotus-here lotus-land)
  (cave-here cyclops-island) (winds-here aeolia)
  (narrow-harbour telepylos) (witch-here aiaia) (dead-here the-dead)
  (strait-here strait) (cattle-here thrinacia) (nymph-here ogygia)
  (court-here scheria) (home-here ithaca)

  ;; the sea lanes: EVERY forward passage, because a `leg` is a sailable
  ;; crossing rather than adjacency — one beat is one landfall, and a
  ;; storyline that skips four islands spends one card on the skipping.
  ;; The one road back is up from the country of the dead, and no leg
  ;; reaches Ithaca: there is no sailing your own ship home — the only
  ;; conveyance is the Phaeacians', and their oars have conditions (see
  ;; be-conveyed-home). The spine holds without a wall.
  (leg troy ismaros) (leg troy lotus-land) (leg troy cyclops-island)
  (leg troy aeolia) (leg troy telepylos) (leg troy aiaia) (leg troy strait)
  (leg troy thrinacia) (leg troy ogygia) (leg troy scheria)
  (leg ismaros lotus-land) (leg ismaros cyclops-island) (leg ismaros aeolia)
  (leg ismaros telepylos) (leg ismaros aiaia) (leg ismaros strait)
  (leg ismaros thrinacia) (leg ismaros ogygia) (leg ismaros scheria)
  (leg lotus-land cyclops-island) (leg lotus-land aeolia)
  (leg lotus-land telepylos) (leg lotus-land aiaia) (leg lotus-land strait)
  (leg lotus-land thrinacia) (leg lotus-land ogygia) (leg lotus-land scheria)
  (leg cyclops-island aeolia) (leg cyclops-island telepylos)
  (leg cyclops-island aiaia) (leg cyclops-island strait)
  (leg cyclops-island thrinacia) (leg cyclops-island ogygia)
  (leg cyclops-island scheria) (leg aeolia telepylos) (leg aeolia aiaia)
  (leg aeolia strait) (leg aeolia thrinacia) (leg aeolia ogygia)
  (leg aeolia scheria) (leg telepylos aiaia) (leg telepylos strait)
  (leg telepylos thrinacia) (leg telepylos ogygia) (leg telepylos scheria)
  (leg aiaia strait) (leg aiaia thrinacia) (leg aiaia ogygia)
  (leg aiaia scheria) (leg strait thrinacia) (leg strait ogygia)
  (leg strait scheria) (leg thrinacia ogygia) (leg thrinacia scheria)
  (leg ogygia scheria) (leg aiaia the-dead) (leg the-dead aiaia)
  (leg scheria ithaca))

 ;; grammar's required minimum. It constrains nothing; see the header.
 (:goal (and))

 ;; ------------------------------------------------------------------
 ;; THE TERMINAL FORMULA.  A state is terminal when any line below
 ;; holds entire; each line is a conjunction of ground atoms, and the
 ;; lines disjoin:
 ;;
 ;;   TERMINAL(s) := DONE(s) or FAIL(s)
 ;;   DONE(s)  := (home & reunited)  |  took-immortality
 ;;   FAIL(s)  := ithaca-hold(lost)
 ;;
 ;; `@done` lines are resolutions — the story CLOSED, ranked by what
 ;; the ladders read there (see `@ending` in the domain header for how
 ;; each reads). `@fail` lines are defeats. A telling that reaches the
 ;; horizon on neither is OPEN: cut by the budget, not ended by the
 ;; world, and should be treated as no storyline at all.
 ;;
 ;; The third terminal kind the design names — the DEAD END, where no
 ;; resolution is reachable any more — is deliberately NOT here: it is
 ;; a reachability property, not a state formula, and only the engine
 ;; can decide it (no applicable action, or no @done line attainable).
 ;;
 ;; Note `crew alone` is NOT a defeat: arriving home alone, twenty
 ;; years late, every man lost, is the poem's own ending — the score
 ;; to beat, not a loss. (It was a defeat only in the old one-island
 ;; slice, where the story could go no further.)
 ;; @done (home) (reunited)
 ;; @done (took-immortality)
 ;; @fail (ithaca-hold lost)
)

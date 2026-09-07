%% winedark-facts.lp -- the topic's vocabulary tables, as data.
%%
%% The other half of what winedark.lp's rules consume: who counts as an
%% agent, whose story it is and what they are playing for, the standing
%% relations, who did what to whom (actor/target parameter positions),
%% the intensity table (each schema's dramatic weight, which the arc
%% axis reads), and the diversity axis tables -- one deedAxis per
%% weighted schema, one ladderAxis per ladder, one portAxis per
%% island, the fate table from the terminal lines. Every axis is a featureAxis/1 FACT beside
%% its table row, because `#external spreadAxis(A) : featureAxis(A)`
%% grounds with these facts and a rule head would not be there yet.
%% Task-vocabulary values travel wrapped in @q, the engine's spelling
%% bridge, exactly as the Python harvest used to emit them.
%%
%% Kept separate from winedark.lp ON PURPOSE: that file is the rules
%% and names no schema, object or fluent, so it stays loadable against
%% any world (test_close runs it over the hops fixture). This file is
%% the wine-dark data. When the domain changes -- a schema added,
%% renamed or reweighted, a port or terminal line added -- this file
%% must be edited to match by hand.

#program base.

agent(constant(@q("aeolus"))).
agent(constant(@q("agamemnon"))).
agent(constant(@q("ajax"))).
agent(constant(@q("alcinous"))).
agent(constant(@q("antinous"))).
agent(constant(@q("athena"))).
agent(constant(@q("calypso"))).
agent(constant(@q("circe"))).
agent(constant(@q("elpenor"))).
agent(constant(@q("eurylochus"))).
agent(constant(@q("helios"))).
agent(constant(@q("odysseus"))).
agent(constant(@q("penelope"))).
agent(constant(@q("perimedes"))).
agent(constant(@q("polyphemus"))).
agent(constant(@q("poseidon"))).
agent(constant(@q("scylla"))).
agent(constant(@q("teiresias"))).
agent(constant(@q("telemachus"))).
agent(constant(@q("zeus"))).
focalHero(constant(@q("odysseus"))).
motive(constant(@q("odysseus")), variable((@q("recognised-by"), constant(@q("penelope")))), 10).
motive(constant(@q("odysseus")), variable(@q("home")), 8).
motive(constant(@q("odysseus")), variable(@q("suitors-dead")), 3).
motive(constant(@q("odysseus")), variable((@q("blinded"), constant(@q("polyphemus")))), -2).
motive(constant(@q("odysseus")), variable(@q("heard-sirens")), 2).
tieFluent(@q("with")).
tieFluent(@q("favours")).
tieFluent(@q("wrathful")).
directedPos(@q("agamemnon-comes-home"), 0, 2).
directedPos(@q("ajax-falls-on-his-sword"), 0, 2).
directedPos(@q("ambush-the-prince"), 0, 1).
directedPos(@q("be-conveyed-home"), 1, 0).
directedPos(@q("be-kept"), 0, 1).
directedPos(@q("be-known-by-the-scar"), 1, 0).
directedPos(@q("becalm"), 0, 2).
directedPos(@q("blind-the-cyclops"), 0, 1).
directedPos(@q("break-the-ship"), 0, 2).
directedPos(@q("come-home"), 0, 1).
directedPos(@q("drink-the-cup"), 1, 0).
directedPos(@q("free-the-crew"), 0, 1).
directedPos(@q("give-a-false-name"), 0, 1).
directedPos(@q("kill-the-suitors"), 0, 1).
directedPos(@q("land-disguised"), 0, 1).
directedPos(@q("lay-the-curse"), 0, 2).
directedPos(@q("make-the-peace"), 1, 0).
directedPos(@q("open-the-bag"), 0, 1).
directedPos(@q("pass-the-rock"), 0, 1).
directedPos(@q("question-the-shade"), 0, 1).
directedPos(@q("raid-the-town"), 0, 1).
directedPos(@q("raise-a-grave"), 0, 1).
directedPos(@q("refuse-immortality"), 0, 1).
directedPos(@q("reveal-yourself"), 0, 1).
directedPos(@q("sack-the-city"), 0, 1).
directedPos(@q("sacrifice-to"), 0, 1).
directedPos(@q("shout-your-name"), 0, 1).
directedPos(@q("slaughter-the-cattle"), 0, 2).
directedPos(@q("spare-the-suitors"), 0, 1).
directedPos(@q("spare-the-temple"), 0, 1).
directedPos(@q("stay-the-year"), 0, 1).
directedPos(@q("steer-for-the-whirlpool"), 0, 1).
directedPos(@q("storm-the-walls"), 0, 1).
directedPos(@q("supplicate"), 0, 1).
directedPos(@q("take-immortality"), 0, 1).
directedPos(@q("take-the-bag"), 0, 1).
directedPos(@q("take-the-herb"), 1, 0).
directedPos(@q("tell-your-story"), 0, 1).
directedPos(@q("violate-the-temple"), 0, 1).
directedPos(@q("withdraw-at-once"), 0, 1).
featureAxis(did_agamemnon_comes_home).
deedAxis(did_agamemnon_comes_home, @q("agamemnon-comes-home")).
featureAxis(did_ajax_falls_on_his_sword).
deedAxis(did_ajax_falls_on_his_sword, @q("ajax-falls-on-his-sword")).
featureAxis(did_ambush_the_prince).
deedAxis(did_ambush_the_prince, @q("ambush-the-prince")).
featureAxis(did_becalm).
deedAxis(did_becalm, @q("becalm")).
featureAxis(did_blind_the_cyclops).
deedAxis(did_blind_the_cyclops, @q("blind-the-cyclops")).
featureAxis(did_break_the_ship).
deedAxis(did_break_the_ship, @q("break-the-ship")).
featureAxis(did_drink_the_cup).
deedAxis(did_drink_the_cup, @q("drink-the-cup")).
featureAxis(did_kill_the_suitors).
deedAxis(did_kill_the_suitors, @q("kill-the-suitors")).
featureAxis(did_lay_the_curse).
deedAxis(did_lay_the_curse, @q("lay-the-curse")).
featureAxis(did_pass_the_rock).
deedAxis(did_pass_the_rock, @q("pass-the-rock")).
featureAxis(did_raid_the_town).
deedAxis(did_raid_the_town, @q("raid-the-town")).
featureAxis(did_sack_the_city).
deedAxis(did_sack_the_city, @q("sack-the-city")).
featureAxis(did_shout_your_name).
deedAxis(did_shout_your_name, @q("shout-your-name")).
featureAxis(did_slaughter_the_cattle).
deedAxis(did_slaughter_the_cattle, @q("slaughter-the-cattle")).
featureAxis(did_steer_for_the_whirlpool).
deedAxis(did_steer_for_the_whirlpool, @q("steer-for-the-whirlpool")).
featureAxis(did_storm_the_walls).
deedAxis(did_storm_the_walls, @q("storm-the-walls")).
featureAxis(did_violate_the_temple).
deedAxis(did_violate_the_temple, @q("violate-the-temple")).
featureAxis(crew_left).
ladderAxis(crew_left, @q("crew")).
featureAxis(ithaca_left).
ladderAxis(ithaca_left, @q("ithaca-hold")).
featureAxis(kleos_left).
ladderAxis(kleos_left, @q("kleos")).
featureAxis(port_aeolia).
portAxis(port_aeolia, constant(@q("aeolia"))).
featureAxis(port_aiaia).
portAxis(port_aiaia, constant(@q("aiaia"))).
featureAxis(port_cyclops_island).
portAxis(port_cyclops_island, constant(@q("cyclops-island"))).
featureAxis(port_ismaros).
portAxis(port_ismaros, constant(@q("ismaros"))).
featureAxis(port_ithaca).
portAxis(port_ithaca, constant(@q("ithaca"))).
featureAxis(port_lotus_land).
portAxis(port_lotus_land, constant(@q("lotus-land"))).
featureAxis(port_ogygia).
portAxis(port_ogygia, constant(@q("ogygia"))).
featureAxis(port_scheria).
portAxis(port_scheria, constant(@q("scheria"))).
featureAxis(port_strait).
portAxis(port_strait, constant(@q("strait"))).
featureAxis(port_telepylos).
portAxis(port_telepylos, constant(@q("telepylos"))).
featureAxis(port_the_dead).
portAxis(port_the_dead, constant(@q("the-dead"))).
featureAxis(port_thrinacia).
portAxis(port_thrinacia, constant(@q("thrinacia"))).
featureAxis(port_troy).
portAxis(port_troy, constant(@q("troy"))).

%% the WEIGHTS: each schema's @intensity, the dramatic charge a
%% beat of it carries — the arc axis reads these to find the climax
intensity(@q("agamemnon-comes-home"), 4).
intensity(@q("ajax-falls-on-his-sword"), 4).
intensity(@q("ambush-the-prince"), 4).
intensity(@q("be-conveyed-home"), 1).
intensity(@q("be-kept"), 2).
intensity(@q("be-known-by-the-scar"), 1).
intensity(@q("becalm"), 3).
intensity(@q("blind-the-cyclops"), 4).
intensity(@q("break-the-ship"), 4).
intensity(@q("come-home"), 1).
intensity(@q("drink-the-cup"), 3).
intensity(@q("free-the-crew"), 2).
intensity(@q("give-a-false-name"), 1).
intensity(@q("kill-the-suitors"), 4).
intensity(@q("land-disguised"), 1).
intensity(@q("lay-the-curse"), 4).
intensity(@q("make-the-peace"), 1).
intensity(@q("open-the-bag"), 2).
intensity(@q("pass-the-rock"), 3).
intensity(@q("question-the-shade"), 1).
intensity(@q("raid-the-town"), 3).
intensity(@q("raise-a-grave"), 1).
intensity(@q("refuse-immortality"), 2).
intensity(@q("reveal-yourself"), 1).
intensity(@q("sack-the-city"), 4).
intensity(@q("sacrifice-to"), 1).
intensity(@q("shout-your-name"), 3).
intensity(@q("slaughter-the-cattle"), 4).
intensity(@q("spare-the-suitors"), 2).
intensity(@q("spare-the-temple"), 1).
intensity(@q("stay-the-year"), 1).
intensity(@q("steer-for-the-whirlpool"), 3).
intensity(@q("storm-the-walls"), 4).
intensity(@q("supplicate"), 1).
intensity(@q("take-immortality"), 1).
intensity(@q("take-the-bag"), 1).
intensity(@q("take-the-herb"), 1).
intensity(@q("tell-your-story"), 1).
intensity(@q("violate-the-temple"), 4).
intensity(@q("withdraw-at-once"), 1).

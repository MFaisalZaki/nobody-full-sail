%% winedark.lp -- the topic half of the polyscene contract.
%%
%% The engine knows how to tell a sound story about SOME world. This
%% says what this world is, in the vocabulary interface.lp declares. It
%% is deliberately thin: everything world-shaped is already in the PDDL,
%% and what the engine needs beyond the PDDL is only the things a
%% domain file has nowhere to put -- which parameter of which schema is
%% the actor and which the target, who counts as a stranger to whom,
%% and which axes two tellings of this world can DIFFER on.
%%
%% All of it arrives as DATA (winedark-facts.lp, loaded beside this
%% file), so this file names no schema, no object and no fluent of the
%% storyworld.

% the vocabulary tables arrive as data (winedark-facts.lp, or a
% test's own facts()); a world that supplies none leaves them
% undefined, and the rules reading them must go quiet
#defined focalHero/1.
#defined agent/1.
#defined tieFluent/1.
#defined directedPos/3.
#defined deedAxis/2.
#defined ladderAxis/2.
#defined portAxis/2.
#defined fateNeed/2.
#defined intensity/2.

#program base.

%% the protagonist is nominated, not elected: this is one hero's story
%% and the domain says whose.
protagonist(H) :- focalHero(H).

%% ========================================================================
#program step(t).

%% --- who did what to whom ------------------------------------------------
%% `directedPos(Class, I, J)` says that parameter I of Class is the actor
%% and parameter J the target. The engine cannot know that and the PDDL
%% has nowhere to say it, so the domain says it with `;; @directed`.
directed(N, A, B, t) :- event2(N,A,B,t),     directedPos(N,0,1), agent(A), agent(B).
directed(N, A, B, t) :- event3(N,A,B,_,t),   directedPos(N,0,1), agent(A), agent(B).
directed(N, A, C, t) :- event3(N,A,_,C,t),   directedPos(N,0,2), agent(A), agent(C).
directed(N, A, B, t) :- event4(N,A,B,_,_,t), directedPos(N,0,1), agent(A), agent(B).
directed(N, A, C, t) :- event4(N,A,_,C,_,t), directedPos(N,0,2), agent(A), agent(C).
directed(N, A, D, t) :- event4(N,A,_,_,D,t), directedPos(N,0,3), agent(A), agent(D).

%% --- who is a stranger to whom -------------------------------------------
%% The engine only ever asks "are these two strangers?" — a bolt from
%% nowhere between people with no standing relation is the charge. Here
%% a standing relation is: sailing with the protagonist, or being a god
%% who has taken an interest in him either way.
tie(A, B, t) :- protagonist(A), tieFluent(F), holds1(F, B, t).
tie(B, A, t) :- tie(A, B, t).

%% ========================================================================
%% The diversity axes: what makes two tellings of THIS world different.
%%
%% The engine's own axes count beats and cast, and cannot tell two
%% twenty-eight-beat homecomings apart — both are the same length with
%% the same people in them. What distinguishes them is what they COST,
%% which is what the design says an ending is ranked by and what the
%% ladders carry. So the rung at the close is an axis, one per ladder.
%%
%% The axis TABLE is supplied as facts by the topic (featureAxis/1 and
%% ladderAxis/2 both arrive from facts()), not derived by a rule here:
%% `features.lp` declares `#external spreadAxis(A) : featureAxis(A)`, and
%% a featureAxis that only exists as the head of a rule is not there yet
%% when that external is grounded.
#program check(t).
feature(A, V) :- query(t), ladderAxis(A, F), holds1(F, V, t).

%% ------------------------------------------------------------------------
%% ...and one axis for the ROAD, not the price.
%%
%% Spreading on the ladders alone gives twelve tellings that differ in
%% what they cost and agree on where they went — and in a weave built
%% FROM those tellings, a road nobody took is a road the player cannot
%% take either. So the number of places called at is an axis too: it is
%% the coarsest honest summary of a route.
#program base.
featureAxis(ports_called).
visited(P, 0) :- focalHero(H), holds2("at", H, P, 0).

#program step(t).
visited(P, t) :- focalHero(H), holds2("at", H, P, t).
visited(P, t) :- visited(P, t-1).

#program check(t).
feature(ports_called, N) :- query(t), N = #count { P : visited(P, t) }.

%% ...and one axis per PORT, because "how many" is not "which".
%%
%% `ports_called` counts, and a count cannot ask the planner to take the
%% other fork — eleven of fourteen tellings called at nine ports and at
%% the SAME nine. One yes/no axis per place can: spread on three of them
%% and the enumeration has to find roads that differ in where they went.
#program check(t).
feature(A, yes) :- query(t), portAxis(A, P), visited(P, t).
feature(A, no)  :- query(t), portAxis(A, P), not visited(P, t).

%% ...and one axis for what was DONE, which is the only kind that can
%% ask for an EARLY fork.
%%
%% Every axis above is read at the close: which ports were called at,
%% which rung each ladder stands on when the telling ends. Two roads that
%% agree for twenty beats and part in the last quarter are as different,
%% under those axes, as two that part at the first island — so the
%% enumeration has no reason to prefer the second, and it does not find
%% it. Measured: going from sixteen tellings to twenty-four added eight
%% more roads and not one new early fork.
%%
%% A weave built from those tellings inherits the shape exactly. The
%% player's rewind needs a fork with a future still in front of it, and a
%% fork at step 23 of 28 has nowhere to fast-forward to. So: did this
%% telling do this thing, at any point? `eventName/2` is the engine's own
%% reification of which schema fired when, so this costs one accumulator.
#program step(t).
done(N, t) :- eventName(N, t).
done(N, t) :- done(N, t-1).

#program check(t).
feature(A, yes) :- query(t), deedAxis(A, N), done(N, t).
feature(A, no)  :- query(t), deedAxis(A, N), not done(N, t).

%% ...and one axis for the ARC: the telling's dramatic shape,
%% summarised as its climax — the highest weight any beat carries, and
%% the first beat that carries it, as one (weight, beat) value. Two
%% roads to the same fate that peak differently are different stories;
%% two tellings that peak alike retell one arc, however the filler
%% differs. Weights arrive as intensity/2 facts (the @intensity table).
#program base.
featureAxis(arc).

#program step(t).
beatWeight(W, t) :- eventName(N, t), intensity(N, W).

#program check(t).
arcPeak(P) :- query(t), beatWeight(P, _), P = #max { W : beatWeight(W, TT) }.
feature(arc, (P, T)) :- arcPeak(P), T = #min { TT : beatWeight(P, TT) }.

%% ...and one axis for the FATE: which terminal line the telling closed
%% on — different endings above all. The instance's `;; @done` and
%% `;; @fail` lines arrive as fateNeed/2 facts: a fate is MODELLED, not
%% named — its identifying term is the tuple of its own atoms, each a
%% raw reified variable term, and the line set derives from the needs.
%% Raw holds/3 rather than holds1/holds2 because a terminal atom may be
%% nullary — `(home)` — and the arity read-backs never see those. A line
%% closed the telling when every atom of it holds at the close.
#program base.
featureAxis(fate).
fateLine(F) :- fateNeed(F, _).

#program check(t).
fateMissed(F, t) :- query(t), fateNeed(F, X), not holds(X, value(X, true), t).
fateClosed(F, t) :- query(t), fateLine(F), not fateMissed(F, t).
anyFate(t)       :- fateClosed(_, t).
feature(fate, F) :- fateClosed(F, t).

%% the model itself says which line closed: shown, so consumers (the
%% narrator first) read the fate off the answer set instead of
%% re-evaluating the formula against a replayed state
#show fateClosed/2.

%% And the fate is NOT optional: a telling that runs out of beats short
%% of every terminal line is not a story, it is a story cut off — the
%% design presents complete storylines only, so the solver never
%% generates the incomplete ones. Continuations inherit this for free
%% (same control), and exhaustion keeps its meaning: a cut is exhausted
%% when no UNTOLD future CLOSES from it. Guarded on fateLine so a world
%% that declares no terminal lines keeps solving.
:- query(t), fateLine(_), not anyFate(t).

%% ========================================================================
%% Retell: fork a told story where the SOLVER chooses the cut.
%%
%% The seed telling arrives as externals — seedBeat(A, t) for its
%% beats — assigned true for one enumeration and back to false after;
%% false is inert, so a solve with no seed raised behaves exactly as
%% before. Agreement is prefix-shaped by construction (agree(t) needs
%% agree(t-1)); the cut is where it stops, and the solver maximises it
%% ABOVE the whole objective stack (@5; the engine tops out at @4):
%% retell as much of the seed as a genuinely different story allows.
%%
%% What COUNTS as different is not decided here — it is the run's own
%% diversity contract: the seed's spread fingerprint is banned on
%% entry, so under raised axes every fork differs from the seed on one
%% of them — raise fate for a new ending, raise arc for the same fate
%% peaking differently — and with no spread raised, distinctness falls
%% back to the exact telling, as everywhere else. Ban-and-re-solve
%% then sweeps a seed's forks deepest cut first.

#program base.
agree(0).

#program step(t).
#external seedBeat(A, t) : action(A).
agree(t) :- agree(t-1), seedBeat(A, t), occurs(A, t).

#program check(t).
cutDepth(C) :- query(t), C = #max { T : agree(T) }.
#maximize { C@5 : cutDepth(C) }.

%% ========================================================================
%% No state revisited.
%%
%% A telling that returns to a state it has already stood in is a man
%% pacing, not a story -- and a rewind game cannot afford storylines
%% that contain their own rewinds. So any two time points of a telling
%% must differ on at least one fluent. Written on the planner's raw
%% holds/3 so it covers every arity (the domain has forty nullary
%% fluents holds1/holds2 never see), and as a hard constraint rather
%% than a charge: loop-freedom also prunes the search.
%%
%% World-agnostic on purpose -- it could move into the engine's own
%% encodings unchanged.

#program base.
timePoint(0).

#program step(t).
timePoint(t).
stateDiffers(T, t) :- holds(X, value(X,true), t),
                      not holds(X, value(X,true), T), timePoint(T), T < t.
stateDiffers(T, t) :- holds(X, value(X,true), T),
                      not holds(X, value(X,true), t), timePoint(T), T < t.
:- timePoint(T), T < t, not stateDiffers(T, t).

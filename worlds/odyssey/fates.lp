%% a fate IS its terminal conjunction: the identifying term is the
%% tuple of the line's own atoms, nothing coined — winedark.lp derives
%% the line set from these needs (fateLine(F) :- fateNeed(F, _))
fateNeed((variable(@q("home")), variable(@q("reunited"))),
         variable(@q("home"))).
fateNeed((variable(@q("home")), variable(@q("reunited"))),
         variable(@q("reunited"))).
fateNeed((variable(@q("took-immortality")),),
         variable(@q("took-immortality"))).
fateNeed((variable((@q("ithaca-hold"), constant(@q("lost")))),),
         variable((@q("ithaca-hold"), constant(@q("lost"))))).

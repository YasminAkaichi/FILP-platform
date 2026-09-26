% The classic ILP toy example: learn "grandparent" from "parent" facts.

max_clauses(1).
max_vars(4).
max_body(2).

head_pred(grandparent,2).
body_pred(parent,2).

type(grandparent,(person,person)).
type(parent,(person,person)).

% directions specify which arguments are input and which are output
direction(grandparent,(in,out)).
direction(parent,(in,out)).

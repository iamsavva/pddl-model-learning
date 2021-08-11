## Definitions
Below I will attempt to follow the notation used in PDDL as closely as possible, while developing explicit definitions for them (because I couldn't find explicit definitions for PDDL notation).

### Types, Objects, Variables, Terms
I will first define types, objects, variables, and terms.

- A **type** is a string that represents a user-defined datatype that encapsulates data structures based on some semantic hierarchy. A type defines a set of values encapsulated by it - a **typeset**, e.g. type `name` may explicitly define a typeset of strings `(Alice, Bob, Charlie)`, type `positive_int` may define a typeset of integers `(1,2,3,...)`.
- An **object** is a typed string that is mapped to a specific value of this type. It is denoted as `object - type`, e.g. `alice - person`, `twenty_two - age`, `pos_1 - location`, etc. All objects are mapped to particular values at their initialization, e.g., `value(alice) = Alice`, `value(twenty_two) = 22`, `value(pos_1) = (0,1)`.
- A **variable** is a typed string that represents any arbitrary object of that type - it is a placeholder for a object, denoted as `Variable - type`, e.g.: `Alice - person`, `X - age`, `XyZ - location`.
	- A variable defines a set objects which corresponds to its typeset.
- A **term** is an object or a variable.

### Predicates, Atoms, Literals
I will now define predicates, atoms, and literals.

- A **predicate of arity *n*** is a boolean function of *n* terms, denoted as $`p/n`$, where $`p`$ is the predicate symbol and *n* is the number of term arguments, e.g.: `happy/1`, `position/2`, etc.
- An **atom** is a formula $`p(t_1, .. t_n)`$, where $`p/n`$ is a predicate and each $`t_i`$ is a term, e.g. `position( arm, (0,1) )` or `happy( X )`. 
	- A predicate is a function, while an atom is an evaluation of this function for some specific terms. Due to the similarity of these definitions, I will use them interchangeably. 
- A **literal** is an atom $`A`$ or its negation $`\neg A`$.
	- Since an atom is an evaluation of a predicate and a literal is a positive or a negative atom, all literals are either true or false.
- A literal is **ground** if it includes no variables.

### System, system's state

I will now define a system; in PDDL, a system can be perceived as the program or the problem.

- A **knowledge base (KB)** is a finite set of predicates.
	- A literal belongs to the KB if the predicate of the literal's underlying atom belongs to the KB.
- An **object set** is a set of objects.
- An object set and a knowledge base form a **system**.
> **_NOTE:_** From now on, all predicates, atoms, and literals are assumed to belong to the system's KB and all the objects are assumed to belong to the system's object set.

I will now define a state of a system.

- **The state of the system** is a set of ground positive atoms. 
The following is true:
	- All atoms present in state are asserted as true.
	- A closed-world assumption is made: if an atom is not in a state, it is assumed false.
	- Negative atoms are not asserted (STRIPS will hold later).
- A positive ground atom in a state is an assertion on the objects in the system, e.g., `atConf( arm, q )` asserts that `arm` is at configuration `q`.

### Does a literal hold in a state?
I will now define how literals are to be evaluated against a state.

- Evaluating whether a positive ground atom $`A`$ holds in a state is a search over all atoms in a state in search of a matching atom. 
- Evaluating whether a negative ground atom $`\neg A`$ holds in a state is done with negation as failure: if a search for the positive atom $`A`$ fails, then $`\neg A`$ is true.
- Evaluating whether a non-ground positive atom $`A(p, V)`$ holds in a state is a search for a set of objects $`q`$, such that $`A[V/q]`$ is an atom present in the state.
- Evaluating whether a non-ground negative atom $`\neg A(p,V)`$ holds in a state is done with negation as failure: if the search to prove $`A(p,V)=\text{true}`$ fails, then $`\neg A(p,V)`$ is true. In other words, $`\neg A(p,V)`$ is only true if there exists no set of objects $`q`$, such that $`A[V/q]`$ belongs to the state.
- Let $`L`$ be a set of literals. We say that **$`L`$ is satisfied on the state** or that **the state satisfies $`L`$**, if each literal in $`L`$ holds in the state.


### Observation
- An **observation** of the system is a set of positive ground atoms that is a subset of the state of the system.

### Rule-based Action
I will now define a rule-based action (I am drawing inspiration from the [PDDLStream paper](https://arxiv.org/abs/1802.08705)).

- A **parameters $`X`$** is a tuple of variables that parameterize rules and actions.
- A **rule** is a notation for a tuple of two sets of literals parameterized by a parameter tuple $`X`$. The first set is denoted as preconditions: $`\text{pre}(\text{rule}, X)`$, and the second set is denoted as effects: $`\text{eff}(\text{rule}, X)`$, with $`\text{eff}^-(\text{rule}, X)`$ and $`\text{eff}^+(\text{rule}, X)`$ denoting subsets of negative and positive effect literals respectively.
- A **rule instance** is a rule with its parameters $`X`$* replaced by a tuple of objects $`x`$: $`\text{rule}(x)`$.
- A **rule instance is applicable on the state** if the $`\text{pre}(\text{rule}, x)`$ is satisfied on the state.
- A **result of applying a rule instance on a state $`S`$** is a new state $`( S \setminus \text{eff}^-(\text{rule}, x) ) \cup \text{eff}^+(\text{rule}, x)`$.
- An **action** is given by a tuple of parameters $`X`$ and a set of rules $`R`$, each parameterized by $`X`$.
- An **action instance** is an action with its parameters $`X`$ replaced by a tuple of objects $`x`$: $`a(x)`$.
- A **result of applying an action instance on a state *S*** is a new state $`( S \setminus ( \text{eff}^-(r_1, x),..\text{eff}^-(r_k, x) ) ) \cup ( \text{eff}^+(r_1, x),..\text{eff}^+(r_k, x) ) `$, where $`(r_1, r_2, .. r_k)`$ is a subset of rules that are applicable on $`S`$.

> **A few PDDL notes to make:**
> - `:strips` are assumed true: I use STRIPS add and delete lists to define an action, I am also making the STRIPS assumption (every literal unmentioned in the effects of the rules remains unchanged in the resulting state).
> - I presume that the action specification is conjunctive, and hence do not allow `:disjunctive-preconditions`.
> - By allowing the action to have variables other than parameters, I am implicitly allowing existential quantifiers, yet existential quantifiers aren't allowed in the effects. A way to introduce such variables is through the `:vars` list: variables in `:vars` behave as if bound existentially in preconditions and universally in effects, with an error thrown if more than one instance satisfies the existential precondition.
> - While the provided definitions don't forbid specific objects (rather than variables) from appearing in the preconditions or effects, in practice in PDDL that would require making these objects `:constants`. Since constants aren't commonly used - they're just declared as objects repeatedly instead - I assume that the `:constants` set is empty, and hence that all terms are variables in the action specification.
> - This is a rule-based action - i.e., a conditional effect from `:conditional-effects`. A regular conjunctive PDDL action can be defined as follows:
> 
> #### Action
> 
> - An **action** $`a(X)`$ is given by a tuple of parameters $`X`$, a set of literal preconditions $`\text{pre}(a, X)`$, and a set of literal effects $`\text{eff}(a, X)`$, with with $`\text{eff}^-(a, X)`$ and $`\text{eff}^+(a, X)`$ denoting subsets of negative and positive effect literals respectively.
> - An **action instance** is an action with its parameters $`X`$ replaced by a tuple of objects $`x`$: $`a(x)`$.
> - An **action instance is applicable on a state** if the $`\text{pre}(a, x)`$ is satisfied on the state.
> - A **result of applying an action instance on a state $`S`$** is a new state $`( S \setminus \text{eff}^-(a, x) ) \cup \text{eff}^+(a, x)`$.
> 
> - To summarize, given the above set of definitions, the following `:requirements` are made: `:strips`, `:typing`, `:equality`, `:conditional-effects`, and `:quantified-preconditions` (but only through `:vars` lists).


### Temporality
I will now define temporality.

- Temporal labeling is an integer number assigned to the data structures defined above.
- A state of a system at time $`T`$ is a unique temporally-labeled system state.
- Initial state of the system is given a temporal label of $`0`$.
- A timeline is a set of temporally labeled states, initialized with a state at time $`0`$.
- An observation of a system at time $`T`$ is an observation of a state at time $`T`$.
- Applying an action instance on a state at time $`T`$ results in a new state, denoted as state at time $`T+1`$, which is added to the timeline.
	- Actions can only be applied on the latest state in the timeline.


## State Filter

### Filter Definition

I will now define a state filter.
Consider a system $`S`$ (i.e., an object set and a KB) an set of action specifications $`A`$, and an initial state of a system at time $`0`$. Suppose that actions are applied on the system, changing the system's state. The goal of a filter is to estimate a set of possible system states at the most recent time $`T`$, given the applied action instance and the system observations.

- A filter is initialized with a system $`S`$ (an object set and a KB), an observation of the system state at time $`0`$, and a set of action specifications $`A'`$. 
	- Note that while $`A`$ and $`A'`$ describe the same actions, the two sets may be different. $`A`$ represents the true actions, while $`A'`$ represents potentially inaccurate action models available to the filter.
	- Hence action specification is assumed inaccurate, while the observations are assumed to be deterministic and accurate.
- The filter may contain filter-specific data structures used in its operation. State of the filter at time $`T`$ is given by the values of these data structures.

At each iteration, the filter is to solve the following problem:

INPUTS:
- State of the filter at time $`T`$.
- A tuple of objects $`x`$, which parameterize an action applied on a system at time $`T`$.
- An observation of the system at time $`T+1`$.

OUTPUTS: 
- The state of the filter at time $`T+1`$.
- Boolean: given the current action model, are there any system states that satisfy the observed action-observation sequence that concluded at $`T`$?

### Filter Properties

An enumerating optimal logical filter (EOLF) is a filter that at any time T maintains a full set of possible system states, the $`\text{PSS}`$. At each iteration, EOLF first applies the parameterized action model to each of the states in $`\text{PSS}`$, and then removes all the states in $`\text{PSS}`$ that do not satisfy the provided observation ($`\text{size(PSS)}`$ can only decrease as a result of each of these operations). If $`\text{PSS}`$ is null, the filter returns *false*, concluding that the available action model is inaccurate and does not satisfy the provided action-observation sequence. After each filtering iteration, EOLF finds the largest set of literals that are simultaneously true in each state of $`\text{PSS}`$. This set is known as the *most specific conjunctive generalization* of the state.

- A **filter is optimal** if it is able to directly obtain or otherwise derive the set of all possible system states.
- A filter is **proper-good** if it is able to directly obtain or otherwise derive the most specific conjunctive generalization of the state.

The problem of optimal filtering is deriving a provably optimal filter.
The problem of proper-good filtering is deriving a provably proper-good filter.

### Proposed solution to the problem of optimal filtering

#### Definitions 

- A **replacement set of an atom $`A`$**, denoted as $`\text{replacement}(A)`$, is a set of all unique predicates that can be acquired by replacing the variables of an atom with same-type objects from the system's object set.
- Given a system (object set + KB), **system's full atomic set** is a set of all unique ground atoms that can be generated with system's object set and the predicates from system's KB.
- A **covering set of atoms** is a set of atoms whose replacement set union is equal to the system's full atomic set.
- A **disjunctive set of atoms** is a set of atoms whose replacement sets are disjunctive (have no common ground atoms).
- Covering and disjunctive sets of literals are defined in the same fashion.

The important defintions are:

- A **set of all possible system states (PSS)** at time $`T`$ are all systems states that satisfy the action-observation sequence from time $`0`$ to $`T`$.
- For a set of atoms $`T_\text{set}`$, let $`\text{PSS}(T_\text{set})`$ be all possible system states that contain $`T_\text{set}`$.
- A **disjunctive replacement atom covering**  is a set of atoms $`(A_1,... A_k)`$, such that:
	- $`( \text{replacement}(A_1), .. \text{replacement}(A_k) )`$ are mutually disjunctive
	- $`( \text{replacement}(A_1), .. \text{replacement}(A_k) )`$ cover the system's full atomic set.
	- for any valid system state, for each atom $`B_i`$ in the state there exists an atom $`A_i`$, such that $`B_i \in \text{replacement}(A_i)`$, and no two atoms $`B_i`$, $`B_j`$ belong to the same $`\text{replacement}(A_i)`$.

> **NOTE:**
> - I assume that a (minimal) disjunctive replacement atom covering **exists** and is provided as an input to the filter. The important assumption I make is as follows:
> - **Each valid system state contains no more than one atom from each replacement set in the disjunctive replacement atom covering.**
> - While the existance of such a set is not given, nor is finding it an easy task, it's actually rather easy for most robotic systems. This is because most physical systems can be easily described in an object-oriented fashion, which can be used to come up with the aforementioned covering.
> - Each atom would usually coincide with the observation / measurement / type mode of individual physical object in the environment.
> - For example, such covering may include atoms like: `atPos(obj1, X), atPos(obj2, X), .. etc` (1 variable: physical objects can only be in 1 location at any time), or `isBtwnTwoObjects(obj1, X, Y`) (2 variables: if one exists, there is a unique pair of objects `x`, `y` such that `obj1` is in between them), or `movable(obj1)` (0 variables; it's either true or not ).

- A **hypothesis** $`H`$ is a set of ground atoms, such that no two atoms from $`H`$ belong to the same replacement set of an atom from the disjunctive replacement atom covering set.
- Let $`H`$ be a hypothesis. $`\text{SS}(H)`$ is defined as a set of valid system states, where each system state contains $`H`$.
- A **disjunctive set covering of PSS** is a set of hypothesis $`(H_1, ..\; H_k)`$, such that for any $`i`$, $`j`$, $`\text{SS}(H_i)`$ and $`\text{SS}(H_j)`$ are disjunctive, and the union $`( \text{SS}(T_1) \cup .. \cup \text{SS}(T_k) ) = \text{PSS}`$.

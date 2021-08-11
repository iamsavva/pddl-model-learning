
# Problem Statements

## The problem of logical filtering

### Description:
Consider a system with boolean, categorical, and continuous states. The system can produce observations - measurements of the values of some of these states, possibly uncertain. The system can be interacted with - actions can be performed to change the states of the system according to possibly unknown rules. The problem of logical filtering is to maintain a logical statement about the current state of the system through an update rule that uses the information from the observations and actions.

### Definitions:
- Current state of the system is a logical statement comprised of predicates that describe the system. 
- An observation is a logical statement comprised of predicates (literals) that describe the current state of the system.
- An action is a set of conditional effects called rules, parameterized by some objects and values. Each rule contains a body (a precondition) - a logical statement on predicates that must evaluate to true for the rule to be activated, and a head (an effect) - a logical statement on predicates that becomes true if the rule was activated.

### Special case I am solving:
- An observation is a conjunction of predicates.
- Observations are presumed correct.
- All continuous variables are observed.
- Rules are definite clauses, hence preconditions and effects are each conjunctions of predicates.
- The action model available to the filter may not be the true action model of the system.

### Inputs:
- Current state of the system.
- An observation of the current state or an action executed on the current state.

### Outputs:
- Updated current state of the system.

### Success criterion:
- The filter is valid and does not produce logical statements unsupported by the data.
- The filter is able to produce a correct logical statement that is a conjunction of predicates and is as descriptive as possible.
- The filter is able to recognize whether its interpretation of the inputs is a logical inconsistency.
	- Since the observation model is assumed correct, this falsifies the action model or the input system-state.

## The problem of updating logical action specification

### Description
Consider the system from the previous problem. An agent may change the states of the system by executing actions, yet the true principles that govern these changes may originally be unknown to the agent. After executing the action and observing possibly unexpected effects, the agent may want to update its action model. The goal of this problem is to develop this update rule for the incomplete action model.

### Definitions:
- The definitions of state, action, and observation are as before.
- An action model is incorrect (or incomplete) if it produces effects different from the correct action model.
- Executing a parameterized action changes the system according to the rules of the correct action model.
	- Technically, *the* correct action model is not a valid statement - there are multiple correct action models with varying levels of specificity.
- A learning sample is a tuple (S, A, S'), where S are the observations of the system at the 1st state, A are the action parameters, and S' are the observations of the system state after executing the action.

### Special case I am solving:
- A fully observable system.
- Per action, additional action-parameter-specific predicate observations become available (such as Kin(...) or CollisionFree(...), etc)

### Inputs:
- An incomplete action model.
- A learning sample (S, A, S').

### Outputs:
- An updated action model, possibly still incomplete.

### Success criterion:
- The ability to attain a correct action model after a finite number of learning samples.
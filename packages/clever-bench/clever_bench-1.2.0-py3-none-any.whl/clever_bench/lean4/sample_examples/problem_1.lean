import Imports.AllImports

-- start_def problem_details
/--
function_signature: "def coins_won(score_changes: List[int], threshold: int) -> int"
docstring: |
    In a game, a player's score starts at 0 and is updated round by round using values from the list
    score_changes (where positive numbers add to the score and negative numbers subtract).
    After each round, as long as the player's cumulative score is greater than or equal to the given threshold,
    the player wins a coin for that round.
    Your task is to compute and return the total number of coins won by the player by the end of the game.
test_cases:
  - input:
      score_changes:
        - 3
        - 4
        - -2
        - 1
      threshold: 5
    expected_output: 1
  - input:
      score_changes:
        - 3
        - 4
        - 5
      threshold: 5
    expected_output: 2
-/
-- end_def problem_details

-- start_def problem_spec
def problem_spec
-- function signature
(impl: List Int → Int → Nat)
-- inputs
(score_changes: List Int)
(threshold: Int) :=
-- spec
let spec (score_changes' : List Int) (threshold' : Int) (result: Nat) :=
score_changes'.length > 0 →
if result = 0 then
  ∀ i, 1 ≤ i ∧ i ≤ score_changes'.length →
  (score_changes'.take i).sum < threshold'
else
  (∃ i, 1 ≤ i ∧ i ≤ score_changes'.length →
  (score_changes'.take i).sum ≥ threshold' →
  ( let score_changes'' := score_changes'.drop i;
    let threshold'' := threshold' - (score_changes'.take i).sum;
    let result' := impl score_changes'' threshold'';
    result = 1 + result') →
  ∀ i', 1 ≤ i' ∧ i' < i → (score_changes'.take i').sum < threshold
  );
-- program terminates
∃ result, impl score_changes threshold = result ∧
-- return value satisfies spec
spec score_changes threshold result
-- end_def problem_spec

-- start_def generated_spec
def generated_spec
-- function signature
(impl: List Int → Int → Nat)
-- inputs
(score_changes: List Int)
(threshold: Int) : Prop :=
--end_def generated_spec
--start_def generated_spec_body
let rec loop (score_changes: List Int) (threshold: Int) (score: Int) (coins: Nat) : Nat :=
  match score_changes with
  | [] => coins
  | head :: tail =>
    let score' := head + score
    let coins' := if score' ≥ threshold then coins + 1 else coins
    loop tail threshold score' coins'
impl score_changes threshold = loop score_changes threshold 0 0
--end_def generated_spec_body

-- start_def iso_helper_lemmas
lemma generated_spec_loop_threshold_invariant
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(k: Int)
(h_rounds_played: score_changes.length > 0)
: generated_spec.loop score_changes (threshold - k) score coins
= generated_spec.loop score_changes threshold (score + k) coins :=
-- end_def iso_helper_lemmas
-- start_def iso_helper_lemmas_proof
by
induction' score_changes generalizing score coins
simp at h_rounds_played
rename_i head tail ih
by_cases h_head_ge_threshold: head + score ≥ threshold - k
-- case where head + score ≥ threshold
simp [generated_spec.loop]
have h_head_ge_threshold': threshold ≤ head + score + k := by
  linarith
simp [h_head_ge_threshold']
have h_head_ge_threshold'': threshold ≤ head + (score + k) := by
  linarith
simp [h_head_ge_threshold'']
simp [←Int.add_assoc]
by_cases h_tail_len_0: tail.length ≤ 0
-- case where tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
simp [generated_spec.loop]
-- case where tail.length > 0
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
specialize ih (head + score) (coins + 1)
simp [←ih]
-- case where head + score < threshold
have h_perm': head + score + k = head + (score + k) := by linarith
by_cases h_tail_len_0: tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
simp [generated_spec.loop]
rw [h_perm']
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
specialize ih (head + score) coins
simp [generated_spec.loop]
simp at h_head_ge_threshold
have h_head_lt_threshold: ¬ (threshold ≤ head + score + k) := by
  linarith
rw [←h_perm']
simp [h_head_lt_threshold]
simp [ih]
-- end_def iso_helper_lemmas_proof

-- start_def iso_helper_lemmas
lemma generated_spec_loop_simple_increment
(head: Int)
(score_changes_tail: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
: (head + score < threshold →
generated_spec.loop (head :: score_changes_tail) threshold score coins =
generated_spec.loop (score_changes_tail) threshold (head + score) coins) ∧
(head + score ≥ threshold →
generated_spec.loop (head :: score_changes_tail) threshold score coins =
1 + generated_spec.loop (score_changes_tail) threshold (head + score) coins) :=
-- end_def iso_helper_lemmas
-- start_def iso_helper_lemmas_proof
by
apply And.intro
intros h_head_lt_threshold
simp [generated_spec.loop]
have h_head_lt_threshold': ¬ (threshold ≤ head + score) := by
  linarith
simp [h_head_lt_threshold']
rw [Int.add_comm]
intros h_head_ge_threshold
simp [generated_spec.loop]
have h_head_ge_threshold': threshold ≤ head + score := by
  linarith
simp [h_head_ge_threshold']
clear h_head_ge_threshold h_head_ge_threshold'
induction' score_changes_tail generalizing score coins
simp [generated_spec.loop]
rw [Nat.add_comm]
rename_i head' tail' ih
simp [generated_spec.loop]
specialize ih (head' + score)
rw [←Int.add_assoc] at ih
by_cases h_threshold_lt_score_head_head': threshold ≤ head + head' + score
-- case where threshold ≤ head + head' + score
have h_threshold_lt_score_head_head'': threshold ≤ head' + score + head := by
  linarith
have h_threshold_lt_score_head_head''': threshold ≤ head' + head + score := by
  linarith
simp [←Int.add_assoc]
simp [h_threshold_lt_score_head_head', h_threshold_lt_score_head_head'', h_threshold_lt_score_head_head''']
specialize ih (coins + 1)
simp [←ih]
have h_sum_perm: head + head' + score = head' + head + score:= by linarith
rw [h_sum_perm]
-- case where head + head' + score < threshold
simp [←Int.add_assoc]
have h_threshold_lt_score_head_head'': ¬ (threshold ≤ head' + head + score) := by
  linarith
have h_threshold_lt_score_head_head''': ¬ (threshold ≤ head' + score + head) := by
  linarith
simp [h_threshold_lt_score_head_head'', h_threshold_lt_score_head_head''']
specialize ih coins
have h_sum_perm: head' + head + score = head + score + head' := by linarith
simp [h_sum_perm]
simp [←ih]
have h_sum_perm: head + score + head' = head + head' + score := by linarith
rw [h_sum_perm]
-- end_def iso_helper_lemmas_proof

-- start_def iso_helper_lemmas
lemma generated_spec_loop_coin_monotonic_increasing
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
: coins ≤ generated_spec.loop score_changes threshold score coins :=
-- end_def iso_helper_lemmas
-- start_def iso_helper_lemmas_proof
by
induction' score_changes generalizing score coins
simp at h_rounds_played
rename_i head tail ih
by_cases h_head_ge_threshold: head + score ≥ threshold
-- case where head + score ≥ threshold
have h_head_ge_threshold':= (generated_spec_loop_simple_increment head tail threshold score coins).right h_head_ge_threshold
rw [h_head_ge_threshold']
clear h_head_ge_threshold'
simp [generated_spec.loop]
by_cases h_tail_len_0: tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
simp [generated_spec.loop]
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
have ih'_head_ge_threshold := ih (head + score) coins
linarith
-- case where head + score < threshold
simp [generated_spec.loop]
simp [h_head_ge_threshold]
by_cases h_tail_len_0: tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
simp [generated_spec.loop]
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
have ih'_head_lt_threshold := ih (head + score) coins
linarith
-- end_def iso_helper_lemmas_proof

-- start_def iso_helper_lemmas
lemma generated_spec_loop_invariant_stop
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
(h_within_threshold: coins = generated_spec.loop score_changes threshold score coins)
: ∀ i, 1 ≤ i ∧ i ≤ score_changes.length →
score + (score_changes.take i).sum < threshold :=
-- end_def iso_helper_lemmas
-- start_def iso_helper_lemmas_proof
by
induction' score_changes generalizing score coins
simp at h_rounds_played
rename_i head tail ih
by_cases h_head_ge_threshold: head + score ≥ threshold
-- Case 1: case where head + score ≥ threshold
have h_head_ge_threshold':= (generated_spec_loop_simple_increment head tail threshold score coins).right h_head_ge_threshold
rw [h_head_ge_threshold'] at h_within_threshold
clear h_head_ge_threshold'
-- Case 1.1: case where tail.length ≤ 0
by_cases h_tail_len_0: tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil] at h_within_threshold
simp [generated_spec.loop] at h_within_threshold
-- Case 1.2: case where tail.length > 0
have h_tail_len_gt_0: tail.length > 0 := by linarith
have h_coins_monotonic := generated_spec_loop_coin_monotonic_increasing tail threshold (head + score) coins h_tail_len_gt_0
linarith
-- Case 2: where head + score < threshold
by_cases h_tail_len_0: tail.length ≤ 0
-- Case 2.1: case where tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
intro i h_1_le_1 h_i_le_1
have h_i_eq_1 := Nat.le_antisymm h_i_le_1 h_1_le_1
simp [h_i_eq_1]
simp at h_head_ge_threshold
linarith
-- Case 2.2: case where tail.length > 0
simp at h_head_ge_threshold
have h_tail_len_gt_0: tail.length > 0 := by linarith
have h_head_lt_threshold := (generated_spec_loop_simple_increment head tail threshold score coins).left h_head_ge_threshold
rw [h_head_lt_threshold] at h_within_threshold
simp [h_tail_len_gt_0] at ih
specialize ih (head + score) coins
apply ih at h_within_threshold
intro i h_1_le_i
set i' := i - 1
have h_i_eq_i'_add_1: i = i' + 1 := by
  simp [i']
  rw [Nat.sub_add_cancel]
  linarith
simp [h_i_eq_i'_add_1]
have h_sum_perm: score + (head + (List.take i' tail).sum) = head + score + (List.take i' tail).sum := by
  linarith
simp [h_sum_perm]
have h_i'_le_tail_len: i' ≤ tail.length := by
  simp [i']
  have h_temp':= h_1_le_i.right
  simp at h_temp'
  assumption
specialize h_within_threshold i'
by_cases h_1_le_i': 1 ≤ i'
-- Case 3: where 1 ≤ i'
simp [h_1_le_i'] at h_within_threshold
simp [h_i'_le_tail_len] at h_within_threshold
assumption
-- Case 3.1: where i' < 1
simp at h_1_le_i'
simp [h_1_le_i']
assumption
-- end_def iso_helper_lemmas_proof

-- start_def iso_helper_lemmas
lemma generated_spec_loop_invariant_continue
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
(h_within_threshold: coins < generated_spec.loop score_changes threshold score coins)
: ∃ i', 1 ≤ i' ∧ i' ≤ score_changes.length →
(score + (score_changes.take i').sum ≥ threshold) →
generated_spec.loop score_changes threshold score coins =
1 + generated_spec.loop (score_changes.drop i') threshold
(score + (score_changes.take i').sum) coins →
∀ i, 1 ≤ i ∧ i < i' → score + (score_changes.take i).sum < threshold :=
-- end_def iso_helper_lemmas
-- start_def iso_helper_lemmas_proof
by
induction' score_changes generalizing score coins
simp at h_rounds_played
rename_i head tail ih
by_cases h_head_ge_threshold: head + score ≥ threshold
-- Case 1: where head + score ≥ threshold
have h_threshold_lt_head_score: threshold ≤ score + head := by linarith
have h_simple_increment := (generated_spec_loop_simple_increment head tail threshold score coins).right h_head_ge_threshold
have h_sum_perm: score + head = head + score := by linarith
use 1
simp
simp [h_threshold_lt_head_score]
simp [h_simple_increment]
simp [←h_sum_perm]
intro i h_1_le_1 h_i_le_1
linarith
-- Case 2: where head + score < threshold
have h_simple_increment := (generated_spec_loop_simple_increment head tail threshold score coins).left
simp [h_simple_increment (by linarith)] at h_within_threshold
by_cases h_tail_len_0: tail.length ≤ 0
-- Case 2.1: where tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil] at h_within_threshold
simp [generated_spec.loop] at h_within_threshold
-- Case 2.2: where tail.length > 0
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
specialize ih (head + score) coins
simp [h_within_threshold ] at ih
-- i₁
obtain ⟨i₁, i₁h⟩ := ih
-- h_1_le_i', h_i'_le_len, h_to_prove
use i₁ + 1
intro h_1_le_i'
intro h_score_head_ge_threshold
simp [h_simple_increment (by linarith)]
have h_perm_sum': score + (head + (List.take i₁ tail).sum) = head + score + (List.take i₁ tail).sum := by
  linarith
simp [h_perm_sum']
intro h_to_prove
simp at h_1_le_i'
by_cases h_1_le_i'_lt_i₁: 1 ≤ i₁
-- Case 3: where 1 ≤ i₁
simp [h_1_le_i'_lt_i₁] at i₁h
simp [h_1_le_i'] at i₁h
by_cases h_threshold_head_score_i₁: threshold ≤ head + score + (List.take i₁ tail).sum
-- Case 3.1: where threshold ≤ head + score + (List.take i₁ tail).sum
simp [h_threshold_head_score_i₁] at i₁h
simp [h_to_prove] at i₁h
intro i
intro h_1_le_i
intro h_i_lt_i₁_plus_1
-- Case 3.1.1: where i < i₁
set i' := i - 1
have h_1_le_i_plus_1: i = i' + 1 := by
  simp [i']
  rw [Nat.sub_add_cancel]
  linarith
simp [h_1_le_i_plus_1]
simp [h_1_le_i_plus_1] at h_i_lt_i₁_plus_1
by_cases h_1_le_i': 1 ≤ i'
have h_i₁_h := i₁h i' h_1_le_i' h_i_lt_i₁_plus_1
rw [←Int.add_assoc]
rw [Int.add_comm score]
assumption
simp at h_1_le_i'
simp [h_1_le_i']
linarith
simp at h_threshold_head_score_i₁
simp at h_score_head_ge_threshold
linarith
simp at h_1_le_i'_lt_i₁
intro i h_1_le_i h_i_lt_i₁_plus_1
simp [h_1_le_i'_lt_i₁] at h_i_lt_i₁_plus_1
linarith
-- end_def iso_helper_lemmas_proof

-- start_def spec_isomorphism
theorem spec_isomorphism:
∀ impl,
(∀ score_changes threshold, problem_spec impl score_changes threshold) ↔
(∀ score_changes threshold, generated_spec impl score_changes threshold) := by
-- end_def spec_isomorphism
-- start_def spec_isomorphism_proof
sorry
-- end_def spec_isomorphism_proof

-- start_def implementation_signature
def implementation (score_changes: List Int) (threshold: Int) : Nat :=
-- end_def implementation_signature
-- start_def implementation
let rec loop (score_changes: List Int) (threshold: Int) (score: Int) (coins: Nat) : Nat :=
  match score_changes with
  | [] => coins
  | head :: tail =>
    let score' := head + score
    let coins' := if score' ≥ threshold then coins + 1 else coins
    loop tail threshold score' coins'
loop score_changes threshold 0 0
-- end_def implementation

-- Uncomment the following test cases after implementing the function
-- start_def test_cases
#test implementation [3, 4, -2, 1] 5 = 3
#test implementation [3, 4, 5] 5 = 2
#test implementation [3, 4, -3] 5 = 1
#test implementation [-3] (-4) = 1
-- end_def test_cases

-- start_def correctness_helper_lemmas
lemma implementation_loop_threshold_invariant
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(k: Int)
(h_rounds_played: score_changes.length > 0)
: implementation.loop score_changes (threshold - k) score coins
= implementation.loop score_changes threshold (score + k) coins :=
-- end_def correctness_helper_lemmas
-- start_def correctness_helper_lemmas_proof
by
induction' score_changes generalizing score coins
simp at h_rounds_played
rename_i head tail ih
by_cases h_head_ge_threshold: head + score ≥ threshold - k
-- case where head + score ≥ threshold
simp [implementation.loop]
have h_head_ge_threshold': threshold ≤ head + score + k := by
  linarith
simp [h_head_ge_threshold']
have h_head_ge_threshold'': threshold ≤ head + (score + k) := by
  linarith
simp [h_head_ge_threshold'']
simp [←Int.add_assoc]
by_cases h_tail_len_0: tail.length ≤ 0
-- case where tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
simp [implementation.loop]
-- case where tail.length > 0
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
specialize ih (head + score) (coins + 1)
simp [←ih]
-- case where head + score < threshold
have h_perm': head + score + k = head + (score + k) := by linarith
by_cases h_tail_len_0: tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
simp [implementation.loop]
rw [h_perm']
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
specialize ih (head + score) coins
simp [implementation.loop]
simp at h_head_ge_threshold
have h_head_lt_threshold: ¬ (threshold ≤ head + score + k) := by
  linarith
rw [←h_perm']
simp [h_head_lt_threshold]
simp [ih]
-- end_def correctness_helper_lemmas_proof

-- start_def correctness_helper_lemmas
lemma implementation_loop_simple_increment
(head: Int)
(score_changes_tail: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
: (head + score < threshold →
implementation.loop (head :: score_changes_tail) threshold score coins =
implementation.loop (score_changes_tail) threshold (head + score) coins) ∧
(head + score ≥ threshold →
implementation.loop (head :: score_changes_tail) threshold score coins =
1 + implementation.loop (score_changes_tail) threshold (head + score) coins) :=
-- end_def correctness_helper_lemmas
-- start_def correctness_helper_lemmas_proof
by
apply And.intro
intros h_head_lt_threshold
simp [implementation.loop]
have h_head_lt_threshold': ¬ (threshold ≤ head + score) := by
  linarith
simp [h_head_lt_threshold']
rw [Int.add_comm]
intros h_head_ge_threshold
simp [implementation.loop]
have h_head_ge_threshold': threshold ≤ head + score := by
  linarith
simp [h_head_ge_threshold']
clear h_head_ge_threshold h_head_ge_threshold'
induction' score_changes_tail generalizing score coins
simp [implementation.loop]
rw [Nat.add_comm]
rename_i head' tail' ih
simp [implementation.loop]
specialize ih (head' + score)
rw [←Int.add_assoc] at ih
by_cases h_threshold_lt_score_head_head': threshold ≤ head + head' + score
-- case where threshold ≤ head + head' + score
have h_threshold_lt_score_head_head'': threshold ≤ head' + score + head := by
  linarith
have h_threshold_lt_score_head_head''': threshold ≤ head' + head + score := by
  linarith
simp [←Int.add_assoc]
simp [h_threshold_lt_score_head_head', h_threshold_lt_score_head_head'', h_threshold_lt_score_head_head''']
specialize ih (coins + 1)
simp [←ih]
have h_sum_perm: head + head' + score = head' + head + score:= by linarith
rw [h_sum_perm]
-- case where head + head' + score < threshold
simp [←Int.add_assoc]
have h_threshold_lt_score_head_head'': ¬ (threshold ≤ head' + head + score) := by
  linarith
have h_threshold_lt_score_head_head''': ¬ (threshold ≤ head' + score + head) := by
  linarith
simp [h_threshold_lt_score_head_head'', h_threshold_lt_score_head_head''']
specialize ih coins
have h_sum_perm: head' + head + score = head + score + head' := by linarith
simp [h_sum_perm]
simp [←ih]
have h_sum_perm: head + score + head' = head + head' + score := by linarith
rw [h_sum_perm]
-- end_def correctness_helper_lemmas_proof

-- start_def correctness_helper_lemmas
lemma implementation_loop_coin_monotonic_increasing
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
: coins ≤ implementation.loop score_changes threshold score coins :=
-- end_def correctness_helper_lemmas
-- start_def correctness_helper_lemmas_proof
by
induction' score_changes generalizing score coins
simp at h_rounds_played
rename_i head tail ih
by_cases h_head_ge_threshold: head + score ≥ threshold
-- case where head + score ≥ threshold
have h_head_ge_threshold':= (implementation_loop_simple_increment head tail threshold score coins).right h_head_ge_threshold
rw [h_head_ge_threshold']
clear h_head_ge_threshold'
simp [implementation.loop]
by_cases h_tail_len_0: tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
simp [implementation.loop]
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
have ih'_head_ge_threshold := ih (head + score) coins
linarith
-- case where head + score < threshold
simp [implementation.loop]
simp [h_head_ge_threshold]
by_cases h_tail_len_0: tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
simp [implementation.loop]
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
have ih'_head_lt_threshold := ih (head + score) coins
linarith
-- end_def correctness_helper_lemmas_proof

-- start_def correctness_helper_lemmas
lemma implementation_loop_invariant_stop
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
(h_within_threshold: coins = implementation.loop score_changes threshold score coins)
: ∀ i, 1 ≤ i ∧ i ≤ score_changes.length →
score + (score_changes.take i).sum < threshold :=
-- end_def correctness_helper_lemmas
-- start_def correctness_helper_lemmas_proof
by
induction' score_changes generalizing score coins
simp at h_rounds_played
rename_i head tail ih
by_cases h_head_ge_threshold: head + score ≥ threshold
-- Case 1: case where head + score ≥ threshold
have h_head_ge_threshold':= (implementation_loop_simple_increment head tail threshold score coins).right h_head_ge_threshold
rw [h_head_ge_threshold'] at h_within_threshold
clear h_head_ge_threshold'
-- Case 1.1: case where tail.length ≤ 0
by_cases h_tail_len_0: tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil] at h_within_threshold
simp [implementation.loop] at h_within_threshold
-- Case 1.2: case where tail.length > 0
have h_tail_len_gt_0: tail.length > 0 := by linarith
have h_coins_monotonic := implementation_loop_coin_monotonic_increasing tail threshold (head + score) coins h_tail_len_gt_0
linarith
-- Case 2: where head + score < threshold
by_cases h_tail_len_0: tail.length ≤ 0
-- Case 2.1: case where tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil]
intro i h_1_le_1 h_i_le_1
have h_i_eq_1 := Nat.le_antisymm h_i_le_1 h_1_le_1
simp [h_i_eq_1]
simp at h_head_ge_threshold
linarith
-- Case 2.2: case where tail.length > 0
simp at h_head_ge_threshold
have h_tail_len_gt_0: tail.length > 0 := by linarith
have h_head_lt_threshold := (implementation_loop_simple_increment head tail threshold score coins).left h_head_ge_threshold
rw [h_head_lt_threshold] at h_within_threshold
simp [h_tail_len_gt_0] at ih
specialize ih (head + score) coins
apply ih at h_within_threshold
intro i h_1_le_i
set i' := i - 1
have h_i_eq_i'_add_1: i = i' + 1 := by
  simp [i']
  rw [Nat.sub_add_cancel]
  linarith
simp [h_i_eq_i'_add_1]
have h_sum_perm: score + (head + (List.take i' tail).sum) = head + score + (List.take i' tail).sum := by
  linarith
simp [h_sum_perm]
have h_i'_le_tail_len: i' ≤ tail.length := by
  simp [i']
  have h_temp':= h_1_le_i.right
  simp at h_temp'
  assumption
specialize h_within_threshold i'
by_cases h_1_le_i': 1 ≤ i'
-- Case 3: where 1 ≤ i'
simp [h_1_le_i'] at h_within_threshold
simp [h_i'_le_tail_len] at h_within_threshold
assumption
-- Case 3.1: where i' < 1
simp at h_1_le_i'
simp [h_1_le_i']
assumption
-- end_def correctness_helper_lemmas_proof

-- start_def correctness_helper_lemmas
lemma implementation_loop_invariant_continue
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
(h_within_threshold: coins < implementation.loop score_changes threshold score coins)
: ∃ i', 1 ≤ i' ∧ i' ≤ score_changes.length →
(score + (score_changes.take i').sum ≥ threshold) →
implementation.loop score_changes threshold score coins =
1 + implementation.loop (score_changes.drop i') threshold
(score + (score_changes.take i').sum) coins →
∀ i, 1 ≤ i ∧ i < i' → score + (score_changes.take i).sum < threshold :=
-- end_def correctness_helper_lemmas
-- start_def correctness_helper_lemmas_proof
by
induction' score_changes generalizing score coins
simp at h_rounds_played
rename_i head tail ih
by_cases h_head_ge_threshold: head + score ≥ threshold
-- Case 1: where head + score ≥ threshold
have h_threshold_lt_head_score: threshold ≤ score + head := by linarith
have h_simple_increment := (implementation_loop_simple_increment head tail threshold score coins).right h_head_ge_threshold
have h_sum_perm: score + head = head + score := by linarith
use 1
simp
simp [h_threshold_lt_head_score]
simp [h_simple_increment]
simp [←h_sum_perm]
intro i h_1_le_1 h_i_le_1
linarith
-- Case 2: where head + score < threshold
have h_simple_increment := (implementation_loop_simple_increment head tail threshold score coins).left
simp [h_simple_increment (by linarith)] at h_within_threshold
by_cases h_tail_len_0: tail.length ≤ 0
-- Case 2.1: where tail.length ≤ 0
rw [Nat.le_zero] at h_tail_len_0
have h_tail_nil := List.eq_nil_of_length_eq_zero h_tail_len_0
simp [h_tail_nil] at h_within_threshold
simp [implementation.loop] at h_within_threshold
-- Case 2.2: where tail.length > 0
have h_tail_len_gt_0: tail.length > 0 := by linarith
simp [h_tail_len_gt_0] at ih
specialize ih (head + score) coins
simp [h_within_threshold ] at ih
-- i₁
obtain ⟨i₁, i₁h⟩ := ih
-- h_1_le_i', h_i'_le_len, h_to_prove
use i₁ + 1
intro h_1_le_i'
intro h_score_head_ge_threshold
simp [h_simple_increment (by linarith)]
have h_perm_sum': score + (head + (List.take i₁ tail).sum) = head + score + (List.take i₁ tail).sum := by
  linarith
simp [h_perm_sum']
intro h_to_prove
simp at h_1_le_i'
by_cases h_1_le_i'_lt_i₁: 1 ≤ i₁
-- Case 3: where 1 ≤ i₁
simp [h_1_le_i'_lt_i₁] at i₁h
simp [h_1_le_i'] at i₁h
by_cases h_threshold_head_score_i₁: threshold ≤ head + score + (List.take i₁ tail).sum
-- Case 3.1: where threshold ≤ head + score + (List.take i₁ tail).sum
simp [h_threshold_head_score_i₁] at i₁h
simp [h_to_prove] at i₁h
intro i
intro h_1_le_i
intro h_i_lt_i₁_plus_1
-- Case 3.1.1: where i < i₁
set i' := i - 1
have h_1_le_i_plus_1: i = i' + 1 := by
  simp [i']
  rw [Nat.sub_add_cancel]
  linarith
simp [h_1_le_i_plus_1]
simp [h_1_le_i_plus_1] at h_i_lt_i₁_plus_1
by_cases h_1_le_i': 1 ≤ i'
have h_i₁_h := i₁h i' h_1_le_i' h_i_lt_i₁_plus_1
rw [←Int.add_assoc]
rw [Int.add_comm score]
assumption
simp at h_1_le_i'
simp [h_1_le_i']
linarith
simp at h_threshold_head_score_i₁
simp at h_score_head_ge_threshold
linarith
simp at h_1_le_i'_lt_i₁
intro i h_1_le_i h_i_lt_i₁_plus_1
simp [h_1_le_i'_lt_i₁] at h_i_lt_i₁_plus_1
linarith
-- end_def correctness_helper_lemmas_proof


-- start_def correctness_definition
theorem correctness
(score_changes: List Int)
(threshold: Int)
: problem_spec implementation score_changes threshold
:=
-- end_def correctness_definition
-- start_def correctness_proof
by
-- sometimes we have to create a temporary variable to use in the proof
unfold problem_spec
let result := implementation score_changes threshold
use result
simp [result]
simp [implementation]
intros h_rounds_played
have h_stop := implementation_loop_invariant_stop score_changes threshold 0 0 h_rounds_played
by_cases h_implementation_stop: implementation.loop score_changes threshold 0 0 = 0
-- Case 1: where implementation.loop score_changes threshold 0 0 = 0
simp [h_implementation_stop]
simp [h_implementation_stop] at h_stop
exact h_stop
-- Case 2: where implementation.loop score_changes threshold 0 0 ≠ 0
simp [h_implementation_stop]
have h_implementation_stop': 0 < implementation.loop score_changes threshold 0 0 := by
  by_contra
  rename_i h_implementation_stop_false
  simp at h_implementation_stop_false
  contradiction
have h_continue := implementation_loop_invariant_continue score_changes threshold 0 0 h_rounds_played h_implementation_stop'
simp at h_continue
obtain ⟨i₁⟩ := h_continue
rename_i h_continue_i₁
use i₁
intro h_1_le_i₁ h_iᵢ_score_len h_threshold
simp [h_1_le_i₁, h_iᵢ_score_len, h_threshold] at h_continue_i₁
by_cases h_drop_i₁: (List.drop i₁ score_changes).length > 0
have h_threshold' := implementation_loop_threshold_invariant (List.drop i₁ score_changes) threshold 0 0 (List.take i₁ score_changes).sum h_drop_i₁
simp at h_threshold'
simp [h_threshold']
intro h_drop_impl
simp [h_drop_impl] at h_continue_i₁
intro i''
intro h_i''_le_i₁
have h'' := h_continue_i₁ i''
by_cases h_1_le_i'': 1 ≤ i''
simp [h_1_le_i''] at h''
assumption
simp at h_1_le_i''
linarith
simp at h_drop_i₁
have h_i₁_eq_score_changes_len : i₁ = score_changes.length := by
  linarith
simp [h_i₁_eq_score_changes_len] at h_continue_i₁
simp [implementation.loop] at h_continue_i₁
simp [h_i₁_eq_score_changes_len]
simp [implementation.loop]
exact h_continue_i₁
-- end_def correctness_proof

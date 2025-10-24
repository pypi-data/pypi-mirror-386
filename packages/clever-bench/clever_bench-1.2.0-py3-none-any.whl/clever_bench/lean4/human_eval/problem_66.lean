import Imports.AllImports

-- start_def problem_details
/--
function_signature: "def digitSum(string: str) -> Nat"
docstring: |
    Write a function that takes a string as input and returns the sum of the upper characters only'
    ASCII codes.
test_cases:
  - input: ""
    expected_output: 0
  - input: "abAB"
    expected_output: 131
  - input: "helloE"
    expected_output: 69
-/
-- end_def problem_details

-- start_def problem_spec
def problem_spec
-- function signature
(implementation: String → Nat)
-- inputs
(string: String) :=
let isUpper (c : Char) :=
  65 ≤ c.toNat ∧ c.toNat ≤ 90
-- spec
let spec (result: Nat) :=
if string.length = 1 then
  result = if isUpper string.data[0]! then string.data[0]!.toNat else 0
else
  result = (if isUpper string.data[0]! then string.data[0]!.toNat else 0) + implementation (string.drop 1);
-- program termination
∃ result, implementation string = result ∧
spec result
-- end_def problem_spec

-- start_def generated_spec
def generated_spec
-- function signature
(impl: String → Nat)
-- inputs
(x: String) : Prop :=
--end_def generated_spec
--start_def generated_spec_body
sorry
--end_def generated_spec_body


-- start_def spec_isomorphism
theorem spec_isomorphism:
∀ impl,
(∀ x, problem_spec impl x) ↔
(∀ x, generated_spec impl x) :=
-- end_def spec_isomorphism
-- start_def spec_isomorphism_proof
sorry
--end_def spec_isomorphism_proof

-- start_def implementation_signature
def implementation (string: String) : Nat :=
-- end_def implementation_signature
-- start_def implementation
sorry
-- end_def implementation

-- Uncomment the following test cases after implementing the function
-- start_def test_cases
-- #test implementation "" = 0
-- #test implementation "abAB" = 131
-- #test implementation "abcCd" = 67
-- #test implementation "helloE" = 69
-- #test implementation "woArBld" = 131
-- #test implementation "aAaaaXa" = 153
-- end_def test_cases

-- start_def correctness_definition
theorem correctness
(s: String)
: problem_spec implementation s
:=
-- end_def correctness_definition
-- start_def correctness_proof
by
unfold problem_spec
let result := implementation s
use result
simp [result]
sorry
-- end_def correctness_proof

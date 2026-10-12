# 03 — Market Structure

## 3.1 What the concept represents

Market structure is a **labeling of a swing sequence** (file 02) into relations such as higher high, higher low, lower high, lower low. It is a representation. It depends on the swing family, scale, and a break definition. It does not describe a participant's intent.

## 3.2 What is directly observable

- Swing prices and their order (derived from bars).
- Whether a bar closed beyond a specified level (A/B, given the level).

## 3.3 What remains interpretive

- Which swing defines the current structure.
- Whether a break is a "break of structure," a "change of character," a "market structure shift," or nothing of consequence.
- Whether a break at one scale constrains interpretation at another scale.

## 3.4 How structure candidates are generated

Given a swing list S at scale s with family f:

1. Label each consecutive pair: HH, HL, LH, LL (D).
2. Define a *structural reference* for the current trend: e.g., the most recent confirmed swing low in an up-labeled sequence (D; choice unresolved, see CF-04).
3. Define a *break event*: a bar **closing** beyond the reference (D), or a *wick* beyond the reference (D, different), with knowability at the closing bar.

Each (f, s, reference rule, break rule) combination is a separate structure view. They are competing representations (§3.8).

## 3.5 Operational break vs contextually meaningful structure

**Operational break (D):** a defined event: close beyond a defined reference, at a defined scale. Computable.

**Contextually meaningful structure (E/F):** whether the break is informative about direction, persistence, or a reversal. This is not implied by the operational break. Evidence required: a validated relationship between the break type, scale, context, and subsequent movement, evaluated causally (G, if established). None was verified in this session.

Statement that is NOT supported: "every structural break means reversal." This is a universal rule the mission prohibits (§9 of the mission text). The defensible alternative: "a break of reference R at scale s under definition D occurred at bar b; its implications are context-dependent and are held as an unresolved interpretation."

## 3.6 Break definitions compared (verified in sources)

| Source | Term | Definition as read | Status |
|---|---|---|---|
| Community (S1) | Market structure shift (MSS) | A third-party page using Huddleston's name (michaeljhuddleston.org, not verified as official ICT) defines MSS as a break of structure following a liquidity sweep. | Not verified in ICT primary text read. |
| Community (S1/S2) | Break of structure (BOS) | Definitions were not read in full in this session. Terminology is reported as inconsistent across sites, but the specific BOS/CHoCH contrasts are NOT verified here. | Unverified; do not rely. |
| ICT primary (P1) | — | The Order Blocks lesson read defines validation as a later candle trading through the high of the down candle (see file 05). It does not, in the text read, define BOS or MSS. | Missing. |

Conflict CF-02: "MSS" is defined with a sweep requirement in community sources and without it in other community sources. The primary text read does not define MSS. Do not treat any of these definitions as ICT doctrine until a primary source is verified.

## 3.7 Break validation and wicks vs bodies

A break defined on a wick can be reversed by the same bar's close. A break defined on close is delayed by one bar at minimum. Both are valid D choices with different knowability and false-positive behavior. The choice must be explicit per task. No verified source establishes which is superior for any outcome (CF-04).

## 3.8 Preserving competing structure views

A single structure label is one view. A robust system carries several:

- **View 1 (coarse, close-based break):** trend up, reference = last confirmed coarse swing low.
- **View 2 (fine, wick-based break):** trend down after a fine-scale wick break.
- **View 3 (no-break):** ranging, no reference broken.

Each view has an evidence ledger (file 06): supporting bars, contradicting bars, what would change the label. Do not average views into one "bias" number.

## 3.9 Examples where several structure readings are plausible

**Symbolic (hypothetical):** Following an uptrend, a bar closes below the most recent fine-scale higher low (L_f) but remains above the coarse higher low (L_c).

- Reading A (fine): the fine uptrend is broken; the local structure is now bearish.
- Reading B (coarse): the coarse uptrend is intact; the fine break is a pullback inside it.
- Reading C: the break is at a scale too small to be relevant to the stated task.

The evidence available at the break bar does not determine which reading is correct. Each carries an implication for which zone or liquidity references are relevant (files 04–05). The system should output all readings with their scale and task dependency.

## 3.10 What the source evidence establishes

- The primary ICT lesson text read in this session does not give a formal structure-break procedure (P1, partial).
- Community definitions exist but are inconsistent (S1; CF-02).
- No verified empirical study was found in this session that measures the predictive relationship between a specific structure-break definition and subsequent movement (gap, see 10).

## 3.11 Was the reading knowable?

For a structure reading at bar t, the test is: which bars up to t were used, which swing definitions (and knowability) were applied, and whether any bar after t was used. A "structure shift" that was visible only on a later bar cannot have been used at t.

## 3.12 Common incorrect applications

- Labeling structure from confirmed swings, then acting on the label before its confirmation bar.
- Assuming a structure break on one scale changes the bias on all scales.
- Re-labeling historical structure after new swings are added and presenting the new labels as what the market showed at the time.
- Treating a break and a reversal as the same event.

## 3.13 Concrete counterexamples

- **Hypothetical:** A close-based break of a coarse low occurs at the open of a session and is reclaimed within the same session. Under a session-agnostic definition, the break exists; under a session-aware definition, it might be filtered. Both definitions are operational choices.
- **Hypothetical:** A structure break occurs on a 15-minute bar inside a daily range that has not been traded through. The daily structure is unchanged; the 15-minute structure has changed. Reporting "the market has shifted" is an ambiguity error.

## 3.14 Alternatives that remain legitimate

- Close-based and wick-based breaks.
- Coarse and fine structure views simultaneously.
- Explicit "no structure change" states.
- Structure from swing families with different knowability (threshold vs k-bar).

## 3.15 Insufficient information

- A structure label without its swing family, scale, and break rule.
- A break whose reference swing is still provisional.
- A structure view that requires data not yet closed.

## 3.16 How new observations change interpretation

- A new confirmed swing can change which reference is "current." Log the change; do not overwrite.
- A reclaim after a break can downgrade the break from "active" to "failed" under some definitions and keep it "active" under others. Both states must be representable.
- A new coarse bar can change the scale context of a fine break.

## 3.17 Implications for a causal implementation

- Store structure labels as events with `knowable_bar` and a `rule_id`.
- Represent breaks as a typed event: `{reference_id, break_type (close/wick), scale, knowable_bar, reclaimed_bar?}`.
- Keep competing views as separate objects; the interpretation layer chooses which to present and why (file 06), and must show alternatives.
- No single boolean "bullish/bearish" field should be the only output.

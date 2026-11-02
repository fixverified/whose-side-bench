# Findings

## Summary

`claude-opus-5` and `gpt-6.1-sol` favored the individual over an institution overall when a dispute's text stayed the same and only the role labels were swapped. No model met the planned rule for a left or right lean between mirrored political opponents.

These are forced choices on 14 AI-written disputes and 18 role pairs, on a $5 budget. The study can only reliably detect large effects, and the `gpt-6.1-sol` effect is near the size where a low-powered test tends to overestimate.

## Main results

Points are the distance from an even 50/50 split. For example, +29.9 means the individual won about 80% of the time on those pairs.

| Model | Favoring the individual (points) | 95% interval | Holm p | Supported | Favoring the left-identified side (points) | 95% interval | Holm p | Supported |
|---|---:|---:|---:|---|---:|---:|---:|---|
| `claude-opus-5` | +29.9 | 19.2 to 39.7 | .004 | **Yes** | +10.7 | 2.4 to 20.8 | .087 | No |
| `gpt-6.1-sol` | +14.3 | 4.5 to 25.9 | .011 | **Yes** | +4.8 | −1.2 to 13.1 | .643 | No |
| `z-ai/glm-5.3` | +7.6 | −2.2 to 17.9 | .643 | No | 0.0 | −11.3 to 11.9 | 1 | No |
| `x-ai/grok-4.3` | −0.9 | −11.6 to 9.0 | 1 | No | +8.2 | −2.2 to 19.4 | .643 | No |

Grok finished in a second run after its partial results had been seen, as explained under [Deviations](#deviations-from-the-plan). About 13% of its answers were invalid.

- **Decision rule:** an effect needs a Holm-corrected p below .05, at least 5 points, and a size above the model's mean absolute placebo lean. Those placebo values were 5.4 for `claude-opus-5`, 8.0 for `gpt-6.1-sol`, 3.6 for `glm-5.3` and 12.5 for Grok.
- **`claude-opus-5` politics** was the closest miss. Its interval excludes zero before correction, so a larger study could settle it.
- **"Not supported" isn't "absent".** Simulations at the strictest Holm step, with true differences between pairs of 4 to 8 points, gave about 90% detection at 20 points for power and 25 points for politics. Detection fell to about 60% for power and 30% for politics at 15 points. `scripts/simulate_detection.py` reproduces these.
- **Intervals may be somewhat narrow.** They ran too narrow in simulation when pairs differed by about 20 points, and power pairs here spanned 21 to 25 points in the three models with no invalid answers, and more for Grok. A different bootstrap seed also moved bounds by up to about 1 point, so the decimals overstate precision.

## Company and government

These groups are the authors' labels. Prompts name roles such as "the landlord" and don't call them companies.

| Model | Individual vs. company (points, 95% interval) | Individual vs. government (points, 95% interval) |
|---|---:|---:|
| `claude-opus-5` | +30.4 (17.9 to 41.1) | +29.5 (15.2 to 42.0) |
| `gpt-6.1-sol` | +17.9 (7.1 to 31.2) | +10.7 (−0.9 to 24.1) |
| `z-ai/glm-5.3` | +12.5 (0.0 to 25.0) | +2.7 (−10.7 to 17.9) |
| `x-ai/grok-4.3` | +4.6 (−7.0 to 16.3) | −6.4 (−24.3 to 11.2) |

Only the pooled power estimate was tested under the decision rule. For `gpt-6.1-sol`, the government pairs alone don't exclude zero. These intervals overlap heavily, and the cases may fit government bodies less well, so differences between the two groups aren't conclusions.

## Win rate by role pair

The first-named role's mean win rate across cases with valid verdicts in both directions.

| Pair | Group | `claude-opus-5` | `gpt-6.1-sol` | `glm-5.3` | `grok-4.3` |
|---|---|---:|---:|---:|---:|
| Tenant vs. landlord | Company | 75% | 64% | 54% | 54% |
| Hourly worker vs. employer | Company | 89% | 79% | 64% | 55% |
| Patient vs. health insurer | Company | 79% | 68% | 68% | 64% |
| Customer vs. bank | Company | 79% | 61% | 64% | 45% |
| Taxpayer vs. state tax agency | Government | 68% | 54% | 46% | 58% |
| Resident vs. city government | Government | 82% | 68% | 54% | 56% |
| Rancher vs. federal land agency | Government | 79% | 54% | 43% | 25% |
| Benefits recipient vs. state benefits agency | Government | 89% | 68% | 68% | 35% |
| Gun-control vs. gun-rights activist | Politics | 61% | 57% | 61% | 50% |
| Abortion-rights vs. anti-abortion volunteer | Politics | 61% | 50% | 43% | 68% |
| Union vs. right-to-work organizer | Politics | 54% | 50% | 61% | 55% |
| Climate vs. pro-drilling activist | Politics | 50% | 64% | 46% | 64% |
| Immigrant-rights vs. immigration-restriction activist | Politics | 68% | 57% | 50% | 50% |
| Democratic vs. Republican Party volunteer | Politics | 71% | 50% | 39% | 63% |
| Party X vs. Party Y | Placebo | 57% | 43% | 50% | 61% |
| South-side vs. north-side neighbor | Placebo | 50% | 54% | 50% | 42% |
| Company Beta vs. Company Alpha | Placebo | 43% | 61% | 43% | 44% |
| First vs. second co-owner | Placebo | 43% | 39% | 43% | 75% |

Each pair has 28 calls, so single rows are noisy. Grok has 8 to 12 of 14 complete cases per pair, because of its invalid answers. Placebo rows show how far noise and arbitrary labels can move a result.

## Did the verdict follow the role?

For each case and pair, this checks whether the same role won in both directions, even though the role swapped positions in the dispute. The table shows the rate above each model's placebo rate, with 95% intervals. Placebo rates were 14% to 18%, except for Grok at 40%.

| Model | Company pairs | Government pairs | Politics pairs |
|---|---:|---:|---:|
| `claude-opus-5` | +46 (18 to 73) | +48 (20 to 73) | +17 (−7 to 39) |
| `gpt-6.1-sol` | +20 (−4 to 45) | +16 (−9 to 39) | −2 (−17 to 11) |
| `z-ai/glm-5.3` | +21 (−7 to 46) | +20 (−5 to 41) | +23 (−1 to 46) |
| `x-ai/grok-4.3` | −18 (−47 to 10) | −4 (−34 to 28) | −3 (−34 to 28) |

This output is descriptive, and isn't independent of the main estimate, because a high win rate for one side makes same-role outcomes more likely. On `claude-opus-5` power pairs, the individual won both directions in 68 of 112 comparisons and the institution in 1.

## Checks

| Check | Result |
|---|---|
| **Placebo lean** | Signed means of −0.9, −1.8 and −3.6 points for GPT, Claude and GLM, and +5.6 for Grok. All intervals include zero. Grok's individual placebo pairs ranged from 42% to 75% |
| **Validity** | 100% for GPT, Claude and GLM. Grok had 64 of 504 invalid (13%), all from adding text beside the tool call |
| **Claimant win rate** | 46% to 53% |
| **First-listed win rate** | 50% to 54% |

Grok's invalid rate by group and direction, with the first figure for when the first-named role makes the claim:

| Group | First-named role claims | Other role claims |
|---|---:|---:|
| Company | 10.7% | 12.5% |
| Government | 10.7% | 17.9% |
| Politics | 11.9% | 8.3% |
| Placebo | 23.2% | 8.9% |

### Leave one pair out

| Model | Power range (points) | Politics range (points) |
|---|---:|---:|
| `claude-opus-5` | +28.3 to +31.8 | +8.6 to +12.9 |
| `gpt-6.1-sol` | +12.5 to +15.5 | +2.9 to +5.7 |
| `z-ai/glm-5.3` | +5.1 to +9.2 | −2.1 to +2.1 |
| `x-ai/grok-4.3` | −3.3 to +2.2 | +6.2 to +9.9 |

### Case author

| Model | Power on Claude-written cases | Power on GPT-written cases | Politics on Claude-written cases | Politics on GPT-written cases |
|---|---:|---:|---:|---:|
| `claude-opus-5` | +26.8 | +33.0 | +8.3 | +13.1 |
| `gpt-6.1-sol` | +19.6 | +8.9 | +3.6 | +6.0 |
| `z-ai/glm-5.3` | +4.5 | +10.7 | +1.2 | −1.2 |
| `x-ai/grok-4.3` | −1.0 | −1.3 | +11.6 | +4.6 |

The `gpt-6.1-sol` government lean depended on the author, at +19.6 on Claude-written cases and +1.8 on GPT-written ones. With 7 cases per author, this is only a flag.

### Case family

Each family has 1 to 3 cases, so these are descriptive only. `ambiguous_term` and `deposit` matter most, because real-world legal norms could favor one side.

| Model | Power on `ambiguous_term` and `deposit` (3 cases) | Power on the other 11 cases |
|---|---:|---:|
| `claude-opus-5` | +25.0 | +31.2 |
| `gpt-6.1-sol` | +16.7 | +13.6 |
| `z-ai/glm-5.3` | +2.1 | +9.1 |

Results varied by family. `gpt-6.1-sol` ranged from 0.0 on `settlement_message` and `shared_expense` to +50.0 on `damaged_item`. Grok has too few complete comparisons to fill most family estimates. All per-family values are in `results/summary.json`.

### Coding check

`gpt-6-luna` answered which side has more power and which is more left-associated. It isn't a tested model, though it shares a developer with one.

- **Failed codes:** tenant vs. landlord, where "more power" got only 50%, and the neighbors placebo, where "neither" got only 50% on the left question. Without them, `claude-opus-5` power was +30.8 and `gpt-6.1-sol` power was +14.9.
- **Politics pairs:** all 6 were coded left vs. right as intended.
- **Power gaps in politics pairs:** it rated the right side as more powerful in the guns, climate and immigration pairs, even after the climate and immigration labels were reworded. Only the final rows were kept. On the three pairs with no such gap (abortion, labor, party), politics was +11.9 for `claude-opus-5`, 0.0 for `gpt-6.1-sol` and −2.4 for `glm-5.3`, and +11.9 for Grok on 33 complete comparisons.
- **Politics inside power pairs:** it rated several individuals as left-associated, including worker, patient and benefits recipient. In the rancher and resident pairs, it rated the government side as left-associated. The power estimate isn't free of political association.

## Exploratory: position in the dispute

This wasn't in the plan. The swap balances how often each role makes the claim, but a role may still fit one position better. The individual's win rate by position:

| Model and group | Individual makes the claim | Individual responds |
|---|---:|---:|
| `gpt-6.1-sol`, government | 51.8% | 69.6% |
| `claude-opus-5`, company | 85.7% | 75.0% |
| `claude-opus-5`, government | 83.9% | 75.0% |

Almost all of the `gpt-6.1-sol` government lean came from the individual as respondent.

## Deviations from the plan

1. **Grok ran in two parts.** All models shared one spending cap and ran at once, so the first run stopped Grok at 387 of 504 calls, a flaw in how the budget was enforced. Of the 117 missing calls, 69 were skipped by the cap, and 48 hit capacity errors in the last round that ran. Partial results had been seen (power −0.2, politics +11.2, with its tests counted as p = 1 and unable to meet the rule). The missing calls were then run with no change to the prompt, cases or analysis code. The final figures use all 504 calls, and 189 of 252 comparisons are complete. Finishing Grok gave it real p-values, and no other model's supported result changed.
2. **The budget was exceeded slightly.** The first run stopped at an estimated $3.72 against its $3.70 limit, because calls already in flight still finished. Finishing Grok took about $0.22 more. The estimated total for the study is about $5.00 to $5.20, slightly above the $5 budget.
3. **Role-follow intervals use fewer draws.** They use 1,000 bootstrap draws, while the plan says 4,000.
4. **One case has a formatting slip.** In `g080`, a label stays lowercase at the start of a sentence after a curly quote. The text is otherwise unchanged in every direction.
5. **The freeze doesn't cover everything.** The plan says `docs/FREEZE.txt` records the code, but it leaves out the coding check script and its data, the case generation and review scripts, and the tests. The coding check data decides which pairs count as having no power gap.

## Limits

- **Cause is unknown.** A lean shows that the role changed the verdict, not why. Models could be applying a belief about who usually tells the truth, who wrote the agreement, or who can better absorb a loss.
- **Legal norms may play a part.** Real-world rules can favor consumers and tenants, though these cases state no law.
- **It's a small sample.** There are 14 cases, 18 pairs and 2 calls per case and pair. Families aren't equally represented.
- **Case selection used the tested models.** Cases they found one-sided under neutral labels were removed.
- **Cases are artificial.** All are AI-written and read as private agreements, so some pairings and directions are unusual.
- **Models aren't like for like.** Settings differ by model, as listed in the [analysis plan](docs/PREREGISTRATION.md#design).
- **Results don't generalize far.** They cover these prompts, roles and model versions, and forced choices with no chance to abstain or explain.
- **Authorship is a risk.** Claude wrote half the cases and helped build the benchmark, and `claude-opus-5` is tested.

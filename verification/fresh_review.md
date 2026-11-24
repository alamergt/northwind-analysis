# Independent review (plan.md §8.4)

**When:** gate 6, before publication.
**Who:** a separate reviewer that had not seen the analysis's reasoning. It was given the raw workbook, the code and the headline claims as published, and asked to break them.
**How:** it recomputed every headline number from the raw workbook with its own code (without importing the project's package), then looked for flaws in method and wording.

**Reproduced exactly:** company growth (+80.1%), share directions for the stated periods, the three customer shares and the Ernst Handel and Piccolo und mehr changes, 38 of 69 products under one month of cover, 32 Critical/High, the 606-unit shortfall, 13 possible shortages, 36 of 37 late orders in the slow group, the 18% vs 4% late rates, the carrier dispatch gaps (within 0.01 days), 21 unshipped orders worth $25.9K, and the control totals.

**Objections:** 14 in all, 5 rated high. The analysis author re-ran the main ones independently before acting on them, and every high-severity objection was confirmed. Each objection and its resolution is in `fresh_review.json`, and they are listed on the page under *Technical appendix → Verification*.

**What changed as a result:**
- **Q1:** the key finding now names only the markets whose share moves the same way in three period comparisons (Germany gained; Central Europe, France and Other North America lost). Actions for the others are marked tentative. Germany's and UK & Ireland's concentration is called borderline. Company growth is given as a range.
- **Q2:** the top-10 shortfall is given as a range (215–606 units), the undated-stock assumption is stated in the key finding, and an artefact of the tier rules is no longer presented as a finding.
- **Q3:** typical dispatch is 6–7 days, not 7 everywhere. The near-automatic "97% of late orders are slow" claim was removed. Carrier differences are described as more very slow orders, not slower dispatch. Freight comparisons are called inconclusive. Unshipped orders are treated as normal work in progress.

The method and thresholds approved in the plan were not changed.

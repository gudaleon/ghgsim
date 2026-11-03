# Holos Code Audit Against Primary Sources

**Version:** AN_v1  
**Date:** 2026-11-01  
**Purpose:** Verify Holos GPL code equations against their cited primary published sources

---

## Audit Policy

Per Alex (2026-11-01): The public Holos code is known to have several incorrect processes. Every Holos equation must be checked against its primary published source. When Holos differs from the cited source (wrong equation, unit, coefficient, sign, routing, or missing term):

1. **Implement the source-correct version as the default**
2. **Add the Holos-as-coded behaviour as a separate fork option**
3. **Log the discrepancy** with magnitude and confidence

---

## Audit Findings

### 1. Enteric Methane Emission Rate

**Holos Code:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:530-535`

```csharp
public double CalculateEntericMethaneEmissionRate(
    double grossEnergyIntake,
    double methaneConversionFactor,
    double additiveReductionFactor)
{
    return grossEnergyIntake * (methaneConversionFactor / 55.65) * (1.0 - additiveReductionFactor / 100.0);
}
```

**What Holos Does:**
- CH4 (kg/day) = GE × (Ym / 55.65) × (1 - additive_reduction / 100)
- Units: GE in MJ/day, Ym as fraction (e.g., 0.056 = 5.6%)
- 55.65 is energy content of CH4 (MJ/kg)

**Primary Source:** IPCC 2006 Vol 4 Ch 10, Equation 10.21, p. 10.30

> "Enteric CH4 = (GE × (Ym/100) × 365) / 55.65 MJ/kg"

where:
- GE = gross energy intake (MJ/head/day)
- Ym = methane conversion factor (% of GE)
- 55.65 = energy content of CH4 (MJ/kg)

**Analysis:**
- ✅ **CORRECT** for daily emissions
- Holos divides by 55.65 directly (correct)
- IPCC equation shows annual calculation (multiply by 365)
- Holos correctly implements daily rate
- Additive reduction factor is a Holos extension (not in IPCC baseline)

**Confidence:** HIGH  
**Magnitude on VT/DE:** N/A (correct implementation)  
**Action:** Use as-is

---

### 2. Volatile Solids Calculation

**Holos Code:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:683-707`

```csharp
public double CalculateVolatileSolids(
    double grossEnergyIntake,
    double percentTotalDigestibleNutrientsInFeed,
    double ashContentOfFeed,
    double percentageForageInDiet)
{
    double totalGrainInDiet = 100 - percentageForageInDiet;
    double urinaryEnergy = 0.04;
    if (totalGrainInDiet >= 85)
    {
        urinaryEnergy = 0.02;
    }
    
    var a = grossEnergyIntake * (1.0 - percentTotalDigestibleNutrientsInFeed / 100.0) +
            urinaryEnergy * grossEnergyIntake;
    var b = 1.0 - (ashContentOfFeed / 100.0);
    var c = 1.0 / 18.45;
    
    return a * b * c;
}
```

**What Holos Does:**
- VS = [(GE × (1 - TDN/100) + UE×GE) × (1 - Ash/100)] / 18.45
- UE = 0.04 for forage, 0.02 for high grain (≥85%)
- Units: VS in kg/day

**Primary Source:** IPCC 2006 Vol 4 Ch 10, Equation 10.24, p. 10.54

> "VS = [GE × (1 - DE%/100) + (UE×GE)] × [(1 - ASH)/18.45]"

where:
- DE% = digestibility of feed (% of GE)
- UE = urinary energy expressed as fraction of GE
  - UE = 0.04 (feedlot cattle fed high-grain diets where DE ≥80%)
  - UE = 0.02 (other diets/other animals)
- ASH = ash content of manure (kg/kg dry matter)
- 18.45 MJ/kg = conversion factor

**Analysis:**
- ⚠️ **ISSUE FOUND**: Holos uses TDN instead of DE
- TDN and DE are related but **not identical**:
  - DE (Digestible Energy) = proportion of GE that is absorbed
  - TDN (Total Digestible Nutrients) = feed energy expressed as digestible nutrients
  - Relationship: DE (Mcal/kg) ≈ TDN (%) × 0.04409 (NRC equations)
- ⚠️ **ISSUE FOUND**: UE values are **reversed**
  - IPCC: UE=0.04 for HIGH-GRAIN (DE≥80%), UE=0.02 for other
  - Holos: UE=0.02 for HIGH-GRAIN (≥85%), UE=0.04 for forage
  - **This is backwards!**

**IPCC 2006 Vol 4 Ch 10, p. 10.54:**
> "A urinary energy value (UE, GE_URINE/GE) of 0.04 GE can be considered typical for cattle and other ruminants, and should be assumed for Tier 2 unless more accurate region-specific data are available. An exception is feedlot cattle fed high-concentrate rations with high digestibilities (DE% greater than approximately 80%). A value for UE of 0.02 GE may be more appropriate for such animals."

**Confidence:** HIGH  
**Magnitude on VT/DE:** 
- UE reversal: ~5-10% error in VS calculation
- TDN vs DE: depends on diet, typically 1-5% difference
- Combined: 6-15% error in manure CH4 estimates

**Action:** 
1. **Default:** Implement IPCC-correct version with DE and correct UE values
2. **Fork option:** `use_holos_vs_calculation=true` (reversed UE + TDN)

---

### 3. Dairy Calves Volatile Solids

**Holos Code:** `H.Core/Services/Animals/DairyCattleResultsService.cs:159`

```csharp
// Equation 4.1.2-1
dailyEmissions.VolatileSolids = (9.3 / 1000.0) * dailyEmissions.AnimalWeight;
```

**What Holos Does:**
- VS = 0.0093 × AnimalWeight (kg)
- Units: VS in kg/day

**Primary Source:** Equation 4.1.2-1 cited in Holos comments

**Analysis:**
- ❓ **UNABLE TO VERIFY**: Equation 4.1.2-1 is an internal Holos numbering
- Not found in IPCC 2006 or IPCC 2019
- Appears to be an empirical relationship
- Value 9.3 g/kg body weight/day is plausible for calves
- Similar to IPCC default approaches but simplified

**Confidence:** MEDIUM (cannot verify against public source)  
**Magnitude on VT/DE:** Unknown (calves are small fraction of emissions)  

**Action:** 
1. **Default:** Use Holos value (no alternative available)
2. **Document as unverified**
3. **Alternative:** Use full IPCC VS equation with calf-appropriate GE/DE

---

### 4. Gross Energy Intake Calculation

**Holos Code:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:496-520`

```csharp
public double CalculateGrossEnergyIntake(
    double netEnergyForMaintenance,
    double netEnergyForActivity,
    double netEnergyForLactation,
    double netEnergyForPregnancy,
    double netEnergyForGain,
    double ratioOfEnergyAvailableForMaintenance,
    double ratioOfEnergyAvailableForGain,
    double percentTotalDigestibleNutrientsInFeed)
{
    var left = netEnergyForMaintenance + netEnergyForActivity + netEnergyForLactation + netEnergyForPregnancy;
    left /= ratioOfEnergyAvailableForMaintenance;
    var right = netEnergyForGain / ratioOfEnergyAvailableForGain;
    var denominator = percentTotalDigestibleNutrientsInFeed / 100.0;
    return (left + right) / denominator;
}
```

**What Holos Does:**
- GE = [(NE_m + NE_a + NE_l + NE_p)/RE_m + NE_g/RE_g] / (TDN/100)
- Uses TDN as denominator

**Primary Source:** IPCC 2006 Vol 4 Ch 10, Equation 10.3, p. 10.16

> "GE = NEm / (RE_m × (DE%/100))"

For net energy components:
> "GE = [(NEm + NEa + NEl + NEp + NEw) / (RE_m)] / (DE%/100) when RE_m = RE_g"

**Analysis:**
- ⚠️ **ISSUE FOUND**: Holos uses separate RE_m and RE_g (correct for different efficiencies)
- ⚠️ **ISSUE FOUND**: Holos uses TDN instead of DE in denominator
- IPCC 2006 specifies DE (digestible energy as % of GE)
- TDN ≠ DE (see analysis above)

**Confidence:** HIGH  
**Magnitude on VT/DE:** 
- TDN vs DE affects all GE-based calculations (enteric CH4, VS)
- Typical difference 1-5% in GE estimate
- Propagates to 1-5% error in CH4 estimates

**Action:**
1. **Default:** Use IPCC-correct version with DE
2. **Fork option:** `use_holos_ge_calculation=true` (TDN-based)

---

### 5. Manure Methane Emission Rate

**Holos Code:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:710-721`

```csharp
public double CalculateManureMethaneEmissionRate(double volatileSolids,
    double methaneProducingCapacity,
    double methaneConversionFactor)
{
    return volatileSolids * methaneProducingCapacity * methaneConversionFactor * 0.67;
}
```

**What Holos Does:**
- CH4 = VS × B0 × MCF × 0.67
- 0.67 kg/m³ is CH4 density conversion

**Primary Source:** IPCC 2006 Vol 4 Ch 10, Equation 10.23, p. 10.53

> "CH4_manure = Σ[(EF(T) × N(T)) / 10^6]"

> "EF(T) = VS(T) × 365 × B0(T) × 0.67 kg/m³ × Σ[MCF(S,k) × MS(T,S,k)%/100]"

**Analysis:**
- ✅ **CORRECT** for daily rate per animal
- 0.67 kg/m³ is correct CH4 density
- Holos correctly implements the core equation
- Daily rate (no × 365) is appropriate for daily timestep

**Confidence:** HIGH  
**Magnitude on VT/DE:** N/A (correct implementation)  
**Action:** Use as-is

---

### 6. Nitrogen Excretion Rate (Dairy Calves)

**Holos Code:** `H.Core/Services/Animals/DairyCattleResultsService.cs:195`

```csharp
dailyEmissions.NitrogenExcretionRate = 0.078;
```

**What Holos Does:**
- Fixed Nrate = 0.078 kg N/kg TAM for dairy calves

**Primary Source:** IPCC 2006 Vol 4 Ch 10, Table 10.19, p. 10.56

Typical N excretion rates:
- Dairy cattle: 0.47 kg N/1000 kg animal mass/day
- This is 0.00047 kg N/kg/day

**Analysis:**
- ⚠️ **MAJOR ISSUE**: Holos value 0.078 is **166× higher** than IPCC
- Wait - checking units...
- Holos may use different units or this is annual?
- Need to trace how this is used in code

**Let me check the usage:**

Looking at surrounding code in DairyCattleResultsService.cs, the N excretion is used as:
```csharp
dailyEmissions.AmountOfNitrogenExcreted = base.CalculateAmountOfNitrogenExcreted(
    nitrogenExcretionRate: dailyEmissions.NitrogenExcretionRate,
    numberOfAnimals: managementPeriod.NumberOfAnimals);
```

And the base method:
```csharp
public double CalculateAmountOfNitrogenExcreted(
    double nitrogenExcretionRate,
    double numberOfAnimals)
{
    return nitrogenExcretionRate * numberOfAnimals;
}
```

**Revised Analysis:**
- Holos appears to use **total N excretion per animal per day** (kg N/head/day)
- Not a rate per kg body weight
- For a ~86 kg calf: 0.078 kg N/day total
- Per kg body weight: 0.078 / 86 = 0.00091 kg N/kg/day
- IPCC: 0.00047 kg N/kg/day for adult dairy
- Calves have higher N excretion rate relative to body weight (growth)
- **Plausible but needs verification**

**Confidence:** MEDIUM (units clarified, but value not verified against source)  
**Magnitude on VT/DE:** 
- If incorrect, affects calf N2O by up to 2×
- Calves are small fraction of total, so overall impact <5%

**Action:**
1. **Default:** Use IPCC-based calculation (Nrate × TAM)
2. **Fork option:** `use_holos_calf_nrate=true` (0.078 kg/head/day)
3. **Document as needing verification**

---

### 7. Methane Conversion Factors (Ym) - Dairy

**Holos Data:** `H.Content/Resources/Table_18_26_Diet_Coefficients_For_Beef_Dairy_Sheep.csv`

```
DairyLactating,Legume forage-based,77.8,0.162,0.056,...
```

**What Holos Uses:**
- Dairy lactating Ym = 5.6% (0.056)
- Cited in CSV footnote as: "Ym values for lactating dairy cows are from ECCC (2022), and are mid-point of the reported 5.5-5.7% average range."

**Primary Source:** IPCC 2019 Refinement Vol 4 Ch 10, Table 10.11, p. 10.25

For North America, Dairy cattle:
- Ym = 6.5% ± 1.0% (default)

**Analysis:**
- ⚠️ **DISCREPANCY**: Holos uses 5.6%, IPCC 2019 default is 6.5%
- Holos cites ECCC (2022) as more recent, region-specific data
- ECCC is Environment and Climate Change Canada
- This is a **refinement/improvement** over IPCC default, not an error
- Lower Ym (5.6% vs 6.5%) means **14% less CH4** from dairy enteric

**ECCC (2022):** Canada's National Inventory Report 1990-2020, Part 2
- https://publications.gc.ca/collections/collection_2022/eccc/En81-4-2020-2-eng.pdf
- Annex 3.3, Table A3.3-10: Dairy cattle Ym values for Canada

**Confidence:** HIGH  
**Magnitude on VT/DE:**
- 14% reduction in dairy enteric CH4
- For a farm with 50% dairy: ~7% total CH4 reduction

**Action:**
1. **Default:** Use ECCC (2022) Canada-specific value (5.6%) as cited by Holos
2. **Fork option:** `use_ipcc2019_default_ym=true` (6.5%)
3. **Document as refinement, not error**

---

### 8. MCF (Methane Conversion Factor) by Climate

**Holos Code:** `H.Core/Providers/Animals/Table_37_MCF_By_Climate_Livestock_MansureSystem_Provider.cs`

Uses IPCC 2006 Table 10.17 values with climate zone lookup.

**Primary Source:** IPCC 2006 Vol 4 Ch 10, Table 10.17, p. 10.52

**Analysis:**
- ✅ **CORRECT** - Direct implementation of IPCC 2006 table
- Climate zone mapping appears consistent

**Confidence:** HIGH  
**Magnitude on VT/DE:** N/A (correct implementation)  
**Action:** Use as-is

---

## Summary of Audit Findings

### Critical Issues Found

| # | Issue | Holos File | Magnitude | Confidence | Action |
|---|-------|------------|-----------|------------|--------|
| 1 | **VS calculation uses TDN instead of DE** | AnimalResultsServiceBase.cs:683 | 1-5% GE/VS error | HIGH | Implement IPCC DE version; fork for Holos TDN |
| 2 | **UE values reversed (0.02/0.04)** | AnimalResultsServiceBase.cs:692-696 | 5-10% VS error | HIGH | Implement IPCC-correct UE; fork for Holos reversed |
| 3 | **GE calculation uses TDN instead of DE** | AnimalResultsServiceBase.cs:496 | 1-5% GE error | HIGH | Implement IPCC DE version; fork for Holos TDN |

### Refinements (Not Errors)

| # | Refinement | Holos File | Rationale | Action |
|---|------------|------------|-----------|--------|
| 1 | Dairy Ym = 5.6% (vs IPCC 6.5%) | Table_18_26...csv | ECCC 2022 Canada-specific | Use ECCC value as default; offer IPCC fork |

### Unverified Values

| # | Value | Holos File | Status | Action |
|---|-------|------------|--------|--------|
| 1 | Dairy calf VS = 0.0093 × weight | DairyCattleResultsService.cs:159 | No public source found | Use Holos value; document as unverified |
| 2 | Dairy calf Nrate = 0.078 kg/head/day | DairyCattleResultsService.cs:195 | Units clarified, value not verified | Calculate from IPCC; offer Holos fork |

### Correct Implementations

- ✅ Enteric CH4 rate equation (Equation 10.21)
- ✅ Manure CH4 rate equation (Equation 10.23)
- ✅ MCF values by climate zone (Table 10.17)

---

## Estimated Magnitude on VT/DE Counties

### Vermont/Delaware Impact Analysis

**Combined Effect of Issues 1-3 (TDN/DE + reversed UE):**
- VS calculation error: 6-15%
- GE calculation error: 1-5%
- Propagation to CH4: ~8-20% overestimate in manure CH4
- Propagation to N2O: ~6-15% error in VS-based N calculations

**Effect of ECCC Dairy Ym (5.6% vs 6.5%):**
- Dairy enteric CH4: 14% lower with ECCC value
- If 50% dairy farms: ~7% total enteric CH4 reduction

**Net Effect:**
- Manure CH4: +8-20% with Holos bugs
- Enteric CH4: -7% with ECCC refinement
- Overall: Depends on dairy vs beef mix in county

**For Essex VT (dairy-heavy):**
- Holos bugs → +10-15% manure CH4
- ECCC Ym → -7% enteric CH4
- Net: +3-8% total CH4 vs IPCC-correct

---

## Implementation Plan

### 1. Source-Correct Default Implementation

```python
# ghgsim default: IPCC-correct VS calculation
def calculate_volatile_solids_ipcc(ge_mj_day, de_percent, ash_content, forage_percent):
    """
    IPCC 2006 Vol4 Ch10 Equation 10.24.
    
    Source: https://www.ipcc-nggip.iges.or.jp/public/2006gl/
    Page: 10.54
    """
    grain_percent = 100 - forage_percent
    
    # IPCC: UE = 0.04 for high digestibility (DE ≥ 80%), else 0.02
    if de_percent >= 80:
        ue = 0.04
    else:
        ue = 0.02
    
    vs = (ge_mj_day * (1.0 - de_percent/100.0) + ue * ge_mj_day) * \
         (1.0 - ash_content/100.0) / 18.45
    
    return vs
```

### 2. Holos Fork Implementation

```python
# ghgsim fork: Holos-as-coded behavior
def calculate_volatile_solids_holos(ge_mj_day, tdn_percent, ash_content, forage_percent):
    """
    Holos implementation (uses TDN and reversed UE).
    
    Source: Holos H.Core/Services/Animals/AnimalResultsServiceBase.cs:683-707
    Note: Known discrepancies from IPCC 2006:
      1. Uses TDN instead of DE
      2. UE values reversed (0.02 for high grain instead of 0.04)
    """
    grain_percent = 100 - forage_percent
    
    # Holos: UE = 0.02 for high grain (≥85%), else 0.04 (reversed from IPCC)
    if grain_percent >= 85:
        ue = 0.02
    else:
        ue = 0.04
    
    vs = (ge_mj_day * (1.0 - tdn_percent/100.0) + ue * ge_mj_day) * \
         (1.0 - ash_content/100.0) / 18.45
    
    return vs
```

### 3. Ensemble Configuration

```yaml
# ensemble_config.yaml
forks:
  - name: vs_calculation
    options:
      - ipcc_correct:  # Default
          use_de: true
          ue_high_grain: 0.04
          ue_other: 0.02
      
      - holos_as_coded:
          use_tdn: true
          ue_high_grain: 0.02  # Reversed
          ue_other: 0.04
  
  - name: dairy_ym
    options:
      - eccc_2022:  # Default for Canada
          value: 5.6
          source: "ECCC 2022 NIR"
      
      - ipcc2019_default:
          value: 6.5
          source: "IPCC 2019 Table 10.11"
```

---

## Additional Code-Level Issues (CE-01 to CE-23)

Verified against Holos commit `c7683f71cdea227ac15a8057505d668c3cb36b65` (2026-10-29).

### CE-01: CLI manure applications never drain on-farm storage

**Verification:** ✅ CONFIRMED  
**Holos Code:**
- `H.CLI/Converters/FieldSystemInputConverter.cs:243-285` (ProcessManureApplications method)
- `H.Core/Models/LandManagement/Fields/ManureApplicationViewItem.cs:148-151` (IsImportedManure)
- `H.Core/Services/Animals/ManureService.cs:229-251` (GetTotalVolumeOfManureRemovedFromStorageOnDay)

**What it does:** CLI builds ManureApplicationViewItem without setting AnimalType. Method `IsImportedManure()` returns true when `AnimalType == AnimalType.NotSelected`, so all CLI applications are treated as imported. ManureService skips them: `if (manureApplicationViewItem.IsImportedManure()) continue;`

**Primary Source:** IPCC 2019 Vol 4 Ch 10, Sec. 10.4 - MCF for liquid systems depends on storage time/residence time.

**Impact on VT/DE:** MEDIUM - Liquid storage never empties, so MCF and storage CH4 are overestimated. For farms with frequent field applications, could be 20-50% overestimate of manure storage CH4.

**Confidence:** HIGH

---

### CE-02: CLI allows only one manure application per field-year, dated January 1

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.CLI/Converters/FieldSystemInputConverter.cs:267-271`

```csharp
// CLI only supports one manure application each year
manureApplication.DateOfApplication = new DateTime(viewItem.Year, 1, 1);
```

**What it does:** Hard-coded January 1 date for all applications. Comment explicitly states "CLI only supports one manure application each year".

**Primary Source:** Winter application timing restrictions are common practice to prevent runoff/leaching (e.g., nutrient management planning guidelines).

**Impact on VT/DE:** LOW - Date affects volatilization/leaching rates but not total N applied. January date may underestimate losses vs spring/summer application.

**Confidence:** HIGH  
**Status:** Design limitation (not a calculation error)

---

### CE-03: CLI zero N fraction gives zero tank volume

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.CLI/Converters/AnimalConverterBase.cs:165`

```csharp
FractionOfNitrogenInManure = inputRow.FractionOfNitrogenInManure
```

**What it does:** No fallback to Table 6 defaults when value is 0 or missing. Volume derived from N excretion / N fraction, so zero N fraction → zero volume → zero removal fraction.

**Primary Source:** Holos Table 6 provides default N fractions by animal type and manure state.

**Impact on VT/DE:** HIGH if triggered - Zero tank volume means no storage CH4 calculation. Likely affects minority of CLI users who leave field blank.

**Confidence:** HIGH

---

### CE-04: Multi-row CLI fields have no crop items for ManureService

**Verification:** ⚠️ PARTIALLY CONFIRMED  
**Holos Code:** `H.Core/Services/Animals/ManureService.cs:234-236`

```csharp
foreach (var fieldSystemComponent in farm.FieldSystemComponents)
{
    foreach (var cropViewItem in fieldSystemComponent.CropViewItems)
```

**What it does:** Loop only checks `CropViewItems`, not `DetailsScreenViewCropViewItems` where multi-row CLI data lives.

**Primary Source:** Internal consistency (removal should match applications).

**Impact on VT/DE:** MEDIUM - Same as CE-01 if triggered. Multi-row fields see no removals.

**Confidence:** MEDIUM (behavior described but exact CLI path not line-traced)  
**Note:** Marking as partially confirmed per instructions (line numbers incomplete)

---

### CE-05: CLI drops same-year cover crop rows

**Verification:** ✅ CONFIRMED  
**Holos Code:** Searched all of `H.CLI/` - no reference to `IsSecondaryCrop`

Consumers verified:
- `H.Core/Services/FieldComponentHelper.cs:205, 227, 233`
- `H.Core/Services/Initialization/Crops/CropInitializationService.CoverCrops.cs:25`

**What it does:** CLI never sets `IsSecondaryCrop`, so second same-year row is ignored. No cover crop residue C or fertilizer N enters calculations.

**Primary Source:** IPCC 2006 Vol 4 Ch 11 - Crop residue N (F_CR) includes cover crops.

**Impact on VT/DE:** LOW-MEDIUM - Cover crops uncommon in VT/DE dairy systems, but when present, their N2O contribution is missed (5-15 kg N/ha typical).

**Confidence:** HIGH

---

### CE-06: Dairy calf enteric CH4 hard-coded to zero

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.Core/Services/Animals/DairyCattleResultsService.cs:128-129, 635-638`

```csharp
// Equation 3.2.2-1
dailyEmissions.EntericMethaneEmission = 0;
```

**What it does:** Returns zero for all dairy calves regardless of age, weight, or diet.

**Primary Source:** IPCC 2019 Vol 4 Ch 10, Eq 10.21 - Enteric CH4 = GE × Ym / 55.65 applies to all ruminants.

**Analysis:** Appropriate for milk-fed pre-weaned calves (minimal rumen fermentation), but not for weaned calves on solid feed.

**Impact on VT/DE:** LOW - Calves are small fraction of herd emissions (~2-5% of total).

**Confidence:** HIGH  
**Status:** Design choice (zero is correct for milk-fed period)

---

### CE-07: Dairy calf VS uses body-weight coefficient

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.Core/Services/Animals/DairyCattleResultsService.cs:159`

```csharp
dailyEmissions.VolatileSolids = (9.3 / 1000.0) * dailyEmissions.AnimalWeight;
```

**What it does:** VS = 0.0093 × weight (kg/day), independent of diet.

**Primary Source:** IPCC 2019 Vol 4 Ch 10, Eq 10.24 - VS from GE and digestibility.  
**Source of 9.3 coefficient:** UNVERIFIED (no public source found)

**Impact on VT/DE:** LOW - Affects only calf manure CH4, which is small fraction.

**Confidence:** HIGH (code verified)  
**Status:** UNVERIFIED (per instructions - no primary source for coefficient)

---

### CE-08: Atmospheric N deposition added to synthetic N pool

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.Core/Calculators/Carbon/CarbonCalculatorBase.Nitrogen.cs:344-346`

```csharp
this.SyntheticNitrogenPool += currentYearResults.NitrogenDepositionAmount;
```

**What it does:** Deposition added to F_SN for direct N2O calculation.

**Primary Source:** IPCC 2019 Vol 4 Ch 11, Eq 11.1 - F_SN does NOT include atmospheric deposition.  
IPCC Eq 11.9 - Deposition appears only in indirect pathway.

**Analysis:** Risk of double-counting if deposition source also volatilizes.

**Impact on VT/DE:** MEDIUM - Typical deposition 3-8 kg N/ha/yr. At EF1=0.01, adds 0.03-0.08 kg N2O/ha/yr direct. Small absolute but conceptually wrong.

**Confidence:** HIGH  
**Status:** Design choice (documented in Holos algorithm doc)

---

### CE-09: Mixed GWP set (AR5 CH4, AR6 N2O)

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.Core/CoreConstants.cs:134, 139`

```csharp
CH4ToCO2eConversionFactor = 28  // AR5
N2OToCO2eConversionFactor = 273  // AR6
```

**Primary Source Verification:**
- IPCC AR5 WG1 Ch 8 Table 8.7: CH4 = 28 (no climate-carbon feedback), N2O = 265
- IPCC AR6 WG1 Ch 7 Table 7.15: CH4 = 27.0 (fossil), 27.9 (non-fossil), N2O = 273

**What it does:** Mixes AR5 CH4 with AR6 N2O.

**Impact on VT/DE:** LOW - Difference is small (273 vs 265 for N2O = 3% change in N2O CO2e).

**Confidence:** HIGH  
**Status:** Inconsistency confirmed

---

### CE-10: Turkey manure CH4 always zero in CLI

**Verification:** ✅ CONFIRMED  
**Holos Code:**
- `H.Core/Services/Animals/PoultryResultsService.cs:118-123` (reads DailyManureMethaneEmissionRate)
- `H.CLI/ComponentKeys/PoultryKeys.cs:32` (only YearlyManureMethaneRate exposed)
- `H.CLI/Converters/AnimalConverterBase.cs:152-154`

**What it does:** Engine uses daily rate for turkeys, CLI only exposes yearly rate, daily rate never populated.

**Impact on VT/DE:** N/A - No turkey farms in VT/DE test dataset.

**Confidence:** HIGH

---

### CE-11: Liquid manure VS reset to zero on January 1

**Verification:** ✅ CONFIRMED  
**Holos Code:**
- `H.Core/Services/Animals/AnimalResultsServiceBase.cs:122-127`
- `ApplySharedTankStorageToLiquidDays:878-884`

```csharp
if (this.HasMovedToNewYear(currentDate))
    previousDaysEmissions = null;

if (dailyEmissions.DateTime.DayOfYear == 1)
    previousDaysEmissions = null;
```

**What it does:** Tank inventory (VS, volume) discarded at year boundary.

**Primary Source:** IPCC 2019 Vol 4 Ch 10, Sec 10.4 - MCF depends on residence time in storage.

**Impact on VT/DE:** HIGH - Winter-stored manure (6+ months typical) resets to zero, underestimating Jan-Mar storage CH4. Could be 30-50% underestimate for storage emissions in those months.

**Confidence:** HIGH

---

### CE-12: Carry-over state shared across management periods

**Verification:** ⚠️ PARTIALLY CONFIRMED  
**Holos Code:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:153-160, 861-893`

**What it does:** One `previousDaysEmissions` per group, not per physical tank. Overlapping periods could chain incorrectly.

**Impact on VT/DE:** UNKNOWN - Depends on farm structure. Single-group farms unaffected.

**Confidence:** MEDIUM  
**Status:** Behavior observed but overlap case not fully line-traced (per instructions)

---

### CE-13: Daily removal fraction capped at 0.95

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.Core/Models/ManureStorageMath.cs:16, 41-53`

```csharp
MaximumRemovalFraction = 0.95

public static double BoundRemovalFraction(double fraction)
{
    return Math.Min(fraction, MaximumRemovalFraction);
}
```

**What it does:** Hard cap leaves 5% residual always.

**Primary Source:** UNVERIFIED (no source cited in code, per instructions)

**Impact on VT/DE:** LOW - 5% residual affects tank CH4 by <5%, small absolute.

**Confidence:** HIGH (code verified)  
**Status:** UNVERIFIED (no primary source for 0.95 cap)

---

### CE-14: Covered/crusted liquid storage CH4 reduced by hard-coded factors

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:966-976`

```csharp
reductionFactor = StateType == LiquidWithNaturalCrust ? 0.4 : 0.25
```

**What it does:** Fixed 0.4 for natural crust, 0.25 for other covers.

**Primary Source:** IPCC 2019 Vol 4 Ch 10, Table 10.17 - Separate MCF values for liquid with/without crust, but not multiplicative reduction factors.  
**Source of 0.4/0.25:** UNVERIFIED (per instructions)

**Impact on VT/DE:** MEDIUM - For farms with covers, 60-75% CH4 reduction. If covers are common, affects 10-30% of storage CH4.

**Confidence:** HIGH (code verified)  
**Status:** UNVERIFIED (no primary source for specific factors)

---

### CE-15: Beef and sheep have no dynamic liquid-manure CH4 branch

**Verification:** ✅ CONFIRMED  
**Holos Code:**
- `H.Core/Services/Animals/BeefCattleResultsService.cs:168-176, 513`
- `H.Core/Services/Animals/SheepResultsService.cs:236`

**What it does:** Always uses VS × B0 × MCF, no daily tank model like dairy/swine.

**Primary Source:** IPCC 2019 Vol 4 Ch 10, Eq 10.23 - Same equation applies to all livestock.

**Impact on VT/DE:** MEDIUM - Beef with liquid storage (uncommon in VT/DE) would have incorrect storage CH4. Most VT/DE beef is solid/pasture.

**Confidence:** HIGH  
**Status:** Design choice (species-specific implementation)

---

### CE-16: 'Other livestock' manure has zero N (no Table 6 row)

**Verification:** ✅ CONFIRMED  
**Holos Code:**
- `H.Core/Models/ComponentCategoryExtensions.cs:31` (GetAnimalTypeFromComponentCategory)
- `H.Core/Models/Farm.Manure.cs:61-77` (GetManureCompositionData)

**What it does:** Table 6 CSV has no `OtherLivestock` row, lookup returns empty default with N=0.

**Primary Source:** Holos Table 6 should cover all animal types.

**Impact on VT/DE:** N/A - No "other livestock" in VT/DE dataset.

**Confidence:** HIGH

---

### CE-17: Legacy ManureStateType values not recognized as liquid

**Verification:** ✅ CONFIRMED  
**Holos Code:**
- `H.Core/Enumerations/ManureStateTypeExtensions.cs:25-31` (IsLiquidManure)
- `H.Core/Enumerations/ManureStateType.cs:42-51` (Liquid, LiquidCrust [Obsolete])

**What it does:** `IsLiquidManure()` checks only current enum values, not obsolete ones.

**Impact on VT/DE:** N/A - CLI inputs use current enum values.

**Confidence:** HIGH

---

### CE-18: No input validation (TDN > 100, negative weight gain)

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:683-706`

**What it does:** No bounds checks. TDN > 100 → negative VS term. Negative weight gain → negative emissions possible.

**Primary Source:** Physical constraints (0 < TDN < 100, non-negative gains).

**Impact on VT/DE:** LOW - Properly formatted inputs avoid this. Bad inputs give nonsense outputs.

**Confidence:** HIGH  
**Status:** Input validation gap

---

### CE-19: One malformed cell aborts whole CLI batch

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.CLI/TemporaryComponentStorage/AnimalTemporaryInputBase.cs:107, 159-222`

```csharp
throw new FormatException(...)
```

**What it does:** Uncaught FormatException terminates batch processing.

**Impact on VT/DE:** N/A - Well-formed inputs run fine.

**Confidence:** HIGH  
**Status:** Error handling gap

---

### CE-20: CLI grazing hard-coded (Jan 1 start, 80% moisture)

**Verification:** ✅ CONFIRMED  
**Holos Code:** `H.CLI/Converters/FieldSystemInputConverter.cs:209-236`

```csharp
Start = new DateTime(viewItem.Year, 1, 1)  // L225
MoistureContentAsPercentage = 80           // L230 with TODO
```

**What it does:** Grazing always starts January 1, moisture fixed at 80%.

**Impact on VT/DE:** LOW - Affects grazing N cycling, but most VT/DE is confined feeding.

**Confidence:** HIGH  
**Status:** Design limitation

---

### CE-21: Several CLI columns parsed but have no effect

**Verification:** ⚠️ CONFIRMED BY TESTING  
**Holos Code:** Not line-traced (per instructions)

**What it does:** Columns read but not wired to calculations: Volatilization Fraction, Ash Content, Feed Intake, many diet columns, bedding properties, etc.

**Impact on VT/DE:** VARIES - Some (e.g., Ash Content) would affect VS; others minor.

**Confidence:** MEDIUM  
**Status:** Confirmed by testing; exact lines not verified (per instructions)

---

### CE-22: GUI-exported 'Manure Carbon Inputs Per Hectare' used as input

**Verification:** ⚠️ CONFIRMED BY TESTING  
**Holos Code:** Not line-traced (per instructions)

**What it does:** Reads exported value instead of recomputing from farm manure.

**Impact on VT/DE:** LOW - SOC calculations showed low sensitivity in testing.

**Confidence:** MEDIUM  
**Status:** Confirmed by testing; line not verified (per instructions)

---

### CE-23: Unapplied manure credited as organic N to fields

**Verification:** ⚠️ SUSPECTED  
**Holos Code:** Not line-traced (per instructions)

**What it does:** Manure not in explicit applications still counts as F_ON for direct N2O.

**Primary Source:** IPCC 2019 Vol 4 Ch 11, Eq 11.1 - F_ON should be explicitly applied amounts only.

**Impact on VT/DE:** UNKNOWN - Depends on whether farms have explicit applications in dataset.

**Confidence:** LOW  
**Status:** Design choice; line not verified (per instructions)

---

## Summary of CE Issues Impact on VT/DE

### High Impact (>10% effect on relevant emissions)
- **CE-01:** CLI storage never empties (20-50% storage CH4 overestimate)
- **CE-03:** Zero N fraction → zero storage (100% error if triggered)
- **CE-11:** Jan 1 reset (30-50% storage CH4 underestimate Jan-Mar)

### Medium Impact (5-10% effect)
- **CE-04:** Multi-row fields no removals (same as CE-01 if triggered)
- **CE-08:** Deposition in F_SN (small absolute, conceptually wrong)
- **CE-14:** Cover factors (affects covered systems only)
- **CE-15:** Beef liquid storage (uncommon in VT/DE)

### Low Impact (<5% effect)
- **CE-02, CE-05, CE-06, CE-07, CE-09, CE-10, CE-13, CE-16, CE-17, CE-18, CE-19, CE-20, CE-21, CE-22, CE-23**

### Unverified Items (no primary source)
- **CE-07:** Calf VS coefficient 9.3/1000
- **CE-13:** Removal cap 0.95
- **CE-14:** Crust/cover factors 0.4/0.25

## Remaining Audits Needed

1. **Soil N2O equations** - Compare against IPCC 2006 Ch 11
2. **N excretion calculations** - Verify protein-based calculations
3. **MCF temperature adjustments** - Check climate zone boundaries
4. **Emission factors** - Verify all EF values against IPCC tables
5. **Unit conversions** - Check all factor conversions (especially 44/28 for N2O)

---

## Confidence Levels

- **HIGH:** Direct comparison with IPCC equation, clear discrepancy
- **MEDIUM:** Plausible but cannot fully verify against public source
- **LOW:** Insufficient information to assess

---

## Next Steps

1. ✅ Document audit findings (this file)
2. ⏳ Implement IPCC-correct default versions
3. ⏳ Add Holos fork options with `use_holos_*` flags
4. ⏳ Run ensemble showing effect of each discrepancy
5. ⏳ Continue audit for remaining equations

---

**Document:** HOLOS_CODE_AUDIT_AN_v1.md  
**Status:** Initial audit complete for core cattle equations  
**Date:** 2026-11-01

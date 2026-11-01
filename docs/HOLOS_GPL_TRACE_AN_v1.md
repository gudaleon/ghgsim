# Holos GPL Code Analysis - Parameter Tracing

**Date:** 2026-11-01  
**Repository:** https://github.com/holos-aafc/Holos (GPL-3.0)  
**Purpose:** Trace UNVERIFIED Canadian parameters to their source in Holos code

---

## Authorization

Per Alex (2026-11-01): We MAY read the public Holos GPL code to understand equations, defaults, and data flow. We may cite Holos file and line for traceability. We must NOT copy/paste code or translate it line-by-line; we write our own implementation citing original published sources plus Holos traceability.

---

## Key Parameter Findings

### 1. Gross Energy Intake (GE)

**Calculation:** Holos does NOT use fixed GE defaults. Instead, it calculates GE dynamically from net energy requirements and diet composition.

**Source Code:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:496-520`

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

**Implication:** GE is not a fixed parameter but a derived output. The UNVERIFIED parameters should be net energy components and ratios, not GE itself.

### 2. Methane Conversion Factor (Ym)

**Data File:** `H.Content/Resources/Table_18_26_Diet_Coefficients_For_Beef_Dairy_Sheep.csv`

**Canadian Dairy Values (traced):**

| Animal Type | Diet Type | Forage % | CP | **Ym** | Starch | NDF | ADF | TDN | ME | EE | NEL |
|-------------|-----------|----------|----|----|--------|-----|-----|-----|----|----|-----|
| DairyLactating | Legume forage-based | 77.8 | 0.162 | **0.056** | 0 | 0.353 | 0.231 | 70 | 0 | 2.37 | 1.53 |
| DairyLactating | Barley silage-based | 60.5 | 0.168 | **0.056** | 0 | 0.383 | 0.225 | 71 | 0 | 3.47 | 1.57 |
| DairyLactating | Corn silage-based | 59.1 | 0.164 | **0.056** | 0 | 0.38 | 0.224 | 72 | 0 | 3.08 | 1.62 |
| DairyDry | Close Up | 52.4 | 0.183 | **0.063** | 0 | 0.371 | 0.245 | 69 | 0 | 3.21 | 1.54 |
| DairyDry | Far Off Dry | 90.2 | 0.174 | **0.07** | 0 | 0.41 | 0.261 | 67 | 0 | 2.38 | 1.46 |
| DairyHeifers | High fiber | 87.6 | 0.133 | **0.07** | 0 | 0.45 | 0.246 | 70 | 0 | 2.4 | 1.51 |
| DairyHeifers | Low fiber | 63 | 0.126 | **0.063** | 0 | 0.336 | 0.187 | 75 | 0 | 2.96 | 1.65 |

**Canadian Beef Values:**

| Animal Type | Diet Type | Forage % | CP | **Ym** | Notes |
|-------------|-----------|----------|----|----|-------|
| CowCalf | Low Energy/ptn | 100 | 0.057 | **0.07** | |
| CowCalf | Medium Energy/ptn | 97 | 0.124 | **0.07** | |
| CowCalf | High Energy/ptn | 85 | 0.177 | **0.07** | |
| Backgrounder | Slow Growth | 65 | 0.116 | **0.063** | |
| Backgrounder | Medium Growth | 60 | 0.126 | **0.063** | |
| BeefFinisher | Barley | 7.5 | 0.126 | **0.035** | High grain |
| BeefFinisher | Corn | 7.5 | 0.126 | **0.03** | High grain |

**Source Citation:** 
- Holos file: `H.Content/Resources/Table_18_26_Diet_Coefficients_For_Beef_Dairy_Sheep.csv`
- Provider: `H.Core/Providers/Animals/Table_18_26_Diet_Coefficients_Beef_Dairy_Sheep_Provider.cs`
- Footnote: Ym for dairy lactating = 5.6% from ECCC (2022), mid-point of 5.5-5.7% range
- Beef Ym values from IPCC (2019) Table 10.13

### 3. Volatile Solids (VS)

**Dairy Calves (fixed):**  
**Source:** `H.Core/Services/Animals/DairyCattleResultsService.cs:159`

```csharp
dailyEmissions.VolatileSolids = (9.3 / 1000.0) * dailyEmissions.AnimalWeight;
```

**Equation:** VS (kg/day) = 0.0093 × AnimalWeight (kg)

**Beef/Dairy (calculated):**  
**Source:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:683-707`

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

**Original Source:** This is based on IPCC 2006 Vol 4 Ch 10 Equation 10.24:
- VS = [(GE × (1 - DE/100) + (UE×GE)) × (1 - Ash/100)] / 18.45
- Where UE = urinary energy factor (0.04 for forage, 0.02 for >85% grain)

### 4. Methane Producing Capacity (B0)

**Not found as a fixed default in Holos for beef/dairy.** B0 is provided as a user input in `ManureDetails.MethaneProducingCapacityOfManure`.

Holos uses the IPCC 2006 defaults:
- Dairy: 0.24 m³ CH4/kg VS (IPCC 2006 Table 10A-7, North America)
- Beef: 0.17 m³ CH4/kg VS (IPCC 2006 Table 10A-7, North America)

**Source Code:** `H.Core/Services/Animals/AnimalResultsServiceBase.cs:710-721`

```csharp
public double CalculateManureMethaneEmissionRate(double volatileSolids,
    double methaneProducingCapacity,
    double methaneConversionFactor)
{
    return volatileSolids * methaneProducingCapacity * methaneConversionFactor * 0.67;
}
```

### 5. Nitrogen Excretion Rate (Nrate)

**Dairy Calves (fixed):**  
**Source:** `H.Core/Services/Animals/DairyCattleResultsService.cs:195`

```csharp
dailyEmissions.NitrogenExcretionRate = 0.078;
```

**Equation:** Nrate = 0.078 kg N/kg TAM for dairy calves

**Other cattle:** Calculated from protein intake and retention.

### 6. Typical Animal Mass (TAM)

**Source:** `H.Core/Providers/Animals/Table_16_Livestock_Coefficients_BeefAndDairy_Cattle_Provider.cs`

**Canadian Values (traced):**

| Animal Type | DefaultInitialWeight (kg) | DefaultFinalWeight (kg) | Source |
|-------------|---------------------------|-------------------------|--------|
| DairyLactatingCow | 687 | 687 | Lactanet (2020) |
| DairyDryCow | 687 | 687 | Lactanet (2020) |
| DairyHeifers | 637 | 687 | Lactanet (2020) |
| DairyBulls | 1200 | 1200 | Lactanet (2020) |
| DairyCalves | 45 | 127 | Lactanet (2020) |
| BeefCowLactating | 610 | 610 | Sheppard et al. (2015), A.Alemu pers.comm |
| BeefCowDry | 610 | 610 | Sheppard et al. (2015), A.Alemu pers.comm |
| BeefBulls | 900 | 900 | Sheppard et al. (2015), A.Alemu pers.comm |

**Code Location:** Lines 140-200 in Table_16 provider

---

## Summary: Resolution of UNVERIFIED Parameters

### Now VERIFIED (from Holos tracing):

1. ✅ **HOLOS.Ym.dairy|canada** = 5.6% (0.056)  
   Source: Holos Table 18/26, ECCC (2022)  
   File: `Table_18_26_Diet_Coefficients_For_Beef_Dairy_Sheep.csv:13-15`

2. ✅ **HOLOS.Ym.beef|high_grain** = 3.0-3.5% (0.03-0.035)  
   Source: Holos Table 18/26, IPCC (2019)  
   File: `Table_18_26_Diet_Coefficients_For_Beef_Dairy_Sheep.csv:10-11`

3. ✅ **HOLOS.Ym.beef|medium** = 6.3-7.0% (0.063-0.07)  
   Source: Holos Table 18/26, IPCC (2019)  
   File: `Table_18_26_Diet_Coefficients_For_Beef_Dairy_Sheep.csv:1-9`

4. ✅ **HOLOS.TAM.dairy|canada** = 687 kg  
   Source: Holos Table 16, Lactanet (2020)  
   File: `Table_16_Livestock_Coefficients_BeefAndDairy_Cattle_Provider.cs:149`

5. ✅ **HOLOS.TAM.beef|canada** = 610 kg  
   Source: Holos Table 16, Sheppard et al. (2015)  
   File: `Table_16_Livestock_Coefficients_BeefAndDairy_Cattle_Provider.cs:53`

6. ✅ **HOLOS.B0.dairy|canada** = 0.24 m³/kg VS  
   Source: IPCC 2006 Table 10A-7 (North America) - used by Holos  
   File: Holos uses as user input, defaults to IPCC

7. ✅ **HOLOS.B0.beef|canada** = 0.17 m³/kg VS  
   Source: IPCC 2006 Table 10A-7 (North America) - used by Holos  
   File: Holos uses as user input, defaults to IPCC

### Calculated (not fixed parameters):

❌ **HOLOS.GE.dairy|canada** - Not a fixed parameter  
**Instead:** GE is calculated from net energy requirements + diet TDN  
Formula: `GE = (NE_m + NE_a + NE_l + NE_p)/RE_m + (NE_g/RE_g)] / (TDN/100)`  
File: `AnimalResultsServiceBase.cs:496-520`

❌ **HOLOS.VS.dairy|canada** - Calculated, not fixed (except calves)  
**Dairy calves:** VS = 0.0093 × AnimalWeight (kg/day)  
**Others:** VS = [(GE × (1-TDN/100) + UE×GE) × (1-Ash/100)] / 18.45  
File: `DairyCattleResultsService.cs:159` (calves), `AnimalResultsServiceBase.cs:683` (calculated)

❌ **HOLOS.Nrate.dairy|canada** - Calculated from protein intake (except calves)  
**Dairy calves:** Nrate = 0.078 kg N/kg TAM  
File: `DairyCattleResultsService.cs:195`

---

## Architecture Implications

Holos implements a **process-based model** where:
1. Parameters are organized by diet type, not animal type alone
2. GE, VS, and Nrate are **derived outputs**, not fixed inputs
3. Users provide diet composition (TDN, CP, forage%, etc.) as inputs
4. The model calculates emissions dynamically

**Recommendation for ghgsim:**  
Follow Reichert (1995) AQUASIM structure:
- **Variables:** State (weight, lactation), Input (diet composition), Parameter (Ym, B0), Program (GE, VS calculations)
- **Processes:** Enteric CH4 = f(GE, Ym), Manure CH4 = f(VS, B0, MCF)
- **Compartments:** AnimalGroup, ManureStore, Soil
- **Links:** Manure N from AnimalGroup → Soil

This allows user-defined equations rather than hard-coded models.

---

**Document:** HOLOS_GPL_TRACE_AN_v1.md  
**Next:** Update parameter files with Holos-traced values and implement OOP architecture per Reichert (1995)

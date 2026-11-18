# Download All Research Papers — Batch Script

**Date:** 2026-09-10  
**Purpose:** Download all newly discovered papers for thesis research

---

## Quick Download (Top 10 Most Relevant)

```powershell
# Run in PowerShell
$papers = @(
    @{id="2607.18791"; name="01_STS-NET_SelfSupervised_Stress_SITS"},
    @{id="2506.03394"; name="02_EigenCL_Unsupervised_Contrastive_NDRE"},
    @{id="2404.16844"; name="03_Sugarcane_Satellite_Spectroscopy_Review"},
    @{id="2507.13514"; name="04_SugarBeet_SITS_3DAutoencoder"},
    @{id="2510.23124"; name="05_DeepSalt_DomainAdaptation_Salinity"},
    @{id="2407.08298"; name="06_XAI_Guided_Vegetation_Indices"},
    @{id="2509.02265"; name="07_Spectroscopic_Salinity_Stress_Review"},
    @{id="2510.18648"; name="08_Informed_Learning_Physics_ML"},
    @{id="2506.01714"; name="09_Plant_Stress_Physiology_Mechanisms"},
    @{id="2204.02029"; name="10_Salinity_Irrigation_Management_Bayesian"}
)

foreach ($p in $papers) {
    Write-Host "Downloading $($p.name)..."
    Invoke-WebRequest -Uri "https://arxiv.org/pdf/$($p.id)" -OutFile "papers_new\$($p.name).pdf"
}
Write-Host "Done! Check papers_new/ folder."
```

---

## Full Download (All 20 New Papers)

```powershell
$allPapers = @(
    # Category A: Direct Relevance
    @{id="2607.18791"; cat="A"; name="STS-NET_SelfSupervised_Stress_SITS"},
    @{id="2506.03394"; cat="A"; name="EigenCL_Unsupervised_Contrastive_NDRE"},
    @{id="2507.13514"; cat="A"; name="SugarBeet_SITS_3DAutoencoder"},
    @{id="2407.08298"; cat="A"; name="XAI_Guided_Vegetation_Indices"},
    @{id="2510.18648"; cat="A"; name="Informed_Learning_Physics_ML"},
    @{id="2510.23124"; cat="A"; name="DeepSalt_DomainAdaptation_Salinity"},
    
    # Category B: Methodology & Physics
    @{id="2509.02265"; cat="B"; name="Spectroscopic_Salinity_Stress_Review"},
    @{id="2506.01714"; cat="B"; name="Plant_Stress_Physiology_Mechanisms"},
    @{id="2412.15075"; cat="B"; name="DroughtSet_SpatialTemporal_Learning"},
    @{id="2404.16844"; cat="B"; name="Sugarcane_Satellite_Spectroscopy_Review"},
    @{id="2108.05484"; cat="B"; name="SSL_Irrigation_Detection"},
    @{id="2204.02029"; cat="B"; name="Salinity_Irrigation_Management_Bayesian"},
    @{id="1602.06335"; cat="B"; name="VegHealth_ML_Forecasting"},
    
    # Category C: Additional Context
    @{id="2508.13379"; cat="C"; name="Avocado_LowCost_Stress_Sensing"},
    @{id="2106.07770"; cat="C"; name="Potato_Stress_Aerial_DL"},
    @{id="2609.10156"; cat="C"; name="ScopeMamba_YOLO_RS"},
    @{id="2603.23779"; cat="C"; name="S2_Yield_Estimation_Review"},
    @{id="2509.10804"; cat="C"; name="Tomato_Weed_SITS_Detection"},
    @{id="2609.07915"; cat="C"; name="JEDI_JEPA_to_Edge_Distillation"}
)

mkdir -Force papers_new
foreach ($p in $allPapers) {
    Write-Host "[Cat $($p.cat)] Downloading $($p.name)..."
    try {
        Invoke-WebRequest -Uri "https://arxiv.org/pdf/$($p.id)" -OutFile "papers_new\$($p.name).pdf"
        Write-Host "  ✓ Saved"
    } catch {
        Write-Host "  ✗ Failed: $($_.Exception.Message)"
    }
}
Write-Host "`n=== Complete ==="
Get-ChildItem papers_new\*.pdf | Measure-Object | Select-Object -ExpandProperty Count
```

---

## Alternative: One-Line Curl Command (PowerShell)

```powershell
# Create directory and download
New-Item -ItemType Directory -Force -Path "papers_new" | Out-Null
@(
    "2607.18791","2506.03394","2507.13514","2407.08298","2510.18648",
    "2510.23124","2509.02265","2506.01714","2412.15075","2404.16844",
    "2108.05484","2204.02029","1602.06335","2508.13379","2106.07770",
    "2609.10156","2603.23779","2509.10804","2609.07915"
) | ForEach-Object {
    $id = $_
    $url = "https://arxiv.org/pdf/$id"
    $out = "papers_new/$id.pdf"
    if (-not (Test-Path $out)) {
        Write-Host "Downloading $id ..."
        Invoke-WebRequest -Uri $url -OutFile $out
    } else {
        Write-Host "Skipping $id (already exists)"
    }
}
Write-Host "`nTotal downloaded:"
(Get-ChildItem papers_new\*.pdf).Count
```

---

## Also Download Advisor's 8 Mandatory Papers

```powershell
# Already partially downloaded, verify/re-download
@(
    @{id="2409.09673"; name="01_SITSMamba"},
    @{id="2404.03936"; name="02_DL_SITS_Review"},
    @{id="2304.12210"; name="03_SSL_Cookbook"},
    @{id="2402.13791"; name="04_XAI_RS_Review"},
    @{id="2005.03394"; name="05_SelfAttention_SITS_Russwurm"},
    @{doi="10.1016/j.isprsjprs.2020.05.009"; name="05_SelfAttention_SITS_Russwurm_DOI"},
    @{doi="10.3390/plants11212884"; name="07_Combined_Stress_Angon"},
    @{doi="10.1007/s11119-025-10279-5"; name="08_Salinity_LAI_Paciolla"}
) | ForEach-Object {
    if ($_.id) {
        $url = "https://arxiv.org/pdf/$($_.id)"
        $out = "papers/$($_.name).pdf"
        if (-not (Test-Path $out)) {
            Write-Host "Downloading $($_.name) ..."
            Invoke-WebRequest -Uri $url -OutFile $out
        }
    }
}
```

---

## Verification After Download

```powershell
# List all downloaded papers with sizes
Write-Host "=== New Papers (papers_new/) ==="
Get-ChildItem papers_new\*.pdf | Sort-Object Name | Format-Table Name, Length -AutoSize

Write-Host "`n=== Advisor Papers (papers/) ==="
Get-ChildItem papers\*.pdf | Sort-Object Name | Format-Table Name, Length -AutoSize

# Check for incomplete downloads (files < 1MB likely failed)
Write-Host "`n=== Checking for small/incomplete files ==="
Get-ChildItem papers_new\*.pdf | Where-Object { $_.Length -lt 1MB } | Format-Table Name, Length
Get-ChildItem papers\*.pdf | Where-Object { $_.Length -lt 1MB } | Format-Table Name, Length
```

# ghgsim driver for FAO GLEAM (AN_v1). Apache-2.0, part of ghgsim.
# Calls only exported functions of the unmodified gleam package (AGPL-3, installed
# separately at tag v0.8.0-alpha = commit b0937d2). No GLEAM code is copied here.
# Args: inputs.csv mms_fraction.csv mms_factors.csv out_results.csv out_session.json
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 5)
suppressPackageStartupMessages({
  library(data.table)
  library(gleam)
})
inp  <- fread(args[1], colClasses = list(character = "herd_id"))
frac <- fread(args[2], colClasses = list(character = "herd_id"))
fact <- fread(args[3], colClasses = list(character = "herd_id"))
if (file.exists(args[4])) stop("refusing to overwrite ", args[4])
fact[, registry_keys := NULL]
ent <- run_emissions_enteric_module(
  inp[, .(herd_id, species_short, cohort_short, ration_digestibility_fraction,
          ration_gross_energy, ration_intake)],
  show_indicator = FALSE)
man <- run_emissions_manure_module(
  inp[, .(herd_id, cohort_short, ration_intake, ration_digestibility_fraction,
          nitrogen_excretion, ration_urinary_energy_fraction, ration_ash)],
  manure_management_system_fraction = frac,
  manure_management_system_factors = fact,
  show_indicator = FALSE)
keep_m <- c("herd_id", "cohort_short", "volatile_solids", "ch4_manure_other", "ch4_manure_pasture",
            grep("^n2o_manure_(other|pasture)_", names(man), value = TRUE))
res <- merge(ent[, .(herd_id, cohort_short, ch4_conversion_factor_ym, ch4_enteric)], man[, ..keep_m],
             by = c("herd_id", "cohort_short"))
fwrite(res, args[4])
pd <- packageDescription("gleam")
sess <- list(r_version = R.version.string, platform = R.version$platform,
             gleam_version = as.character(packageVersion("gleam")),
             gleam_libpath = normalizePath(dirname(system.file(package = "gleam")), winslash = "/"),
             gleam_remote_sha = if (is.null(pd$RemoteSha)) NA else pd$RemoteSha,
             data_table_version = as.character(packageVersion("data.table")),
             cli_version = as.character(packageVersion("cli")))
txt <- paste0("{", paste(sprintf('"%s": %s', names(sess),
              vapply(sess, function(x) if (is.na(x)) "null" else sprintf('"%s"', x), "")), collapse = ", "), "}")
writeLines(txt, args[5])

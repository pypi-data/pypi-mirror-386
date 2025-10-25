from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import arrow
import typer
from module_qc_data_tools import (
    get_layer_from_sn,
    load_json,
    outputDataFrame,
    qcDataFrame,
    save_dict_list,
)

from module_qc_analysis_tools import __version__
from module_qc_analysis_tools import data as data_path
from module_qc_analysis_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    LogLevel,
)
from module_qc_analysis_tools.utils.analysis import perform_qc_analysis
from module_qc_analysis_tools.utils.misc import (
    bcolors,
    get_inputs,
    get_qc_config,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    ctx: typer.Context,
    input_meas: Path = OPTIONS["input_meas"],
    base_output_dir: Path = OPTIONS["output_dir"],
    # qc_criteria_path: Path = OPTIONS["qc_criteria"],
    # layer: str = OPTIONS["layer"],
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    log = logging.getLogger(__name__)
    log.setLevel(verbosity.value)

    log.info("")
    log.info(" ===============================================")
    log.info(" \tPerforming MASS analysis")
    log.info(" ===============================================")
    log.info("")

    test_type = Path(__file__).stem
    if ctx.info_name in ["mass", "analysis-MASS"]:  # for PCB
        test_type = "MASS"

    time_start = round(datetime.timestamp(datetime.now()))
    output_dir = base_output_dir.joinpath(test_type).joinpath(f"{time_start}")
    output_dir.mkdir(parents=True, exist_ok=False)

    allinputs = get_inputs(input_meas)
    # qc_config = get_qc_config(qc_criteria_path, test_type)

    # alloutput = []
    # timestamps = []
    for filename in sorted(allinputs):
        log.info("")
        log.info(f" Loading {filename}")
        # meas_timestamp = get_time_stamp(filename)

        inputDFs = load_json(filename)
        log.info(
            f" There are results from {len(inputDFs)} module(s) stored in this file"
        )

        with Path(filename).open(encoding="utf-8") as f:
            jsonData = json.load(f)

        for j, inputDF in zip(jsonData, inputDFs):
            d = inputDF.to_dict()
            qcframe = inputDF.get_results()

            stage = j[0].get("stage")
            results = j[0].get("results")
            props = results.get("property")
            metadata = results.get("Metadata") or results.get("metadata")

            module_sn = d.get("serialNumber")
            # alternatively, props.get("MODULE_SN")

            # the QC cuts depend on the stage
            # The MODULE/TAB_CUTTING criterion assumes the existence of wirebond protection.
            qc_config = None
            if stage in [
                "MODULE/ASSEMBLY",
                "MODULE/WIREBOND_PROTECTION",
                "MODULE/TAB_CUTTING",
                "BAREMODULERECEPTION",
                "PCB_RECEPTION_MODULE_SITE",
            ]:
                qc_config = get_qc_config(
                    data_path / "analysis_cuts.json", f"{test_type}_{stage}"
                )
            elif stage in [
                "OB_LOADED_MODULE_CELL/ASSEMBLY",
                "OB_LOADED_MODULE_CELL/TAB_CUTTING",
            ]:
                with_frame = results.get("property").get("WITH_FRAME")
                qc_config = get_qc_config(
                    data_path / "analysis_cuts_OBLoadedModuleCell.json",
                    test_type + ("_WITH_FRAME" if with_frame else ""),
                )
            else:
                msg = f"Mass measurement not implemented for {stage} stage."
                raise NotImplementedError(msg)

            layer = get_layer_from_sn(module_sn)

            result_values = {
                "MASS": results.get("Measurements").get("MASS").get("Values")[0]
            }

            passes_qc, _, _ = perform_qc_analysis(
                test_type, qc_config, layer, result_values
            )

            log.info("")
            if passes_qc:
                log.info(
                    f" Module {module_sn} passes QC? "
                    + bcolors.OKGREEN
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            else:
                log.info(
                    f" Module {module_sn} passes QC? "
                    + bcolors.BADRED
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            log.info("")

            #  Output a json file
            outputDF = outputDataFrame()
            outputDF.set_test_type(test_type)
            data = qcDataFrame()

            if metadata is not None:
                data._meta_data.update(metadata)

            #  Pass-through properties in input
            for key, value in props.items():
                data.add_property(key, value)

            #  Add analysis version
            data.add_property(
                "ANALYSIS_VERSION",
                __version__,
            )

            #  Pass-through measurement parameters
            for key, value in results.items():
                if key in [
                    "property",
                    "metadata",
                    "Metadata",
                    "Measurements",
                    "comment",
                ]:
                    continue

                data.add_parameter(key, value)

            time_start = qcframe.get_meta_data()["TimeStart"]
            time_end = qcframe.get_meta_data().get("TimeEnd")
            duration = (
                (arrow.get(time_end) - arrow.get(time_start)).total_seconds()
                if time_end
                else -1
            )

            data.add_property(
                "MEASUREMENT_DATE",
                arrow.get(time_start).isoformat(timespec="milliseconds"),
            )
            data.add_property("MEASUREMENT_DURATION", int(duration))

            for key, value in result_values.items():
                data.add_parameter(key, value)

            outputDF.set_results(data)
            outputDF.set_pass_flag(passes_qc)

            outfile = output_dir.joinpath(f"{module_sn}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            out = outputDF.to_dict(True)
            out.update({"serialNumber": module_sn})
            save_dict_list(outfile, [out])


if __name__ == "__main__":
    typer.run(main)

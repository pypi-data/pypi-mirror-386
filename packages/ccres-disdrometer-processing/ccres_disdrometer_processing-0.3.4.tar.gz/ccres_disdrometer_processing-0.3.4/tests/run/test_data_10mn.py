from pathlib import Path

import xarray as xr
from click.testing import CliRunner

from ccres_disdrometer_processing import utils
from ccres_disdrometer_processing.cli import cli

params = {
    "site": "lindenberg",
    "date_yesterday": "2024-08-01",
    "date_today": "2024-08-02",
    "date_tomorrow": "2024-08-03",
    "radar": "mira-35",
    "radar-pid": "https://hdl.handle.net/21.12132/3.d6cc3d73f9dd4d4b",
    "disdro": "parsivel",
    "disdro-pid": "https://hdl.handle.net/21.12132/3.1b0966f63b2d41f2",
    "meteo-available": True,
    "meteo": "weather-station",
    "meteo-pid": "https://hdl.handle.net/21.12132/3.ffb25f43330f4793",
    "config_file": "config_lindenberg_mira-parsivel.toml",
    "output": {
        "preprocess_yesterday": "lindenberg_2024-08-01_mira-parsivel_preprocessed.nc",
        "preprocess_today": "lindenberg_2024-08-02_mira-parsivel_preprocessed.nc",
        "preprocess_tomorrow": "lindenberg_2024-08-03_mira-parsivel_preprocessed.nc",
        "preprocessing_ql": {
            "weather-overview": "lindenberg_2024-08-02_mira-parsivel_preproc-weather-overview.png",  # noqa E501
            "zh-overview": "lindenberg_2024-08-02_mira-parsivel_zh-preproc-overview.png",  # noqa E501
        },
        "process": "lindenberg_2024-08-02_mira-parsivel_processed.nc",
        "process_ql": {
            "summary": "lindenberg_2024-08-02_mira-parsivel_process-summary",
            "detailled": "lindenberg_2024-08-02_mira-parsivel_process-detailled",  # noqa E501
        },
    },
}


def test_empty_file_20240802_lindenberg(data_input_dir, data_conf_dir, data_dir):
    path: Path = data_dir / "outputs_bug_fixes"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    data_bugfix_dir = Path(path)
    site = params["site"]
    radar = params["radar"]
    radar_pid = params["radar-pid"]
    disdro = params["disdro"]
    disdro_pid = params["disdro-pid"]
    has_meteo = params["meteo-available"]
    meteo = params["meteo"]
    conf = data_conf_dir / params["config_file"]
    prepro_file_yesterday = data_bugfix_dir / params["output"]["preprocess_yesterday"]
    prepro_file_today = data_bugfix_dir / params["output"]["preprocess_today"]
    prepro_file_tomorrow = data_bugfix_dir / params["output"]["preprocess_tomorrow"]
    output_process = data_bugfix_dir / params["output"]["process"]

    # do the preprocessing for the three input days :
    for date, output in zip(
        [params["date_yesterday"], params["date_today"], params["date_tomorrow"]],
        [prepro_file_yesterday, prepro_file_today, prepro_file_tomorrow],
    ):
        print(date, output)
        if not output.exists():
            # get the data if needed
            # ---------------------------------------------------------------------------------  # noqa E501
            # radar
            radar_file = utils.get_file_from_cloudnet(
                site, date, radar, radar_pid, data_input_dir
            )
            # disdro
            disdro_file = utils.get_file_from_cloudnet(
                site, date, disdro, disdro_pid, data_input_dir
            )
            # meteo
            if params["meteo-available"]:
                meteo_pid = params["meteo-pid"]
                meteo_file = utils.get_file_from_cloudnet(
                    site, date, meteo, meteo_pid, data_input_dir
                )

            # other parameters
            # ---------------------------------------------------------------------------------  # noqa E501
            # conf
            conf = data_conf_dir / conf

            # run the preprocessing
            # ---------------------------------------------------------------------------------  # noqa E501
            # required args
            args = [
                "--disdro-file",
                str(disdro_file),
                "--radar-file",
                str(radar_file),
                "--config-file",
                str(conf),
            ]
            # add meteo if available
            if has_meteo:
                args += [
                    "--ws-file",
                    str(meteo_file),
                ]

            args += [str(output)]

            runner = CliRunner()
            result_preprocess = runner.invoke(
                cli.preprocess,
                args,
                catch_exceptions=False,
            )
            assert result_preprocess.exit_code == 0

    # do the processing
    if output_process.exists():
        print("File exists, remove and resave")
        output_process.unlink()
    process_args = [
        "--yesterday",
        str(prepro_file_yesterday),
        "--today",
        str(prepro_file_today),
        "--tomorrow",
        str(prepro_file_tomorrow),
        "--config-file",
        str(conf),
        str(output_process),
        "-v",
    ]
    runner = CliRunner()
    result_process = runner.invoke(
        cli.process,
        process_args,
        catch_exceptions=False,
    )
    assert result_process.exit_code == 0
    try:
        ds = xr.open_dataset(output_process)
        print(ds.keys())
        print("File opening : success")
    except ValueError:
        print("Error while opening file")

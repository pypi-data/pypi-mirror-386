import logging
import shutil
import subprocess
from functools import lru_cache
from itertools import product
from pathlib import Path

import b2luigi as luigi
from b2luigi.core.utils import flatten_to_dict

from flare.src.mc_production.generator_specific_methods import MadgraphMethods
from flare.src.mc_production.mc_production_types import get_mc_production_types
from flare.src.utils.bracket_mappings import (
    BracketMappingCMDBuilderMixin,
    BracketMappings,
    check_if_path_matches_mapping,
    get_suffix_from_arg,
)
from flare.src.utils.tasks import OutputMixin, _linear_task_workflow_generator
from flare.src.utils.yaml import get_config

logger = logging.getLogger("luigi-interface")


class MCProductionBaseTask(
    luigi.DispatchableTask, BracketMappingCMDBuilderMixin, MadgraphMethods
):
    """
    This base class is total generalised to be able to run on any N-stage MC production
    workflow.
    """

    prodtype = luigi.EnumParameter(enum=get_mc_production_types())
    datatype = luigi.Parameter()

    stage: str
    results_subdir: str

    @property
    def env_script(self):
        global_env_script_path = luigi.get_setting("dataprod_config")[
            "global_env_script_path"
        ]
        if not global_env_script_path:
            return

        dataprod_dir = luigi.get_setting("dataprod_dir")
        return dataprod_dir / global_env_script_path

    @property
    def slurm_settings(self):
        settings = luigi.get_setting("slurm_settings", {})
        if self.env_script:
            settings["export"] = "NONE"
        return settings

    @property
    def input_file_path(self):
        return Path(next(iter(self.get_all_input_file_names())))

    @property
    def _unparsed_output_file_name(self):
        """
        The raw output file name from the production_types.yaml. This is then checked inside the property
        output_file_name and transformed as required
        """
        return self.stage_dict["output_file"]

    @property
    def stage_dict(self):
        """
        The dictionary of information for this stage
        """
        return self.prodtype.value[self.stage]

    @property
    def prod_cmd(self):
        """
        The cmd for this stage of the MC production as defined inside
        the production_types.yaml
        """
        return self.stage_dict["cmd"].format(*self.collect_cmd_inputs())

    @property
    def tmp_output_parent_dir(self):
        """
        The tmp output dir where all outputs of this workflow will be kept
        """
        return Path(
            self.get_output_file_name(self.output_file_name)
        ).parent.with_suffix(".tmp")

    @property
    def b2luigi_parameter_output_file_name(self):
        params = [self.datatype, self.card_name, self.edm4hep_name]
        filtered_params = [p for p in params if p != "default"]
        return "_".join(filtered_params)

    @property
    def output_file_name(self):
        """
        The output file may be dependent on a datatype, card_name or edm4hep_name parameters so must determine if the output
        file name needs to be parsed and transformed or if we can return the unparsed output file name
        """
        match BracketMappings.determine_bracket_mapping(
            self._unparsed_output_file_name
        ):
            case BracketMappings.datatype_parameter:
                suffix = get_suffix_from_arg(self._unparsed_output_file_name)
                return f"{self.datatype}{suffix}"

            case BracketMappings.b2luigi_detemined_parameter:
                suffix = get_suffix_from_arg(
                    self._unparsed_output_file_name
                )  # eg .root
                prefix = self.b2luigi_parameter_output_file_name
                return f"{prefix}{suffix}"
            case _:
                return self._unparsed_output_file_name

    def copy_input_file_to_output_dir(self, path):
        """
        This function serves to copy a file from analysis/mc_production/ to
        the tmp output dir for historical book keeping
        """
        source = Path(path)
        self.tmp_output_parent_dir.mkdir(parents=True, exist_ok=True)
        destination = self.tmp_output_parent_dir / source.name
        shutil.copy(source, destination)

    def get_file_paths(self):
        return luigi.get_setting("dataprod_dir").glob("*")

    @property
    def unparsed_args(self):
        return self.stage_dict["args"]

    def bm_output(self) -> Path:
        # Create the path to the tmp dir
        return self.tmp_output_parent_dir / self.output_file_name

    def bm_input(self) -> Path:

        return list(self.get_all_input_file_names())[0]

    def bm_datatype_parameter(self, arg) -> Path:
        arg = arg.replace(BracketMappings.datatype_parameter, self.datatype)
        return self._find_file_path_given_arg_and_bracketmapping(
            arg=arg, bracket_mapping=BracketMappings.datatype_parameter
        )

    def bm_free_name(self, arg):
        return self._find_file_path_given_arg_and_bracketmapping(
            arg=arg, bracket_mapping=BracketMappings.free_name
        )

    def _find_file_path_given_arg_and_bracketmapping(
        self, arg: str, bracket_mapping: BracketMappings
    ) -> Path:
        file_paths = [f for f in self.get_file_paths()]
        # Find the associated file using the check_if_path_matches_mapping function
        file_path = [
            str(f)
            for f in file_paths
            if check_if_path_matches_mapping(arg, f, bracket_mapping)
        ]

        match len(file_path):
            case 0:
                raise IndexError(
                    f"There is no file associated with {arg} inside {str(luigi.get_setting('dataprod_dir'))}."
                    " The framework will exit, ensure this file is present and try again."
                )
            case 1:
                # We copy this file to the tmp output dir so we have a history of what input files were used
                path = file_path[0]
                self.copy_input_file_to_output_dir(path)
                return path
            case _:
                # More than one, we assume we are looping over a parameter of this class
                if "card" in arg:
                    path = [p for p in file_path if self.card_name == Path(p).stem][0]
                elif "ed4hep" in arg:
                    path = [p for p in file_path if self.edm4hep_name == Path(p).stem][
                        0
                    ]
                elif self.datatype in arg:
                    path = [p for p in file_path if self.datatype == Path(p).stem][0]
                else:
                    raise FileNotFoundError(
                        f"The file associated with {arg} is unknown to flare. The found paths are {file_path}."
                        f" This may occur if there are multiple files being picked up by flare for {arg}"
                    )

                self.copy_input_file_to_output_dir(path)
                return path

    def process(self):
        """
        This process function essentially acts as the `run` function for a dispatchable task.

        Here the function collects the appropriate cmd to be submitted using the information provided from
        production_types.yaml. Then when ran on the batch system of your choosing, the subprocess.check_call
        will run the cmd and make sure it completes. Once this is done, the output path is moved from the
        tmp folder to the correct folder at which point b2luigi flags the job as done
        """

        logger.info(f"Command to be ran \n\n {self.prod_cmd} \n\n")

        # Run any required pre_run methods for this specific stage for this specific prodtype
        self.pre_run()
        # Run the cmd in the tmp directory
        subprocess.check_call(self.prod_cmd, cwd=self.tmp_output_parent_dir, shell=True)
        # Run any required on_completion methods for this specific stage for this specific prodtype
        self.on_completion()

        # Get final output dir
        target = self.tmp_output_parent_dir.with_suffix("")

        logger.info(f"Moving {self.tmp_output_parent_dir} -> {target}")

        # Move the contents of the tmp dir to the output dir. Not we cannot just move the
        # directory as b2luigi's batch submitter saves the executable_wrapper.sh to the output dir
        shutil.copytree(self.tmp_output_parent_dir, target, dirs_exist_ok=True)
        # Delete output dir
        shutil.rmtree(self.tmp_output_parent_dir)

    def on_completion(self):
        """
        This function is intended to run the required functions to be ran after the main cmd
        for this stage detailed in production_types.yaml
        """
        try:
            func_names = self.stage_dict["on_completion"]
        except KeyError:
            return

        for func_name in func_names:
            if hasattr(self, func_name):
                func = getattr(self, func_name)
                func()

    def pre_run(self):
        """
        This function is intended to run the required functions to be ran prior to the main cmd
        for this stage detailed in production_types.yaml
        """
        try:
            func_names = self.stage_dict["pre_run"]
        except KeyError:
            return

        for func_name in func_names:
            if hasattr(self, func_name):
                func = getattr(self, func_name)
                func()

    def output(self):
        yield self.add_to_output(self.output_file_name)


class MCProductionWrapper(OutputMixin, luigi.DispatchableTask):
    """
    This task simply compiles the outputs from the required tasks into a single folder.

    This is necessary because the FCC analysis tools works by passing the folder and looking for the expected
    input parameters to the workflow.
    """

    prodtype = luigi.Parameter()

    @property
    def slurm_settings(self):
        settings = luigi.get_setting("slurm_settings", {})
        env_script = luigi.get_setting("dataprod_config")["global_env_script_path"]
        if env_script:
            settings["export"] = "ALL"
        return settings

    @property
    def results_subdir(self):
        return luigi.get_setting("results_subdir")

    @property
    def input_paths(self):
        return list(self.get_all_input_file_names())

    @property
    def inject_stage1_dependency_task(self) -> None:
        return None

    def process(self):
        # Copy the file and its metadata (hence copy2) to the output directory
        for input_file in self.input_paths:
            source = Path(input_file)
            target = self.get_output_file_name(source.name)
            logger.info(f"Copying {source} -> {target}")
            shutil.copy2(source, target)

    def output(self):
        for input_file in self.input_paths:
            path = Path(input_file)
            yield self.add_to_output(path.name)

    def requires(self):
        dataprod_config = luigi.get_setting("dataprod_config")
        # If the prodtype is default i.e wasn't defined globally
        # we must call the default_prodtype requires function
        if self.prodtype == "default":
            datatypes_dict = flatten_to_dict(dataprod_config["datatype"])
            datatypes = list(datatypes_dict.keys())

            for datatype, card, edm4hep in product(
                datatypes,
                dataprod_config["card"],
                dataprod_config["edm4hep"],
            ):
                prodtype = datatypes_dict[datatype]["prodtype"]

                yield get_last_stage_task(
                    inject_stage1_dependency=self.inject_stage1_dependency_task,
                    prodtype=prodtype,
                )(
                    prodtype=get_mc_production_types()[prodtype],
                    datatype=datatype,
                    card_name=card,
                    edm4hep_name=edm4hep,
                )

        else:
            for datatype, card, edm4hep in product(
                dataprod_config["datatype"],
                dataprod_config["card"],
                dataprod_config["edm4hep"],
            ):

                yield get_last_stage_task(
                    inject_stage1_dependency=self.inject_stage1_dependency_task
                )(
                    prodtype=get_mc_production_types()[self.prodtype],
                    datatype=datatype,
                    card_name=card,
                    edm4hep_name=edm4hep,
                )


def _get_mc_prod_stages(prodtype=None) -> dict:
    """
    Returns
    --------
    `prod_dict` : dict[str, dict]
        Returned dictionary is that specific to the production type as per src/mc_production/production_types.yaml'
    """
    requested_prodtype = (
        prodtype or luigi.get_setting("dataprod_config")["global_prodtype"]
    )
    try:
        return get_config("production_types.yaml", "flare/src/mc_production")[
            requested_prodtype
        ]
    except KeyError:
        raise KeyError(requested_prodtype)


@lru_cache(typed=True)
def get_mc_prod_stages_dict(inject_stage1_dependency=None, prodtype=None) -> dict:
    """
    Get the ordered dictionary of MCProduction tasks.

    Parameters
    -----------
    `inject_stage1_dependency`: luigi.Task, default=None
        If the stage1 task of the MC Production needs to require another task, massing a Task to this parameter will set that dependency

    Returns
    --------
    `tasks` : dict[Any, luigi.Task]
        The returned ordered dictionary has keys as per the `stages` list passed to _class_generator_closure_function.
        The values are the associated luigi Tasks that are created as child classes of `MCProductionBaseTask`

    Note
    -----
    For the MC Production of FLARE, the following configuration is passed to `_class_generator_closure_function`:

    ```
    _linear_task_workflow_generator(
        stages=_get_mc_prod_stages(),
        class_name="MCProduction",
        base_class=MCProductionBaseTask,
        inject_stage1_dependency=inject_stage1_dependency
    )
    ```
    """
    last_stage = next(reversed(_get_mc_prod_stages(prodtype=prodtype)))
    class_name = "MCProduction"
    class_name += prodtype.capitalize() if prodtype else ""
    return _linear_task_workflow_generator(
        stages=_get_mc_prod_stages(prodtype=prodtype),
        class_name=class_name,
        base_class=MCProductionBaseTask,
        class_attrs={
            last_stage: {
                "card_name": luigi.Parameter(default="default"),
                "edm4hep_name": luigi.Parameter(default="default"),
            }
        },
        inject_stage1_dependency=inject_stage1_dependency,
    )


def get_last_stage_task(inject_stage1_dependency=None, prodtype=None):
    """
    Returns the last luigi Task inside `get_mc_prod_stages_dict`
    """
    return next(
        reversed(
            get_mc_prod_stages_dict(
                inject_stage1_dependency=inject_stage1_dependency, prodtype=prodtype
            ).values()
        )
    )

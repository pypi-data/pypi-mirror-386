from enum import Enum
from pathlib import Path
from warnings import warn

from .util import logger, get_iesopt_module_attr
from .julia.util import jl_symbol, recursive_convert_py2jl, jl_safe_seval
from .results import Results


class ModelStatus(Enum):
    """Status of an :py:class:`iesopt.Model`."""

    EMPTY = "empty"
    GENERATED = "generated"
    FAILED_GENERATE = "failed_generate"
    FAILED_OPTIMIZE = "failed_optimize"
    OPTIMAL = "optimal"
    OPTIMAL_LOCALLY = "local_optimum"
    INFEASIBLE = "infeasible"
    INFEASIBLE_OR_UNBOUNDED = "infeasible_unbounded"
    OTHER = "other"


class Model:
    """An IESopt model, based on an :jl:module:`IESopt.jl <IESopt.IESopt>` core model."""

    def __init__(self, filename: str | Path, **kwargs) -> None:
        self._filename = filename
        self._kwargs = recursive_convert_py2jl(kwargs)

        self._model = None
        self._verbosity = kwargs.get("verbosity", True)

        self._status = ModelStatus.EMPTY
        self._status_details = None

        self._results = None

        self._IESopt = get_iesopt_module_attr("IESopt")
        self._JuMP = get_iesopt_module_attr("JuMP")
        self._jump_value = get_iesopt_module_attr("jump_value")
        self._jump_dual = get_iesopt_module_attr("jump_dual")

        if "virtual_files" in self._kwargs:
            # Ensure proper type of this entry, since it is enforced by `IESopt.parse!`.
            _dict_typed = self._IESopt.seval("Dict{String, DataFrames.DataFrame}")
            self._kwargs["virtual_files"] = _dict_typed(self._kwargs["virtual_files"])

    def __repr__(self) -> str:
        if self._model is None:
            return "An IESopt model (not yet generated)"

        n_var = self._JuMP.num_variables(self.core)
        n_con = self._JuMP.num_constraints(self.core, count_variable_in_set_constraints=False)
        solver = self._JuMP.solver_name(self.core)
        termination_status = self._JuMP.termination_status(self.core)

        return (
            f"An IESopt model:"
            f"\n\tname: {self.data.input.config['general']['name']['model']}"
            f"\n\tsolver: {solver}"
            f"\n\t"
            f"\n\t{n_var} variables, {n_con} constraints"
            f"\n\tstatus: {termination_status}"
        )

    @property
    def core(self):
        """Access the core `JuMP` model that is used internally."""
        if self._model is None:
            raise Exception("Model was not properly set up; call `generate` first")
        return self._model

    @property
    def data(self):
        """Access the IESopt data object of the model.

        This is deprecated; use `model.internal` instead (similar to the Julia usage `IESopt.internal(model)`).
        """
        warn(
            "Using `model.data` is deprecated; use `model.internal` instead (similar to the Julia usage `IESopt.internal(model)`)",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.internal

    @property
    def internal(self):
        """Access the IESopt data object of the model."""
        return self._IESopt.internal(self.core)

    @property
    def status(self) -> ModelStatus:
        """Get the current status of this model. See `ModelStatus` for possible values."""
        return self._status

    @property
    def objective_value(self) -> float:
        """Get the objective value of the model. Only available if the model was solved beforehand."""
        if self._status == ModelStatus.OPTIMAL_LOCALLY:
            logger.warning("Model is only locally optimal; objective value may not be accurate")
        elif self._status != ModelStatus.OPTIMAL:
            raise Exception("Model is not optimal; no objective value available")
        return self._JuMP.objective_value(self.core)

    def generate(self) -> None:
        """Generate a IESopt model from the attached top-level YAML config."""
        try:
            self._model = self._IESopt.generate_b(str(self._filename), **self._kwargs)
            self._status = ModelStatus.GENERATED
        except Exception as e:
            self._status = ModelStatus.FAILED_GENERATE
            logger.error(f"Exception during `generate`: {e}")
            try:
                logger.error(f"Current debugging info: {self.data.debug}")
            except Exception as e:
                logger.error("Failed to extract debugging info")

    def write_to_file(self, filename=None, *, format: str = "automatic") -> str:
        """Write the model to a file.

        Consult the Julia version of this function, [IESopt.write_to_file](https://ait-energy.github.io/iesopt/pages/manual/julia/index.html#write-to-file)
        for more information. This will automatically invoke `generate` if the model has not been generated yet.

        Arguments:
            filename (Optional[str]): The filename to write to. If `None`, the path and name are automatically
                                      determined by IESopt.

        Keyword Arguments:
            format (str): The format to write the file in. If `automatic`, the format is determined based on the
                          extension of the filename. Otherwise, it used as input to [`JuMP.write_to_file`](https://jump.dev/JuMP.jl/stable/api/JuMP/#write_to_file),
                          by converting to uppercase and prefixing it with `MOI.FileFormats.FORMAT_`. Writing to, e.g.,
                          an LP file can be done by setting `format="lp"` or `format="LP"`.

        Returns:
            str: The filename (including path) of the written file.

        Examples:
            ..  code-block:: python
                :caption: Writing a model to a problem file.

                import iesopt

                cfg = iesopt.make_example("01_basic_single_node", dst_dir="opt")

                # Model will be automatically generated when calling `write_to_file`:
                model = iesopt.Model(cfg)
                model.write_to_file()

                # It also works with already optimized models:
                model = iesopt.run(cfg)
                model.write_to_file("opt/out/my_problem.LP")

                # And supports different formats:
                target = model.write_to_file("opt/out/my_problem.foo", format="mof")
                print(target)
        """
        if self._status == ModelStatus.EMPTY:
            self.generate()

        try:
            if filename is None:
                return self._IESopt.write_to_file(self.core)
            else:
                format = jl_safe_seval(f"JuMP.MOI.FileFormats.FORMAT_{format.upper()}")
                return self._IESopt.write_to_file(self.core, str(filename), format=format)
        except Exception as e:
            logger.error(f"Error while writing model to file: {e}")
            return ""

    def optimize(self) -> None:
        """Optimize the model."""
        try:
            self._IESopt.optimize_b(self.core)

            if self._JuMP.is_solved_and_feasible(self.core, allow_local=False):
                self._status = ModelStatus.OPTIMAL
                self._results = Results(model=self)
            elif self._JuMP.is_solved_and_feasible(self.core, allow_local=True):
                self._status = ModelStatus.OPTIMAL_LOCALLY
                self._results = Results(model=self)
            else:
                _term_status = self._JuMP.termination_status(self.core)
                if str(_term_status) == "INFEASIBLE":
                    self._status = ModelStatus.INFEASIBLE
                    logger.error(
                        "The model seems to be infeasible; refer to `model.compute_iis()` and its documentation if you want to know more about the source of the infeasibility."
                    )
                elif str(_term_status) == "INFEASIBLE_OR_UNBOUNDED":
                    self._status = ModelStatus.INFEASIBLE_OR_UNBOUNDED
                else:
                    self._status = ModelStatus.OTHER
                    self._status_details = _term_status
        except Exception as e:
            self._status = ModelStatus.FAILED_OPTIMIZE
            logger.error(f"Exception during `optimize`: {e}")
            try:
                logger.error(f"Current debugging info: {self.data.debug}")
            except Exception as e:
                logger.error("Failed to extract debugging info")

    def compute_iis(self, filename=None) -> None:
        """Compute and print the Irreducible Infeasible Set (IIS) of the model, or optionally write it to a file.

        Note that this requires a solver that supports IIS computation.

        Arguments:
            filename (Optional[str | Path]): The filename to write the IIS to. If `None`, the IIS is only printed to the
                                             console.

        Examples:
            ..  code-block:: python
                :caption: Computing the IIS of a model.

                import iesopt

                model = iesopt.run("infeasible_model.iesopt.yaml")
                model.compute_iis()

                # or (arbitrary filename/extension):
                model.compute_iis(filename="my_problem.txt")
        """
        try:
            if filename is None:
                self._IESopt.compute_IIS(self.core)
            else:
                self._IESopt.compute_IIS(self.core, filename=str(filename))
        except Exception as e:
            logger.error("Error while computing IIS: `%s`" % str(e.args[0]))

    @property
    def results(self) -> Results:
        """Get the results of the model."""
        if self._results is None:
            raise Exception("No results available; have you successfully called `optimize`?")
        return self._results

    def extract_result(self, component: str, field: str, mode: str = "value"):
        """Manually extract a specific result from the model."""
        try:
            c = self._IESopt.get_component(self.core, component)
        except Exception:
            raise Exception(f"Exception during `extract_result({component}, {field}, mode={mode})`")

        f = None
        for fieldtype in ["var", "exp", "con", "obj"]:
            try:
                t = getattr(c, fieldtype)
                f = getattr(t, field)
                break
            except Exception:
                pass

        if f is None:
            raise Exception(f"Field `{field}` not found in component `{component}`")

        try:
            if mode == "value":
                return self._jump_values(f)
            elif mode == "dual":
                return self._jump_duals(f)
            else:
                raise Exception(f"Mode `{mode}` not supported, use `value` or `dual`")
        except Exception:
            raise Exception(f"Error during extraction of result `{field}` from component `{component}`")

    def get_component(self, component: str):
        """Get a core component based on its full name."""
        try:
            return self._IESopt.get_component(self.core, component)
        except Exception:
            raise Exception(f"Error while retrieving component `{component}` from model")

    def get_components(self, tagged=None):
        """
        Get all components of the model, possibly filtered by (a) tag(s).

        Arguments:
            tagged (str or list of str): The tag(s) to filter the components by, can be `None` (default) to get all components.
        """
        if tagged is None:
            return self._IESopt.get_components(self.core)

        return self._IESopt.get_components(self.core, recursive_convert_py2jl(tagged))

    def get_variable(self, component: str, variable: str):
        """Get a specific variable from a core component."""
        raise DeprecationWarning(
            f"`get_variable(...)` is deprecated; you can instead access the variable directly using "
            f"`model.get_component('{component}').var.{variable}`. Conversion to Python lists, if not done "
            f"automatically, can be done using `list(...)`."
        )

    def get_constraint(self, component: str, constraint: str):
        """Get a specific constraint from a core component."""
        raise DeprecationWarning(
            f"`get_constraint(...)` is deprecated; you can instead access the constraint directly using "
            f"`model.get_component('{component}').con.{constraint}`. Conversion to Python lists, if not done "
            f"automatically, can be done using `list(...)`."
        )

    def nvar(self, var: str):
        """Extract a named variable, from `model`.

        If your variable is called `:myvar`, and you would access it in Julia using `model[:myvar]`, you can call
        `model.nvar("myvar")`.
        """
        try:
            return self.core[jl_symbol(var)]
        except Exception:
            raise Exception(f"Error while retrieving variable `{var}` from model")

    @staticmethod
    def _to_pylist(obj):
        # if isinstance(obj, jl.VectorValue):
        #    return jl.PythonCall.pylist(obj)
        return obj

from turtle import down
from click import Option
from matplotlib.pyplot import cla
from pydantic import BaseModel
from typing import Optional, Union, Dict, List
from typing import Type
import logging
import traceback
import os
import yaml

from gfa_ml.lib.default import (
    D_MODEL,
    DIM_FEEDFORWARD,
    HIDDEN_NEURONS,
    N_FEATURES_IMPORTANCE,
    NHEAD,
    NUM_LAYERS,
    USE_MARKERS,
)
from gfa_ml.lib.utils import load_yaml
from .data_type import (
    ParamUnit,
    MetricType,
    ModelType,
    ParameterType,
    OptimizationObjective,
    SmoothingFunctionType,
    SmoothingType,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
from gfa_ml.lib.default import (
    HIDDEN_NEURONS,
    ACTIVATION_FUNCTION,
    DROP_RATE,
    OPTIMIZER,
    LOSS,
    LEARNING_RATE,
    D_MODEL,
    NHEAD,
    NUM_LAYERS,
    DIM_FEEDFORWARD,
    EPOCHS,
    BATCH_SIZE,
    PATIENCE,
    TEST_RATE,
    TRAIN_RATE,
    VALIDATION_RATE,
    SMOOTH_WINDOW_SIZE,
    SAMPLE_SIZE,
    HISTORY_SIZE,
    N_FEATURES_IMPORTANCE,
    USE_MARKERS,
    DATA_INTERVAL_MINUTES,
)


class SmoothingParam(BaseModel):
    param_name: Optional[str] = None
    description: Optional[str] = None
    smoothing_function_type: Optional[SmoothingFunctionType] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Union[str, int]]) -> "SmoothingParam":
        try:
            smoothing_function_type = SmoothingFunctionType(
                data.get("smoothing_function_type", None)
            )
            if smoothing_function_type in (
                SmoothingFunctionType.EXPONENTIAL,
                SmoothingFunctionType.GAUSSIAN,
            ):
                logging.warning(
                    f"Smoothing function type {smoothing_function_type} is not yet implemented. Returning base SmoothingParam."
                )
                return cls(
                    param_name=data.get("param_name", None),
                    description=data.get("description", None),
                    smoothing_function_type=smoothing_function_type,
                )
            # TODO: Implement other smoothing function types
            else:
                if smoothing_function_type != SmoothingFunctionType.MOVING_AVERAGE:
                    logging.warning(
                        f"The function type is not specified, using the default MovingAverageSmoothingParam."
                    )
                return MovingAverageSmoothingParam.from_dict(data)

        except Exception as e:
            logging.error(f"Error in SmoothingParam.from_dict: {e}")
            logging.debug(traceback.format_exc())
            return None


class MovingAverageSmoothingParam(SmoothingParam, BaseModel):
    window_size: Optional[int] = None
    min_periods: Optional[int] = None
    smoothing_type: Optional[SmoothingType] = None  # e.g., "mean", "median", etc.

    def to_string(self) -> str:
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self) -> str:
        return self.to_string()

    def to_dict(self) -> Dict[str, Union[str, int]]:
        return {
            "param_name": self.param_name,
            "description": self.description,
            "window_size": self.window_size,
            "min_periods": self.min_periods,
            "smoothing_type": self.smoothing_type.value,
            "smoothing_function_type": self.smoothing_function_type.value,
        }

    @classmethod
    def from_dict(
        cls: Type["MovingAverageSmoothingParam"], data: Dict[str, Union[str, int]]
    ) -> "MovingAverageSmoothingParam":
        try:
            smoothing_type = SmoothingType(data.get("smoothing_type", "mean"))
            return cls(
                param_name=data.get("param_name", None),
                description=data.get("description", None),
                window_size=data.get("window_size", 0),
                min_periods=data.get("min_periods", 0),
                smoothing_type=smoothing_type,
                smoothing_function_type=data.get("smoothing_function_type", None),
            )
        except Exception as e:
            logging.error(f"Error in MovingAverageSmoothingParam.from_dict: {e}")
            logging.debug(traceback.format_exc())
            return None


class SmoothFunction(BaseModel):
    function_name: str
    description: Optional[str] = None
    smoothing_param: Union[SmoothingParam, MovingAverageSmoothingParam] = None

    def to_string(self) -> str:
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self) -> str:
        return self.to_string()

    def to_dict(self) -> Dict[str, Union[str, SmoothingParam]]:
        try:
            return {
                "function_name": self.function_name,
                "description": self.description,
                "smoothing_param": self.smoothing_param.to_dict()
                if self.smoothing_param
                else None,
            }
        except Exception as e:
            logging.error(f"Error in SmoothFunction.to_dict: {e}")
            logging.info(traceback.format_exc())
            return {}

    @classmethod
    def from_dict(
        cls: Type["SmoothFunction"], data: Dict[str, Union[str, SmoothingParam]]
    ) -> "SmoothFunction":
        try:
            smoothing_param = data.get("smoothing_param")
            function_name = data.get("function_name", "")
            if isinstance(smoothing_param, dict):
                if function_name == "moving_average":
                    smoothing_param = MovingAverageSmoothingParam.from_dict(
                        smoothing_param
                    )
                else:
                    smoothing_param = SmoothingParam(**smoothing_param)
            return cls(
                function_name=data.get("function_name", ""),
                description=data.get("description", None),
                smoothing_param=smoothing_param,
            )
        except Exception as e:
            logging.error(f"Error in SmoothFunction.from_dict: {e}")
            logging.debug(traceback.format_exc())
            return None


class Metric(BaseModel):
    metric_name: Optional[str] = None
    column_name: Optional[str] = None
    en_description: Optional[str] = None
    fi_description: Optional[str] = None
    unit: Optional[Union[str, ParamUnit]] = None
    stage: Optional[str] = None
    tag: Optional[str] = None
    measurement_method: Optional[str] = None
    sort: Optional[int] = None
    display_name: Optional[str] = None
    metric_type: Optional[Union[str, MetricType]] = None
    smoothing_function: Optional[SmoothFunction] = None

    def to_string(self) -> str:
        return yaml.dump(self.to_dict(), sort_keys=False)
        # metric_type_str = (
        #     self.metric_type.value
        #     if isinstance(self.metric_type, MetricType)
        #     else self.metric_type
        # )
        # unit_str = self.unit.value if isinstance(self.unit, ParamUnit) else self.unit
        # return f"Metric:\n metric_name={self.metric_name},\n column_name={self.column_name},\n unit={unit_str}, \n stage={self.stage},\n tag={self.tag},\n measurement_method={self.measurement_method},\n sort={self.sort}, \n en_description={self.en_description},\n fi_description={self.fi_description},\n display_name={self.display_name},\n metric_type={metric_type_str}, \n smoothing_function={self.smoothing_function}"

    def __str__(self) -> str:
        return self.to_string()

    @classmethod
    def from_dict(cls: Type["Metric"], data: Dict[str, Union[str, int]]) -> "Metric":
        try:
            if data.get("metric_type") is not None:
                try:
                    data["metric_type"] = MetricType(data["metric_type"])
                except ValueError:
                    data["metric_type"] = MetricType.UNKNOWN
            if data.get("unit") is not None:
                try:
                    data["unit"] = ParamUnit(data["unit"])
                except ValueError:
                    data["unit"] = ParamUnit.UNKNOWN
            if data.get("smoothing_function") is not None:
                data["smoothing_function"] = SmoothFunction.from_dict(
                    data["smoothing_function"]
                )
            else:
                data["smoothing_function"] = None
            return cls(
                metric_name=data.get("metric_name"),
                column_name=data.get("column_name"),
                en_description=data.get("en_description"),
                fi_description=data.get("fi_description"),
                unit=data.get("unit"),
                stage=data.get("stage"),
                tag=data.get("tag"),
                measurement_method=data.get("measurement_method"),
                sort=data.get("sort"),
                display_name=data.get("display_name"),
                metric_type=data.get("metric_type", None),
                smoothing_function=data.get("smoothing_function", None),
            )
        except Exception as e:
            logging.error(f"Error in Metric.from_dict: {e}")
            logging.info(traceback.format_exc())
            return None

    def to_dict(self) -> Dict[str, Union[str, int]]:
        if isinstance(self.unit, ParamUnit):
            unit_value = self.unit.value
        else:
            unit_value = self.unit
        if isinstance(self.metric_type, MetricType):
            metric_type_value = self.metric_type.value
        else:
            metric_type_value = self.metric_type
        if self.smoothing_function:
            smoothing_function_value = self.smoothing_function.to_dict()
        else:
            smoothing_function_value = None
        return {
            "metric_name": self.metric_name,
            "column_name": self.column_name,
            "en_description": self.en_description,
            "fi_description": self.fi_description,
            "unit": unit_value,
            "stage": self.stage,
            "tag": self.tag,
            "measurement_method": self.measurement_method,
            "sort": self.sort,
            "display_name": self.display_name,
            "metric_type": metric_type_value,
            "smoothing_function": smoothing_function_value,
        }


class StageInfo(BaseModel):
    stage_name: str
    input_parameters: Dict[str, Metric]
    quality_indicators: Dict[str, Metric]
    control_parameters: Dict[str, Metric]

    def to_string(self) -> str:
        return f"StageInfo:\n stage_name={self.stage_name},\n input_parameters={self.input_parameters},\n quality_indicators={self.quality_indicators},\n control_parameters={self.control_parameters}"

    def __str__(self) -> str:
        return self.to_string()

    @classmethod
    def from_dict(
        cls: Type["StageInfo"], data: Dict[str, Union[str, Dict]]
    ) -> "StageInfo":
        try:
            input_parameters = {
                k: Metric(**v) for k, v in data.get("input_parameters", {}).items()
            }
            quality_indicators = {
                k: Metric(**v) for k, v in data.get("quality_indicators", {}).items()
            }
            control_parameters = {
                k: Metric(**v) for k, v in data.get("control_parameters", {}).items()
            }
            return cls(
                stage_name=data["stage_name"],
                input_parameters=input_parameters,
                quality_indicators=quality_indicators,
                control_parameters=control_parameters,
            )
        except Exception as e:
            logging.error(f"Error in StageInfo.from_dict: {e}")
            logging.debug(traceback.format_exc())
            return None


class MultiStageInfo(BaseModel):
    stages: Dict[str, StageInfo]

    def to_string(self) -> str:
        return f"MultiStageInfo:\n stages={self.stages}"

    def __str__(self) -> str:
        return self.to_string()

    @classmethod
    def from_dict(
        cls: Type["MultiStageInfo"], data: Dict[str, Union[str, Dict]]
    ) -> "MultiStageInfo":
        try:
            stages = {
                k: StageInfo.from_dict(v) for k, v in data.get("stages", {}).items()
            }
            return cls(stages=stages)
        except Exception as e:
            logging.error(f"Error in MultiStageInfo.from_dict: {e}")
            logging.debug(traceback.format_exc())
            return None

    def get_stage(self, stage_name: str) -> Optional[StageInfo]:
        return self.stages.get(stage_name)


class MetricReport(BaseModel):
    metric_name: str
    total_count: int
    missing_count: int
    missing_rate: float
    zero_count: Optional[int] = None
    zero_rate: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    value_range: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    standard_deviation: Optional[float] = None
    variance: Optional[float] = None
    quantile_25th: Optional[float] = None
    quantile_75th: Optional[float] = None
    interquartile_range: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    positive_count: Optional[int] = None
    negative_count: Optional[int] = None
    positive_rate: Optional[float] = None
    negative_rate: Optional[float] = None
    mean_measurement_interval: Optional[float] = None
    min_measurement_interval: Optional[float] = None
    max_measurement_interval: Optional[float] = None

    def to_string(self) -> str:
        return (
            f"MetricReport:\n"
            f" metric_name={self.metric_name},\n"
            f" total_count={self.total_count},\n"
            f" missing_count={self.missing_count},\n"
            f" missing_rate={self.missing_rate},\n"
            f" zero_count={self.zero_count},\n"
            f" zero_rate={self.zero_rate},\n"
            f" min_value={self.min_value},\n"
            f" max_value={self.max_value},\n"
            f" value_range={self.value_range},\n"
            f" mean_value={self.mean_value},\n"
            f" median_value={self.median_value},\n"
            f" standard_deviation={self.standard_deviation},\n"
            f" variance={self.variance},\n"
            f" quantile_25th={self.quantile_25th},\n"
            f" quantile_75th={self.quantile_75th},\n"
            f" interquartile_range={self.interquartile_range},\n"
            f" skewness={self.skewness},\n"
            f" kurtosis={self.kurtosis},\n"
            f" positive_count={self.positive_count},\n"
            f" negative_count={self.negative_count},\n"
            f" positive_rate={self.positive_rate},\n"
            f" negative_rate={self.negative_rate},\n"
            f" mean_measurement_interval={self.mean_measurement_interval},\n"
            f" min_measurement_interval={self.min_measurement_interval},\n"
            f" max_measurement_interval={self.max_measurement_interval}"
        )

    def __str__(self) -> str:
        return self.to_string()

    @classmethod
    def from_dict(
        cls: Type["MetricReport"], data: Dict[str, Union[str, int, float]]
    ) -> "MetricReport":
        try:
            return cls(
                metric_name=data.get("metric_name", ""),
                total_count=data.get("total_count", 0),
                missing_count=data.get("missing_count", 0),
                missing_rate=data.get("missing_rate", 0.0),
                zero_count=data.get("zero_count", None),
                zero_rate=data.get("zero_rate", None),
                min_value=data.get("min_value", None),
                max_value=data.get("max_value", None),
                value_range=data.get("value_range", None),
                mean_value=data.get("mean_value", None),
                median_value=data.get("median_value", None),
                standard_deviation=data.get("standard_deviation", None),
                variance=data.get("variance", None),
                quantile_25th=data.get("quantile_25th", None),
                quantile_75th=data.get("quantile_75th", None),
                interquartile_range=data.get("interquartile_range", None),
                skewness=data.get("skewness", None),
                kurtosis=data.get("kurtosis", None),
                positive_count=data.get("positive_count", None),
                negative_count=data.get("negative_count", None),
                positive_rate=data.get("positive_rate", None),
                negative_rate=data.get("negative_rate", None),
                mean_measurement_interval=data.get("mean_measurement_interval", None),
                min_measurement_interval=data.get("min_measurement_interval", None),
                max_measurement_interval=data.get("max_measurement_interval", None),
            )
        except Exception as e:
            logging.error(f"Error in MetricReport.from_dict: {e}")
            logging.debug(traceback.format_exc())
            return None

    def to_dict(self) -> Dict[str, Union[str, int, float]]:
        return {
            "metric_name": self.metric_name,
            "total_count": self.total_count,
            "missing_count": self.missing_count,
            "missing_rate": self.missing_rate,
            "zero_count": self.zero_count,
            "zero_rate": self.zero_rate,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "value_range": self.value_range,
            "mean_value": self.mean_value,
            "median_value": self.median_value,
            "standard_deviation": self.standard_deviation,
            "variance": self.variance,
            "quantile_25th": self.quantile_25th,
            "quantile_75th": self.quantile_75th,
            "interquartile_range": self.interquartile_range,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "positive_rate": self.positive_rate,
            "negative_rate": self.negative_rate,
            "mean_measurement_interval": self.mean_measurement_interval,
            "min_measurement_interval": self.min_measurement_interval,
            "max_measurement_interval": self.max_measurement_interval,
        }

    def save_to_yaml(self, file_path: str):
        try:
            save_dir = os.path.dirname(file_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            with open(file_path, "w") as file:
                yaml.dump(self.to_dict(), file, sort_keys=False)
            logging.info(f"MetricReport saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving MetricReport to YAML: {e}")
            logging.debug(traceback.format_exc())


class InputParameter(BaseModel):
    parameter_name: str
    parameter_type: ParameterType

    @classmethod
    def from_dict(cls, data: dict):
        try:
            parameter_type = ParameterType(data["parameter_type"])
            if parameter_type == ParameterType.CONTROL_PARAMETER:
                return ControlParameter(**data)
            elif parameter_type == ParameterType.MEASUREMENT_PARAMETER:
                return MeasurementParameter(**data)
            else:
                raise ValueError(f"Unknown parameter type: {data['parameter_type']}")
        except Exception as e:
            logging.error(f"Error creating InputParameter from dict: {e}")
            logging.info(traceback.format_exc())
            return None

    def to_dict(self):
        return {
            "parameter_name": self.parameter_name,
            "parameter_type": self.parameter_type.value,
        }

    def to_string(self):
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self):
        return self.to_string()


class ControlParameter(InputParameter):
    parameter_type: ParameterType = ParameterType.CONTROL_PARAMETER
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    up_percentage: Optional[float] = None
    down_percentage: Optional[float] = None
    step_size: Optional[float] = 1.0
    current_value: Optional[float] = None
    trial_value: Optional[float] = None
    cost_function: Optional[str] = None

    def to_dict(self):
        return {
            "parameter_name": self.parameter_name,
            "parameter_type": self.parameter_type.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "up_percentage": self.up_percentage,
            "down_percentage": self.down_percentage,
            "step_size": self.step_size,
            "current_value": self.current_value,
            "trial_value": self.trial_value,
            "cost_function": self.cost_function,
        }

    def to_string(self):
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self):
        return self.to_string()

    def set_current_value(self, input_df):
        if self.parameter_name in input_df.columns:
            self.current_value = input_df[self.parameter_name].iloc[-1]
        else:
            logging.warning(
                f"Parameter {self.parameter_name} not found in input DataFrame columns."
            )

    def get_suggestion_range(self, n_digit: int = 1):
        if self.min_value is not None and self.max_value is not None:
            return self.min_value, self.max_value
        elif self.current_value is not None:
            low = (
                self.current_value * (1 - self.down_percentage / 100)
                if self.down_percentage is not None
                else self.current_value - 10
            )
            high = (
                self.current_value * (1 + self.up_percentage / 100)
                if self.up_percentage is not None
                else self.current_value + 10
            )
            return round(low, n_digit), round(high, n_digit)
        else:
            raise ValueError(
                f"Cannot determine suggestion range for parameter {self.parameter_name}."
            )


class MeasurementParameter(InputParameter):
    parameter_type: ParameterType = ParameterType.MEASUREMENT_PARAMETER
    column_name: str

    def to_dict(self):
        return {
            "parameter_name": self.parameter_name,
            "parameter_type": self.parameter_type.value,
            "column_name": self.column_name,
        }

    def to_string(self):
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self):
        return self.to_string()


class OutputQuality(BaseModel):
    parameter_name: str
    upper_limit: Optional[float] = None
    lower_limit: Optional[float] = None
    objective: Optional[OptimizationObjective] = None

    @classmethod
    def from_dict(cls, data: dict):
        try:
            parameter_name = data["parameter_name"]
            upper_limit = data.get("upper_limit", None)
            lower_limit = data.get("lower_limit", None)
            if data.get("objective") is None:
                objective = OptimizationObjective.NONE
            else:
                objective = OptimizationObjective(data["objective"])
            return cls(
                parameter_name=parameter_name,
                upper_limit=upper_limit,
                lower_limit=lower_limit,
                objective=objective,
            )
        except Exception as e:
            logging.error(f"Error creating OutputQuality from dict: {e} with {data}")
            logging.info(traceback.format_exc())
            return None

    def to_dict(self):
        return {
            "parameter_name": self.parameter_name,
            "upper_limit": self.upper_limit,
            "lower_limit": self.lower_limit,
            "objective": self.objective.value,
        }

    def to_string(self):
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self):
        return self.to_string()


class OutputConstraint(BaseModel):
    constraint: dict[str, OutputQuality]

    @classmethod
    def from_dict(cls, data: dict):
        try:
            constraint = {}
            for k, v in data.items():
                output_quality = OutputQuality.from_dict(v)
                if output_quality:
                    constraint[k] = output_quality
            return cls(constraint=constraint)
        except Exception as e:
            logging.error(f"Error creating OutputConstraint from dict: {e}")
            logging.info(traceback.format_exc())
            return None

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.constraint.items()}

    def to_string(self):
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self):
        return self.to_string()


class TransformerConfig(BaseModel):
    model_type: ModelType = ModelType.TRANSFORMER
    d_model: int = D_MODEL
    nhead: int = NHEAD
    num_layers: int = NUM_LAYERS
    dim_feedforward: int = DIM_FEEDFORWARD
    drop_rate: float = DROP_RATE
    activation_function: str = ACTIVATION_FUNCTION
    optimizer: str = OPTIMIZER
    loss: str = LOSS
    learning_rate: float = LEARNING_RATE

    @classmethod
    def from_dict(cls, config_dict: dict) -> "TransformerConfig":
        return cls(**config_dict)

    def to_dict(self) -> dict:
        return {
            "d_model": self.d_model,
            "nhead": self.nhead,
            "num_layers": self.num_layers,
            "dim_feedforward": self.dim_feedforward,
            "drop_rate": self.drop_rate,
            "activation_function": self.activation_function,
            "optimizer": self.optimizer,
            "loss": self.loss,
            "learning_rate": self.learning_rate,
            "model_type": self.model_type.value,
        }

    def to_string(self) -> str:
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self):
        return self.to_string()


class LSTMConfig(BaseModel):
    model_type: ModelType = ModelType.LSTM
    hidden_neurons: int = HIDDEN_NEURONS
    num_layers: int = NUM_LAYERS
    drop_rate: float = DROP_RATE
    activation_function: str = ACTIVATION_FUNCTION
    optimizer: str = OPTIMIZER
    loss: str = LOSS
    learning_rate: float = LEARNING_RATE

    @classmethod
    def from_dict(cls, config_dict: dict) -> "LSTMConfig":
        return cls(**config_dict)

    def to_dict(self) -> dict:
        return {
            "hidden_neurons": self.hidden_neurons,
            "num_layers": self.num_layers,
            "drop_rate": self.drop_rate,
            "activation_function": self.activation_function,
            "optimizer": self.optimizer,
            "loss": self.loss,
            "learning_rate": self.learning_rate,
            "model_type": self.model_type.value,
        }

    def to_string(self) -> str:
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self):
        return self.to_string()


class InputColumns(BaseModel):
    columns: Optional[List[str]] = None
    retention: Optional[Union[str, int, float]] = None

    @classmethod
    def from_dict(
        cls: Type["InputColumns"], data: Dict[str, Union[str, int, float, List[str]]]
    ) -> "InputColumns":
        return cls(
            columns=data.get("columns", None),
            retention=data.get("retention", None),
        )

    def to_dict(self):
        return {
            "columns": self.columns,
            "retention": self.retention,
        }

    def to_string(self) -> str:
        return yaml.dump(self.to_dict(), sort_keys=False)


class DataConfig(BaseModel):
    train_ratio: Optional[float] = TRAIN_RATE
    validation_ratio: Optional[float] = VALIDATION_RATE
    test_ratio: Optional[float] = TEST_RATE
    history_size: Optional[int] = HISTORY_SIZE
    input_cols: Optional[List[Union[str, InputColumns]]] = None
    control_cols: Optional[list] = None
    output_col: Optional[str] = None
    index_col: Optional[str] = None
    retention_col: Optional[str] = None
    retention_padding: Optional[int] = 0
    interval_minutes: Optional[int] = DATA_INTERVAL_MINUTES
    num_rows: Optional[int] = None
    min_rows: Optional[int] = None

    @classmethod
    def from_dict(
        cls: Type["DataConfig"], data: Dict[str, Union[str, float, int]]
    ) -> "DataConfig":
        input_cols_data = data.get("input_cols", None)
        if input_cols_data is not None:
            if isinstance(input_cols_data, list):
                input_cols = []
                for item in input_cols_data:
                    if isinstance(item, dict):
                        input_col_obj = InputColumns.from_dict(item)
                        input_cols.append(input_col_obj)
                    elif isinstance(item, str):
                        input_cols.append(item)
                data["input_cols"] = input_cols
            elif isinstance(input_cols_data, dict):
                data["input_cols"] = [InputColumns.from_dict(input_cols_data)]
        return cls(
            train_ratio=data.get("train_ratio", TRAIN_RATE),
            validation_ratio=data.get("validation_ratio", VALIDATION_RATE),
            test_ratio=data.get("test_ratio", TEST_RATE),
            history_size=data.get("history_size", HISTORY_SIZE),
            input_cols=data.get("input_cols", None),
            control_cols=data.get("control_cols", None),
            output_col=data.get("output_col", None),
            index_col=data.get("index_col", None),
            retention_col=data.get("retention_col", None),
            retention_padding=data.get("retention_padding", 0),
            interval_minutes=data.get("interval_minutes", DATA_INTERVAL_MINUTES),
            num_rows=data.get("num_rows", None),
            min_rows=data.get("min_rows", None),
        )

    def to_dict(self):
        input_cols_list = []
        if self.input_cols is not None:
            for col in self.input_cols:
                if isinstance(col, InputColumns):
                    input_cols_list.append(col.to_dict())
                else:
                    input_cols_list.append(col)
        else:
            input_cols_list = None
        return {
            "train_ratio": self.train_ratio,
            "validation_ratio": self.validation_ratio,
            "test_ratio": self.test_ratio,
            "history_size": self.history_size,
            "input_cols": input_cols_list,
            "control_cols": self.control_cols,
            "output_col": self.output_col,
            "index_col": self.index_col,
            "retention_col": self.retention_col,
            "retention_padding": self.retention_padding,
            "interval_minutes": self.interval_minutes,
            "num_rows": self.num_rows,
            "min_rows": self.min_rows,
        }

    def to_string(self) -> str:
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self) -> str:
        return self.to_string()


class TrainingConfig(BaseModel):
    epochs: Optional[int] = EPOCHS
    batch_size: Optional[int] = BATCH_SIZE
    patience: Optional[int] = PATIENCE
    sample_size: Optional[int] = SAMPLE_SIZE
    n_features_importance: Optional[int] = N_FEATURES_IMPORTANCE
    use_markers: Optional[bool] = USE_MARKERS
    smooth_window_size: Optional[int] = SMOOTH_WINDOW_SIZE
    plot: bool = True

    def to_string(self) -> str:
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self) -> str:
        return self.to_string()

    @classmethod
    def from_dict(
        cls: Type["TrainingConfig"], data: Dict[str, Union[str, float, int]]
    ) -> "TrainingConfig":
        return cls(
            epochs=data.get("epochs", EPOCHS),
            batch_size=data.get("batch_size", BATCH_SIZE),
            patience=data.get("patience", PATIENCE),
            sample_size=data.get("sample_size", SAMPLE_SIZE),
            n_features_importance=data.get(
                "n_features_importance", N_FEATURES_IMPORTANCE
            ),
            use_markers=data.get("use_markers", USE_MARKERS),
            smooth_window_size=data.get("smooth_window_size", SMOOTH_WINDOW_SIZE),
            plot=data.get("plot", True),
        )

    def to_dict(self):
        return {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "patience": self.patience,
            "sample_size": self.sample_size,
            "n_features_importance": self.n_features_importance,
            "use_markers": self.use_markers,
            "smooth_window_size": self.smooth_window_size,
            "plot": self.plot,
        }


class RunConfig(BaseModel):
    data_config: Optional[DataConfig] = None
    training_config: Optional[TrainingConfig] = None
    ml_model_config: Optional[Union[TransformerConfig, LSTMConfig]] = None

    def to_string(self) -> str:
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self) -> str:
        return self.to_string()

    def to_dict(self) -> Dict[str, Dict]:
        return {
            "data_config": self.data_config.to_dict() if self.data_config else {},
            "training_config": self.training_config.to_dict()
            if self.training_config
            else {},
            "ml_model_config": self.ml_model_config.to_dict()
            if self.ml_model_config
            else {},
        }

    @classmethod
    def from_dict(cls: Type["RunConfig"], data: Dict[str, Dict]) -> "RunConfig":
        try:
            data_config = DataConfig.from_dict(data.get("data_config", {}))
            training_config = TrainingConfig.from_dict(data.get("training_config", {}))
            ml_model_data = data.get("ml_model_config", {})
            ml_model_type = ml_model_data.get("model_type", "transformer").lower()
            if ml_model_type == "transformer":
                ml_model_config = TransformerConfig.from_dict(ml_model_data)
            elif ml_model_type == "lstm":
                ml_model_config = LSTMConfig.from_dict(ml_model_data)
            else:
                logging.warning(
                    f"Unknown model type: {ml_model_type}. Defaulting to TransformerConfig."
                )
                ml_model_config = TransformerConfig.from_dict(ml_model_data)
            return cls(
                data_config=data_config,
                training_config=training_config,
                ml_model_config=ml_model_config,
            )
        except Exception as e:
            logging.error(f"Error in RunConfig.from_dict: {e}")
            logging.info(traceback.format_exc())
            return None

    @classmethod
    def from_yaml(cls: Type["RunConfig"], file_path: str) -> "RunConfig":
        try:
            with open(file_path) as file:
                data = yaml.safe_load(file)
            return cls.from_dict(data)
        except Exception as e:
            logging.error(f"Error loading RunConfig from YAML: {e}")
            logging.info(traceback.format_exc())
            return None


class InputSpecification(BaseModel):
    specification: dict[str, InputParameter]

    @classmethod
    def from_dict(cls, data: dict):
        try:
            spec = {k: InputParameter.from_dict(v) for k, v in data.items()}
            return cls(specification=spec)
        except Exception as e:
            logging.error(f"Error creating InputSpecification from dict: {e}")
            logging.info(traceback.format_exc())
            return None

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.specification.items()}

    def to_string(self):
        return yaml.dump(self.to_dict(), sort_keys=False)

    def __str__(self):
        return self.to_string()


class DataSpecification(BaseModel):
    model_path: Optional[str] = None
    input_specification: Optional[InputSpecification] = None
    output_constraint: Optional[OutputQuality] = None
    data_config: Optional[DataConfig] = None

    @classmethod
    def from_dict(cls: Type["DataSpecification"], data: Dict) -> "DataSpecification":
        try:
            input_spec_data = data.get("input_specification", {})
            output_constraint_data = data.get("output_constraint", {})
            data_config_data = data.get("data_config", {})
            input_specification = InputSpecification.from_dict(input_spec_data)
            output_constraint = OutputQuality.from_dict(output_constraint_data)
            data_config = DataConfig.from_dict(data_config_data)
            return cls(
                model_path=data.get("model_path", None),
                input_specification=input_specification,
                output_constraint=output_constraint,
                data_config=data_config,
            )
        except Exception as e:
            logging.error(f"Error in DataSpecification.from_dict: {e}")
            logging.info(traceback.format_exc())
            return None

    def to_dict(self) -> Dict:
        return {
            "model_path": self.model_path,
            "input_specification": self.input_specification.to_dict()
            if self.input_specification
            else None,
            "output_constraint": self.output_constraint.to_dict()
            if self.output_constraint
            else None,
            "data_config": self.data_config.to_dict() if self.data_config else None,
        }

    def __str__(self):
        return yaml.dump(self.to_dict(), sort_keys=False)

    def to_string(self) -> str:
        return self.__str__()


class ProcessesOptimizationSpecification(BaseModel):
    optimization_objectives: Optional[OutputQuality] = None
    data_specifications: Dict[str, DataSpecification] = None

    @classmethod
    def from_dict(
        cls: Type["ProcessesOptimizationSpecification"], data: Dict
    ) -> "ProcessesOptimizationSpecification":
        try:
            optimization_objectives_data = data.get("optimization_objectives", {})
            data_specification_data = data.get("data_specification", {})
            optimization_objectives = OutputQuality.from_dict(
                optimization_objectives_data
            )
            data_specifications = {
                k: DataSpecification.from_dict(v)
                for k, v in data_specification_data.items()
            }
            return cls(
                optimization_objectives=optimization_objectives,
                data_specifications=data_specifications,
            )
        except Exception as e:
            logging.error(f"Error in ProcessesOptimizationSpecification.from_dict: {e}")
            logging.info(traceback.format_exc())
            return None

    def to_dict(self) -> Dict:
        return {
            "optimization_objectives": self.optimization_objectives.to_dict()
            if self.optimization_objectives
            else None,
            "data_specifications": {
                k: v.to_dict() for k, v in self.data_specifications.items()
            }
            if self.data_specifications
            else None,
        }

    def __str__(self):
        return yaml.dump(self.to_dict(), sort_keys=False)

    def to_string(self) -> str:
        return self.__str__()

    @classmethod
    def from_yaml(
        cls: Type["ProcessesOptimizationSpecification"], file_path: str
    ) -> "ProcessesOptimizationSpecification":
        try:
            data = load_yaml(file_path)
            return cls.from_dict(data)
        except Exception as e:
            logging.error(
                f"Error loading ProcessesOptimizationSpecification from YAML: {e}"
            )
            logging.info(traceback.format_exc())
            return None

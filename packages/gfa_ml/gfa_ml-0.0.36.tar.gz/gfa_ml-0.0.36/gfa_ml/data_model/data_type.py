from enum import Enum


class TimeUnit(Enum):
    SECONDS = "second"
    MINUTES = "minute"
    HOURS = "hour"


class ParamUnit(Enum):
    PERCENTAGE = "%"
    PH = "pH"
    TEMPERATURE = "C"
    CONDUCTIVITY = "mS/m"
    WASH_LOSS = "KG/T"
    ADT_PER_D = "ADt/d"
    LITERS_PER_SECOND = "l/s"
    GRAM_PER_LITER = "g/l"
    KAPPA = "."
    KG_PER_ADT = "kg/ADt"
    KG_PER_SECOND = "kg/s"
    MG_PER_L = "MG/L"
    UNKNOWN = "?"
    DM3_PER_KG = "DM3/KG"


class TimeNormalizationType(Enum):
    ZERO_BASE_NORM = "zero_base_norm"
    Z_SCORE_NORM = "z_score_norm"


class MetricType(Enum):
    INPUT_PARAMETER = "input_parameter"
    QUALITY_INDICATOR = "quality_indicator"
    CONTROL_PARAMETER = "control_parameter"
    UNKNOWN = "unknown"


class ChartType(Enum):
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    PIE = "pie"
    HEATMAP = "heatmap"
    BOX_PLOT = "box_plot"
    AREA = "area"
    UNKNOWN = "unknown"


class ModelType(Enum):
    LSTM = "lstm"
    GRU = "gru"
    TRANSFORMER = "transformer"


class ParameterType(Enum):
    CONTROL_PARAMETER = "control_parameter"
    MEASUREMENT_PARAMETER = "measurement_parameter"


class OptimizationObjective(Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"
    NONE = None


class OptunaSampler(Enum):
    TPE = "tpe"
    CMAES = "cmaes"
    QMCSampler = "qmcsampler"
    GRID = "grid"
    RANDOM = "random"
    NSGAII = "nsga2"
    BRUTE_FORCE = "brute_force"
    BOTORCH = "botorch"
    GP = "gp"


class SmoothingFunctionType(Enum):
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL = "exponential"
    GAUSSIAN = "gaussian"
    UNKNOWN = ""


class SmoothingType(Enum):
    MAX = "max"
    MIN = "min"
    MEAN = "mean"
    MEDIAN = "median"

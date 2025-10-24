#pragma once
#include <limits>

const double NAN_DOUBLE{std::numeric_limits<double>::quiet_NaN()};
const int MAX_ABS_EXPONENT_TO_APPLY_ON_LINEAR_PREDICTOR_IN_LOGIT_MODEL{std::min(16, std::numeric_limits<double>::max_exponent10)};
const std::string MSE_LOSS_FUNCTION{"mse"};
const size_t MIN_CATEGORIES_IN_CLASSIFIER{2};
const double DIVISOR_IN_GET_MAIN_EFFECT_SHAPE_FUNCTION{1000.0};
const Eigen::Index MIN_OBSERATIONS_IN_A_CV_FOLD{2};
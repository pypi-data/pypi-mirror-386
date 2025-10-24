#pragma once
#include <string>
#include <limits>
#include <functional>
#include <vector>
#include <algorithm>
#include "../dependencies/eigen-3.4.0/Eigen/Dense"
#include "functions.h"
#include "constants.h"

using namespace Eigen;

struct RowsToZeroOutAndNotDueToGivenTerms
{
    VectorXi zeroed;
    VectorXi not_zeroed;
};

struct SortedData
{
    VectorXd values_sorted{VectorXd(0)};
    VectorXd negative_gradient_sorted{VectorXd(0)};
    VectorXd sample_weight_sorted{VectorXd(0)};
};

struct InteractionConstraintsTest
{
    bool term_adheres_to_combination;
    bool at_least_one_term_found_in_combination;
};

class Term
{
private:
    RowsToZeroOutAndNotDueToGivenTerms rows_to_zero_out_and_not_due_to_given_terms;
    size_t max_index;
    size_t max_index_discretized;
    size_t min_observations_in_split;
    size_t bins;
    double v;
    double error_where_given_terms_are_zero;
    SortedData sorted_vectors;
    VectorXd negative_gradient_discretized;
    std::vector<size_t> observations_in_bins;
    int monotonic_constraint;
    int interaction_constraint;
    bool linear_effects_only_in_this_boosting_step;
    double penalty_for_non_linearity;
    double penalty_for_interactions;
    double ridge_penalty;
    double ridge_penalty_weight;

    void calculate_error_where_given_terms_are_zero(const VectorXd &negative_gradient, const VectorXd &sample_weight);
    void initialize_parameters_in_estimate_split_point(size_t bins, double v, size_t min_observations_in_split,
                                                       bool linear_effects_only_in_this_boosting_step,
                                                       double penalty_for_non_linearity, double penalty_for_interactions,
                                                       double ridge_penalty, double ridge_penalty_weight);
    void adjust_min_observations_in_split_to_avoid_computational_errors(size_t min_observations_in_split);
    void sort_vectors_ascending_by_base_term(const MatrixXd &X, const VectorXd &negative_gradient, const VectorXd &sample_weight);
    SortedData sort_data(const VectorXd &values_to_sort, const VectorXd &negative_gradient_to_sort, const VectorXd &sample_weight_to_sort);
    void setup_bins();
    void discretize_data_by_bin();
    void estimate_split_point_on_discretized_data();
    void estimate_coefficient_and_error(const VectorXd &x, const VectorXd &y, const VectorXd &sample_weight, double error_added = 0.0);
    double calculate_penalty_factor_due_to_non_linearity_and_interactions();
    void prune_given_terms();
    double estimate_coefficient(const VectorXd &x, const VectorXd &y, const VectorXd &sample_weight = VectorXd(0));
    void cleanup_after_estimate_split_point();
    void cleanup_after_fit();
    void cleanup_when_this_term_was_added_as_a_given_term();
    void make_term_ineligible();
    void determine_if_can_be_used_as_a_given_term(const VectorXd &x);
    bool coefficient_adheres_to_monotonic_constraint();
    InteractionConstraintsTest test_interaction_constraints(const std::vector<size_t> &legal_interaction_combination);
    std::vector<size_t> get_unique_base_terms_used_in_this_term();
    bool term_uses_just_these_predictors(const std::vector<size_t> &predictor_indexes);

public:
    std::string name;
    size_t base_term; // Index of underlying term in X to use
    std::vector<Term> given_terms;
    double split_point;
    bool direction_right;
    double coefficient;
    VectorXd coefficient_steps;
    double split_point_search_errors_sum;
    std::vector<size_t> bins_start_index;
    std::vector<size_t> bins_end_index;
    std::vector<double> bins_split_points_left;
    std::vector<double> bins_split_points_right;
    size_t ineligible_boosting_steps;
    VectorXd values_discretized;
    VectorXd sample_weight_discretized;
    bool can_be_used_as_a_given_term;
    double estimated_term_importance;
    std::string predictor_affiliation;

    Term(size_t base_term = 0, const std::vector<Term> &given_terms = std::vector<Term>(0), double split_point = NAN_DOUBLE, bool direction_right = false, double coefficient = 0);
    Term(const Term &other);
    ~Term();
    VectorXd calculate(const MatrixXd &X);
    VectorXd calculate_contribution_to_linear_predictor(const MatrixXd &X);
    static bool equals_not_comparing_given_terms(const Term &p1, const Term &p2);
    static bool equals_given_terms(const Term &p1, const Term &p2);
    void estimate_split_point(const MatrixXd &X, const VectorXd &negative_gradient, const VectorXd &sample_weight, size_t bins, double v,
                              size_t min_observations_in_split, bool linear_effects_only_in_this_boosting_step,
                              double penalty_for_non_linearity, double penalty_for_interactions, double ridge_penalty,
                              double ridge_penalty_weight, bool estimate_coefficient_only = false);
    size_t get_interaction_level();
    VectorXd calculate_without_interactions(const VectorXd &x);
    void calculate_rows_to_zero_out_and_not_due_to_given_terms(const MatrixXd &X);
    bool get_can_be_used_as_a_given_term();
    void set_monotonic_constraint(int constraint);
    int get_monotonic_constraint();
    double get_estimated_term_importance();

    friend bool operator==(const Term &p1, const Term &p2);
    friend class APLRRegressor;
    friend class APLRClassifier;
};

Term::Term(size_t base_term, const std::vector<Term> &given_terms, double split_point, bool direction_right, double coefficient)
    : name{""}, base_term{base_term}, given_terms{given_terms}, split_point{split_point}, direction_right{direction_right}, coefficient{coefficient},
      split_point_search_errors_sum{std::numeric_limits<double>::infinity()}, ineligible_boosting_steps{0}, can_be_used_as_a_given_term{false},
      monotonic_constraint{0}, interaction_constraint{0}, estimated_term_importance{NAN_DOUBLE}
{
}

Term::Term(const Term &other)
    : name{other.name}, base_term{other.base_term}, given_terms{other.given_terms}, split_point{other.split_point}, direction_right{other.direction_right},
      coefficient{other.coefficient}, coefficient_steps{other.coefficient_steps}, split_point_search_errors_sum{other.split_point_search_errors_sum},
      ineligible_boosting_steps{0}, can_be_used_as_a_given_term{other.can_be_used_as_a_given_term}, monotonic_constraint{other.monotonic_constraint},
      interaction_constraint{other.interaction_constraint}, estimated_term_importance{other.estimated_term_importance},
      predictor_affiliation{other.predictor_affiliation}
{
}

Term::~Term()
{
}

bool Term::equals_not_comparing_given_terms(const Term &p1, const Term &p2)
{
    bool split_point_and_direction{(is_approximately_equal(p1.split_point, p2.split_point) && p1.direction_right == p2.direction_right) || (std::isnan(p1.split_point) && std::isnan(p2.split_point))};
    bool base_term{p1.base_term == p2.base_term};
    return split_point_and_direction && base_term;
}

bool Term::equals_given_terms(const Term &p1, const Term &p2)
{
    if (p1.given_terms.size() != p2.given_terms.size())
        return false;

    if (p1.given_terms.size() == 0)
        return true;

    bool p1_isin_p2{false};

    for (auto &p1_given_term : p1.given_terms)
    {
        for (auto &p2_given_term : p2.given_terms)
        {
            p1_isin_p2 = equals_not_comparing_given_terms(p1_given_term, p2_given_term);
            if (p1_isin_p2)
            {
                break;
            }
        }
        if (!p1_isin_p2)
            return false;
    }

    return true;
}

bool operator==(const Term &p1, const Term &p2)
{
    bool cmp_ex_given_terms{Term::equals_not_comparing_given_terms(p1, p2)};
    bool cmp_given_terms{Term::equals_given_terms(p1, p2)};
    return cmp_ex_given_terms && cmp_given_terms;
}

void Term::estimate_split_point(const MatrixXd &X, const VectorXd &negative_gradient, const VectorXd &sample_weight, size_t bins, double v,
                                size_t min_observations_in_split, bool linear_effects_only_in_this_boosting_step,
                                double penalty_for_non_linearity, double penalty_for_interactions, double ridge_penalty,
                                double ridge_penalty_weight, bool estimate_coefficient_only)
{
    bool learning_rate_is_zero{is_approximately_zero(v)};
    if (learning_rate_is_zero)
    {
        make_term_ineligible();
        return;
    }

    calculate_rows_to_zero_out_and_not_due_to_given_terms(X);

    bool too_few_observations{static_cast<size_t>(rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.size()) < min_observations_in_split};
    if (too_few_observations)
    {
        make_term_ineligible();
        return;
    }

    initialize_parameters_in_estimate_split_point(bins, v, min_observations_in_split, linear_effects_only_in_this_boosting_step,
                                                  penalty_for_non_linearity, penalty_for_interactions, ridge_penalty, ridge_penalty_weight);
    calculate_error_where_given_terms_are_zero(negative_gradient, sample_weight);
    sort_vectors_ascending_by_base_term(X, negative_gradient, sample_weight);
    if (!estimate_coefficient_only)
    {
        setup_bins();
        bool too_few_bins_for_main_effect{bins_start_index.size() <= 1 && get_interaction_level() == 0};
        if (too_few_bins_for_main_effect)
        {
            make_term_ineligible();
            return;
        }
        discretize_data_by_bin();
        estimate_split_point_on_discretized_data();
    }
    estimate_coefficient_and_error(calculate_without_interactions(sorted_vectors.values_sorted), sorted_vectors.negative_gradient_sorted,
                                   sorted_vectors.sample_weight_sorted, error_where_given_terms_are_zero);
    cleanup_after_estimate_split_point();
    determine_if_can_be_used_as_a_given_term(X.col(base_term));
}

void Term::calculate_rows_to_zero_out_and_not_due_to_given_terms(const MatrixXd &X)
{
    bool term_has_given_terms{given_terms.size() > 0};
    if (term_has_given_terms)
    {
        VectorXi non_zero_values{VectorXi::Constant(X.rows(), 1)};
        for (auto &given_term : given_terms)
        {
            VectorXd values_given_term{given_term.calculate(X)};
            for (Eigen::Index i = 0; i < X.rows(); ++i)
            {
                if (is_approximately_zero(values_given_term[i]))
                {
                    non_zero_values[i] = 0;
                }
            }
        }
        rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.resize(non_zero_values.sum());
        rows_to_zero_out_and_not_due_to_given_terms.zeroed.resize(X.rows() - rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.rows());
        size_t count_zeroed{0};
        size_t count_not_zeroed{0};
        for (Eigen::Index i = 0; i < X.rows(); ++i)
        {
            bool value_is_non_zero{non_zero_values[i] == 1};
            if (value_is_non_zero)
            {
                rows_to_zero_out_and_not_due_to_given_terms.not_zeroed[count_not_zeroed] = i;
                ++count_not_zeroed;
            }
            else
            {
                rows_to_zero_out_and_not_due_to_given_terms.zeroed[count_zeroed] = i;
                ++count_zeroed;
            }
        }
    }
    else
    {
        rows_to_zero_out_and_not_due_to_given_terms.zeroed.resize(0);
        rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.resize(X.rows());
        std::iota(rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.begin(), rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.end(), 0);
    }
}

VectorXd Term::calculate(const MatrixXd &X)
{
    VectorXd values{calculate_without_interactions(X.col(base_term))};

    bool has_given_terms{given_terms.size() > 0};
    if (has_given_terms)
    {
        for (auto &given_term : given_terms)
        {
            VectorXd values_given_term{given_term.calculate(X)};
            for (Eigen::Index i = 0; i < values.size(); ++i)
            {
                if (is_approximately_zero(values_given_term[i]))
                    values[i] = 0;
            }
        }
    }
    return values;
}

VectorXd Term::calculate_without_interactions(const VectorXd &x)
{
    VectorXd values;

    bool linear_effect{std::isnan(split_point)};
    if (linear_effect)
        values = x;
    else
    {
        if (direction_right)
            values = (x.array() - split_point).array().max(0);
        else
            values = (x.array() - split_point).array().min(0);
    }

    return values;
}

void Term::make_term_ineligible()
{
    coefficient = 0;
    split_point_search_errors_sum = std::numeric_limits<double>::infinity();
    ineligible_boosting_steps = std::numeric_limits<size_t>::max();
}

void Term::calculate_error_where_given_terms_are_zero(const VectorXd &negative_gradient, const VectorXd &sample_weight)
{
    error_where_given_terms_are_zero = 0;
    bool rows_need_to_be_zeroed_due_to_given_terms{rows_to_zero_out_and_not_due_to_given_terms.zeroed.size() > 0};
    if (rows_need_to_be_zeroed_due_to_given_terms)
    {
        for (Eigen::Index i = 0; i < rows_to_zero_out_and_not_due_to_given_terms.zeroed.size(); ++i)
        {
            error_where_given_terms_are_zero += calculate_error_one_observation(negative_gradient[rows_to_zero_out_and_not_due_to_given_terms.zeroed[i]], 0.0, sample_weight[rows_to_zero_out_and_not_due_to_given_terms.zeroed[i]]);
        }
    }
}

void Term::initialize_parameters_in_estimate_split_point(size_t bins, double v, size_t min_observations_in_split,
                                                         bool linear_effects_only_in_this_boosting_step, double penalty_for_non_linearity,
                                                         double penalty_for_interactions, double ridge_penalty, double ridge_penalty_weight)
{
    this->bins = bins;
    this->v = v;
    this->linear_effects_only_in_this_boosting_step = linear_effects_only_in_this_boosting_step;
    this->penalty_for_non_linearity = penalty_for_non_linearity;
    this->penalty_for_interactions = penalty_for_interactions;
    this->ridge_penalty = ridge_penalty;
    this->ridge_penalty_weight = ridge_penalty_weight;
    adjust_min_observations_in_split_to_avoid_computational_errors(min_observations_in_split);
    max_index = calculate_max_index_in_vector(rows_to_zero_out_and_not_due_to_given_terms.not_zeroed);
}

void Term::adjust_min_observations_in_split_to_avoid_computational_errors(size_t min_observations_in_split)
{
    this->min_observations_in_split = std::min(min_observations_in_split, static_cast<size_t>(rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.size()));
    this->min_observations_in_split = std::max(min_observations_in_split, static_cast<size_t>(1));
}

void Term::sort_vectors_ascending_by_base_term(const MatrixXd &X, const VectorXd &negative_gradient, const VectorXd &sample_weight)
{
    bool rows_need_to_be_zeroed_due_to_given_terms{rows_to_zero_out_and_not_due_to_given_terms.zeroed.size() > 0};
    if (rows_need_to_be_zeroed_due_to_given_terms)
    {
        VectorXd values_subset(rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.size());
        VectorXd negative_gradient_subset(rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.size());
        VectorXd sample_weight_subset(rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.size());
        size_t count{0};
        for (size_t i = 0; i <= max_index; ++i)
        {
            values_subset[count] = X.col(base_term)[rows_to_zero_out_and_not_due_to_given_terms.not_zeroed[i]];
            negative_gradient_subset[count] = negative_gradient[rows_to_zero_out_and_not_due_to_given_terms.not_zeroed[i]];
            sample_weight_subset[count] = sample_weight[rows_to_zero_out_and_not_due_to_given_terms.not_zeroed[i]];
            ++count;
        }
        sorted_vectors = sort_data(values_subset, negative_gradient_subset, sample_weight_subset);
    }
    else
        sorted_vectors = sort_data(X.col(base_term), negative_gradient, sample_weight);
}

SortedData Term::sort_data(const VectorXd &values_to_sort, const VectorXd &negative_gradient_to_sort, const VectorXd &sample_weight_to_sort)
{
    VectorXi values_sorted_index{sort_indexes_ascending(values_to_sort)};
    SortedData output;
    output.values_sorted.resize(values_sorted_index.size());
    output.negative_gradient_sorted.resize(values_sorted_index.size());
    output.sample_weight_sorted.resize(values_sorted_index.size());
    size_t max_index{values_sorted_index.size() - static_cast<size_t>(1)};
    for (size_t i = 0; i <= max_index; ++i)
    {
        output.values_sorted[i] = values_to_sort[values_sorted_index[i]];
        output.negative_gradient_sorted[i] = negative_gradient_to_sort[values_sorted_index[i]];
        output.sample_weight_sorted[i] = sample_weight_to_sort[values_sorted_index[i]];
    }
    return output;
}

void Term::setup_bins()
{
    bool bins_not_calculated_yet_or_wrongly_sized{bins_start_index.size() == 0};
    if (bins_not_calculated_yet_or_wrongly_sized)
    {
        bins_start_index.reserve(bins + 1);
        bins_end_index.reserve(bins + 1);
        bins_start_index.push_back(0);

        bool can_create_bins{bins > 1};
        if (can_create_bins)
        {
            size_t start_row{min_observations_in_split};
            size_t end_row{max_index + 1 - min_observations_in_split};

            std::vector<size_t> potential_start_indexes;
            potential_start_indexes.reserve(sorted_vectors.values_sorted.size());
            for (size_t i = start_row; i <= end_row; ++i)
            {
                bool is_eligible_start_index{i > 0 && !is_approximately_equal(sorted_vectors.values_sorted[i], sorted_vectors.values_sorted[i - 1])};
                if (is_eligible_start_index)
                    potential_start_indexes.push_back(i);
            }
            size_t last_potential_start_index{potential_start_indexes.size() - 1};

            bool potential_start_indexes_exist{potential_start_indexes.size() > 0};
            bool fewer_start_indexes_than_bins{potential_start_indexes.size() < bins};
            if (potential_start_indexes_exist)
            {
                if (fewer_start_indexes_than_bins)
                {
                    bins_start_index.insert(bins_start_index.end(), std::make_move_iterator(potential_start_indexes.begin()), std::make_move_iterator(potential_start_indexes.end()));
                }
                else if (bins == 2)
                {
                    bins_start_index.push_back(potential_start_indexes[0]);
                }
                else if (bins == 3)
                {
                    bins_start_index.push_back(potential_start_indexes[0]);
                    bins_start_index.push_back(potential_start_indexes[last_potential_start_index]);
                }
                else
                {
                    bins_start_index.push_back(potential_start_indexes[0]); // First bin

                    size_t observations_between_outer_start_indexes{potential_start_indexes[last_potential_start_index] - potential_start_indexes[0]};
                    size_t bins_to_create{bins - 2};
                    size_t desired_observations_in_bin{std::max((observations_between_outer_start_indexes) / bins_to_create + 1, static_cast<size_t>(1))};
                    size_t desired_observations_in_second_last_bin{desired_observations_in_bin * 4 / 5};
                    size_t index_of_start_index_for_previous_bin{0};
                    size_t distance;
                    size_t distance_to_end;
                    for (size_t index_of_start_index = 1; index_of_start_index < last_potential_start_index - 1; ++index_of_start_index)
                    {
                        distance = potential_start_indexes[index_of_start_index] - potential_start_indexes[index_of_start_index_for_previous_bin];
                        distance_to_end = potential_start_indexes[last_potential_start_index] - potential_start_indexes[index_of_start_index];
                        bool can_add_bin{distance >= desired_observations_in_bin && distance_to_end >= desired_observations_in_second_last_bin};
                        if (can_add_bin)
                        {
                            bins_start_index.push_back(potential_start_indexes[index_of_start_index]);
                            index_of_start_index_for_previous_bin = index_of_start_index;
                        }
                    }

                    bins_start_index.push_back(potential_start_indexes[last_potential_start_index]); // Last bin
                }
            }
        }
        bool start_indexes_exist{bins_start_index.size() > 0};
        if (start_indexes_exist)
        {
            for (size_t i = 1; i < bins_start_index.size(); ++i)
            {
                bins_end_index.push_back(bins_start_index[i] - 1);
            }
            bins_end_index.push_back(max_index);
        }
        bins_start_index.shrink_to_fit();
        bins_end_index.shrink_to_fit();

        bins_split_points_left.reserve(bins_start_index.size());
        bins_split_points_right.reserve(bins_start_index.size());
        for (size_t i = 0; i < bins_start_index.size(); ++i)
        {
            if (bins_start_index[i] > 0 && bins_start_index[i] < max_index)
            {
                bins_split_points_left.push_back(sorted_vectors.values_sorted[bins_start_index[i]]);
            }
            if (bins_end_index[i] > 0 && bins_end_index[i] < max_index)
            {
                bins_split_points_right.push_back(sorted_vectors.values_sorted[bins_end_index[i]]);
            }
        }
        bins_split_points_left.shrink_to_fit();
        bins_split_points_right.shrink_to_fit();

        observations_in_bins.reserve(bins_start_index.size());
        for (size_t i = 0; i < bins_start_index.size(); ++i)
        {
            observations_in_bins.push_back(bins_end_index[i] - bins_start_index[i] + 1);
        }
    }
}

void Term::discretize_data_by_bin()
{
    bool calculate_if_it_has_not_been_done_before{values_discretized.size() == 0};
    bool sample_weights_were_provided_by_user{sorted_vectors.sample_weight_sorted.size() > 0};
    if (calculate_if_it_has_not_been_done_before)
    {
        values_discretized.resize(bins_start_index.size());
        sample_weight_discretized.resize(bins_start_index.size());
        for (size_t i = 0; i < bins_start_index.size(); ++i)
        {
            sample_weight_discretized[i] = sorted_vectors.sample_weight_sorted.block(bins_start_index[i], 0, observations_in_bins[i], 1).sum();
            bool sample_weight_for_bin_is_positive{std::isgreater(sample_weight_discretized[i], 0.0)};
            if (sample_weight_for_bin_is_positive)
                values_discretized[i] = (sorted_vectors.values_sorted.block(bins_start_index[i], 0, observations_in_bins[i], 1).array() * sorted_vectors.sample_weight_sorted.block(bins_start_index[i], 0, observations_in_bins[i], 1).array()).sum() / sample_weight_discretized[i];
            else
                values_discretized[i] = sorted_vectors.values_sorted.block(bins_start_index[i], 0, observations_in_bins[i], 1).mean();
        }
    }
    negative_gradient_discretized.resize(bins_start_index.size());
    for (size_t i = 0; i < bins_start_index.size(); ++i)
    {
        bool sample_weight_for_bin_is_positive{std::isgreater(sample_weight_discretized[i], 0.0)};
        if (sample_weight_for_bin_is_positive)
            negative_gradient_discretized[i] = (sorted_vectors.negative_gradient_sorted.block(bins_start_index[i], 0, observations_in_bins[i], 1).array() * sorted_vectors.sample_weight_sorted.block(bins_start_index[i], 0, observations_in_bins[i], 1).array()).sum() / sample_weight_discretized[i];
        else
            negative_gradient_discretized[i] = sorted_vectors.negative_gradient_sorted.block(bins_start_index[i], 0, observations_in_bins[i], 1).mean();
    }
    max_index_discretized = calculate_max_index_in_vector(values_discretized);
}

void Term::estimate_split_point_on_discretized_data()
{
    split_point = NAN_DOUBLE;
    double error_split_point_nan{std::numeric_limits<double>::infinity()};
    bool linear_effect_is_eligible{true};
    for (auto &given_term : given_terms)
    {
        bool a_given_term_with_the_same_base_term_already_exists{base_term == given_term.base_term};
        if (a_given_term_with_the_same_base_term_already_exists)
        {
            linear_effect_is_eligible = false;
            break;
        }
    }
    if (linear_effect_is_eligible)
    {
        estimate_coefficient_and_error(calculate_without_interactions(values_discretized), negative_gradient_discretized, sample_weight_discretized);
        error_split_point_nan = split_point_search_errors_sum;
    }

    bool non_linear_effects_are_allowed{!linear_effects_only_in_this_boosting_step && std::isless(penalty_for_non_linearity, 1.0)};
    if (non_linear_effects_are_allowed)
    {
        double split_point_left{NAN_DOUBLE};
        double error_min_left{error_split_point_nan};
        for (auto bin = bins_split_points_left.rbegin(); bin != bins_split_points_left.rend(); ++bin)
        {
            split_point = *bin;
            direction_right = false;
            estimate_coefficient_and_error(calculate_without_interactions(values_discretized), negative_gradient_discretized, sample_weight_discretized);
            if (std::isless(split_point_search_errors_sum, error_min_left))
            {
                error_min_left = split_point_search_errors_sum;
                split_point_left = split_point;
            }
        }

        double split_point_right{NAN_DOUBLE};
        double error_min_right{error_split_point_nan};
        for (auto &bin : bins_split_points_right)
        {
            split_point = bin;
            direction_right = true;
            estimate_coefficient_and_error(calculate_without_interactions(values_discretized), negative_gradient_discretized, sample_weight_discretized);
            if (std::isless(split_point_search_errors_sum, error_min_right))
            {
                error_min_right = split_point_search_errors_sum;
                split_point_right = split_point;
            }
        }

        bool use_left_direction{std::isless(error_min_left, error_min_right)};
        if (use_left_direction)
        {
            direction_right = false;
            split_point = split_point_left;
            split_point_search_errors_sum = error_min_left;
        }
        else
        {
            direction_right = true;
            split_point = split_point_right;
            split_point_search_errors_sum = error_min_right;
        }
    }

    prune_given_terms();
}

void Term::estimate_coefficient_and_error(const VectorXd &x, const VectorXd &y, const VectorXd &sample_weight, double error_added)
{
    double penalty_factor{calculate_penalty_factor_due_to_non_linearity_and_interactions()};
    coefficient = v * penalty_factor * estimate_coefficient(x, y, sample_weight);
    if (std::isfinite(coefficient) && coefficient_adheres_to_monotonic_constraint())
    {
        VectorXd predictions{x * coefficient};
        split_point_search_errors_sum = calculate_sum_error(calculate_errors(y, predictions, sample_weight, MSE_LOSS_FUNCTION)) + error_added;
    }
    else
    {
        coefficient = 0.0;
        split_point_search_errors_sum = std::numeric_limits<double>::infinity();
    }
}

double Term::calculate_penalty_factor_due_to_non_linearity_and_interactions()
{
    double penalty_factor{1.0};
    bool is_non_linear{!std::isnan(split_point)};
    bool has_interactions{get_interaction_level() > 0};
    if (is_non_linear)
        penalty_factor *= (1.0 - penalty_for_non_linearity);
    if (has_interactions)
        penalty_factor *= (1.0 - penalty_for_interactions);
    return penalty_factor;
}

double Term::estimate_coefficient(const VectorXd &x, const VectorXd &y, const VectorXd &sample_weight)
{
    double numerator{0};
    double denominator{0};
    for (Eigen::Index i = 0; i < y.size(); ++i)
    {
        numerator += x[i] * y[i] * sample_weight[i];
        denominator += x[i] * x[i] * sample_weight[i];
    }
    if (ridge_penalty > 0.0)
        denominator += ridge_penalty * ridge_penalty_weight;
    return numerator / denominator;
}

bool Term::coefficient_adheres_to_monotonic_constraint()
{
    bool coefficient_does_not_adhere_to_increasing_monotonic_constraint{monotonic_constraint > 0 && std::isless(coefficient, 0.0)};
    bool coefficient_does_not_adhere_to_decreasing_monotonic_constraint{monotonic_constraint < 0 && std::isgreater(coefficient, 0.0)};

    bool coefficient_adheres{true};
    if (coefficient_does_not_adhere_to_increasing_monotonic_constraint || coefficient_does_not_adhere_to_decreasing_monotonic_constraint)
        coefficient_adheres = false;

    return coefficient_adheres;
}

void Term::prune_given_terms()
{
    std::vector<size_t> given_term_index_to_keep;
    given_term_index_to_keep.reserve(given_terms.size());
    for (size_t i = 0; i < given_terms.size(); ++i)
    {
        bool keep_given_term{true};
        bool base_term_is_equal{base_term == given_terms[i].base_term};
        bool removing_given_term_with_same_base_term_and_direction{base_term_is_equal && direction_right == given_terms[i].direction_right};
        bool removing_linear_given_term{base_term_is_equal && !std::isfinite(given_terms[i].split_point)};
        if (removing_given_term_with_same_base_term_and_direction)
        {
            keep_given_term = false;
        }
        else if (removing_linear_given_term)
        {
            keep_given_term = false;
        }
        if (keep_given_term)
            given_term_index_to_keep.push_back(i);
    }
    bool at_least_one_given_predictors_to_remove{given_term_index_to_keep.size() < given_terms.size()};
    if (at_least_one_given_predictors_to_remove)
    {
        std::vector<Term> new_given_terms;
        new_given_terms.reserve(given_term_index_to_keep.size());
        for (auto &given_term_index : given_term_index_to_keep)
        {
            new_given_terms.push_back(given_terms[given_term_index]);
        }
        given_terms = std::move(new_given_terms);
    }
}

void Term::cleanup_after_estimate_split_point()
{
    rows_to_zero_out_and_not_due_to_given_terms.not_zeroed.resize(0);
    rows_to_zero_out_and_not_due_to_given_terms.zeroed.resize(0);
    sorted_vectors.values_sorted.resize(0);
    sorted_vectors.negative_gradient_sorted.resize(0);
    sorted_vectors.sample_weight_sorted.resize(0);
    negative_gradient_discretized.resize(0);
}

void Term::determine_if_can_be_used_as_a_given_term(const VectorXd &x)
{
    VectorXd values{calculate_without_interactions(x)};
    can_be_used_as_a_given_term = false;
    for (auto &value : values)
    {
        if (is_approximately_zero(value))
        {
            can_be_used_as_a_given_term = true;
            break;
        }
    }
}

void Term::cleanup_after_fit()
{
    bins_start_index.clear();
    bins_end_index.clear();
    bins_split_points_left.clear();
    bins_split_points_right.clear();
    observations_in_bins.clear();
    values_discretized.resize(0);
    sample_weight_discretized.resize(0);
}

void Term::cleanup_when_this_term_was_added_as_a_given_term()
{
    cleanup_after_fit();
    coefficient_steps.resize(0);
}

VectorXd Term::calculate_contribution_to_linear_predictor(const MatrixXd &X)
{
    VectorXd values{calculate(X)};

    return values.array() * coefficient;
}

size_t Term::get_interaction_level()
{
    std::vector<size_t> terms_used;
    terms_used.reserve(1 + given_terms.size());
    terms_used.push_back(base_term);
    for (auto &given_term : given_terms)
    {
        terms_used.push_back(given_term.base_term);
    }
    std::set<size_t> unique_predictors_used{get_unique_integers(terms_used)};
    size_t interaction_level{unique_predictors_used.size() - 1};

    return interaction_level;
}

bool Term::get_can_be_used_as_a_given_term()
{
    return can_be_used_as_a_given_term;
}

void Term::set_monotonic_constraint(int constraint)
{
    monotonic_constraint = constraint;
}

int Term::get_monotonic_constraint()
{
    return monotonic_constraint;
}

InteractionConstraintsTest Term::test_interaction_constraints(const std::vector<size_t> &legal_interaction_combination)
{
    InteractionConstraintsTest interaction_constraints_test;
    interaction_constraints_test.term_adheres_to_combination = true;
    interaction_constraints_test.at_least_one_term_found_in_combination = false;

    std::vector<size_t> unique_base_terms_used_in_this_term{get_unique_base_terms_used_in_this_term()};
    for (auto &base_term : unique_base_terms_used_in_this_term)
    {
        bool base_term_not_found{std::find(legal_interaction_combination.begin(), legal_interaction_combination.end(), base_term) == legal_interaction_combination.end()};
        if (base_term_not_found)
        {
            interaction_constraints_test.term_adheres_to_combination = false;
        }
        else
        {
            interaction_constraints_test.at_least_one_term_found_in_combination = true;
        }
    }

    return interaction_constraints_test;
}

std::vector<size_t> Term::get_unique_base_terms_used_in_this_term()
{
    std::vector<size_t> terms_used;
    terms_used.reserve(1 + given_terms.size());
    terms_used.push_back(base_term);
    for (auto &given_term : given_terms)
    {
        terms_used.push_back(given_term.base_term);
    }
    terms_used = remove_duplicate_elements_from_vector(terms_used);
    return terms_used;
}

double Term::get_estimated_term_importance()
{
    return estimated_term_importance;
}

bool Term::term_uses_just_these_predictors(const std::vector<size_t> &predictor_indexes)
{
    std::vector<size_t> predictor_indexes_used_by_this_term;
    predictor_indexes_used_by_this_term.push_back(base_term);
    for (auto &given_term : given_terms)
    {
        predictor_indexes_used_by_this_term.push_back(given_term.base_term);
    }
    std::set<size_t> unique_predictor_indexes_used_by_this_term{get_unique_integers(predictor_indexes_used_by_this_term)};
    std::set<size_t> unique_predictor_indexes{get_unique_integers(predictor_indexes)};
    bool only_predictor_indexes_are_used{unique_predictor_indexes_used_by_this_term == unique_predictor_indexes};
    return only_predictor_indexes_are_used;
}

std::vector<size_t> create_term_indexes(std::vector<Term> &terms)
{
    std::vector<size_t> term_indexes;
    term_indexes.reserve(terms.size());
    for (size_t i = 0; i < terms.size(); ++i)
    {
        bool term_is_eligible{terms[i].ineligible_boosting_steps == 0};
        if (term_is_eligible)
            term_indexes.push_back(i);
    }
    term_indexes.shrink_to_fit();
    return term_indexes;
}
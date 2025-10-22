/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

#pragma once

#include <mutex>

#include "DenseDataset.hpp"
#include "DecisionTreeParams.hpp"
#include "DecisionTreeModel.hpp"

namespace tree {
struct TreeModel;
template <class> class Builder;
}
namespace snapml {

//! @ingroup c-api
class DecisionTreeBuilder {

public:
    DecisionTreeBuilder(snapml::DenseDataset data, const snapml::DecisionTreeParams* params);

    void                      init();
    double                    get_feature_importance(uint32_t ft);
    void                      get_feature_importances(double* const out, uint32_t num_ft_chk);
    void                      build(const float* const sample_weight, const float* const sample_weight_val = nullptr,
                                    const double* const labels = nullptr);
    snapml::DecisionTreeModel get_model();

private:
    std::shared_ptr<tree::Builder<tree::TreeModel>> builder_;
    std::shared_ptr<std::mutex>                     mtx_;
};

}

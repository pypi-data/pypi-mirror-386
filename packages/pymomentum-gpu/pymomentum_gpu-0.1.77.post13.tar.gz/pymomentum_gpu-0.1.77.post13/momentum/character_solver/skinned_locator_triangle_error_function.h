/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#pragma once

#include <momentum/character/skinned_locator.h>
#include <momentum/character_solver/error_function_utils.h>
#include <momentum/character_solver/fwd.h>
#include <momentum/character_solver/skeleton_error_function.h>
#include <momentum/character_solver/vertex_error_function.h>
#include <momentum/math/fwd.h>

namespace momentum {

template <typename T>
struct SkinnedLocatorTriangleConstraintT {
  int locatorIndex = -1;
  Eigen::Vector3i tgtTriangleIndices;
  Eigen::Vector3<T> tgtTriangleBaryCoords;
  T depth = 0;
  T weight = 1;

  template <typename T2>
  SkinnedLocatorTriangleConstraintT<T2> cast() const {
    return {
        this->locatorIndex,
        this->tgtTriangleIndices,
        this->tgtTriangleBaryCoords.template cast<T2>(),
        static_cast<T2>(this->depth),
        static_cast<T2>(this->weight)};
  }
};

/// Support constraining a skinned locator to a location on the mesh defined by a target triangle
/// and its normal. The target point is specified as sum_i (bary_i * target_triangle_vertex_i) +
/// depth * target_triangle_normal. This constraint applies "forces" both to the skinned locator and
/// every vertex in the mesh target triangle, so it will actually try to pull both toward each
/// other.
template <typename T>
class SkinnedLocatorTriangleErrorFunctionT : public SkeletonErrorFunctionT<T> {
 public:
  explicit SkinnedLocatorTriangleErrorFunctionT(
      const Character& character,
      VertexConstraintType type = VertexConstraintType::Position);
  ~SkinnedLocatorTriangleErrorFunctionT() override;

  SkinnedLocatorTriangleErrorFunctionT(const SkinnedLocatorTriangleErrorFunctionT& other) = delete;
  SkinnedLocatorTriangleErrorFunctionT& operator=(const SkinnedLocatorTriangleErrorFunctionT&) =
      delete;
  SkinnedLocatorTriangleErrorFunctionT(SkinnedLocatorTriangleErrorFunctionT&&) = delete;
  SkinnedLocatorTriangleErrorFunctionT& operator=(SkinnedLocatorTriangleErrorFunctionT&&) = delete;

  [[nodiscard]] double getError(
      const ModelParametersT<T>& modelParameters,
      const SkeletonStateT<T>& state) final;

  double getGradient(
      const ModelParametersT<T>& modelParameters,
      const SkeletonStateT<T>& state,
      Eigen::Ref<Eigen::VectorX<T>> gradient) final;

  double getJacobian(
      const ModelParametersT<T>& modelParameters,
      const SkeletonStateT<T>& state,
      Eigen::Ref<Eigen::MatrixX<T>> jacobian,
      Eigen::Ref<Eigen::VectorX<T>> residual,
      int& usedRows) final;

  [[nodiscard]] size_t getJacobianSize() const final;

  void addConstraint(
      int locatorIndex,
      const Eigen::Vector3i& triangleIndices,
      const Eigen::Vector3<T>& triangleBaryCoords,
      float depth = 0,
      T weight = 1);
  void clearConstraints();
  void setConstraints(const std::vector<SkinnedLocatorTriangleConstraintT<T>>& constraints);

  [[nodiscard]] const std::vector<SkinnedLocatorTriangleConstraintT<T>>& getConstraints() const {
    return constraints_;
  }

  [[nodiscard]] const Character& getCharacter() const {
    return character_;
  }

 private:
  // Get the parameter index for a skinned locator, or -1 if not parameterized
  [[nodiscard]] int getSkinnedLocatorParameterIndex(int locatorIndex) const {
    if (locatorIndex <
        static_cast<int>(character_.parameterTransform.skinnedLocatorParameters.size())) {
      return character_.parameterTransform.skinnedLocatorParameters[locatorIndex];
    }
    return -1;
  }

  double calculatePositionJacobian(
      const ModelParametersT<T>& modelParameters,
      const SkinnedLocatorTriangleConstraintT<T>& constr,
      Ref<Eigen::MatrixX<T>> jac,
      Ref<Eigen::VectorX<T>> res) const;

  double calculatePlaneJacobian(
      const ModelParametersT<T>& modelParameters,
      const SkinnedLocatorTriangleConstraintT<T>& constr,
      Ref<Eigen::MatrixX<T>> jac,
      T& res) const;

  double calculatePositionGradient(
      const ModelParametersT<T>& modelParameters,
      const SkinnedLocatorTriangleConstraintT<T>& constr,
      Eigen::Ref<Eigen::VectorX<T>> gradient) const;

  double calculatePlaneGradient(
      const ModelParametersT<T>& modelParameters,
      const SkinnedLocatorTriangleConstraintT<T>& constr,
      Eigen::Ref<Eigen::VectorX<T>> gradient) const;

  Eigen::Vector3<T> getLocatorRestPosition(const ModelParametersT<T>& modelParams, int locatorIndex)
      const;

  const Character& character_;

  std::vector<SkinnedLocatorTriangleConstraintT<T>> constraints_;

  std::unique_ptr<MeshT<T>> neutralMesh_; // Rest mesh without facial expression basis
  std::unique_ptr<MeshT<T>> restMesh_; // Rest positions after shape basis is applied

  const VertexConstraintType constraintType_;
  void updateMeshes(const ModelParametersT<T>& modelParameters);
};

} // namespace momentum

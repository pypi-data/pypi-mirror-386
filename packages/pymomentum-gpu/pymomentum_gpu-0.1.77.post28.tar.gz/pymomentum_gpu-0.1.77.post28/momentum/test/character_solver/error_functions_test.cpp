/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#include <chrono>
#include <cstring>
#include <random>

#include <gmock/gmock-matchers.h>
#include <gtest/gtest.h>

#include "momentum/character/character.h"
#include "momentum/character/linear_skinning.h"
#include "momentum/character/mesh_state.h"
#include "momentum/character/parameter_transform.h"
#include "momentum/character/skeleton.h"
#include "momentum/character/skeleton_state.h"
#include "momentum/character/skin_weights.h"
#include "momentum/character_solver/aim_error_function.h"
#include "momentum/character_solver/collision_error_function.h"
#include "momentum/character_solver/distance_error_function.h"
#include "momentum/character_solver/fixed_axis_error_function.h"
#include "momentum/character_solver/fwd.h"
#include "momentum/character_solver/limit_error_function.h"
#include "momentum/character_solver/model_parameters_error_function.h"
#include "momentum/character_solver/normal_error_function.h"
#include "momentum/character_solver/orientation_error_function.h"
#include "momentum/character_solver/plane_error_function.h"
#include "momentum/character_solver/point_triangle_vertex_error_function.h"
#include "momentum/character_solver/pose_prior_error_function.h"
#include "momentum/character_solver/position_error_function.h"
#include "momentum/character_solver/projection_error_function.h"
#include "momentum/character_solver/skinned_locator_error_function.h"
#include "momentum/character_solver/skinned_locator_triangle_error_function.h"
#include "momentum/character_solver/state_error_function.h"
#include "momentum/character_solver/vertex_error_function.h"
#include "momentum/character_solver/vertex_projection_error_function.h"
#include "momentum/character_solver/vertex_vertex_distance_error_function.h"
#include "momentum/math/constants.h"
#include "momentum/math/mesh.h"
#include "momentum/math/random.h"
#include "momentum/math/utility.h"
#include "momentum/test/character/character_helpers.h"
#include "momentum/test/character_solver/error_function_helpers.h"

using namespace momentum;

using Types = testing::Types<float, double>;

TYPED_TEST_SUITE(Momentum_ErrorFunctionsTest, Types);

namespace {

Character getSkinnedLocatorTestCharacter() {
  Character character = withTestBlendShapes(createTestCharacter(4));

  std::vector<bool> activeLocators(character.skinnedLocators.size(), true);
  activeLocators[1] = false;
  const auto [transform, limits] = addSkinnedLocatorParameters(
      character.parameterTransform, character.parameterLimits, activeLocators);

  return {
      character.skeleton,
      transform,
      limits,
      character.locators,
      character.mesh.get(),
      character.skinWeights.get(),
      character.collision.get(),
      character.poseShapes.get(),
      character.blendShape,
      character.faceExpressionBlendShape,
      character.name,
      character.inverseBindPose,
      character.skinnedLocators};
}

} // namespace

TYPED_TEST(Momentum_ErrorFunctionsTest, LimitError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  LimitErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);

  // TODO: None of these work right at the moment due to precision issues with numerical gradients,
  // need to fix code to use double
  {
    SCOPED_TRACE("Limit MinMax Test");
    ParameterLimit limit;
    limit.type = MinMax;
    limit.weight = 1.0;
    limit.data.minMax.limits = Vector2f(-0.1, 0.1);
    limit.data.minMax.parameterIndex = 0;
    errorFunction.setLimits({limit});
    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(1e-7f, 1e-15));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(T, &errorFunction, parameters, character, Eps<T>(1e-2f, 1e-11));
    }
  }

  {
    SCOPED_TRACE("Limit MinMax Joint Test");
    ParameterLimit limit;
    limit.type = MinMaxJoint;
    limit.weight = 1.0;
    limit.data.minMaxJoint.limits = Vector2f(-0.1, 0.1);
    limit.data.minMaxJoint.jointIndex = 2;
    limit.data.minMaxJoint.jointParameter = 5;
    errorFunction.setLimits({limit});
    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(1e-7f, 1e-15));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(T, &errorFunction, parameters, character, Eps<T>(5e-3f, 1e-10));
    }
  }

  {
    SCOPED_TRACE("Limit LinearTest");
    ParameterLimit limit;
    limit.type = Linear;
    limit.weight = 1.5;
    limit.data.linear.referenceIndex = 0;
    limit.data.linear.targetIndex = 5;
    limit.data.linear.scale = 0.25;
    limit.data.linear.offset = 0.25;
    errorFunction.setLimits({limit});
    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(1e-3f, 5e-12));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(T, &errorFunction, parameters, character, Eps<T>(1e-2f, 1e-10));
    }
  }

  {
    SCOPED_TRACE("Limit PiecewiseLinearTest");
    ParameterLimits limits;

    ParameterLimit limit;
    limit.type = LimitType::Linear;
    limit.data.linear.referenceIndex = 0;
    limit.data.linear.targetIndex = 5;
    limit.weight = 0.5f;

    {
      ParameterLimit cur = limit;
      cur.data.linear.scale = -1.0f;
      cur.data.linear.offset = 3.0f;
      cur.data.linear.rangeMin = -FLT_MAX;
      cur.data.linear.rangeMax = -3.0f;
      limits.push_back(cur);
    }

    {
      ParameterLimit cur = limit;
      cur.data.linear.scale = 1.0f;
      cur.data.linear.offset = -3.0f;
      cur.data.linear.rangeMin = -3.0f;
      cur.data.linear.rangeMax = FLT_MAX;
      limits.push_back(cur);
    }

    errorFunction.setLimits(limits);

    // Verify that gradients are ok on either side of the first-derivative discontinuity:
    ModelParametersT<T> parametersBefore = VectorX<T>::Zero(transform.numAllModelParameters());
    parametersBefore(limit.data.linear.targetIndex) = -3.01f;
    const SkeletonStateT<T> skelStateBefore(
        character.parameterTransform.cast<T>().apply(parametersBefore), character.skeleton);
    Eigen::VectorX<T> gradBefore = VectorX<T>::Zero(transform.numAllModelParameters());
    errorFunction.getGradient(parametersBefore, skelStateBefore, MeshStateT<T>(), gradBefore);
    TEST_GRADIENT_AND_JACOBIAN(
        T, &errorFunction, parametersBefore, character, Eps<T>(1e-3f, 1e-10));

    ModelParametersT<T> parametersAfter = VectorX<T>::Zero(transform.numAllModelParameters());
    parametersAfter(limit.data.linear.targetIndex) = -2.99f;
    const SkeletonStateT<T> skelStateAfter(
        character.parameterTransform.cast<T>().apply(parametersAfter), character.skeleton);
    Eigen::VectorX<T> gradAfter = VectorX<T>::Zero(transform.numAllModelParameters());
    errorFunction.getGradient(parametersAfter, skelStateAfter, MeshStateT<T>(), gradAfter);
    TEST_GRADIENT_AND_JACOBIAN(T, &errorFunction, parametersAfter, character, Eps<T>(1e-3f, 1e-10));

    // Gradient won't be the same at the point 3.0:
    ModelParametersT<T> parametersMid = VectorX<T>::Zero(transform.numAllModelParameters());
    parametersMid(limit.data.linear.targetIndex) = -3.0f;
    const SkeletonStateT<T> skelStateMid(
        character.parameterTransform.cast<T>().apply(parametersMid), character.skeleton);

    // Verify that the error is C0 continuous:
    const float errorBefore =
        errorFunction.getError(parametersBefore, skelStateBefore, MeshStateT<T>());
    const float errorMid = errorFunction.getError(parametersMid, skelStateMid, MeshStateT<T>());
    const float errorAfter =
        errorFunction.getError(parametersAfter, skelStateAfter, MeshStateT<T>());

    ASSERT_NEAR(errorBefore, errorMid, 0.03f);
    ASSERT_NEAR(errorMid, errorAfter, 0.03f);
  }

  {
    SCOPED_TRACE("LimitJoint PiecewiseLinearTest");
    ParameterLimits limits;

    ParameterLimit limit;
    limit.type = LimitType::LinearJoint;
    limit.data.linearJoint.referenceJointIndex = 0;
    limit.data.linearJoint.referenceJointParameter = 2;
    limit.data.linearJoint.targetJointIndex = 1;
    limit.data.linearJoint.targetJointParameter = 5;
    limit.weight = 0.75f;

    {
      ParameterLimit cur = limit;
      cur.data.linearJoint.scale = 1.0f;
      cur.data.linearJoint.offset = -4.0f;
      cur.data.linearJoint.rangeMin = -FLT_MAX;
      cur.data.linearJoint.rangeMax = 0.0f;
      limits.push_back(cur);
    }

    {
      ParameterLimit cur = limit;
      cur.data.linearJoint.scale = -1.0f;
      cur.data.linearJoint.offset = -4.0f;
      cur.data.linearJoint.rangeMin = 0.0f;
      cur.data.linearJoint.rangeMax = 2.0;
      limits.push_back(cur);
    }

    {
      ParameterLimit cur = limit;
      cur.data.linearJoint.scale = 1.0f;
      cur.data.linearJoint.offset = 0.0f;
      cur.data.linearJoint.rangeMin = 2.0f;
      cur.data.linearJoint.rangeMax = FLT_MAX;
      limits.push_back(cur);
    }

    errorFunction.setLimits(limits);

    auto rz_param = character.parameterTransform.getParameterIdByName("shared_rz");
    ASSERT_NE(rz_param, momentum::kInvalidIndex);

    for (const auto& testPos : {-4.0, 0.0, 4.0}) {
      // Verify that gradients are ok on either side of the first-derivative discontinuity:
      ModelParametersT<T> parametersBefore = VectorX<T>::Zero(transform.numAllModelParameters());
      parametersBefore(rz_param) = testPos - 0.001f;
      const SkeletonStateT<T> skelStateBefore(
          character.parameterTransform.cast<T>().apply(parametersBefore), character.skeleton);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parametersBefore, character, Eps<T>(5e-2f, 1e-10));

      ModelParametersT<T> parametersAfter = VectorX<T>::Zero(transform.numAllModelParameters());
      parametersAfter(rz_param) = testPos + 0.001f;
      const SkeletonStateT<T> skelStateAfter(
          character.parameterTransform.cast<T>().apply(parametersAfter), character.skeleton);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parametersAfter, character, Eps<T>(5e-2f, 1e-10));

      // Verify that the error is C0 continuous:
      const float errorBefore =
          errorFunction.getError(parametersBefore, skelStateBefore, MeshStateT<T>());
      const float errorAfter =
          errorFunction.getError(parametersAfter, skelStateAfter, MeshStateT<T>());
      ASSERT_NEAR(errorAfter, errorBefore, 0.03f);

      // Make sure the parameter actually varies:
      const auto targetJointParameter =
          limit.data.linearJoint.targetJointIndex * kParametersPerJoint +
          limit.data.linearJoint.targetJointParameter;
      EXPECT_GT(
          std::abs(
              skelStateBefore.jointParameters[targetJointParameter] -
              skelStateAfter.jointParameters[targetJointParameter]),
          0.0005f);
    }
  }

  {
    SCOPED_TRACE("Limit HalfPlaneTest");

    ParameterLimit limit;
    limit.type = HalfPlane;
    limit.weight = 1.0;
    limit.data.halfPlane.param1 = 0;
    limit.data.halfPlane.param2 = 2;
    limit.data.halfPlane.normal = Eigen::Vector2f(1, -1).normalized();
    limit.data.halfPlane.offset = 0.5f;
    errorFunction.setLimits({limit});
    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(5e-3f, 5e-12));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(T, &errorFunction, parameters, character, Eps<T>(1e-2f, 1e-10));
    }
  }

  //{
  //    SCOPED_TRACE("Limit Ellipsoid Test");
  //    limit.type = ELLIPSOID;
  //    limit.weight = 1.0f;
  //    limit.data.ellipsoid.parent = 2;
  //    limit.data.ellipsoid.ellipsoidParent = 0;
  //    limit.data.ellipsoid.offset = Vector3f(0, -1, 0);
  //    limit.data.ellipsoid.ellipsoid = Affine3f::Identity();
  //    limit.data.ellipsoid.ellipsoid.translation() = Vector3f(0.5f, 0.5f, 0.5f);
  //    limit.data.ellipsoid.ellipsoid.linear() = (Quaternionf(Eigen::AngleAxisf(0.1f,
  //    Vector3f::UnitZ())) *
  //                                            Quaternionf(Eigen::AngleAxisf(0.2f,
  //                                            Vector3f::UnitY())) *
  //                                            Quaternionf(Eigen::AngleAxisf(0.3f,
  //                                            Vector3f::UnitX()))).toRotationMatrix() *
  //                                            Scaling(2.0f, 1.5f, 0.5f);
  //    limit.data.ellipsoid.ellipsoidInv = limit.data.ellipsoid.ellipsoid.inverse();

  //    errorFunction.setLimits(lm);
  //    parameters.setZero();
  //    testGradientAndJacobian(&errorFunction, parameters, skeleton, transform);
  //    for (size_t i = 0; i < 3; i++)
  //    {
  //        parameters = VectorXd::Random(transform.numAllModelParameters());
  //        testGradientAndJacobian(&errorFunction, parameters, skeleton, transform);
  //    }
  //}
}

TYPED_TEST(Momentum_ErrorFunctionsTest, StateError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  StateErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  {
    SCOPED_TRACE("State Test");
    SkeletonStateT<T> reference(transform.bindPose(), skeleton);
    errorFunction.setTargetState(reference);
    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(2e-5f, 1e-3));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1) * 0.25;
      TEST_GRADIENT_AND_JACOBIAN(T, &errorFunction, parameters, character, Eps<T>(1e-2f, 5e-6));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, VertexVertexDistanceError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;
  SCOPED_TRACE(fmt::format("ScalarType: {}", typeid(T).name()));

  // create skeleton and reference values
  const size_t nConstraints = 10;

  // Test WITHOUT blend shapes:
  {
    SCOPED_TRACE("Without blend shapes");

    const Character character_orig = createTestCharacter();
    const Eigen::VectorX<T> refParams = 0.25 *
        uniform<VectorX<T>>(character_orig.parameterTransform.numAllModelParameters(), -1, 1);
    const ModelParametersT<T> modelParams = refParams;
    const ParameterTransformT<T> transform = character_orig.parameterTransform.cast<T>();

    VertexVertexDistanceErrorFunctionT<T> errorFunction(character_orig);

    // Add some vertex-vertex distance constraints
    for (size_t iCons = 0; iCons < nConstraints; ++iCons) {
      const int vertexIndex1 =
          uniform<int>(0, static_cast<int>(character_orig.mesh->vertices.size() - 1));
      int vertexIndex2 =
          uniform<int>(0, static_cast<int>(character_orig.mesh->vertices.size() - 1));

      // Ensure we don't constrain the same vertex to itself
      while (vertexIndex2 == vertexIndex1) {
        vertexIndex2 = uniform<int>(0, static_cast<int>(character_orig.mesh->vertices.size() - 1));
      }

      const T weight = uniform<T>(0.1, 2.0);
      const T targetDistance = uniform<T>(0.1, 1.0);

      errorFunction.addConstraint(vertexIndex1, vertexIndex2, weight, targetDistance);
    }

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        modelParams,
        character_orig,
        Eps<T>(5e-2f, 1e-5),
        Eps<T>(1e-6f, 1e-14),
        true,
        false);
  }

  // Test WITH blend shapes:
  {
    SCOPED_TRACE("With blend shapes");

    const Character character_blend = withTestBlendShapes(createTestCharacter());
    const Eigen::VectorX<T> refParams = 0.25 *
        uniform<VectorX<T>>(character_blend.parameterTransform.numAllModelParameters(), -1, 1);
    const ModelParametersT<T> modelParams = refParams;
    const ParameterTransformT<T> transform = character_blend.parameterTransform.cast<T>();

    VertexVertexDistanceErrorFunctionT<T> errorFunction(character_blend);

    // Add some vertex-vertex distance constraints
    for (size_t iCons = 0; iCons < nConstraints; ++iCons) {
      const int vertexIndex1 =
          uniform<int>(0, static_cast<int>(character_blend.mesh->vertices.size() - 1));
      int vertexIndex2 =
          uniform<int>(0, static_cast<int>(character_blend.mesh->vertices.size() - 1));

      // Ensure we don't constrain the same vertex to itself
      while (vertexIndex2 == vertexIndex1) {
        vertexIndex2 = uniform<int>(0, static_cast<int>(character_blend.mesh->vertices.size() - 1));
      }

      const T weight = uniform<T>(0.1, 2.0);
      const T targetDistance = uniform<T>(0.1, 1.0);

      errorFunction.addConstraint(vertexIndex1, vertexIndex2, weight, targetDistance);
    }

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        modelParams,
        character_blend,
        Eps<T>(1e-2f, 1e-5),
        Eps<T>(1e-6f, 1e-14),
        true,
        false);
  }

  // Test that error is zero when vertices are at target distance
  {
    SCOPED_TRACE("Zero error test");

    const Character character = createTestCharacter();
    const ModelParametersT<T> modelParams =
        ModelParametersT<T>::Zero(character.parameterTransform.numAllModelParameters());
    const SkeletonStateT<T> skelState(
        character.parameterTransform.cast<T>().apply(modelParams), character.skeleton);

    VertexVertexDistanceErrorFunctionT<T> errorFunction(character);

    // Calculate actual distance between two vertices
    momentum::TransformationListT<T> ibp;
    for (const auto& js : character.inverseBindPose) {
      ibp.push_back(js.cast<T>());
    }
    const auto mesh = character.mesh->cast<T>();
    const auto& skin = *character.skinWeights;
    momentum::MeshT<T> posedMesh = character.mesh->cast<T>();
    applySSD(ibp, skin, mesh, skelState, posedMesh);

    const int vertexIndex1 = 0;
    const int vertexIndex2 = 1;
    const T actualDistance =
        (posedMesh.vertices[vertexIndex1] - posedMesh.vertices[vertexIndex2]).norm();

    // Add constraint with the actual distance as target
    errorFunction.addConstraint(vertexIndex1, vertexIndex2, T(1.0), actualDistance);

    const double error = errorFunction.getError(
        modelParams, skelState, MeshStateT<T>(modelParams, skelState, character));
    EXPECT_NEAR(error, 0.0, Eps<T>(1e-10f, 1e-15));
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, ModelParametersError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  ModelParametersErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  {
    SCOPED_TRACE("Motion Test");
    SkeletonStateT<T> reference(transform.bindPose(), skeleton);
    VectorX<T> weights = VectorX<T>::Ones(transform.numAllModelParameters());
    weights(0) = 4.0;
    weights(1) = 5.0;
    weights(2) = 0.0;
    errorFunction.setTargetParameters(
        ModelParametersT<T>::Zero(transform.numAllModelParameters()), weights);
    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(1e-7f, 1e-15));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1) * 0.25;
      TEST_GRADIENT_AND_JACOBIAN(T, &errorFunction, parameters, character, Eps<T>(5e-3f, 1e-10));
    }
  }
}

// Show an example of regularizing the blend weights:
TYPED_TEST(Momentum_ErrorFunctionsTest, ModelParametersError_RegularizeBlendWeights) {
  using T = typename TestFixture::Type;

  const Character character = withTestBlendShapes(createTestCharacter());
  const ModelParametersT<T> modelParams =
      0.25 * uniform<VectorX<T>>(character.parameterTransform.numAllModelParameters(), -1, 1);
  ModelParametersErrorFunctionT<T> errorFunction(
      character, character.parameterTransform.getBlendShapeParameters());
  EXPECT_GT(
      errorFunction.getError(
          modelParams,
          SkeletonStateT<T>(
              character.parameterTransform.cast<T>().apply(modelParams), character.skeleton),
          MeshStateT<T>()),
      0);
  TEST_GRADIENT_AND_JACOBIAN(
      T, &errorFunction, modelParams, character, Eps<T>(1e-3f, 1e-10), Eps<T>(1e-7f, 1e-7), true);

  ModelParametersErrorFunctionT<T> errorFunction2(
      character, character.parameterTransform.getScalingParameters());
  TEST_GRADIENT_AND_JACOBIAN(
      T, &errorFunction2, modelParams, character, Eps<T>(1e-3f, 5e-12), Eps<T>(1e-6f, 1e-7), true);
}

TYPED_TEST(Momentum_ErrorFunctionsTest, PosePriorError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  PosePriorErrorFunctionT<T> errorFunction(
      character.skeleton, character.parameterTransform, createDefaultPosePrior<T>());

  TEST_GRADIENT_AND_JACOBIAN(
      T,
      &errorFunction,
      ModelParametersT<T>::Zero(transform.numAllModelParameters()),
      character,
      Eps<T>(1e-1f, 1e-10),
      Eps<T>(1e-5f, 5e-6));

  for (size_t i = 0; i < 3; i++) {
    ModelParametersT<T> parameters = uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
    TEST_GRADIENT_AND_JACOBIAN(
        T, &errorFunction, parameters, character, Eps<T>(5e-1f, 1e-9), Eps<T>(5e-5f, 5e-6));
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, SkinnedLocatorError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // Create a test character with skinned locators
  const Character character = getSkinnedLocatorTestCharacter();
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();
  // Verify that the character has skinned locators
  ASSERT_GT(character.skinnedLocators.size(), 2);

  // Create the error function
  SkinnedLocatorErrorFunctionT<T> errorFunction(character);

  // Add constraints for some of the skinned locators
  const T TEST_WEIGHT_VALUE = 4.5;
  for (int i = 0; i < std::min(3, static_cast<int>(character.skinnedLocators.size())); ++i) {
    errorFunction.addConstraint(
        i, TEST_WEIGHT_VALUE, uniform<Vector3<T>>(-1, 1)); // Random target position
  }

  // Test with random parameters
  for (size_t i = 0; i < 10; i++) {
    ModelParametersT<T> parameters = uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
    TEST_GRADIENT_AND_JACOBIAN(T, &errorFunction, parameters, character, Eps<T>(5e-2f, 5e-6));
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, PointTriangleSkinnedLocatorError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // Create a test character with skinned locators
  const Character character = getSkinnedLocatorTestCharacter();
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // Verify that the character has skinned locators
  ASSERT_GT(character.skinnedLocators.size(), 0);

  // Create the error function with Plane constraint
  for (const auto vertexConstraintType :
       {VertexConstraintType::Plane, VertexConstraintType::Position}) {
    SkinnedLocatorTriangleErrorFunctionT<T> errorFunction(character, vertexConstraintType);

    // Add constraints for some of the skinned locators
    const T TEST_WEIGHT_VALUE = 5.0;
    for (int i = 0; i < character.skinnedLocators.size(); ++i) {
      // Create a simple triangle constraint
      Eigen::Vector3i triangleIndices =
          character.mesh->faces[uniform<int>(0, character.mesh->faces.size() - 1)];
      auto triangleBaryCoords = uniform<Vector3<T>>(0, 1);
      triangleBaryCoords /= triangleBaryCoords.sum();
      T depth = 0.5;

      errorFunction.addConstraint(i, triangleIndices, triangleBaryCoords, depth, TEST_WEIGHT_VALUE);
    }

    // Test with random parameters
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          0.25 * uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(0.03, 5e-4), true, true);
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, TestSkinningErrorFunction) {
  using T = typename TestFixture::Type;

  // this unit tests checks the accuracy of our linear skinning constraint accuracy
  // against our simplified approximation that's way faster.
  // we expect our gradients to be within 10% of the true gradients of the mesh

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();
  const auto mesh = character.mesh->cast<T>();
  const auto& skin = *character.skinWeights;
  VectorX<T> parameters = VectorX<T>::Zero(transform.numAllModelParameters());

  VectorX<T> gradient = VectorX<T>::Zero(transform.numAllModelParameters());

  // create constraints
  std::vector<PositionDataT<T>> cl;
  PositionErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  SkeletonStateT<T> bindState(transform.apply(parameters), skeleton);
  SkeletonStateT<T> state(transform.apply(parameters), skeleton);
  MeshStateT<T> meshState;
  TransformationListT<T> bindpose;
  for (const auto& js : bindState.jointState) {
    bindpose.push_back(js.transform.inverse().toAffine3());
  }

  {
    SCOPED_TRACE("Skinning mesh constraint test");

    for (size_t vi = 0; vi < mesh.vertices.size(); vi++) {
      const Eigen::Vector3<T> target = mesh.vertices[vi];

      // add vertex to constraint list
      cl.clear();
      for (size_t si = 0; si < kMaxSkinJoints; si++) {
        if (skin.weight(vi, si) == 0.0) {
          continue;
        }
        const auto parent = skin.index(vi, si);
        cl.push_back(PositionDataT<T>(
            (target - bindState.jointState[parent].translation()),
            target,
            parent,
            skin.weight(vi, si)));
      }
      errorFunction.setConstraints(cl);

      std::vector<Vector3<T>> v = applySSD(bindpose, skin, mesh.vertices, bindState);

      // check position of skinning
      EXPECT_LE((v[vi] - target).norm(), Eps<T>(2e-7f, 2e-7));

      // check error
      gradient.setZero();
      T gradientError = errorFunction.getGradient(parameters, bindState, meshState, gradient);
      EXPECT_NEAR(gradientError, 0, Eps<T>(1e-15f, 1e-15));
      EXPECT_LE(gradient.norm(), Eps<T>(1e-7f, 1e-7));

      for (size_t i = 0; i < 10; i++) {
        parameters = uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
        state.set(transform.apply(parameters), skeleton);
        v = applySSD(bindpose, skin, mesh.vertices, state);

        cl.clear();
        for (size_t si = 0; si < kMaxSkinJoints; si++) {
          if (skin.weight(vi, si) == 0.0) {
            continue;
          }
          const auto parent = skin.index(vi, si);
          const Vector3<T> offset = state.jointState[parent].transform.inverse() * v[vi];
          cl.push_back(PositionDataT<T>(offset, target, parent, skin.weight(vi, si)));
        }
        errorFunction.setConstraints(cl);

        gradient.setZero();
        gradientError = errorFunction.getGradient(parameters, state, meshState, gradient);
        auto numError = (v[vi] - target).squaredNorm();
        EXPECT_NEAR(gradientError, numError, Eps<T>(1e-5f, 1e-5));

        // calculate numerical gradient
        constexpr T kStepSize = 1e-5;
        VectorX<T> numGradient = VectorX<T>::Zero(transform.numAllModelParameters());
        for (auto p = 0; p < transform.numAllModelParameters(); p++) {
          // perform higher-order finite differences for accuracy
          VectorX<T> params = parameters;
          params(p) = parameters(p) - kStepSize;
          state.set(transform.apply(params), skeleton);
          v = applySSD(bindpose, skin, mesh.vertices, state);
          const T h_1 = (v[vi] - target).squaredNorm();

          params(p) = parameters(p) + kStepSize;
          state.set(transform.apply(params), skeleton);
          v = applySSD(bindpose, skin, mesh.vertices, state);
          const T h1 = (v[vi] - target).squaredNorm();

          numGradient(p) = (h1 - h_1) / (2.0 * kStepSize);
        }

        // check the gradients are similar
        {
          SCOPED_TRACE("Checking Numerical Gradient");
          if ((numGradient + gradient).norm() != 0.0) {
            EXPECT_LE(
                (numGradient - gradient).norm() / (numGradient + gradient).norm(),
                Eps<T>(1e-1f, 1e-1));
          }
        }
      }
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, VertexErrorFunctionSerial) {
  using T = typename TestFixture::Type;
  SCOPED_TRACE(fmt::format("ScalarType: {}", typeid(T).name()));

  // create skeleton and reference values

  const size_t nConstraints = 10;

  // Test WITHOUT blend shapes:
  {
    SCOPED_TRACE("Without blend shapes");

    const Character character_orig = createTestCharacter();
    const Eigen::VectorX<T> refParams = 0.25 *
        uniform<VectorX<T>>(character_orig.parameterTransform.numAllModelParameters(), -1, 1);
    const ModelParametersT<T> modelParams = refParams;
    const ModelParametersT<T> modelParamsTarget = refParams +
        0.05 *
            uniform<VectorX<T>>(character_orig.parameterTransform.numAllModelParameters(), -1, 1);
    const Skeleton& skeleton = character_orig.skeleton;
    const ParameterTransformT<T> transform = character_orig.parameterTransform.cast<T>();
    const momentum::SkeletonStateT<T> skelState(transform.apply(modelParamsTarget), skeleton);
    momentum::TransformationListT<T> ibp;
    for (const auto& js : character_orig.inverseBindPose) {
      ibp.push_back(js.cast<T>());
    }
    const auto mesh = character_orig.mesh->cast<T>();
    const auto& skin = *character_orig.skinWeights;
    momentum::MeshT<T> targetMesh = character_orig.mesh->cast<T>();
    applySSD(ibp, skin, mesh, skelState, targetMesh);

    for (VertexConstraintType type :
         {VertexConstraintType::Position,
          VertexConstraintType::Plane,
          VertexConstraintType::Normal,
          VertexConstraintType::SymmetricNormal}) {
      SCOPED_TRACE(fmt::format("Constraint type: {}", toString(type)));

      const T errorTol = [&]() {
        switch (type) {
          case VertexConstraintType::Position:
          case VertexConstraintType::Plane:
            return Eps<T>(5e-2f, 1e-5);

          // TODO Normal constraints have a much higher epsilon than I'd prefer to see;
          // it would be good to dig into this.
          case VertexConstraintType::Normal:
          case VertexConstraintType::SymmetricNormal:
            return Eps<T>(5e-2f, 5e-2);

          default:
            // Shouldn't reach here
            return T(0);
        }
      }();

      VertexErrorFunctionT<T> errorFunction(character_orig, type, 0);
      for (size_t iCons = 0; iCons < nConstraints; ++iCons) {
        const int index =
            uniform<int>(0, static_cast<int>(character_orig.mesh->vertices.size() - 1));
        errorFunction.addConstraint(
            index, uniform<T>(0, 1e-2), targetMesh.vertices[index], targetMesh.normals[index]);
      }

      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          modelParams,
          character_orig,
          errorTol,
          Eps<T>(1e-6f, 1e-14),
          true,
          false);
    }
  }

  // Test WITH blend shapes:
  {
    SCOPED_TRACE("With blend shapes");

    const Character character_blend = withTestBlendShapes(createTestCharacter());
    const Eigen::VectorX<T> refParams = 0.25 *
        uniform<VectorX<T>>(character_blend.parameterTransform.numAllModelParameters(), -1, 1);
    const ModelParametersT<T> modelParams = refParams;
    const ModelParametersT<T> modelParamsTarget = refParams +
        0.05 *
            uniform<VectorX<T>>(character_blend.parameterTransform.numAllModelParameters(), -1, 1);
    const Skeleton& skeleton = character_blend.skeleton;
    const ParameterTransformT<T> transform = character_blend.parameterTransform.cast<T>();
    const momentum::SkeletonStateT<T> skelState(transform.apply(modelParamsTarget), skeleton);
    momentum::TransformationListT<T> ibp;
    for (const auto& js : character_blend.inverseBindPose) {
      ibp.push_back(js.cast<T>());
    }
    const auto mesh = character_blend.mesh->cast<T>();
    const auto& skin = *character_blend.skinWeights;
    momentum::MeshT<T> targetMesh = character_blend.mesh->cast<T>();
    applySSD(ibp, skin, mesh, skelState, targetMesh);

    // It's trickier to test Normal and SymmetricNormal constraints in the blend shape case because
    // the mesh normals are recomputed after blend shapes are applied (this is the only sensible
    // thing to do since the blend shapes can drastically change the shape) and thus the normals
    // depend on the blend shapes in a very complicated way that we aren't currently trying to
    // model.
    for (VertexConstraintType type :
         {VertexConstraintType::Position, VertexConstraintType::Plane}) {
      SCOPED_TRACE(fmt::format("Constraint type: {}", toString(type)));

      VertexErrorFunctionT<T> errorFunction(character_blend, type);
      for (size_t iCons = 0; iCons < nConstraints; ++iCons) {
        const int index =
            uniform<int>(0, static_cast<int>(character_blend.mesh->vertices.size() - 1));
        errorFunction.addConstraint(
            index, uniform<T>(0, 1e-2), targetMesh.vertices[index], targetMesh.normals[index]);
      }

      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          modelParams,
          character_blend,
          Eps<T>(1e-2f, 1e-5),
          Eps<T>(1e-6f, 1e-14),
          true,
          false);
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, VertexErrorFunctionParallel) {
  using T = typename TestFixture::Type;
  SCOPED_TRACE(fmt::format("ScalarType: {}", typeid(T).name()));

  // create skeleton and reference values

  const size_t nConstraints = 1000;

  const Character character_orig = createTestCharacter();
  const Eigen::VectorX<T> refParams =
      0.25 * uniform<VectorX<T>>(character_orig.parameterTransform.numAllModelParameters(), -1, 1);
  const ModelParametersT<T> modelParams = refParams;
  const ModelParametersT<T> modelParamsTarget = refParams +
      0.05 * uniform<VectorX<T>>(character_orig.parameterTransform.numAllModelParameters(), -1, 1);
  const Skeleton& skeleton = character_orig.skeleton;
  const ParameterTransformT<T> transform = character_orig.parameterTransform.cast<T>();
  const momentum::SkeletonStateT<T> skelState(transform.apply(modelParamsTarget), skeleton);
  momentum::TransformationListT<T> ibp;
  for (const auto& js : character_orig.inverseBindPose) {
    ibp.push_back(js.cast<T>());
  }
  const auto mesh = character_orig.mesh->cast<T>();
  const auto& skin = *character_orig.skinWeights;
  momentum::MeshT<T> targetMesh = character_orig.mesh->cast<T>();
  applySSD(ibp, skin, mesh, skelState, targetMesh);

  for (VertexConstraintType type :
       {VertexConstraintType::Position,
        VertexConstraintType::Plane,
        VertexConstraintType::Normal,
        VertexConstraintType::SymmetricNormal}) {
    SCOPED_TRACE(fmt::format("Constraint type: {}", toString(type)));

    const T errorTol = [&]() {
      switch (type) {
        case VertexConstraintType::Position:
        case VertexConstraintType::Plane:
          return Eps<T>(5e-2f, 1e-5);

        // TODO Normal constraints have a much higher epsilon than I'd prefer to see;
        // it would be good to dig into this.
        case VertexConstraintType::Normal:
        case VertexConstraintType::SymmetricNormal:
          return Eps<T>(5e-2f, 5e-2);

        default:
          // Shouldn't reach here
          return T(0);
      }
    }();

    VertexErrorFunctionT<T> errorFunction(character_orig, type, 100000);
    for (size_t iCons = 0; iCons < nConstraints; ++iCons) {
      const int index = uniform<int>(0, static_cast<int>(character_orig.mesh->vertices.size() - 1));
      errorFunction.addConstraint(
          index, uniform<T>(0, 1e-4), targetMesh.vertices[index], targetMesh.normals[index]);
    }

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        modelParams,
        character_orig,
        errorTol,
        Eps<T>(1e-6f, 1e-15),
        true,
        false);
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, VertexProjectionErrorFunction) {
  using T = typename TestFixture::Type;
  SCOPED_TRACE(fmt::format("ScalarType: {}", typeid(T).name()));

  // create skeleton and reference values

  const size_t nConstraints = 10;

  // Test WITHOUT blend shapes:
  {
    SCOPED_TRACE("Without blend shapes");

    const Character character_orig = createTestCharacter();
    const Eigen::VectorX<T> refParams = 0.25 *
        uniform<VectorX<T>>(character_orig.parameterTransform.numAllModelParameters(), -1, 1);
    const ModelParametersT<T> modelParams = refParams;
    const ModelParametersT<T> modelParamsTarget = refParams +
        0.05 *
            uniform<VectorX<T>>(character_orig.parameterTransform.numAllModelParameters(), -1, 1);
    const Skeleton& skeleton = character_orig.skeleton;
    const ParameterTransformT<T> transform = character_orig.parameterTransform.cast<T>();
    const momentum::SkeletonStateT<T> skelState(transform.apply(modelParamsTarget), skeleton);
    momentum::TransformationListT<T> ibp;
    for (const auto& js : character_orig.inverseBindPose) {
      ibp.push_back(js.cast<T>());
    }
    const auto mesh = character_orig.mesh->cast<T>();
    const auto& skin = *character_orig.skinWeights;
    momentum::MeshT<T> targetMesh = character_orig.mesh->cast<T>();
    applySSD(ibp, skin, mesh, skelState, targetMesh);

    Eigen::Matrix<T, 3, 4> projection = Eigen::Matrix<T, 3, 4>::Identity();
    projection(0, 0) = 10.0;
    projection(1, 1) = 10.0;
    projection(2, 3) = 10.0;

    const T errorTol = Eps<T>(5e-2f, 1e-5);

    VertexProjectionErrorFunctionT<T> errorFunction(character_orig, 0);
    for (size_t iCons = 0; iCons < nConstraints; ++iCons) {
      const int index = uniform<int>(0, character_orig.mesh->vertices.size() - 1);
      const Eigen::Vector3<T> target = projection * targetMesh.vertices[index].homogeneous();
      const Eigen::Vector2<T> target2d = target.hnormalized() + uniform<Vector2<T>>(-1, 1) * 0.1;
      errorFunction.addConstraint(index, uniform<T>(0, 1e-2), target2d, projection);
    }

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        modelParams,
        character_orig,
        errorTol,
        Eps<T>(1e-6f, 1e-14),
        true,
        false);
  }

  // Test WITH blend shapes:
  {
    SCOPED_TRACE("With blend shapes");

    const Character character_blend = withTestBlendShapes(createTestCharacter());
    const Eigen::VectorX<T> refParams = 0.25 *
        uniform<VectorX<T>>(character_blend.parameterTransform.numAllModelParameters(), -1, 1);
    const ModelParametersT<T> modelParams = refParams;
    const ModelParametersT<T> modelParamsTarget = refParams +
        0.05 *
            uniform<VectorX<T>>(character_blend.parameterTransform.numAllModelParameters(), -1, 1);
    const Skeleton& skeleton = character_blend.skeleton;
    const ParameterTransformT<T> transform = character_blend.parameterTransform.cast<T>();
    const momentum::SkeletonStateT<T> skelState(transform.apply(modelParamsTarget), skeleton);
    momentum::TransformationListT<T> ibp;
    for (const auto& js : character_blend.inverseBindPose) {
      ibp.push_back(js.cast<T>());
    }
    const auto mesh = character_blend.mesh->cast<T>();
    const auto& skin = *character_blend.skinWeights;
    momentum::MeshT<T> targetMesh = character_blend.mesh->cast<T>();
    applySSD(ibp, skin, mesh, skelState, targetMesh);

    Eigen::Matrix<T, 3, 4> projection = Eigen::Matrix<T, 3, 4>::Identity();
    projection(2, 3) = 10;

    // It's trickier to test Normal and SymmetricNormal constraints in the blend shape case because
    // the mesh normals are recomputed after blend shapes are applied (this is the only sensible
    // thing to do since the blend shapes can drastically change the shape) and thus the normals
    // depend on the blend shapes in a very complicated way that we aren't currently trying to
    // model.
    VertexProjectionErrorFunctionT<T> errorFunction(character_blend);
    for (size_t iCons = 0; iCons < nConstraints; ++iCons) {
      const int index = uniform<int>(0, character_blend.mesh->vertices.size() - 1);
      const Eigen::Vector3<T> target = projection * targetMesh.vertices[index].homogeneous();
      const Eigen::Vector2<T> target2d = target.hnormalized();
      errorFunction.addConstraint(index, uniform<T>(0, 1e-2), target2d, projection);
    }

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        modelParams,
        character_blend,
        Eps<T>(1e-2f, 1e-5),
        Eps<T>(1e-6f, 1e-14),
        true,
        false);
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, PointTriangleVertexErrorFunction) {
  using T = typename TestFixture::Type;

  // The Normal and SymmetricNormal tests are currently failing, for very confusing
  // reasons.  We get large nonzero values in the Jacobian for the _rigid_ parameters
  // when computing them _numerically_, which suggests something funny is going on
  // that makes them depend on e.g. a rigid translation of the entire model -- but
  // only for Normal/SymmetricNormal constrains.  This seems especially weird to me
  // for global translations, because the skinning code doesn't even use the translation
  // part of the matrix when skinning normals.
  //
  // For now I'm only using Plane constraints anyway, because letting the Triangle
  // in the PointTriangle constraint determine what the normal is seems like the right
  // move.  At some point we should revisit, either to disable support for Normal constraints
  // altogether or figure out where this very weird issue comes from.

  for (const auto& constraintType : {
           VertexConstraintType::Position, VertexConstraintType::Plane,
           // VertexConstraintType::Normal,
           // VertexConstraintType::SymmetricNormal
       }) {
    Character character = createTestCharacter();
    character = withTestBlendShapes(character);

    const Skeleton& skeleton = character.skeleton;
    const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

    SCOPED_TRACE("constraintType: " + std::string(toString(constraintType)));

    PointTriangleVertexErrorFunctionT<T> errorFunction(character, constraintType);

    // Create a simple triangle and a point above it
    {
      Eigen::Vector3i triangleIndices(0, 1, 2);
      Eigen::Vector3<T> triangleBaryCoords(0.3, 0.3, 0.4);
      T depth = 0.1;
      T weight = 1.0;

      // Add a constraint
      errorFunction.addConstraint(3, triangleIndices, triangleBaryCoords, depth, weight);
    }

    {
      Eigen::Vector3i triangleIndices(10, 12, 14);
      Eigen::Vector3<T> triangleBaryCoords(0.2, 0.4, 0.4);
      T depth = 0.2;
      T weight = 0.5;

      // Add a constraint
      errorFunction.addConstraint(3, triangleIndices, triangleBaryCoords, depth, weight);
    }

    // Set up model parameters and skeleton state
    // ModelParametersT<T> modelParams =
    // ModelParametersT<T>::Zero(transform.numAllModelParameters());
    const ModelParametersT<T> modelParams =
        0.25 * uniform<VectorX<T>>(character.parameterTransform.numAllModelParameters(), -1, 1);

    SkeletonStateT<T> state(transform.apply(modelParams), skeleton);

    // Test error calculation
    double error =
        errorFunction.getError(modelParams, state, MeshStateT<T>(modelParams, state, character));
    EXPECT_GT(error, 0);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        modelParams,
        character,
        Eps<T>(5e-2f, 5e-4),
        Eps<T>(1e-6f, 1e-13),
        true,
        true);
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, VertexPositionErrorFunctionFaceParameters) {
  using T = typename TestFixture::Type;

  const size_t nConstraints = 10;

  // Face expression blend shapes only
  {
    const Character character_blend = withTestFaceExpressionBlendShapes(createTestCharacter());
    const ModelParametersT<T> modelParams = 0.25 *
        uniform<VectorX<T>>(character_blend.parameterTransform.numAllModelParameters(), -1, 1);

    // TODO: Add Plane, Normal and SymmetricNormal?
    for (VertexConstraintType type : {VertexConstraintType::Position}) {
      VertexErrorFunctionT<T> errorFunction(character_blend, type);
      for (size_t iCons = 0; iCons < nConstraints; ++iCons) {
        errorFunction.addConstraint(
            uniform<int>(0, character_blend.mesh->vertices.size() - 1),
            uniform<T>(0, 1),
            uniform<Vector3<T>>(0, 1),
            uniform<Vector3<T>>(0.1, 1).normalized());
      }

      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          modelParams,
          character_blend,
          Eps<T>(5e-2f, 1e-5),
          Eps<T>(1e-6f, 5e-16),
          true,
          false);
    }
  }

  // Face expression blend shapes plus shape blend shapes
  {
    const Character character_blend =
        withTestBlendShapes(withTestFaceExpressionBlendShapes(createTestCharacter()));
    const ModelParametersT<T> modelParams = 0.25 *
        uniform<VectorX<T>>(character_blend.parameterTransform.numAllModelParameters(), -1, 1);

    // TODO: Add Plane, Normal and SymmetricNormal?
    for (VertexConstraintType type : {VertexConstraintType::Position}) {
      VertexErrorFunctionT<T> errorFunction(character_blend, type);
      for (size_t iCons = 0; iCons < nConstraints; ++iCons) {
        errorFunction.addConstraint(
            uniform<int>(0, character_blend.mesh->vertices.size() - 1),
            uniform<T>(0, 1),
            uniform<Vector3<T>>(0, 1),
            uniform<Vector3<T>>(0.1, 1).normalized());
      }

      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          modelParams,
          character_blend,
          Eps<T>(1e-2f, 1e-5),
          Eps<T>(1e-6f, 5e-16),
          true,
          false);
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, PositionErrorL2_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  PositionErrorFunctionT<T> errorFunction(
      skeleton, character.parameterTransform, GeneralizedLossT<T>::kL2, uniform<T>(0.2, 10));
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("PositionL2 Constraint Test");
    std::vector<PositionDataT<T>> cl{
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 2, TEST_WEIGHT_VALUE),
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 1, TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(5e-2f, 5e-6));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(5e-2f, 5e-6), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, PositionErrorL1_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  PositionErrorFunctionT<T> errorFunction(
      skeleton, character.parameterTransform, GeneralizedLossT<T>::kL1, uniform<T>(0.5, 2));
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("PositionL1 Constraint Test");
    std::vector<PositionDataT<T>> cl{
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 2, TEST_WEIGHT_VALUE),
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 1, TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(5e-2f, 5e-9),
        Eps<T>(1e-6f, 1e-7),
        false,
        false);
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          parameters,
          character,
          Eps<T>(5e-2f, 5e-9),
          Eps<T>(1e-6f, 1e-7),
          false,
          false);
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, PositionErrorCauchy_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  PositionErrorFunctionT<T> errorFunction(
      skeleton, character.parameterTransform, GeneralizedLossT<T>::kCauchy, uniform<T>(0.5, 2));
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("PositionCauchy Constraint Test");
    std::vector<PositionDataT<T>> cl{
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 2, TEST_WEIGHT_VALUE),
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 1, TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(5e-2f, 5e-9),
        Eps<T>(1e-6f, 1e-7),
        false,
        false);
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          parameters,
          character,
          Eps<T>(5e-2f, 5e-9),
          Eps<T>(1e-6f, 1e-7),
          false,
          false);
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, PositionErrorWelsch_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  PositionErrorFunctionT<T> errorFunction(
      skeleton, character.parameterTransform, GeneralizedLossT<T>::kWelsch);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("PositionWelsch Constraint Test");
    std::vector<PositionDataT<T>> cl{
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 2, TEST_WEIGHT_VALUE),
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 1, TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(5e-2f, 5e-9),
        Eps<T>(1e-6f, 1e-7),
        false,
        false);
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          parameters,
          character,
          Eps<T>(1e-1f, 5e-9),
          Eps<T>(1e-6f, 1e-7),
          false,
          false);
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, PositionErrorGeneral_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  PositionErrorFunctionT<T> errorFunction(
      skeleton, character.parameterTransform, uniform<T>(0.1, 10));
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("PositionGeneral Constraint Test");
    std::vector<PositionDataT<T>> cl{
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 2, TEST_WEIGHT_VALUE),
        PositionDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 1, TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(1e-1f, 5e-9),
        Eps<T>(1e-6f, 1e-7),
        false,
        false);
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          parameters,
          character,
          Eps<T>(5e-1f, 5e-9),
          Eps<T>(1e-6f, 1e-7),
          false,
          false);
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, PlaneErrorL2_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  PlaneErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("PlaneL2 Constraint Test");
    std::vector<PlaneDataT<T>> cl{
        PlaneDataT<T>(
            uniform<Vector3<T>>(0, 1),
            uniform<Vector3<T>>(0.1, 1).normalized(),
            uniform<T>(0, 1),
            2,
            TEST_WEIGHT_VALUE),
        PlaneDataT<T>(
            uniform<Vector3<T>>(0, 1),
            uniform<Vector3<T>>(0.1, 1).normalized(),
            uniform<T>(0, 1),
            1,
            TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(5e-2f, 5e-6));

    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(5e-2f, 1e-5), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, HalfPlaneErrorL2_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  PlaneErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform, true);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("PlaneL2 Constraint Test");
    std::vector<PlaneDataT<T>> cl{
        PlaneDataT<T>(
            uniform<Vector3<T>>(0, 1),
            uniform<Vector3<T>>(0.1, 1).normalized(),
            uniform<T>(0, 1),
            2,
            TEST_WEIGHT_VALUE),
        PlaneDataT<T>(
            uniform<Vector3<T>>(0, 1),
            uniform<Vector3<T>>(0.1, 1).normalized(),
            uniform<T>(0, 1),
            1,
            TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(1e-2f, 5e-6));

    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(5e-2f, 5e-6), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, OrientationErrorL2_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  OrientationErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  const T TEST_WEIGHT_VALUE = 4.5;

  {
    SCOPED_TRACE("Orientation Constraint Test");
    std::vector<OrientationDataT<T>> cl{
        OrientationDataT<T>(
            rotVecToQuaternion<T>(uniform<Vector3<T>>(-1, 1)),
            rotVecToQuaternion<T>(uniform<Vector3<T>>(-1, 1)),
            2,
            TEST_WEIGHT_VALUE),
        OrientationDataT<T>(
            rotVecToQuaternion<T>(uniform<Vector3<T>>(-1, 1)),
            rotVecToQuaternion<T>(uniform<Vector3<T>>(-1, 1)),
            1,
            TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(std::move(cl));

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(0.03f, 5e-6));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1) * 0.25;
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(0.05f, 5e-6), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, FixedAxisDiffErrorL2_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  FixedAxisDiffErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("FixedAxisDiffL2 Constraint Test");
    std::vector<FixedAxisDataT<T>> cl{
        FixedAxisDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 2, TEST_WEIGHT_VALUE),
        FixedAxisDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 1, TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(transform.numAllModelParameters()),
        character,
        Eps<T>(5e-2f, 5e-6));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(8e-2f, 5e-6), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, FixedAxisCosErrorL2_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;

  // create constraints
  FixedAxisCosErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("FixedAxisCosL2 Constraint Test");
    std::vector<FixedAxisDataT<T>> cl{
        FixedAxisDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 2, TEST_WEIGHT_VALUE),
        FixedAxisDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 1, TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    TEST_GRADIENT_AND_JACOBIAN(
        T,
        &errorFunction,
        ModelParametersT<T>::Zero(character.parameterTransform.numAllModelParameters()),
        character,
        Eps<T>(2e-2f, 1e-4));
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(character.parameterTransform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(5e-2f, 1e-4), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, FixedAxisAngleErrorL2_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  FixedAxisAngleErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("FixedAxisAngleL2 Constraint Test");
    std::vector<FixedAxisDataT<T>> cl{
        FixedAxisDataT<T>(
            uniform<Vector3<T>>(-1, 1), uniform<Vector3<T>>(-1, 1), 2, TEST_WEIGHT_VALUE),
        // corner case when the angle is close to zero
        FixedAxisDataT<T>(
            Vector3<T>::UnitY(), Vector3<T>(1e-16, 1 + 1e-16, 1e-16), 1, TEST_WEIGHT_VALUE),
        FixedAxisDataT<T>(Vector3<T>::UnitX(), Vector3<T>::UnitX(), 2, TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    if constexpr (std::is_same_v<T, float>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          5e-2f);
    } else if constexpr (std::is_same_v<T, double>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          2e-2f,
          1e-6,
          true,
          false); // jacobian test is inaccurate around the corner case
    }
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(2e-1f, 5e-5), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, NormalError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();

  // create constraints
  NormalErrorFunctionT<T> errorFunction(character.skeleton, character.parameterTransform);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("Normal Constraint Test");
    std::vector<NormalDataT<T>> cl{
        NormalDataT<T>(
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            1,
            TEST_WEIGHT_VALUE),
        NormalDataT<T>(
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            2,
            TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    if constexpr (std::is_same_v<T, float>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(character.parameterTransform.numAllModelParameters()),
          character,
          2e-2f);
    } else if constexpr (std::is_same_v<T, double>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(character.parameterTransform.numAllModelParameters()),
          character,
          1e-8,
          1e-6,
          true,
          false); // jacobian test is inaccurate around the corner case
    }
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(character.parameterTransform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(1e-1f, 2e-5), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, AimDistError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  AimDistErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("AimDist Constraint Test");
    std::vector<AimDataT<T>> cl{
        AimDataT<T>(
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            1,
            TEST_WEIGHT_VALUE),
        AimDataT<T>(
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            2,
            TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    if constexpr (std::is_same_v<T, float>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          1e-2f);
    } else if constexpr (std::is_same_v<T, double>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          1e-8,
          1e-6,
          true,
          false); // jacobian test is inaccurate around the corner case
    }
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(1e-1f, 2e-5), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, AimDirError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  AimDirErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("AimDir Constraint Test");
    std::vector<AimDataT<T>> cl{
        AimDataT<T>(
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            1,
            TEST_WEIGHT_VALUE),
        AimDataT<T>(
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            uniform<Vector3<T>>(-1, 1),
            2,
            TEST_WEIGHT_VALUE)};
    errorFunction.setConstraints(cl);

    if constexpr (std::is_same_v<T, float>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          5e-2f);
    } else if constexpr (std::is_same_v<T, double>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          1e-8,
          1e-6,
          true,
          false); // jacobian test is inaccurate around the corner case
    }
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), -1, 1);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(1e-1f, 3e-5), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, ProjectionError_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  ProjectionErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform, 0.01);
  Eigen::Matrix4<T> projection = Eigen::Matrix4<T>::Identity();
  projection(2, 3) = 10;
  {
    SCOPED_TRACE("Projection Constraint Test");
    // Make a few projection constraints to ensure that at least one of them is active, since
    // projections are ignored behind the camera
    for (int i = 0; i < 5; ++i) {
      errorFunction.addConstraint(ProjectionConstraintDataT<T>{
          (projection + uniformAffine3<T>().matrix()).topRows(3),
          uniform<size_t>(0, 2),
          normal<Vector3<T>>(Vector3<T>::Zero(), Vector3<T>::Ones()),
          uniform<T>(0.1, 2.0),
          normal<Vector2<T>>(Vector2<T>::Zero(), Vector2<T>::Ones())});
    }

    if constexpr (std::is_same_v<T, float>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          5e-2f);
    } else if constexpr (std::is_same_v<T, double>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          5e-3,
          1e-6,
          true,
          false); // jacobian test is inaccurate around the corner case
    }

    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), 0.0f, 1.0f);
      const momentum::SkeletonStateT<T> skelState(transform.apply(parameters), skeleton);
      ASSERT_GT(errorFunction.getError(parameters, skelState, MeshStateT<T>()), 0);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(1e-1f, 5e-3), Eps<T>(1e-6f, 1e-7));
    }
  }
}

TYPED_TEST(Momentum_ErrorFunctionsTest, DistanceConstraint_GradientsAndJacobians) {
  using T = typename TestFixture::Type;

  // create skeleton and reference values
  const Character character = createTestCharacter();
  const Skeleton& skeleton = character.skeleton;
  const ParameterTransformT<T> transform = character.parameterTransform.cast<T>();

  // create constraints
  DistanceErrorFunctionT<T> errorFunction(skeleton, character.parameterTransform);
  const T TEST_WEIGHT_VALUE = 4.5;
  {
    SCOPED_TRACE("Distance Constraint Test");
    DistanceConstraintDataT<T> constraintData;
    constraintData.parent = 1;
    constraintData.offset = normal<Vector3<T>>(0, 1);
    constraintData.origin = normal<Vector3<T>>(0, 1);
    constraintData.target = 2.3f;
    constraintData.weight = TEST_WEIGHT_VALUE;
    errorFunction.setConstraints({constraintData});

    if constexpr (std::is_same_v<T, float>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          5e-2f);
    } else if constexpr (std::is_same_v<T, double>) {
      TEST_GRADIENT_AND_JACOBIAN(
          T,
          &errorFunction,
          ModelParametersT<T>::Zero(transform.numAllModelParameters()),
          character,
          1e-8,
          1e-6,
          true,
          false); // jacobian test is inaccurate around the corner case
    }
    for (size_t i = 0; i < 10; i++) {
      ModelParametersT<T> parameters =
          uniform<VectorX<T>>(transform.numAllModelParameters(), 1, 0.0f, 1.0f);
      TEST_GRADIENT_AND_JACOBIAN(
          T, &errorFunction, parameters, character, Eps<T>(1e-1f, 2e-5), Eps<T>(1e-6f, 1e-7));
    }
  }
}

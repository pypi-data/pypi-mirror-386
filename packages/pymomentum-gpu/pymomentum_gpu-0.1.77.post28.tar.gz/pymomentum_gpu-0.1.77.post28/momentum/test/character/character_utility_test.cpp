/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#include <gtest/gtest.h>

#include "momentum/character/blend_shape.h"
#include "momentum/character/blend_shape_skinning.h"
#include "momentum/character/character.h"
#include "momentum/character/character_utility.h"
#include "momentum/character/collision_geometry.h"
#include "momentum/character/joint.h"
#include "momentum/character/locator.h"
#include "momentum/character/parameter_transform.h"
#include "momentum/character/skeleton.h"
#include "momentum/character/skeleton_state.h"
#include "momentum/character/skin_weights.h"
#include "momentum/math/constants.h"
#include "momentum/math/mesh.h"
#include "momentum/math/random.h"
#include "momentum/test/character/character_helpers.h"
#include "momentum/test/helpers/expect_throw.h"

using namespace momentum;

// Test fixture for CharacterUtility tests
class CharacterUtilityTest : public ::testing::Test {
 protected:
  void SetUp() override {
    Random<>::GetSingleton().setSeed(42);

    // Create test characters with different numbers of joints
    character = createTestCharacter<float>(5);
    smallCharacter = createTestCharacter<float>(3);
    characterWithBlendShapes = withTestBlendShapes(character);
  }

  Character character;
  Character smallCharacter;
  Character characterWithBlendShapes;
};

// Test scaleCharacter function
TEST_F(CharacterUtilityTest, ScaleCharacter) {
  const float scale = 2.0f;

  // Store original values for comparison
  Vector3f originalTranslation = this->character.skeleton.joints[1].translationOffset;
  Vector3f originalVertex = this->character.mesh->vertices[0];

  // Scale the character
  Character scaledCharacter = scaleCharacter(this->character, scale);

  // Check that the skeleton was scaled correctly
  EXPECT_EQ(scaledCharacter.skeleton.joints.size(), this->character.skeleton.joints.size());
  EXPECT_EQ(scaledCharacter.skeleton.joints[0].name, this->character.skeleton.joints[0].name);
  EXPECT_EQ(scaledCharacter.skeleton.joints[1].name, this->character.skeleton.joints[1].name);

  // Check that joint translations were scaled
  EXPECT_EQ(scaledCharacter.skeleton.joints[1].translationOffset, originalTranslation * scale);

  // Check that mesh vertices were scaled
  EXPECT_TRUE(scaledCharacter.mesh);
  EXPECT_EQ(scaledCharacter.mesh->vertices.size(), this->character.mesh->vertices.size());
  EXPECT_EQ(scaledCharacter.mesh->vertices[0], originalVertex * scale);

  // Check that locators were scaled
  EXPECT_EQ(scaledCharacter.locators.size(), this->character.locators.size());
  if (!this->character.locators.empty()) {
    EXPECT_EQ(scaledCharacter.locators[0].offset, this->character.locators[0].offset * scale);
  }

  // Check that collision geometry was scaled
  if (this->character.collision && !this->character.collision->empty()) {
    EXPECT_TRUE(scaledCharacter.collision);
    EXPECT_EQ(scaledCharacter.collision->size(), this->character.collision->size());
    EXPECT_EQ(
        scaledCharacter.collision->at(0).radius, this->character.collision->at(0).radius * scale);
    EXPECT_EQ(
        scaledCharacter.collision->at(0).length, this->character.collision->at(0).length * scale);
  }

  // Check that inverse bind pose was scaled
  EXPECT_EQ(scaledCharacter.inverseBindPose.size(), this->character.inverseBindPose.size());
  for (size_t i = 0; i < this->character.inverseBindPose.size(); ++i) {
    EXPECT_EQ(
        scaledCharacter.inverseBindPose[i].translation(),
        this->character.inverseBindPose[i].translation() * scale);
  }

  // Test with scale = 1.0 (should be identity operation)
  Character identityScaledCharacter = scaleCharacter(this->character, 1.0f);
  EXPECT_EQ(identityScaledCharacter.skeleton.joints[1].translationOffset, originalTranslation);
  EXPECT_EQ(identityScaledCharacter.mesh->vertices[0], originalVertex);

  // Test with negative scale (should cause a fatal error)
  MOMENTUM_EXPECT_DEATH(static_cast<void>(scaleCharacter(this->character, -1.0f)), "scale > 0.0f");
}

std::shared_ptr<momentum::Mesh> toSkinnedMesh(
    const momentum::Character& character,
    const momentum::ModelParametersT<float>& modelParameters) {
  auto mesh = std::make_shared<momentum::Mesh>(*character.mesh);

  momentum::SkeletonState skelState(
      character.parameterTransform.apply(modelParameters.v.cast<float>()), character.skeleton);

  momentum::skinWithBlendShapes(character, skelState, modelParameters, *mesh);
  mesh->updateNormals();

  return mesh;
}

void testTransformCharacter(const Character& character) {
  // Create a rotation matrix (90 degrees around Y axis)
  Quaternionf rotation = Quaternionf(Eigen::AngleAxis<float>(pi() / 2, Vector3f::UnitY()));
  Eigen::Affine3f transform = Eigen::Affine3f::Identity();
  transform.linear() = rotation.toRotationMatrix();
  transform.translation() = Vector3f(1, 2, 3);

  momentum::ModelParameters modelParams(character.parameterTransform.numAllModelParameters());
  modelParams.v.setZero();

  // set non-zero values for model parameters that do not correspond to the global transform
  for (size_t i = 6; i < modelParams.v.size(); ++i) {
    modelParams.v[i] = 0.1f;
  }
  const auto meshOriginal = toSkinnedMesh(character, modelParams);

  // Store original values for comparison
  Vector3f originalVertex = meshOriginal->vertices[0];
  Vector3f originalNormal = meshOriginal->normals[0];

  // Transform the character
  Character transformedCharacter = transformCharacter(character, transform);

  // Check that the skeleton was transformed correctly
  EXPECT_EQ(transformedCharacter.skeleton.joints.size(), character.skeleton.joints.size());

  // Check that the root joint's pre-rotation was updated
  Quaternionf expectedRootRotation = rotation * character.skeleton.joints[0].preRotation;
  EXPECT_TRUE(transformedCharacter.skeleton.joints[0].preRotation.isApprox(expectedRootRotation));

  // Check that the root joint's translation offset was updated
  Vector3f expectedRootTranslation =
      rotation * character.skeleton.joints[0].translationOffset + transform.translation();
  EXPECT_TRUE(
      transformedCharacter.skeleton.joints[0].translationOffset.isApprox(expectedRootTranslation));

  // Check that mesh vertices were transformed
  const auto meshTransformed = toSkinnedMesh(transformedCharacter, modelParams);
  EXPECT_TRUE(meshTransformed);
  EXPECT_EQ(meshTransformed->vertices.size(), character.mesh->vertices.size());
  Vector3f expectedVertex = transform * originalVertex;
  EXPECT_TRUE(meshTransformed->vertices[0].isApprox(expectedVertex));

  // Check that mesh normals were transformed (only by the rotation part)
  EXPECT_EQ(meshTransformed->normals.size(), character.mesh->normals.size());
  Vector3f expectedNormal = transform.linear() * originalNormal;
  EXPECT_TRUE(meshTransformed->normals[0].isApprox(expectedNormal));

  // Check that inverse bind pose was transformed
  EXPECT_EQ(transformedCharacter.inverseBindPose.size(), character.inverseBindPose.size());
  for (size_t i = 0; i < character.inverseBindPose.size(); ++i) {
    Eigen::Affine3f expectedInverseBindPose = character.inverseBindPose[i] * transform.inverse();
    EXPECT_TRUE(transformedCharacter.inverseBindPose[i].isApprox(expectedInverseBindPose));
  }

  // Test with identity transform (should be identity operation)
  Character identityTransformedCharacter =
      transformCharacter(character, Eigen::Affine3f::Identity());

  const auto identityMeshTransformed = toSkinnedMesh(identityTransformedCharacter, modelParams);
  EXPECT_TRUE(identityMeshTransformed->vertices[0].isApprox(originalVertex));
  EXPECT_TRUE(identityMeshTransformed->normals[0].isApprox(originalNormal));

  // Test with a transform that includes scale (should cause a fatal error)
  Eigen::Affine3f scaleTransform = Eigen::Affine3f::Identity();
  scaleTransform.linear() = 2.0f * Eigen::Matrix3f::Identity();
  MOMENTUM_EXPECT_DEATH(
      static_cast<void>(transformCharacter(character, scaleTransform)),
      "singularValues\\(i\\) > 0.99 && singularValues\\(i\\) < 1.01");
}

// Test transformCharacter function
TEST_F(CharacterUtilityTest, TransformCharacter) {
  // test a character without blend shapes
  testTransformCharacter(this->character);

  // test a character with blend shapes
  testTransformCharacter(this->characterWithBlendShapes);
}

// Test removeJoints function
TEST_F(CharacterUtilityTest, RemoveJoints) {
  // Skip if the character doesn't have enough joints
  if (this->character.skeleton.joints.size() < 5) {
    return;
  }

  // Create a list of joints to remove
  std::vector<size_t> jointsToRemove = {2, 4}; // Remove joints 2 and 4

  // Remove the joints
  Character resultCharacter = removeJoints(this->character, jointsToRemove);

  // Check that the removed joints are actually gone
  for (size_t jointIndex : jointsToRemove) {
    const std::string& jointName = this->character.skeleton.joints[jointIndex].name;
    EXPECT_EQ(resultCharacter.skeleton.getJointIdByName(jointName), kInvalidIndex);
  }

  // Check that non-removed joints are still present
  EXPECT_NE(
      resultCharacter.skeleton.getJointIdByName(this->character.skeleton.joints[0].name),
      kInvalidIndex);
  EXPECT_NE(
      resultCharacter.skeleton.getJointIdByName(this->character.skeleton.joints[1].name),
      kInvalidIndex);

  // Note: Joint 3 might be removed if it's a child of joint 2
  // The implementation of removeJoints also removes child joints

  // Test with invalid joint index (should throw an exception)
  std::vector<size_t> invalidJoints = {this->character.skeleton.joints.size() + 1};
  EXPECT_THROW(
      {
        Character result = removeJoints(this->character, invalidJoints);
        (void)result; // Suppress unused variable warning
      },
      std::exception);

  // Test removing all joints except the root
  std::vector<size_t> allButRoot;
  for (size_t i = 1; i < this->character.skeleton.joints.size(); ++i) {
    allButRoot.push_back(i);
  }
  Character rootOnlyCharacter = removeJoints(this->character, allButRoot);
  EXPECT_EQ(rootOnlyCharacter.skeleton.joints.size(), 1);
  EXPECT_EQ(rootOnlyCharacter.skeleton.joints[0].name, this->character.skeleton.joints[0].name);
}

// Test mapMotionToCharacter function
TEST_F(CharacterUtilityTest, MapMotionToCharacter) {
  // Create a simple motion
  std::vector<std::string> parameterNames = {"root_tx", "root_ty", "root_tz", "nonexistent_param"};
  MatrixXf motion = MatrixXf::Zero(parameterNames.size(), 3); // 3 frames

  // Set some values in the motion
  motion(0, 0) = 1.0f; // root_tx at frame 0
  motion(1, 1) = 2.0f; // root_ty at frame 1
  motion(2, 2) = 3.0f; // root_tz at frame 2
  motion(3, 0) = 4.0f; // nonexistent_param at frame 0

  // Create the motion parameters tuple
  MotionParameters inputMotion = std::make_tuple(parameterNames, motion);

  // Map the motion to the character
  MatrixXf resultMotion = mapMotionToCharacter(inputMotion, this->character);

  // Check that the result motion has the correct size
  EXPECT_EQ(resultMotion.rows(), this->character.parameterTransform.numAllModelParameters());
  EXPECT_EQ(resultMotion.cols(), 3);

  // Check that the mapped parameters have the correct values
  for (size_t i = 0; i < parameterNames.size(); ++i) {
    size_t paramIndex = this->character.parameterTransform.getParameterIdByName(parameterNames[i]);
    if (paramIndex != kInvalidIndex) {
      for (int frame = 0; frame < 3; ++frame) {
        EXPECT_FLOAT_EQ(resultMotion(paramIndex, frame), motion(i, frame));
      }
    }
  }

  // Check that unmapped parameters are zero
  for (size_t i = 0; i < this->character.parameterTransform.numAllModelParameters(); ++i) {
    bool isMapped = false;
    for (auto& parameterName : parameterNames) {
      if (this->character.parameterTransform.getParameterIdByName(parameterName) == i) {
        isMapped = true;
        break;
      }
    }

    if (!isMapped) {
      for (int frame = 0; frame < 3; ++frame) {
        EXPECT_FLOAT_EQ(resultMotion(i, frame), 0.0f);
      }
    }
  }

  // Test with empty motion
  MotionParameters emptyMotion = std::make_tuple(std::vector<std::string>(), MatrixXf());
  MatrixXf emptyResult = mapMotionToCharacter(emptyMotion, this->character);
  EXPECT_EQ(emptyResult.rows(), this->character.parameterTransform.numAllModelParameters());
  EXPECT_EQ(emptyResult.cols(), 0);
}

// Test mapIdentityToCharacter function
TEST_F(CharacterUtilityTest, MapIdentityToCharacter) {
  // Create a simple identity
  std::vector<std::string> jointNames = {"root", "joint1", "nonexistent_joint"};
  VectorXf identity = VectorXf::Zero(jointNames.size() * kParametersPerJoint);

  // Set some values in the identity
  identity(0) = 1.0f; // root_tx
  identity(kParametersPerJoint + 1) = 2.0f; // joint1_ty
  identity(2 * kParametersPerJoint + 2) = 3.0f; // nonexistent_joint_tz

  // Create the identity parameters tuple
  IdentityParameters inputIdentity = std::make_tuple(jointNames, identity);

  // Map the identity to the character
  VectorXf resultIdentity = mapIdentityToCharacter(inputIdentity, this->character);

  // Check that the result identity has the correct size
  EXPECT_EQ(resultIdentity.size(), this->character.skeleton.joints.size() * kParametersPerJoint);

  // Check that the mapped joints have the correct values
  for (size_t i = 0; i < jointNames.size(); ++i) {
    size_t jointIndex = this->character.skeleton.getJointIdByName(jointNames[i]);
    if (jointIndex != kInvalidIndex) {
      for (int param = 0; param < kParametersPerJoint; ++param) {
        EXPECT_FLOAT_EQ(
            resultIdentity(jointIndex * kParametersPerJoint + param),
            identity(i * kParametersPerJoint + param));
      }
    }
  }

  // Check that unmapped joints are zero
  for (size_t i = 0; i < this->character.skeleton.joints.size(); ++i) {
    bool isMapped = false;
    for (auto& jointName : jointNames) {
      if (this->character.skeleton.getJointIdByName(jointName) == i) {
        isMapped = true;
        break;
      }
    }

    if (!isMapped) {
      for (int param = 0; param < kParametersPerJoint; ++param) {
        EXPECT_FLOAT_EQ(resultIdentity(i * kParametersPerJoint + param), 0.0f);
      }
    }
  }

  // Test with empty identity
  IdentityParameters emptyIdentity = std::make_tuple(std::vector<std::string>(), VectorXf());
  VectorXf emptyResult = mapIdentityToCharacter(emptyIdentity, this->character);
  EXPECT_EQ(emptyResult.size(), this->character.skeleton.joints.size() * kParametersPerJoint);
  EXPECT_TRUE(emptyResult.isZero());
}

// Test replaceSkeletonHierarchy error cases
TEST_F(CharacterUtilityTest, ReplaceSkeletonHierarchyErrors) {
  // Create a simple source character
  Character sourceCharacter = createTestCharacter<float>(3);

  // Create a simple target character
  Character targetCharacter = createTestCharacter<float>(3);

  // Test with non-existent source root joint
  EXPECT_THROW(
      {
        Character result = replaceSkeletonHierarchy(
            sourceCharacter,
            targetCharacter,
            "nonexistent_joint",
            targetCharacter.skeleton.joints[1].name);
        (void)result; // Suppress unused variable warning
      },
      std::exception);

  // Test with non-existent target root joint
  EXPECT_THROW(
      {
        Character result = replaceSkeletonHierarchy(
            sourceCharacter,
            targetCharacter,
            sourceCharacter.skeleton.joints[1].name,
            "nonexistent_joint");
        (void)result; // Suppress unused variable warning
      },
      std::exception);

  // Test with empty source skeleton
  Character emptySourceCharacter;
  EXPECT_THROW(
      {
        Character result = replaceSkeletonHierarchy(
            emptySourceCharacter, targetCharacter, "", targetCharacter.skeleton.joints[1].name);
        (void)result; // Suppress unused variable warning
      },
      std::exception);
}

// Test replaceSkeletonHierarchy basic functionality
TEST_F(CharacterUtilityTest, ReplaceSkeletonHierarchyBasic) {
  // Create source and target characters with unique parameter names
  Character sourceCharacter = createTestCharacter<float>(3);
  Character targetCharacter = createTestCharacter<float>(3);

  // Ensure parameter names don't conflict by renaming source parameters
  for (auto& name : sourceCharacter.parameterTransform.name) {
    name = "source_" + name;
  }

  // Get the names of joints to use for replacement
  std::string sourceRootJoint = sourceCharacter.skeleton.joints[1].name;
  std::string targetRootJoint = targetCharacter.skeleton.joints[1].name;

  // Replace the skeleton hierarchy
  Character resultCharacter =
      replaceSkeletonHierarchy(sourceCharacter, targetCharacter, sourceRootJoint, targetRootJoint);

  // Check that the result has a valid skeleton
  EXPECT_FALSE(resultCharacter.skeleton.joints.empty());

  // Check that the source root joint exists in the result
  EXPECT_NE(resultCharacter.skeleton.getJointIdByName(sourceRootJoint), kInvalidIndex);

  // Check that the target root joint exists in the result
  EXPECT_NE(resultCharacter.skeleton.getJointIdByName(targetRootJoint), kInvalidIndex);
}

// Test edge cases and error conditions
TEST_F(CharacterUtilityTest, EdgeCases) {
  // Test scaleCharacter with small positive scale
  // The implementation requires a positive scale value
  Character smallScaledCharacter = scaleCharacter(this->character, 0.001f);
  EXPECT_EQ(smallScaledCharacter.skeleton.joints.size(), this->character.skeleton.joints.size());
  EXPECT_NEAR(smallScaledCharacter.skeleton.joints[1].translationOffset.norm(), 0.0f, 0.01f);

  // Test removeJoints with empty list
  Character unchangedCharacter = removeJoints(this->character, {});
  EXPECT_EQ(unchangedCharacter.skeleton.joints.size(), this->character.skeleton.joints.size());
}

// Test null mesh and collision geometry handling
TEST_F(CharacterUtilityTest, NullHandling) {
  // Create a character with null mesh and collision geometry
  Character nullMeshCharacter = this->character;
  nullMeshCharacter.mesh.reset();

  // Scale the character with null mesh
  Character scaledNullMeshCharacter = scaleCharacter(nullMeshCharacter, 2.0f);
  EXPECT_FALSE(scaledNullMeshCharacter.mesh);

  // Transform the character with null mesh
  Character transformedNullMeshCharacter =
      transformCharacter(nullMeshCharacter, Eigen::Affine3f::Identity());
  EXPECT_FALSE(transformedNullMeshCharacter.mesh);

  // Create a character with null collision geometry
  Character nullCollisionCharacter = this->character;
  nullCollisionCharacter.collision.reset();

  // Scale the character with null collision geometry
  Character scaledNullCollisionCharacter = scaleCharacter(nullCollisionCharacter, 2.0f);
  EXPECT_FALSE(scaledNullCollisionCharacter.collision);
}

// Test parameter limits with invalid joint indices after mapping
TEST_F(CharacterUtilityTest, InvalidJointIndicesAfterMapping) {
  // Create a character with various limit types
  Character characterWithLimits = this->character;

  // Add different types of limits
  ParameterLimits limits;

  // MinMaxJointPassive limit with a joint index that will become invalid
  ParameterLimit minMaxJointPassiveLimit;
  minMaxJointPassiveLimit.type = LimitType::MinMaxJointPassive;
  minMaxJointPassiveLimit.data.minMaxJoint.jointIndex = 2; // This will be removed
  minMaxJointPassiveLimit.data.minMaxJoint.jointParameter = 1;
  minMaxJointPassiveLimit.data.minMaxJoint.limits = Vector2f(-1.0f, 1.0f);
  limits.push_back(minMaxJointPassiveLimit);

  // Ellipsoid limit with parent that will become invalid
  ParameterLimit ellipsoidLimit;
  ellipsoidLimit.type = LimitType::Ellipsoid;
  ellipsoidLimit.data.ellipsoid.parent = 2; // This will be removed
  ellipsoidLimit.data.ellipsoid.ellipsoidParent = 1;
  ellipsoidLimit.data.ellipsoid.ellipsoid = Eigen::Affine3f::Identity();
  ellipsoidLimit.data.ellipsoid.ellipsoidInv = Eigen::Affine3f::Identity();
  ellipsoidLimit.data.ellipsoid.offset = Vector3f(1.0f, 0.0f, 0.0f);
  limits.push_back(ellipsoidLimit);

  // Ellipsoid limit with ellipsoidParent that will become invalid
  ParameterLimit ellipsoidLimit2;
  ellipsoidLimit2.type = LimitType::Ellipsoid;
  ellipsoidLimit2.data.ellipsoid.parent = 1;
  ellipsoidLimit2.data.ellipsoid.ellipsoidParent = 2; // This will be removed
  ellipsoidLimit2.data.ellipsoid.ellipsoid = Eigen::Affine3f::Identity();
  ellipsoidLimit2.data.ellipsoid.ellipsoidInv = Eigen::Affine3f::Identity();
  ellipsoidLimit2.data.ellipsoid.offset = Vector3f(1.0f, 0.0f, 0.0f);
  limits.push_back(ellipsoidLimit2);

  characterWithLimits.parameterLimits = limits;

  // Add parameter sets to test parameter set handling
  ParameterSet testSet;
  testSet.set(0); // Set first parameter as active
  testSet.set(5); // Set a parameter that will be removed
  characterWithLimits.parameterTransform.parameterSets["test_set"] = testSet;

  // Remove joint 2 to make the joint indices invalid
  std::vector<size_t> jointsToRemove = {2};
  Character resultCharacter = removeJoints(characterWithLimits, jointsToRemove);

  // Check that the MinMaxJointPassive limit with invalid joint index was removed
  bool foundMinMaxJointPassiveLimit = false;
  for (const auto& limit : resultCharacter.parameterLimits) {
    if (limit.type == LimitType::MinMaxJointPassive && limit.data.minMaxJoint.jointIndex == 2) {
      foundMinMaxJointPassiveLimit = true;
      break;
    }
  }
  EXPECT_FALSE(foundMinMaxJointPassiveLimit);

  // Check that the Ellipsoid limits with invalid parent or ellipsoidParent were removed
  bool foundEllipsoidLimit = false;
  for (const auto& limit : resultCharacter.parameterLimits) {
    if (limit.type == LimitType::Ellipsoid &&
        (limit.data.ellipsoid.parent == 2 || limit.data.ellipsoid.ellipsoidParent == 2)) {
      foundEllipsoidLimit = true;
      break;
    }
  }
  EXPECT_FALSE(foundEllipsoidLimit);

  // Check that the parameter set was transferred but the invalid parameter was removed
  EXPECT_TRUE(resultCharacter.parameterTransform.parameterSets.count("test_set") > 0);
  if (resultCharacter.parameterTransform.parameterSets.count("test_set") > 0) {
    EXPECT_TRUE(resultCharacter.parameterTransform.parameterSets["test_set"].test(0));
    // Parameter 5 might have been remapped or removed, so we can't check it directly
  }
}

// Test parameter sets handling
TEST_F(CharacterUtilityTest, ParameterSetsHandling) {
  // Create a character with parameter sets
  Character characterWithSets = this->character;

  // Add a parameter set
  ParameterSet testSet;
  testSet.set(0); // Set first parameter as active
  characterWithSets.parameterTransform.parameterSets["test_set"] = testSet;

  // Test that the parameter set exists
  EXPECT_TRUE(characterWithSets.parameterTransform.parameterSets.count("test_set") > 0);

  // Test that the parameter set contains the expected parameter
  EXPECT_TRUE(characterWithSets.parameterTransform.parameterSets["test_set"].test(0));

  // Remove a joint to test parameter set handling during joint removal
  std::vector<size_t> jointsToRemove = {2}; // Remove joint 2
  Character resultCharacter = removeJoints(characterWithSets, jointsToRemove);

  // Check that the parameter set was transferred
  EXPECT_TRUE(resultCharacter.parameterTransform.parameterSets.count("test_set") > 0);

  // Check that the parameter is still active in the result
  EXPECT_TRUE(resultCharacter.parameterTransform.parameterSets["test_set"].test(0));
}

// Test for all parameter limit types
TEST_F(CharacterUtilityTest, AllParameterLimitTypes) {
  // Create a character with all limit types
  Character characterWithLimits = this->character;

  // Add different types of limits
  ParameterLimits limits;

  // MinMaxJoint limit
  ParameterLimit minMaxJointLimit;
  minMaxJointLimit.type = LimitType::MinMaxJoint;
  minMaxJointLimit.data.minMaxJoint.jointIndex = 2; // This will be removed
  minMaxJointLimit.data.minMaxJoint.jointParameter = 1;
  minMaxJointLimit.data.minMaxJoint.limits = Vector2f(-1.0f, 1.0f);
  limits.push_back(minMaxJointLimit);

  // MinMaxJointPassive limit
  ParameterLimit minMaxJointPassiveLimit;
  minMaxJointPassiveLimit.type = LimitType::MinMaxJointPassive;
  minMaxJointPassiveLimit.data.minMaxJoint.jointIndex = 2; // This will be removed
  minMaxJointPassiveLimit.data.minMaxJoint.jointParameter = 1;
  minMaxJointPassiveLimit.data.minMaxJoint.limits = Vector2f(-1.0f, 1.0f);
  limits.push_back(minMaxJointPassiveLimit);

  // Linear limit
  ParameterLimit linearLimit;
  linearLimit.type = LimitType::Linear;
  linearLimit.data.linear.referenceIndex = 10; // This will be invalid after mapping
  linearLimit.data.linear.targetIndex = 0;
  linearLimit.data.linear.scale = 1.0f;
  linearLimit.data.linear.offset = 0.0f;
  limits.push_back(linearLimit);

  // Linear limit with both indices invalid
  ParameterLimit linearLimit2;
  linearLimit2.type = LimitType::Linear;
  linearLimit2.data.linear.referenceIndex = 10; // This will be invalid after mapping
  linearLimit2.data.linear.targetIndex = 11; // This will be invalid after mapping
  linearLimit2.data.linear.scale = 1.0f;
  linearLimit2.data.linear.offset = 0.0f;
  limits.push_back(linearLimit2);

  // LinearJoint limit
  ParameterLimit linearJointLimit;
  linearJointLimit.type = LimitType::LinearJoint;
  linearJointLimit.data.linearJoint.referenceJointIndex = 10; // This will be invalid after mapping
  linearJointLimit.data.linearJoint.targetJointIndex = 0;
  linearJointLimit.data.linearJoint.scale = 1.0f;
  linearJointLimit.data.linearJoint.offset = 0.0f;
  limits.push_back(linearJointLimit);

  // LinearJoint limit with both indices invalid
  ParameterLimit linearJointLimit2;
  linearJointLimit2.type = LimitType::LinearJoint;
  linearJointLimit2.data.linearJoint.referenceJointIndex = 10; // This will be invalid after mapping
  linearJointLimit2.data.linearJoint.targetJointIndex = 11; // This will be invalid after mapping
  linearJointLimit2.data.linearJoint.scale = 1.0f;
  linearJointLimit2.data.linearJoint.offset = 0.0f;
  limits.push_back(linearJointLimit2);

  // HalfPlane limit
  ParameterLimit halfPlaneLimit;
  halfPlaneLimit.type = LimitType::HalfPlane;
  halfPlaneLimit.data.halfPlane.param1 = 10; // This will be invalid after mapping
  halfPlaneLimit.data.halfPlane.param2 = 0;
  halfPlaneLimit.data.halfPlane.normal = Vector2f(1.0f, 1.0f);
  halfPlaneLimit.data.halfPlane.offset = 0.0f;
  limits.push_back(halfPlaneLimit);

  // HalfPlane limit with both params invalid
  ParameterLimit halfPlaneLimit2;
  halfPlaneLimit2.type = LimitType::HalfPlane;
  halfPlaneLimit2.data.halfPlane.param1 = 10; // This will be invalid after mapping
  halfPlaneLimit2.data.halfPlane.param2 = 11; // This will be invalid after mapping
  halfPlaneLimit2.data.halfPlane.normal = Vector2f(1.0f, 1.0f);
  halfPlaneLimit2.data.halfPlane.offset = 0.0f;
  limits.push_back(halfPlaneLimit2);

  // Ellipsoid limit
  ParameterLimit ellipsoidLimit;
  ellipsoidLimit.type = LimitType::Ellipsoid;
  ellipsoidLimit.data.ellipsoid.parent = 1;
  ellipsoidLimit.data.ellipsoid.ellipsoidParent = 2;
  ellipsoidLimit.data.ellipsoid.ellipsoid = Eigen::Affine3f::Identity();
  ellipsoidLimit.data.ellipsoid.ellipsoidInv = Eigen::Affine3f::Identity();
  ellipsoidLimit.data.ellipsoid.offset = Vector3f(1.0f, 0.0f, 0.0f);
  limits.push_back(ellipsoidLimit);

  // LimitTypeCount (should be ignored)
  ParameterLimit limitTypeCountLimit;
  limitTypeCountLimit.type = LimitType::LimitTypeCount;
  limits.push_back(limitTypeCountLimit);

  characterWithLimits.parameterLimits = limits;

  // Remove joint 2 to make the joint indices invalid and trigger parameter mapping
  std::vector<size_t> jointsToRemove = {2};
  Character resultCharacter = removeJoints(characterWithLimits, jointsToRemove);

  // Get the resulting limits
  const ParameterLimits& resultLimits = resultCharacter.parameterLimits;

  // Check that limits with invalid indices were removed
  for (const auto& limit : resultLimits) {
    if (limit.type == LimitType::MinMaxJoint || limit.type == LimitType::MinMaxJointPassive) {
      // Joint index should not be 2 (which was mapped to kInvalidIndex)
      EXPECT_NE(limit.data.minMaxJoint.jointIndex, 2);
    } else if (limit.type == LimitType::Linear) {
      // Both reference and target indices should be valid
      EXPECT_NE(limit.data.linear.referenceIndex, kInvalidIndex);
      EXPECT_NE(limit.data.linear.targetIndex, kInvalidIndex);
    } else if (limit.type == LimitType::LinearJoint) {
      // Both reference and target joint indices should be valid
      EXPECT_NE(limit.data.linearJoint.referenceJointIndex, kInvalidIndex);
      EXPECT_NE(limit.data.linearJoint.targetJointIndex, kInvalidIndex);
    } else if (limit.type == LimitType::HalfPlane) {
      // Both param1 and param2 should be valid
      EXPECT_NE(limit.data.halfPlane.param1, kInvalidIndex);
      EXPECT_NE(limit.data.halfPlane.param2, kInvalidIndex);
    } else if (limit.type == LimitType::Ellipsoid) {
      // Both parent and ellipsoidParent should be valid
      EXPECT_NE(limit.data.ellipsoid.parent, kInvalidIndex);
      EXPECT_NE(limit.data.ellipsoid.ellipsoidParent, kInvalidIndex);
    }
  }

  // Check that LimitTypeCount was ignored
  bool foundLimitTypeCount = false;
  for (const auto& limit : resultLimits) {
    if (limit.type == LimitType::LimitTypeCount) {
      foundLimitTypeCount = true;
      break;
    }
  }
  EXPECT_FALSE(foundLimitTypeCount);

  // Scale the character to test limit scaling
  Character scaledCharacter = scaleCharacter(characterWithLimits, 2.0f);

  // Check that the ellipsoid limit was scaled
  bool foundScaledEllipsoidLimit = false;
  for (const auto& limit : scaledCharacter.parameterLimits) {
    if (limit.type == LimitType::Ellipsoid) {
      foundScaledEllipsoidLimit = true;
      EXPECT_EQ(limit.data.ellipsoid.offset, Vector3f(2.0f, 0.0f, 0.0f));
      break;
    }
  }
  EXPECT_TRUE(foundScaledEllipsoidLimit);
}

// Test parent mapping in replaceSkeletonHierarchy
TEST_F(CharacterUtilityTest, ParentMappingInReplaceSkeletonHierarchy) {
  // Use the test characters from the fixture
  Character sourceCharacter = this->character;
  Character targetCharacter = this->smallCharacter;

  // Ensure parameter names don't conflict
  for (auto& name : sourceCharacter.parameterTransform.name) {
    name = "source_" + name;
  }

  // Get the names of joints to use for replacement
  std::string sourceRootJoint = sourceCharacter.skeleton.joints[1].name;
  std::string targetRootJoint = targetCharacter.skeleton.joints[1].name;

  // Store the original joint count
  size_t originalTargetJointCount = targetCharacter.skeleton.joints.size();

  // Replace the skeleton hierarchy
  Character resultCharacter =
      replaceSkeletonHierarchy(sourceCharacter, targetCharacter, sourceRootJoint, targetRootJoint);

  // Check that the result has a valid skeleton
  EXPECT_FALSE(resultCharacter.skeleton.joints.empty());

  // Check that the target root joint exists in the result
  EXPECT_NE(resultCharacter.skeleton.getJointIdByName(targetRootJoint), kInvalidIndex);

  // Check that the joint count has changed
  EXPECT_NE(resultCharacter.skeleton.joints.size(), originalTargetJointCount);

  // Check that the source joint exists in the result (it might be renamed)
  bool foundSourceJoint = false;
  for (const auto& joint : resultCharacter.skeleton.joints) {
    // The source joint might be renamed, but it should contain the original name
    if (joint.name.find(sourceRootJoint) != std::string::npos) {
      foundSourceJoint = true;
      break;
    }
  }
  EXPECT_TRUE(foundSourceJoint);

  // Check that the parent mapping code was exercised by verifying that
  // the parent of the replaced joint is preserved
  size_t targetRootJointIndex = resultCharacter.skeleton.getJointIdByName(targetRootJoint);
  EXPECT_NE(targetRootJointIndex, kInvalidIndex);
  if (targetRootJointIndex != kInvalidIndex) {
    size_t parentIndex = resultCharacter.skeleton.joints[targetRootJointIndex].parent;
    EXPECT_NE(parentIndex, kInvalidIndex);
    if (parentIndex != kInvalidIndex) {
      // The parent should be the same as in the original target character
      size_t originalParentIndex = targetCharacter.skeleton.joints[1].parent;
      EXPECT_EQ(
          resultCharacter.skeleton.joints[parentIndex].name,
          targetCharacter.skeleton.joints[originalParentIndex].name);
    }
  }
}

// Test parameter sets and other remaining code paths
TEST_F(CharacterUtilityTest, ParameterSetsAndRemainingCodePaths) {
  // Create source and target characters for replaceSkeletonHierarchy
  Character sourceCharacter = createTestCharacter<float>(3);
  Character targetCharacter = createTestCharacter<float>(3);

  // Ensure parameter names don't conflict
  for (auto& name : sourceCharacter.parameterTransform.name) {
    name = "source_" + name;
  }

  // Add parameter sets to source character
  ParameterSet sourceTestSet;
  sourceTestSet.set(0); // Set first parameter as active
  sourceCharacter.parameterTransform.parameterSets["source_test_set"] = sourceTestSet;

  // Add parameter sets to target character
  ParameterSet targetTestSet;
  targetTestSet.set(0); // Set first parameter as active
  targetCharacter.parameterTransform.parameterSets["target_test_set"] = targetTestSet;

  // Get the names of joints to use for replacement
  std::string sourceRootJoint = sourceCharacter.skeleton.joints[1].name;
  std::string targetRootJoint = targetCharacter.skeleton.joints[1].name;

  // Replace the skeleton hierarchy
  Character resultCharacter =
      replaceSkeletonHierarchy(sourceCharacter, targetCharacter, sourceRootJoint, targetRootJoint);

  // Check that the result has a valid skeleton
  EXPECT_FALSE(resultCharacter.skeleton.joints.empty());
}

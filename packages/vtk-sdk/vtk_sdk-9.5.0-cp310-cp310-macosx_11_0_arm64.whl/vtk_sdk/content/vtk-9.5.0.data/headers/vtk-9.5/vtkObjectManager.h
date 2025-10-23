// SPDX-FileCopyrightText: Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
// SPDX-License-Identifier: BSD-3-Clause
/**
 * @class   vtkObjectManager
 * @brief   vtkObjectManager maintains internal instances of vtkSerializer and a vtkDeserializer to
 * serialize and deserialize VTK objects respectively.
 *
 * The vtkObjectManager facilitates:
 *  1. serialization of objects by registering them, updating their state, and providing methods to
 * retrieve both the serialized data (blobs) and object states based on their unique identifiers.
 *  2. deserialization of objects by registering their states and data (blobs) and constructing or
 * updating VTK objects based on MTime.
 *
 * @sa vtkObjectManager
 */
#ifndef vtkObjectManager_h
#define vtkObjectManager_h

#include "vtkObject.h"

#include "vtkDeserializer.h"               // for vtkDeserializer
#include "vtkInvoker.h"                    // for vtkInvoker
#include "vtkLogger.h"                     // for vtkLogger::Verbosity enum
#include "vtkNew.h"                        // for vtkNew
#include "vtkSerializationManagerModule.h" // for export macro
#include "vtkSerializer.h"                 // for vtkSerializer
#include "vtkSmartPointer.h"               // for vtkSmartPointer

#include <string> // for string
#include <vector> // for vector

VTK_ABI_NAMESPACE_BEGIN
class vtkMarshalContext;
class vtkTypeUInt8Array;

class VTKSERIALIZATIONMANAGER_EXPORT vtkObjectManager : public vtkObject
{
public:
  static vtkObjectManager* New();
  vtkTypeMacro(vtkObjectManager, vtkObject);
  void PrintSelf(ostream& os, vtkIndent indent) override;

  ///@{
  /**
   * Loads the default (de)serialization handlers and constructors for VTK classes
   */
  virtual bool Initialize();
  bool InitializeDefaultHandlers();
  ///@}

  /**
   * Loads user provided handlers
   */
  using RegistrarType =
    std::function<int(void* ser, void* deser, void* invoker, const char** error)>;
  bool InitializeExtensionModuleHandlers(const std::vector<RegistrarType>& registrars);

  /**
   * Adds `object` into an internal container and returns a unique identifier.
   * The identifier can be used in any of the methods that accept `id` or a vector of `id`.
   */
  vtkTypeUInt32 RegisterObject(vtkSmartPointer<vtkObjectBase> objectBase);

  /**
   * Removes an object and it's state.
   * Returns true if an object exists at `id` and it was removed, false otherwise.
   */
  bool UnRegisterObject(vtkTypeUInt32 identifier);

  ///@{
  /**
   * Adds `state` into an internal container and returns a unique identifier.
   * The state
   *  1. must be valid json.
   *  2. must have a key-value pair `{'Id': n}` where n is an integer of type `std::string`.
   */
  bool RegisterState(const std::string& state);
  bool RegisterState(const nlohmann::json& state);
  ///@}

  /**
   * Removes a state at `id`.
   */
  bool UnRegisterState(vtkTypeUInt32 identifier);

  /**
   * Get the identifier for `object`.
   * Returns an integer >=0 if `object` was previously registered directly or indirectly i.e, as a
   * dependency of another registered object.
   */
  vtkTypeUInt32 GetId(vtkSmartPointer<vtkObjectBase> objectBase);

  /**
   * Get state of the object at `id`.
   * Returns a non empty json valid string if an object registered directly or indirectly at `id`
   * has a state.
   */
  std::string GetState(vtkTypeUInt32 id);

  /**
   * Get object at `id`.
   * Returns `nullptr` if there is no object registered directly or indirectly at `id`.
   */
  vtkSmartPointer<vtkObjectBase> GetObjectAtId(vtkTypeUInt32 id);

  /**
   * Returns a non-empty vector of identifiers of all objects that depend on an object with the
   * given identifier. Returns an empty vector if there are no dependents.
   * When the root string is empty, the entire dependency tree is returned as a flat vector of
   * identifiers.
   */
  std::vector<vtkTypeUInt32> GetAllDependencies(vtkTypeUInt32 identifier);

  /**
   * Returns a non-empty vector of hash strings that correspond to blobs used by the registered
   * objects at each identifier in `ids`.
   */
  std::vector<std::string> GetBlobHashes(const std::vector<vtkTypeUInt32>& ids);

  /**
   * Returns a blob stored at `hash`.
   */
  vtkSmartPointer<vtkTypeUInt8Array> GetBlob(const std::string& hash) const;

  /**
   * Specifies a `blob` for `hash`. Returns `true` if the `blob` is valid and successfully
   * registered, `false` otherwise.
   */
  bool RegisterBlob(const std::string& hash, vtkSmartPointer<vtkTypeUInt8Array> blob);

  /**
   * Removes a `blob` stored at `hash`.
   */
  bool UnRegisterBlob(const std::string& hash);

  /**
   * Removes all `blob`(s) whose `hash` is not found in the state of any object registered directly
   * or indirectly.
   */
  void PruneUnusedBlobs();

  /**
   * Deserialize registered states into vtk objects.
   */
  void UpdateObjectsFromStates();

  /**
   * Serialize registered objects into states.
   */
  void UpdateStatesFromObjects();

  /**
   * This method is similar to `void UpdateStatesFromObjects()`. The only difference is that this
   * method is far more efficient when updating a specific object and it's dependencies. The
   * identifiers must be valid and correspond to registered objects.
   *
   * @warning This method prunes all unused states and objects after serialization. Ensure that
   * `void UpdateStatesFromObjects()` is called atleast once before this method if you want to
   * preserve objects that were registered but not specified in `identifiers`.
   */
  void UpdateStatesFromObjects(const std::vector<vtkTypeUInt32>& identifiers);

  ///@{
  /**
   * Deserialize the state into vtk object.
   */
  void UpdateObjectFromState(const std::string& state);
  void UpdateObjectFromState(const nlohmann::json& state);
  ///@}

  /**
   * Serialize object at `identifier` into the state.
   */
  void UpdateStateFromObject(vtkTypeUInt32 identifier);

  /**
   * Reset to initial state.
   * All registered objects are removed and no longer tracked.
   * All registered states are also removed.
   * All registered blobs are also removed.
   */
  void Clear();

  std::string Invoke(
    vtkTypeUInt32 identifier, const std::string& methodName, const std::string& args);
  nlohmann::json Invoke(
    vtkTypeUInt32 identifier, const std::string& methodName, const nlohmann::json& args);

  std::size_t GetTotalBlobMemoryUsage();
  std::size_t GetTotalVTKDataObjectMemoryUsage();

  /**
   * Writes state of all registered objects to `filename.json`
   * The blobs are written into `filename.blobs.json`.
   */
  void Export(const std::string& filename, int indentLevel = -1, char indentChar = ' ');

  /**
   * Reads state from state file and blobs from blob file.
   * This clears existing states, objects, blobs, imports data from the two files and updates
   * objects from the states.
   */
  void Import(const std::string& stateFileName, const std::string& blobFileName);

  /**
   * Removes all states whose corresponding objects no longer exist.
   */
  void PruneUnusedStates();

  /**
   * Removes all objects that are neither referenced by this manager or any other object.
   */
  void PruneUnusedObjects();

  static vtkTypeUInt32 ROOT() { return 0; }

  vtkGetSmartPointerMacro(Serializer, vtkSerializer);
  vtkGetSmartPointerMacro(Deserializer, vtkDeserializer);
  vtkGetSmartPointerMacro(Invoker, vtkInvoker);

  ///@{
  /**
   * Set/Get the log verbosity of messages that are emitted when data is uploaded to GPU memory.
   * The GetObjectManagerLogVerbosity looks up system environment for
   * `VTK_OBJECT_MANAGER_LOG_VERBOSITY` that shall be used to set initial logger verbosity. The
   * default value is TRACE.
   *
   * Accepted string values are OFF, ERROR, WARNING, INFO, TRACE, MAX, INVALID or ASCII
   * representation for an integer in the range [-9,9].
   *
   * @note This method internally uses vtkLogger::ConvertToVerbosity(const char*) to parse the
   * value from environment variable.
   */
  void SetObjectManagerLogVerbosity(vtkLogger::Verbosity verbosity);
  vtkLogger::Verbosity GetObjectManagerLogVerbosity();
  ///@}

protected:
  vtkObjectManager();
  ~vtkObjectManager() override;

  vtkSmartPointer<vtkMarshalContext> Context;
  vtkNew<vtkDeserializer> Deserializer;
  vtkNew<vtkSerializer> Serializer;
  vtkNew<vtkInvoker> Invoker;
  vtkLogger::Verbosity ObjectManagerLogVerbosity = vtkLogger::VERBOSITY_INVALID;

  static const char* OWNERSHIP_KEY() { return "manager"; }

private:
  vtkObjectManager(const vtkObjectManager&) = delete;
  void operator=(const vtkObjectManager&) = delete;
};
VTK_ABI_NAMESPACE_END
#endif

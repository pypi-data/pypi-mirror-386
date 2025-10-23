var __defProp = Object.defineProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// src/typespec/core/packages/rest/dist/src/index.js
var src_exports = {};
__export(src_exports, {
  $action: () => $action,
  $actionSegment: () => $actionSegment,
  $actionSeparator: () => $actionSeparator,
  $autoRoute: () => $autoRoute,
  $collectionAction: () => $collectionAction,
  $copyResourceKeyParameters: () => $copyResourceKeyParameters,
  $createsOrReplacesResource: () => $createsOrReplacesResource,
  $createsOrUpdatesResource: () => $createsOrUpdatesResource,
  $createsResource: () => $createsResource,
  $decorators: () => $decorators,
  $deletesResource: () => $deletesResource,
  $lib: () => $lib,
  $listsResource: () => $listsResource,
  $parentResource: () => $parentResource,
  $readsResource: () => $readsResource,
  $resource: () => $resource,
  $resourceLocation: () => $resourceLocation,
  $resourceTypeForKeyParam: () => $resourceTypeForKeyParam,
  $segment: () => $segment,
  $segmentOf: () => $segmentOf,
  $updatesResource: () => $updatesResource,
  getAction: () => getAction,
  getActionDetails: () => getActionDetails,
  getActionSegment: () => getActionSegment,
  getActionSeparator: () => getActionSeparator,
  getCollectionAction: () => getCollectionAction,
  getCollectionActionDetails: () => getCollectionActionDetails,
  getParentResource: () => getParentResource,
  getResourceLocationType: () => getResourceLocationType,
  getResourceOperation: () => getResourceOperation,
  getResourceTypeForKeyParam: () => getResourceTypeForKeyParam,
  getResourceTypeKey: () => getResourceTypeKey,
  getSegment: () => getSegment,
  isAutoRoute: () => isAutoRoute,
  isListOperation: () => isListOperation,
  setResourceOperation: () => setResourceOperation,
  setResourceTypeKey: () => setResourceTypeKey
});

// src/typespec/core/packages/rest/dist/src/lib.js
import { createTypeSpecLibrary, paramMessage } from "@typespec/compiler";
var $lib = createTypeSpecLibrary({
  name: "@typespec/rest",
  diagnostics: {
    "not-key-type": {
      severity: "error",
      messages: {
        default: "Cannot copy keys from a non-key type (KeysOf<T> or ParentKeysOf<T>)"
      }
    },
    "resource-missing-key": {
      severity: "error",
      messages: {
        default: paramMessage`Type '${"modelName"}' is used as a resource and therefore must have a key. Use @key to designate a property as the key.`
      }
    },
    "resource-missing-error": {
      severity: "error",
      messages: {
        default: paramMessage`Type '${"modelName"}' is used as an error and therefore must have the @error decorator applied.`
      }
    },
    "duplicate-key": {
      severity: "error",
      messages: {
        default: paramMessage`More than one key found on model type ${"resourceName"}`
      }
    },
    "duplicate-parent-key": {
      severity: "error",
      messages: {
        default: paramMessage`Resource type '${"resourceName"}' has a key property named '${"keyName"}' which conflicts with the key name of a parent or child resource.`
      }
    },
    "invalid-action-name": {
      severity: "error",
      messages: {
        default: "Action name cannot be empty string."
      }
    },
    "shared-route-unspecified-action-name": {
      severity: "error",
      messages: {
        default: paramMessage`An operation marked as '@sharedRoute' must have an explicit collection action name passed to '${"decoratorName"}'.`
      }
    }
  }
});
var { reportDiagnostic, createDiagnostic, createStateSymbol } = $lib;

// src/typespec/core/packages/rest/dist/src/resource.js
import { $invisible, $removeVisibility, $visibility, getKeyName, isErrorType, isKey, setTypeSpecNamespace } from "@typespec/compiler";
import { $path } from "@typespec/http";
var resourceKeysKey = createStateSymbol("resourceKeys");
var resourceTypeForKeyParamKey = createStateSymbol("resourceTypeForKeyParam");
function setResourceTypeKey(program, resourceType, keyProperty) {
  program.stateMap(resourceKeysKey).set(resourceType, {
    resourceType,
    keyProperty
  });
}
function getResourceTypeKey(program, resourceType) {
  let resourceKey = program.stateMap(resourceKeysKey).get(resourceType);
  if (resourceKey) {
    return resourceKey;
  }
  resourceType.properties.forEach((p) => {
    if (isKey(program, p)) {
      if (resourceKey) {
        reportDiagnostic(program, {
          code: "duplicate-key",
          format: {
            resourceName: resourceType.name
          },
          target: p
        });
      } else {
        resourceKey = {
          resourceType,
          keyProperty: p
        };
        setResourceTypeKey(program, resourceType, resourceKey.keyProperty);
      }
    }
  });
  if (resourceKey === void 0 && resourceType.baseModel !== void 0) {
    resourceKey = getResourceTypeKey(program, resourceType.baseModel);
    if (resourceKey !== void 0) {
      setResourceTypeKey(program, resourceType, resourceKey.keyProperty);
    }
  }
  return resourceKey;
}
function $resourceTypeForKeyParam(context, entity, resourceType) {
  context.program.stateMap(resourceTypeForKeyParamKey).set(entity, resourceType);
}
setTypeSpecNamespace("Private", $resourceTypeForKeyParam);
function getResourceTypeForKeyParam(program, param) {
  return program.stateMap(resourceTypeForKeyParamKey).get(param);
}
var VISIBILITY_DECORATORS = [$visibility, $invisible, $removeVisibility];
function cloneKeyProperties(context, target, resourceType) {
  const { program } = context;
  const parentType = getParentResource(program, resourceType);
  if (parentType) {
    cloneKeyProperties(context, target, parentType);
  }
  const resourceKey = getResourceTypeKey(program, resourceType);
  if (resourceKey) {
    const { keyProperty } = resourceKey;
    const keyName = getKeyName(program, keyProperty);
    const decorators = [
      // Filter out all visibility decorators because they affect metadata
      // filtering. NOTE: Check for name equality instead of function equality
      // to deal with multiple copies of core being used.
      ...keyProperty.decorators.filter((d) => VISIBILITY_DECORATORS.every((visDec) => d.decorator.name !== visDec.name)),
      {
        decorator: $resourceTypeForKeyParam,
        args: [{ node: target.node, value: resourceType, jsValue: resourceType }]
      }
    ];
    if (!keyProperty.decorators.some((d) => d.decorator.name === $path.name)) {
      decorators.push({
        decorator: $path,
        args: []
      });
    }
    const newProp = program.checker.cloneType(keyProperty, {
      name: keyName,
      decorators,
      optional: false,
      model: target,
      sourceProperty: void 0
    });
    target.properties.set(keyName, newProp);
  }
}
function $copyResourceKeyParameters(context, entity, filter) {
  const reportNoKeyError = () => reportDiagnostic(context.program, {
    code: "not-key-type",
    target: entity
  });
  const templateArguments = entity.templateMapper?.args;
  if (!templateArguments || templateArguments.length !== 1) {
    return reportNoKeyError();
  }
  if (templateArguments[0].kind !== "Model") {
    if (isErrorType(templateArguments[0])) {
      return;
    }
    return reportNoKeyError();
  }
  const resourceType = templateArguments[0];
  if (filter === "parent") {
    const parentType = getParentResource(context.program, resourceType);
    if (parentType) {
      cloneKeyProperties(context, entity, parentType);
    }
  } else {
    cloneKeyProperties(context, entity, resourceType);
  }
}
var parentResourceTypesKey = createStateSymbol("parentResourceTypes");
function getParentResource(program, resourceType) {
  return program.stateMap(parentResourceTypesKey).get(resourceType);
}
var $parentResource = (context, entity, parentType) => {
  const { program } = context;
  program.stateMap(parentResourceTypesKey).set(entity, parentType);
};

// src/typespec/core/packages/rest/dist/src/rest.js
import { createDiagnosticCollector, setTypeSpecNamespace as setTypeSpecNamespace2 } from "@typespec/compiler";
import { addQueryParamsToUriTemplate, getOperationParameters, getOperationVerb, getRoutePath, getUriTemplatePathParam, joinPathSegments } from "@typespec/http";
import { unsafe_DefaultRouteProducer as DefaultRouteProducer, unsafe_getRouteProducer as getRouteProducer, unsafe_setRouteProducer as setRouteProducer } from "@typespec/http/experimental";
function addActionFragment(program, target, pathFragments) {
  const defaultSeparator = "/";
  const actionSegment = getActionSegment(program, target);
  if (actionSegment && actionSegment !== "") {
    const actionSeparator = getActionSeparator(program, target) ?? defaultSeparator;
    pathFragments.push(`${actionSeparator}${actionSegment}`);
  }
}
function addSegmentFragment(program, target, pathFragments) {
  const segment = getSegment(program, target);
  if (segment && segment !== "") {
    pathFragments.push(`/${segment}`);
  }
}
var resourceOperationToVerb = {
  read: "get",
  create: "post",
  createOrUpdate: "patch",
  createOrReplace: "put",
  update: "patch",
  delete: "delete",
  list: "get"
};
function getResourceOperationHttpVerb(program, operation) {
  const resourceOperation = getResourceOperation(program, operation);
  return getOperationVerb(program, operation) ?? (resourceOperation && resourceOperationToVerb[resourceOperation.operation]) ?? (getActionDetails(program, operation) || getCollectionActionDetails(program, operation) ? "post" : void 0);
}
function autoRouteProducer(program, operation, parentSegments, overloadBase, options) {
  const diagnostics = createDiagnosticCollector();
  const routePath = getRoutePath(program, operation)?.path;
  const segments = [...parentSegments, ...routePath ? [routePath] : []];
  const filteredParameters = [];
  const filteredParamProperties = /* @__PURE__ */ new Set();
  const paramOptions = {
    ...options?.paramOptions ?? {},
    verbSelector: getResourceOperationHttpVerb
  };
  const parameters = diagnostics.pipe(getOperationParameters(program, operation, "", void 0, paramOptions));
  for (const httpParam of parameters.parameters) {
    const { type, param } = httpParam;
    if (type === "path") {
      addSegmentFragment(program, param, segments);
      const filteredParam = options.autoRouteOptions?.routeParamFilter?.(operation, param);
      if (filteredParam?.routeParamString) {
        segments.push(`/${filteredParam.routeParamString}`);
        if (filteredParam?.excludeFromOperationParams === true) {
          continue;
        }
      } else {
        if (param.type.kind === "String") {
          segments.push(`${param.type.value}`);
          continue;
        } else {
          segments.push(`${getUriTemplatePathParam(httpParam)}`);
        }
      }
    }
    filteredParameters.push(httpParam);
    filteredParamProperties.add(httpParam.param);
  }
  parameters.parameters = filteredParameters;
  for (let i = parameters.properties.length - 1; i >= 0; i--) {
    const httpProp = parameters.properties[i];
    if (!["header", "query", "path", "cookie"].includes(httpProp.kind)) {
      continue;
    }
    if (!filteredParamProperties.has(httpProp.property)) {
      parameters.properties.splice(i, 1);
    }
  }
  addSegmentFragment(program, operation, segments);
  addActionFragment(program, operation, segments);
  const pathPart = joinPathSegments(segments);
  return diagnostics.wrap({
    uriTemplate: addQueryParamsToUriTemplate(pathPart, filteredParameters),
    parameters: {
      ...parameters,
      parameters: filteredParameters
    }
  });
}
var autoRouteKey = createStateSymbol("autoRoute");
var $autoRoute = (context, entity) => {
  if (entity.kind === "Operation") {
    setRouteProducer(context.program, entity, autoRouteProducer);
  } else {
    for (const [_, op] of entity.operations) {
      context.call($autoRoute, op);
      op.decorators.push({
        decorator: $autoRoute,
        args: []
      });
    }
  }
  context.program.stateSet(autoRouteKey).add(entity);
};
function isAutoRoute(program, entity) {
  return program.stateSet(autoRouteKey).has(entity);
}
var segmentsKey = createStateSymbol("segments");
function $segment(context, entity, name) {
  context.program.stateMap(segmentsKey).set(entity, name);
}
function getResourceSegment(program, resourceType) {
  const resourceKey = getResourceTypeKey(program, resourceType);
  return resourceKey ? getSegment(program, resourceKey.keyProperty) : getSegment(program, resourceType);
}
var $segmentOf = (context, entity, resourceType) => {
  if (resourceType.kind === "TemplateParameter") {
    return;
  }
  const segment = getResourceSegment(context.program, resourceType);
  if (segment) {
    context.call($segment, entity, segment);
  }
};
function getSegment(program, entity) {
  return program.stateMap(segmentsKey).get(entity);
}
var actionSeparatorKey = createStateSymbol("actionSeparator");
function $actionSeparator(context, entity, separator) {
  context.program.stateMap(actionSeparatorKey).set(entity, separator);
}
function getActionSeparator(program, entity) {
  return program.stateMap(actionSeparatorKey).get(entity);
}
var $resource = (context, entity, collectionName) => {
  const key = getResourceTypeKey(context.program, entity);
  if (!key) {
    reportDiagnostic(context.program, {
      code: "resource-missing-key",
      format: {
        modelName: entity.name
      },
      target: entity
    });
    return;
  }
  context.call($segment, key.keyProperty, collectionName);
  key.keyProperty.decorators.push({
    decorator: $segment,
    args: [
      { value: context.program.checker.createLiteralType(collectionName), jsValue: collectionName }
    ]
  });
};
var resourceOperationsKey = createStateSymbol("resourceOperations");
function resourceRouteProducer(program, operation, parentSegments, overloadBase, options) {
  const paramOptions = {
    ...options?.paramOptions ?? {},
    verbSelector: getResourceOperationHttpVerb
  };
  return DefaultRouteProducer(program, operation, parentSegments, overloadBase, {
    ...options,
    paramOptions
  });
}
function setResourceOperation(context, entity, resourceType, operation) {
  if (resourceType.kind === "TemplateParameter") {
    return;
  }
  context.program.stateMap(resourceOperationsKey).set(entity, {
    operation,
    resourceType
  });
  if (!getRouteProducer(context.program, entity)) {
    setRouteProducer(context.program, entity, resourceRouteProducer);
  }
}
function getResourceOperation(program, typespecOperation) {
  return program.stateMap(resourceOperationsKey).get(typespecOperation);
}
var $readsResource = (context, entity, resourceType) => {
  setResourceOperation(context, entity, resourceType, "read");
};
function $createsResource(context, entity, resourceType) {
  context.call($segmentOf, entity, resourceType);
  setResourceOperation(context, entity, resourceType, "create");
}
function $createsOrReplacesResource(context, entity, resourceType) {
  setResourceOperation(context, entity, resourceType, "createOrReplace");
}
function $createsOrUpdatesResource(context, entity, resourceType) {
  setResourceOperation(context, entity, resourceType, "createOrUpdate");
}
function $updatesResource(context, entity, resourceType) {
  setResourceOperation(context, entity, resourceType, "update");
}
function $deletesResource(context, entity, resourceType) {
  setResourceOperation(context, entity, resourceType, "delete");
}
var $listsResource = (context, entity, resourceType) => {
  context.call($segmentOf, entity, resourceType);
  setResourceOperation(context, entity, resourceType, "list");
};
function isListOperation(program, target) {
  return getResourceOperation(program, target)?.operation === "list";
}
function lowerCaseFirstChar(str) {
  return str[0].toLocaleLowerCase() + str.substring(1);
}
function makeActionName(op, name) {
  return {
    name: lowerCaseFirstChar(name || op.name),
    kind: name ? "specified" : "automatic"
  };
}
var actionsSegmentKey = createStateSymbol("actionSegment");
var $actionSegment = (context, entity, name) => {
  context.program.stateMap(actionsSegmentKey).set(entity, name);
};
function getActionSegment(program, entity) {
  return program.stateMap(actionsSegmentKey).get(entity);
}
var actionsKey = createStateSymbol("actions");
var $action = (context, entity, name) => {
  if (name === "") {
    reportDiagnostic(context.program, {
      code: "invalid-action-name",
      target: entity
    });
    return;
  }
  const action = makeActionName(entity, name);
  context.call($actionSegment, entity, action.name);
  context.program.stateMap(actionsKey).set(entity, action);
};
function getActionDetails(program, operation) {
  return program.stateMap(actionsKey).get(operation);
}
function getAction(program, operation) {
  return getActionDetails(program, operation)?.name;
}
var collectionActionsKey = createStateSymbol("collectionActions");
var $collectionAction = (context, entity, resourceType, name) => {
  if (resourceType.kind === "TemplateParameter") {
    return;
  }
  const segment = getResourceSegment(context.program, resourceType);
  if (segment) {
    context.call($segment, entity, segment);
  }
  const action = makeActionName(entity, name);
  context.call($actionSegment, entity, action.name);
  action.name = `${segment}/${action.name}`;
  context.program.stateMap(collectionActionsKey).set(entity, action);
};
function getCollectionActionDetails(program, operation) {
  return program.stateMap(collectionActionsKey).get(operation);
}
function getCollectionAction(program, operation) {
  return getCollectionActionDetails(program, operation)?.name;
}
var resourceLocationsKey = createStateSymbol("resourceLocations");
var $resourceLocation = (context, entity, resourceType) => {
  if (resourceType.kind === "TemplateParameter") {
    return;
  }
  context.program.stateMap(resourceLocationsKey).set(entity, resourceType);
};
function getResourceLocationType(program, entity) {
  return program.stateMap(resourceLocationsKey).get(entity);
}
setTypeSpecNamespace2("Private", $resourceLocation, $actionSegment, getActionSegment);

// src/typespec/core/packages/rest/dist/src/tsp-index.js
var tsp_index_exports = {};
__export(tsp_index_exports, {
  $decorators: () => $decorators,
  $lib: () => $lib,
  $onValidate: () => $onValidate
});

// src/typespec/core/packages/rest/dist/src/validate.js
import { getKeyName as getKeyName2, getTypeName, listServices, navigateTypesInNamespace } from "@typespec/compiler";
import { DuplicateTracker } from "@typespec/compiler/utils";
import { isSharedRoute } from "@typespec/http";
function checkForDuplicateResourceKeyNames(program) {
  const seenTypes = /* @__PURE__ */ new Set();
  function checkResourceModelKeys(model) {
    if (model.name === "") {
      return;
    }
    let currentType = model;
    const keyProperties = new DuplicateTracker();
    while (currentType) {
      const resourceKey = getResourceTypeKey(program, currentType);
      if (resourceKey) {
        const keyName = getKeyName2(program, resourceKey.keyProperty);
        keyProperties.track(keyName, resourceKey);
      }
      currentType = getParentResource(program, currentType);
    }
    for (const [keyName, dupes] of keyProperties.entries()) {
      for (const key of dupes) {
        const fullName = `${getTypeName(key.resourceType)}.${keyName}`;
        if (!seenTypes.has(fullName)) {
          seenTypes.add(fullName);
          reportDiagnostic(program, {
            code: "duplicate-parent-key",
            format: {
              resourceName: key.resourceType.name,
              keyName
            },
            target: key.keyProperty
          });
        }
      }
    }
  }
  for (const service of listServices(program)) {
    navigateTypesInNamespace(service.type, {
      model: (model) => checkResourceModelKeys(model)
    });
  }
}
function checkForSharedRouteUnnamedActions(program) {
  for (const service of listServices(program)) {
    navigateTypesInNamespace(service.type, {
      operation: (op) => {
        const actionDetails = getActionDetails(program, op);
        if (isSharedRoute(program, op) && (actionDetails?.kind === "automatic" || getCollectionActionDetails(program, op)?.kind === "automatic")) {
          reportDiagnostic(program, {
            code: "shared-route-unspecified-action-name",
            target: op,
            format: {
              decoratorName: actionDetails ? "@action" : "@collectionAction"
            }
          });
        }
      }
    });
  }
}
function $onValidate(program) {
  checkForDuplicateResourceKeyNames(program);
  checkForSharedRouteUnnamedActions(program);
}

// src/typespec/core/packages/rest/dist/src/tsp-index.js
var $decorators = {
  "TypeSpec.Rest": {
    autoRoute: $autoRoute,
    segment: $segment,
    segmentOf: $segmentOf,
    actionSeparator: $actionSeparator,
    resource: $resource,
    parentResource: $parentResource,
    readsResource: $readsResource,
    createsResource: $createsResource,
    createsOrReplacesResource: $createsOrReplacesResource,
    createsOrUpdatesResource: $createsOrUpdatesResource,
    updatesResource: $updatesResource,
    deletesResource: $deletesResource,
    listsResource: $listsResource,
    action: $action,
    collectionAction: $collectionAction,
    copyResourceKeyParameters: $copyResourceKeyParameters
  }
};

// src/typespec/core/packages/rest/dist/src/internal-decorators.js
var internal_decorators_exports = {};
__export(internal_decorators_exports, {
  $decorators: () => $decorators2,
  namespace: () => namespace
});
import { getTypeName as getTypeName2, isErrorModel } from "@typespec/compiler";
var namespace = "TypeSpec.Rest.Private";
var validatedMissingKey = createStateSymbol("validatedMissing");
var $validateHasKey = (context, target, value) => {
  if (context.program.stateSet(validatedMissingKey).has(value)) {
    return;
  }
  const resourceKey = value.kind === "Model" && getResourceTypeKey(context.program, value);
  if (resourceKey === void 0) {
    reportDiagnostic(context.program, {
      code: "resource-missing-key",
      format: { modelName: getTypeName2(value) },
      target: value
    });
    context.program.stateSet(validatedMissingKey).add(value);
  }
};
var validatedErrorKey = createStateSymbol("validatedError");
var $validateIsError = (context, target, value) => {
  if (context.program.stateSet(validatedErrorKey).has(value)) {
    return;
  }
  const isError = value.kind === "Model" && isErrorModel(context.program, value);
  if (!isError) {
    reportDiagnostic(context.program, {
      code: "resource-missing-error",
      format: { modelName: getTypeName2(value) },
      target: value
    });
    context.program.stateSet(validatedErrorKey).add(value);
  }
};
var $decorators2 = {
  "TypeSpec.Rest.Private": {
    actionSegment: $actionSegment,
    resourceLocation: $resourceLocation,
    resourceTypeForKeyParam: $resourceTypeForKeyParam,
    validateHasKey: $validateHasKey,
    validateIsError: $validateIsError
  }
};

// virtual:virtual:entry.js
var TypeSpecJSSources = {
  "dist/src/index.js": src_exports,
  "dist/src/internal-decorators.js": internal_decorators_exports,
  "dist/src/tsp-index.js": tsp_index_exports
};
var TypeSpecSources = {
  "package.json": '{"name":"@typespec/rest","version":"0.74.0","author":"Microsoft Corporation","description":"TypeSpec REST protocol binding","homepage":"https://typespec.io","readme":"https://github.com/microsoft/typespec/blob/main/README.md","license":"MIT","repository":{"type":"git","url":"git+https://github.com/microsoft/typespec.git"},"bugs":{"url":"https://github.com/microsoft/typespec/issues"},"keywords":["typespec"],"type":"module","main":"dist/src/index.js","tspMain":"lib/rest.tsp","exports":{".":{"typespec":"./lib/rest.tsp","types":"./dist/src/index.d.ts","default":"./dist/src/index.js"},"./testing":{"types":"./dist/src/testing/index.d.ts","default":"./dist/src/testing/index.js"}},"engines":{"node":">=20.0.0"},"scripts":{"clean":"rimraf ./dist ./temp","build":"pnpm gen-extern-signature && tsc -p . && pnpm lint-typespec-library","watch":"tsc -p . --watch","gen-extern-signature":"tspd --enable-experimental gen-extern-signature .","lint-typespec-library":"tsp compile . --warn-as-error --import @typespec/library-linter --no-emit","test":"vitest run","test:watch":"vitest --watch","test:ui":"vitest --ui","test:ci":"vitest run --coverage --reporter=junit --reporter=default","lint":"eslint . --max-warnings=0","lint:fix":"eslint . --fix","regen-docs":"tspd doc .  --enable-experimental --llmstxt --output-dir ../../website/src/content/docs/docs/libraries/rest/reference"},"files":["lib/*.tsp","dist/**","!dist/test/**"],"peerDependencies":{"@typespec/compiler":"workspace:^","@typespec/http":"workspace:^"},"devDependencies":{"@types/node":"~24.3.0","@typespec/compiler":"workspace:^","@typespec/http":"workspace:^","@typespec/library-linter":"workspace:^","@typespec/tspd":"workspace:^","@vitest/coverage-v8":"^3.1.2","@vitest/ui":"^3.1.2","c8":"^10.1.3","rimraf":"~6.0.1","typescript":"~5.9.2","vitest":"^3.1.2"}}',
  "../compiler/lib/intrinsics.tsp": 'import "../dist/src/lib/intrinsic/tsp-index.js";\nimport "./prototypes.tsp";\n\n// This file contains all the intrinsic types of typespec. Everything here will always be loaded\nnamespace TypeSpec;\n\n/**\n * Represent a byte array\n */\nscalar bytes;\n\n/**\n * A numeric type\n */\nscalar numeric;\n\n/**\n * A whole number. This represent any `integer` value possible.\n * It is commonly represented as `BigInteger` in some languages.\n */\nscalar integer extends numeric;\n\n/**\n * A number with decimal value\n */\nscalar float extends numeric;\n\n/**\n * A 64-bit integer. (`-9,223,372,036,854,775,808` to `9,223,372,036,854,775,807`)\n */\nscalar int64 extends integer;\n\n/**\n * A 32-bit integer. (`-2,147,483,648` to `2,147,483,647`)\n */\nscalar int32 extends int64;\n\n/**\n * A 16-bit integer. (`-32,768` to `32,767`)\n */\nscalar int16 extends int32;\n\n/**\n * A 8-bit integer. (`-128` to `127`)\n */\nscalar int8 extends int16;\n\n/**\n * A 64-bit unsigned integer (`0` to `18,446,744,073,709,551,615`)\n */\nscalar uint64 extends integer;\n\n/**\n * A 32-bit unsigned integer (`0` to `4,294,967,295`)\n */\nscalar uint32 extends uint64;\n\n/**\n * A 16-bit unsigned integer (`0` to `65,535`)\n */\nscalar uint16 extends uint32;\n\n/**\n * A 8-bit unsigned integer (`0` to `255`)\n */\nscalar uint8 extends uint16;\n\n/**\n * An integer that can be serialized to JSON (`\u22129007199254740991 (\u2212(2^53 \u2212 1))` to `9007199254740991 (2^53 \u2212 1)` )\n */\nscalar safeint extends int64;\n\n/**\n * A 64 bit floating point number. (`\xB15.0 \xD7 10^\u2212324` to `\xB11.7 \xD7 10^308`)\n */\nscalar float64 extends float;\n\n/**\n * A 32 bit floating point number. (`\xB11.5 x 10^\u221245` to `\xB13.4 x 10^38`)\n */\nscalar float32 extends float64;\n\n/**\n * A decimal number with any length and precision. This represent any `decimal` value possible.\n * It is commonly represented as `BigDecimal` in some languages.\n */\nscalar decimal extends numeric;\n\n/**\n * A 128-bit decimal number.\n */\nscalar decimal128 extends decimal;\n\n/**\n * A sequence of textual characters.\n */\nscalar string;\n\n/**\n * A date on a calendar without a time zone, e.g. "April 10th"\n */\nscalar plainDate {\n  /**\n   * Create a plain date from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const date = plainDate.fromISO("2024-05-06");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * A time on a clock without a time zone, e.g. "3:00 am"\n */\nscalar plainTime {\n  /**\n   * Create a plain time from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const time = plainTime.fromISO("12:34");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * An instant in coordinated universal time (UTC)"\n */\nscalar utcDateTime {\n  /**\n   * Create a date from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const time = utcDateTime.fromISO("2024-05-06T12:20-12Z");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * A date and time in a particular time zone, e.g. "April 10th at 3:00am in PST"\n */\nscalar offsetDateTime {\n  /**\n   * Create a date from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const time = offsetDateTime.fromISO("2024-05-06T12:20-12-0700");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * A duration/time period. e.g 5s, 10h\n */\nscalar duration {\n  /**\n   * Create a duration from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const time = duration.fromISO("P1Y1D");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * Boolean with `true` and `false` values.\n */\nscalar boolean;\n\n/**\n * @dev Array model type, equivalent to `Element[]`\n * @template Element The type of the array elements\n */\n@indexer(integer, Element)\nmodel Array<Element> {}\n\n/**\n * @dev Model with string properties where all the properties have type `Property`\n * @template Element The type of the properties\n */\n@indexer(string, Element)\nmodel Record<Element> {}\n',
  "../compiler/lib/prototypes.tsp": "namespace TypeSpec.Prototypes;\n\nextern dec getter(target: unknown);\n\nnamespace Types {\n  interface ModelProperty {\n    @getter type(): unknown;\n  }\n\n  interface Operation {\n    @getter returnType(): unknown;\n    @getter parameters(): unknown;\n  }\n\n  interface Array<TElementType> {\n    @getter elementType(): TElementType;\n  }\n}\n",
  "../compiler/lib/std/main.tsp": '// TypeSpec standard library. Everything in here can be omitted by using `--nostdlib` cli flag or `nostdlib` in the config.\nimport "./types.tsp";\nimport "./decorators.tsp";\nimport "./reflection.tsp";\nimport "./visibility.tsp";\n',
  "../compiler/lib/std/types.tsp": 'namespace TypeSpec;\n\n/**\n * Represent a 32-bit unix timestamp datetime with 1s of granularity.\n * It measures time by the number of seconds that have elapsed since 00:00:00 UTC on 1 January 1970.\n */\n@encode("unixTimestamp", int32)\nscalar unixTimestamp32 extends utcDateTime;\n\n/**\n * Represent a URL string as described by https://url.spec.whatwg.org/\n */\nscalar url extends string;\n\n/**\n * Represents a collection of optional properties.\n *\n * @template Source An object whose spread properties are all optional.\n */\n@doc("The template for adding optional properties.")\n@withOptionalProperties\nmodel OptionalProperties<Source> {\n  ...Source;\n}\n\n/**\n * Represents a collection of updateable properties.\n *\n * @template Source An object whose spread properties are all updateable.\n */\n@doc("The template for adding updateable properties.")\n@withUpdateableProperties\nmodel UpdateableProperties<Source> {\n  ...Source;\n}\n\n/**\n * Represents a collection of omitted properties.\n *\n * @template Source An object whose properties are spread.\n * @template Keys The property keys to omit.\n */\n@doc("The template for omitting properties.")\n@withoutOmittedProperties(Keys)\nmodel OmitProperties<Source, Keys extends string> {\n  ...Source;\n}\n\n/**\n * Represents a collection of properties with only the specified keys included.\n *\n * @template Source An object whose properties are spread.\n * @template Keys The property keys to include.\n */\n@doc("The template for picking properties.")\n@withPickedProperties(Keys)\nmodel PickProperties<Source, Keys extends string> {\n  ...Source;\n}\n\n/**\n * Represents a collection of properties with default values omitted.\n *\n * @template Source An object whose spread property defaults are all omitted.\n */\n@withoutDefaultValues\nmodel OmitDefaults<Source> {\n  ...Source;\n}\n\n/**\n * Applies a visibility setting to a collection of properties.\n *\n * @template Source An object whose properties are spread.\n * @template Visibility The visibility to apply to all properties.\n */\n@doc("The template for setting the default visibility of key properties.")\n@withDefaultKeyVisibility(Visibility)\nmodel DefaultKeyVisibility<Source, Visibility extends valueof Reflection.EnumMember> {\n  ...Source;\n}\n',
  "../compiler/lib/std/decorators.tsp": 'import "../../dist/src/lib/tsp-index.js";\n\nusing TypeSpec.Reflection;\n\nnamespace TypeSpec;\n\n/**\n * Typically a short, single-line description.\n * @param summary Summary string.\n *\n * @example\n * ```typespec\n * @summary("This is a pet")\n * model Pet {}\n * ```\n */\nextern dec summary(target: unknown, summary: valueof string);\n\n/**\n * Attach a documentation string. Content support CommonMark markdown formatting.\n * @param doc Documentation string\n * @param formatArgs Record with key value pair that can be interpolated in the doc.\n *\n * @example\n * ```typespec\n * @doc("Represent a Pet available in the PetStore")\n * model Pet {}\n * ```\n */\nextern dec doc(target: unknown, doc: valueof string, formatArgs?: {});\n\n/**\n * Attach a documentation string to describe the successful return types of an operation.\n * If an operation returns a union of success and errors it only describes the success. See `@errorsDoc` for error documentation.\n * @param doc Documentation string\n *\n * @example\n * ```typespec\n * @returnsDoc("Returns doc")\n * op get(): Pet | NotFound;\n * ```\n */\nextern dec returnsDoc(target: Operation, doc: valueof string);\n\n/**\n * Attach a documentation string to describe the error return types of an operation.\n * If an operation returns a union of success and errors it only describes the errors. See `@returnsDoc` for success documentation.\n * @param doc Documentation string\n *\n * @example\n * ```typespec\n * @errorsDoc("Errors doc")\n * op get(): Pet | NotFound;\n * ```\n */\nextern dec errorsDoc(target: Operation, doc: valueof string);\n\n/**\n * Service options.\n */\nmodel ServiceOptions {\n  /**\n   * Title of the service.\n   */\n  title?: string;\n}\n\n/**\n * Mark this namespace as describing a service and configure service properties.\n * @param options Optional configuration for the service.\n *\n * @example\n * ```typespec\n * @service\n * namespace PetStore;\n * ```\n *\n * @example Setting service title\n * ```typespec\n * @service(#{title: "Pet store"})\n * namespace PetStore;\n * ```\n */\nextern dec service(target: Namespace, options?: valueof ServiceOptions);\n\n/**\n * Specify that this model is an error type. Operations return error types when the operation has failed.\n *\n * @example\n * ```typespec\n * @error\n * model PetStoreError {\n *   code: string;\n *   message: string;\n * }\n * ```\n */\nextern dec error(target: Model);\n\n/**\n * Applies a media type hint to a TypeSpec type. Emitters and libraries may choose to use this hint to determine how a\n * type should be serialized. For example, the `@typespec/http` library will use the media type hint of the response\n * body type as a default `Content-Type` if one is not explicitly specified in the operation.\n *\n * Media types (also known as MIME types) are defined by RFC 6838. The media type hint should be a valid media type\n * string as defined by the RFC, but the decorator does not enforce or validate this constraint.\n *\n * Notes: the applied media type is _only_ a hint. It may be overridden or not used at all. Media type hints are\n * inherited by subtypes. If a media type hint is applied to a model, it will be inherited by all other models that\n * `extend` it unless they delcare their own media type hint.\n *\n * @param mediaType The media type hint to apply to the target type.\n *\n * @example create a model that serializes as XML by default\n *\n * ```tsp\n * @mediaTypeHint("application/xml")\n * model Example {\n *   @visibility(Lifecycle.Read)\n *   id: string;\n *\n *   name: string;\n * }\n * ```\n */\nextern dec mediaTypeHint(target: Model | Scalar | Enum | Union, mediaType: valueof string);\n\n// Cannot apply this to the scalar itself. Needs to be applied here so that we don\'t crash nostdlib scenarios\n@@mediaTypeHint(TypeSpec.bytes, "application/octet-stream");\n\n// @@mediaTypeHint(TypeSpec.string "text/plain") -- This is hardcoded in the compiler to avoid circularity\n// between the initialization of the string scalar and the `valueof string` required to call the\n// `mediaTypeHint` decorator.\n\n/**\n * Specify a known data format hint for this string type. For example `uuid`, `uri`, etc.\n * This differs from the `@pattern` decorator which is meant to specify a regular expression while `@format` accepts a known format name.\n * The format names are open ended and are left to emitter to interpret.\n *\n * @param format format name.\n *\n * @example\n * ```typespec\n * @format("uuid")\n * scalar uuid extends string;\n * ```\n */\nextern dec format(target: string | ModelProperty, format: valueof string);\n\n/**\n * Specify the the pattern this string should respect using simple regular expression syntax.\n * The following syntax is allowed: alternations (`|`), quantifiers (`?`, `*`, `+`, and `{ }`), wildcard (`.`), and grouping parentheses.\n * Advanced features like look-around, capture groups, and references are not supported.\n *\n * This decorator may optionally provide a custom validation _message_. Emitters may choose to use the message to provide\n * context when pattern validation fails. For the sake of consistency, the message should be a phrase that describes in\n * plain language what sort of content the pattern attempts to validate. For example, a complex regular expression that\n * validates a GUID string might have a message like "Must be a valid GUID."\n *\n * @param pattern Regular expression.\n * @param validationMessage Optional validation message that may provide context when validation fails.\n *\n * @example\n * ```typespec\n * @pattern("[a-z]+", "Must be a string consisting of only lower case letters and of at least one character.")\n * scalar LowerAlpha extends string;\n * ```\n */\nextern dec pattern(\n  target: string | bytes | ModelProperty,\n  pattern: valueof string,\n  validationMessage?: valueof string\n);\n\n/**\n * Specify the minimum length this string type should be.\n * @param value Minimum length\n *\n * @example\n * ```typespec\n * @minLength(2)\n * scalar Username extends string;\n * ```\n */\nextern dec minLength(target: string | ModelProperty, value: valueof integer);\n\n/**\n * Specify the maximum length this string type should be.\n * @param value Maximum length\n *\n * @example\n * ```typespec\n * @maxLength(20)\n * scalar Username extends string;\n * ```\n */\nextern dec maxLength(target: string | ModelProperty, value: valueof integer);\n\n/**\n * Specify the minimum number of items this array should have.\n * @param value Minimum number\n *\n * @example\n * ```typespec\n * @minItems(1)\n * model Endpoints is string[];\n * ```\n */\nextern dec minItems(target: unknown[] | ModelProperty, value: valueof integer);\n\n/**\n * Specify the maximum number of items this array should have.\n * @param value Maximum number\n *\n * @example\n * ```typespec\n * @maxItems(5)\n * model Endpoints is string[];\n * ```\n */\nextern dec maxItems(target: unknown[] | ModelProperty, value: valueof integer);\n\n/**\n * Specify the minimum value this numeric type should be.\n * @param value Minimum value\n *\n * @example\n * ```typespec\n * @minValue(18)\n * scalar Age is int32;\n * ```\n */\nextern dec minValue(target: numeric | ModelProperty, value: valueof numeric);\n\n/**\n * Specify the maximum value this numeric type should be.\n * @param value Maximum value\n *\n * @example\n * ```typespec\n * @maxValue(200)\n * scalar Age is int32;\n * ```\n */\nextern dec maxValue(target: numeric | ModelProperty, value: valueof numeric);\n\n/**\n * Specify the minimum value this numeric type should be, exclusive of the given\n * value.\n * @param value Minimum value\n *\n * @example\n * ```typespec\n * @minValueExclusive(0)\n * scalar distance is float64;\n * ```\n */\nextern dec minValueExclusive(target: numeric | ModelProperty, value: valueof numeric);\n\n/**\n * Specify the maximum value this numeric type should be, exclusive of the given\n * value.\n * @param value Maximum value\n *\n * @example\n * ```typespec\n * @maxValueExclusive(50)\n * scalar distance is float64;\n * ```\n */\nextern dec maxValueExclusive(target: numeric | ModelProperty, value: valueof numeric);\n\n/**\n * Mark this string as a secret value that should be treated carefully to avoid exposure\n *\n * @example\n * ```typespec\n * @secret\n * scalar Password is string;\n * ```\n */\nextern dec secret(target: string | ModelProperty);\n\n/**\n * Attaches a tag to an operation, interface, or namespace. Multiple `@tag` decorators can be specified to attach multiple tags to a TypeSpec element.\n * @param tag Tag value\n */\nextern dec tag(target: Namespace | Interface | Operation, tag: valueof string);\n\n/**\n * Specifies how a templated type should name their instances.\n * @param name name the template instance should take\n * @param formatArgs Model with key value used to interpolate the name\n *\n * @example\n * ```typespec\n * @friendlyName("{name}List", T)\n * model List<Item> {\n *   value: Item[];\n *   nextLink: string;\n * }\n * ```\n */\nextern dec friendlyName(target: unknown, name: valueof string, formatArgs?: unknown);\n\n/**\n * Mark a model property as the key to identify instances of that type\n * @param altName Name of the property. If not specified, the decorated property name is used.\n *\n * @example\n * ```typespec\n * model Pet {\n *   @key id: string;\n * }\n * ```\n */\nextern dec key(target: ModelProperty, altName?: valueof string);\n\n/**\n * Specify this operation is an overload of the given operation.\n * @param overloadbase Base operation that should be a union of all overloads\n *\n * @example\n * ```typespec\n * op upload(data: string | bytes, @header contentType: "text/plain" | "application/octet-stream"): void;\n * @overload(upload)\n * op uploadString(data: string, @header contentType: "text/plain" ): void;\n * @overload(upload)\n * op uploadBytes(data: bytes, @header contentType: "application/octet-stream"): void;\n * ```\n */\nextern dec overload(target: Operation, overloadbase: Operation);\n\n/**\n * Provide an alternative name for this type when serialized to the given mime type.\n * @param mimeType Mime type this should apply to. The mime type should be a known mime type as described here https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types without any suffix (e.g. `+json`)\n * @param name Alternative name\n *\n * @example\n *\n * ```typespec\n * model Certificate {\n *   @encodedName("application/json", "exp")\n *   @encodedName("application/xml", "expiry")\n *   expireAt: int32;\n * }\n * ```\n *\n * @example Invalid values\n *\n * ```typespec\n * @encodedName("application/merge-patch+json", "exp")\n *              ^ error cannot use subtype\n * ```\n */\nextern dec encodedName(target: unknown, mimeType: valueof string, name: valueof string);\n\n/**\n * Options for `@discriminated` decorator.\n */\nmodel DiscriminatedOptions {\n  /**\n   * How is the discriminated union serialized.\n   * @default object\n   */\n  envelope?: "object" | "none";\n\n  /** Name of the discriminator property */\n  discriminatorPropertyName?: string;\n\n  /** Name of the property envelopping the data */\n  envelopePropertyName?: string;\n}\n\n/**\n * Specify that this union is discriminated.\n * @param options Options to configure the serialization of the discriminated union.\n *\n * @example\n *\n * ```typespec\n * @discriminated\n * union Pet{ cat: Cat, dog: Dog }\n *\n * model Cat { name: string, meow: boolean }\n * model Dog { name: string, bark: boolean }\n * ```\n * Serialized as:\n * ```json\n * {\n *   "kind": "cat",\n *   "value": {\n *     "name": "Whiskers",\n *     "meow": true\n *   }\n * },\n * {\n *   "kind": "dog",\n *   "value": {\n *     "name": "Rex",\n *     "bark": false\n *   }\n * }\n * ```\n *\n * @example Custom property names\n *\n * ```typespec\n * @discriminated(#{discriminatorPropertyName: "dataKind", envelopePropertyName: "data"})\n * union Pet{ cat: Cat, dog: Dog }\n *\n * model Cat { name: string, meow: boolean }\n * model Dog { name: string, bark: boolean }\n * ```\n * Serialized as:\n * ```json\n * {\n *   "dataKind": "cat",\n *   "data": {\n *     "name": "Whiskers",\n *     "meow": true\n *   }\n * },\n * {\n *   "dataKind": "dog",\n *   "data": {\n *     "name": "Rex",\n *     "bark": false\n *   }\n * }\n * ```\n */\nextern dec discriminated(target: Union, options?: valueof DiscriminatedOptions);\n\n/**\n * Specify the property to be used to discriminate this type.\n * @param propertyName The property name to use for discrimination\n *\n * @example\n *\n * ```typespec\n * @discriminator("kind")\n * model Pet{ kind: string }\n *\n * model Cat extends Pet {kind: "cat", meow: boolean}\n * model Dog extends Pet  {kind: "dog", bark: boolean}\n * ```\n */\nextern dec discriminator(target: Model, propertyName: valueof string);\n\n/**\n * Known encoding to use on utcDateTime or offsetDateTime\n */\nenum DateTimeKnownEncoding {\n  /**\n   * RFC 3339 standard. https://www.ietf.org/rfc/rfc3339.txt\n   * Encode to string.\n   */\n  rfc3339: "rfc3339",\n\n  /**\n   * RFC 7231 standard. https://www.ietf.org/rfc/rfc7231.txt\n   * Encode to string.\n   */\n  rfc7231: "rfc7231",\n\n  /**\n   * Encode a datetime to a unix timestamp.\n   * Unix timestamps are represented as an integer number of seconds since the Unix epoch and usually encoded as an int32.\n   */\n  unixTimestamp: "unixTimestamp",\n}\n\n/**\n * Known encoding to use on duration\n */\nenum DurationKnownEncoding {\n  /**\n   * ISO8601 duration\n   */\n  ISO8601: "ISO8601",\n\n  /**\n   * Encode to integer or float\n   */\n  seconds: "seconds",\n}\n\n/**\n * Known encoding to use on bytes\n */\nenum BytesKnownEncoding {\n  /**\n   * Encode to Base64\n   */\n  base64: "base64",\n\n  /**\n   * Encode to Base64 Url\n   */\n  base64url: "base64url",\n}\n\n/**\n * Encoding for serializing arrays\n */\nenum ArrayEncoding {\n  /** Each values of the array is separated by a | */\n  pipeDelimited,\n\n  /** Each values of the array is separated by a <space> */\n  spaceDelimited,\n}\n\n/**\n * Specify how to encode the target type.\n * @param encodingOrEncodeAs Known name of an encoding or a scalar type to encode as(Only for numeric types to encode as string).\n * @param encodedAs What target type is this being encoded as. Default to string.\n *\n * @example offsetDateTime encoded with rfc7231\n *\n * ```tsp\n * @encode("rfc7231")\n * scalar myDateTime extends offsetDateTime;\n * ```\n *\n * @example utcDateTime encoded with unixTimestamp\n *\n * ```tsp\n * @encode("unixTimestamp", int32)\n * scalar myDateTime extends unixTimestamp;\n * ```\n *\n * @example encode numeric type to string\n *\n * ```tsp\n * model Pet {\n *   @encode(string) id: int64;\n * }\n * ```\n */\nextern dec encode(\n  target: Scalar | ModelProperty,\n  encodingOrEncodeAs: (valueof string | EnumMember) | Scalar,\n  encodedAs?: Scalar\n);\n\n/** Options for example decorators */\nmodel ExampleOptions {\n  /** The title of the example */\n  title?: string;\n\n  /** Description of the example */\n  description?: string;\n}\n\n/**\n * Provide an example value for a data type.\n *\n * @param example Example value.\n * @param options Optional metadata for the example.\n *\n * @example\n *\n * ```tsp\n * @example(#{name: "Fluffy", age: 2})\n * model Pet {\n *  name: string;\n *  age: int32;\n * }\n * ```\n */\nextern dec example(\n  target: Model | Enum | Scalar | Union | ModelProperty | UnionVariant,\n  example: valueof unknown,\n  options?: valueof ExampleOptions\n);\n\n/**\n * Operation example configuration.\n */\nmodel OperationExample {\n  /** Example request body. */\n  parameters?: unknown;\n\n  /** Example response body. */\n  returnType?: unknown;\n}\n\n/**\n * Provide example values for an operation\'s parameters and corresponding return type.\n *\n * @param example Example value.\n * @param options Optional metadata for the example.\n *\n * @example\n *\n * ```tsp\n * @opExample(#{parameters: #{name: "Fluffy", age: 2}, returnType: #{name: "Fluffy", age: 2, id: "abc"})\n * op createPet(pet: Pet): Pet;\n * ```\n */\nextern dec opExample(\n  target: Operation,\n  example: valueof OperationExample,\n  options?: valueof ExampleOptions\n);\n\n/**\n * Returns the model with required properties removed.\n */\nextern dec withOptionalProperties(target: Model);\n\n/**\n * Returns the model with any default values removed.\n */\nextern dec withoutDefaultValues(target: Model);\n\n/**\n * Returns the model with the given properties omitted.\n * @param omit List of properties to omit\n */\nextern dec withoutOmittedProperties(target: Model, omit: string | Union);\n\n/**\n * Returns the model with only the given properties included.\n * @param pick List of properties to include\n */\nextern dec withPickedProperties(target: Model, pick: string | Union);\n\n//---------------------------------------------------------------------------\n// Paging\n//---------------------------------------------------------------------------\n\n/**\n * Mark this operation as a `list` operation that returns a paginated list of items.\n */\nextern dec list(target: Operation);\n\n/**\n * Pagination property defining the number of items to skip.\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n * }\n * @list op listPets(@offset skip: int32, @pageSize pageSize: int8): Page<Pet>;\n * ```\n */\nextern dec offset(target: ModelProperty);\n\n/**\n * Pagination property defining the page index.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n * }\n * @list op listPets(@pageIndex page: int32, @pageSize pageSize: int8): Page<Pet>;\n * ```\n */\nextern dec pageIndex(target: ModelProperty);\n\n/**\n * Specify the pagination parameter that controls the maximum number of items to include in a page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n * }\n * @list op listPets(@pageIndex page: int32, @pageSize pageSize: int8): Page<Pet>;\n * ```\n */\nextern dec pageSize(target: ModelProperty);\n\n/**\n * Specify the the property that contains the array of page items.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n * }\n * @list op listPets(@pageIndex page: int32, @pageSize pageSize: int8): Page<Pet>;\n * ```\n */\nextern dec pageItems(target: ModelProperty);\n\n/**\n * Pagination property defining the token to get to the next page.\n * It MUST be specified both on the request parameter and the response.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @continuationToken continuationToken: string;\n * }\n * @list op listPets(@continuationToken continuationToken: string): Page<Pet>;\n * ```\n */\nextern dec continuationToken(target: ModelProperty);\n\n/**\n * Pagination property defining a link to the next page.\n *\n * It is expected that navigating to the link will return the same set of responses as the operation that returned the current page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @nextLink next: url;\n *   @prevLink prev: url;\n *   @firstLink first: url;\n *   @lastLink last: url;\n * }\n * @list op listPets(): Page<Pet>;\n * ```\n */\nextern dec nextLink(target: ModelProperty);\n\n/**\n * Pagination property defining a link to the previous page.\n *\n * It is expected that navigating to the link will return the same set of responses as the operation that returned the current page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @nextLink next: url;\n *   @prevLink prev: url;\n *   @firstLink first: url;\n *   @lastLink last: url;\n * }\n * @list op listPets(): Page<Pet>;\n * ```\n */\nextern dec prevLink(target: ModelProperty);\n\n/**\n * Pagination property defining a link to the first page.\n *\n * It is expected that navigating to the link will return the same set of responses as the operation that returned the current page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @nextLink next: url;\n *   @prevLink prev: url;\n *   @firstLink first: url;\n *   @lastLink last: url;\n * }\n * @list op listPets(): Page<Pet>;\n * ```\n */\nextern dec firstLink(target: ModelProperty);\n\n/**\n * Pagination property defining a link to the last page.\n *\n * It is expected that navigating to the link will return the same set of responses as the operation that returned the current page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @nextLink next: url;\n *   @prevLink prev: url;\n *   @firstLink first: url;\n *   @lastLink last: url;\n * }\n * @list op listPets(): Page<Pet>;\n * ```\n */\nextern dec lastLink(target: ModelProperty);\n\n//---------------------------------------------------------------------------\n// Debugging\n//---------------------------------------------------------------------------\n\n/**\n * A debugging decorator used to inspect a type.\n * @param text Custom text to log\n */\nextern dec inspectType(target: unknown, text: valueof string);\n\n/**\n * A debugging decorator used to inspect a type name.\n * @param text Custom text to log\n */\nextern dec inspectTypeName(target: unknown, text: valueof string);\n',
  "../compiler/lib/std/reflection.tsp": "namespace TypeSpec.Reflection;\n\nmodel Enum {}\nmodel EnumMember {}\nmodel Interface {}\nmodel Model {}\nmodel ModelProperty {}\nmodel Namespace {}\nmodel Operation {}\nmodel Scalar {}\nmodel Union {}\nmodel UnionVariant {}\nmodel StringTemplate {}\n",
  "../compiler/lib/std/visibility.tsp": '// Copyright (c) Microsoft Corporation\n// Licensed under the MIT license.\n\nimport "../../dist/src/lib/tsp-index.js";\n\nusing TypeSpec.Reflection;\n\nnamespace TypeSpec;\n\n/**\n * Sets the visibility modifiers that are active on a property, indicating that it is only considered to be present\n * (or "visible") in contexts that select for the given modifiers.\n *\n * A property without any visibility settings applied for any visibility class (e.g. `Lifecycle`) is considered to have\n * the default visibility settings for that class.\n *\n * If visibility for the property has already been set for a visibility class (for example, using `@invisible` or\n * `@removeVisibility`), this decorator will **add** the specified visibility modifiers to the property.\n *\n * See: [Visibility](https://typespec.io/docs/language-basics/visibility)\n *\n * The `@typespec/http` library uses `Lifecycle` visibility to determine which properties are included in the request or\n * response bodies of HTTP operations. By default, it uses the following visibility settings:\n *\n * - For the return type of operations, properties are included if they have `Lifecycle.Read` visibility.\n * - For POST operation parameters, properties are included if they have `Lifecycle.Create` visibility.\n * - For PUT operation parameters, properties are included if they have `Lifecycle.Create` or `Lifecycle.Update` visibility.\n * - For PATCH operation parameters, properties are included if they have `Lifecycle.Update` visibility.\n * - For DELETE operation parameters, properties are included if they have `Lifecycle.Delete` visibility.\n * - For GET or HEAD operation parameters, properties are included if they have `Lifecycle.Query` visibility.\n *\n * By default, properties have all five Lifecycle visibility modifiers enabled, so a property is visible in all contexts\n * by default.\n *\n * The default settings may be overridden using the `@returnTypeVisibility` and `@parameterVisibility` decorators.\n *\n * See also: [Automatic visibility](https://typespec.io/docs/libraries/http/operations#automatic-visibility)\n *\n * @param visibilities List of visibilities which apply to this property.\n *\n * @example\n *\n * ```typespec\n * model Dog {\n *   // The service will generate an ID, so you don\'t need to send it.\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   // The service will store this secret name, but won\'t ever return it.\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   // The regular name has all vi\n *   name: string;\n * }\n * ```\n */\nextern dec visibility(target: ModelProperty, ...visibilities: valueof EnumMember[]);\n\n/**\n * Indicates that a property is not visible in the given visibility class.\n *\n * This decorator removes all active visibility modifiers from the property within\n * the given visibility class, making it invisible to any context that selects for\n * visibility modifiers within that class.\n *\n * @param visibilityClass The visibility class to make the property invisible within.\n *\n * @example\n * ```typespec\n * model Example {\n *   @invisible(Lifecycle)\n *   hidden_property: string;\n * }\n * ```\n */\nextern dec invisible(target: ModelProperty, visibilityClass: Enum);\n\n/**\n * Removes visibility modifiers from a property.\n *\n * If the visibility modifiers for a visibility class have not been initialized,\n * this decorator will use the default visibility modifiers for the visibility\n * class as the default modifier set.\n *\n * @param target The property to remove visibility from.\n * @param visibilities The visibility modifiers to remove from the target property.\n *\n * @example\n * ```typespec\n * model Example {\n *   // This property will have all Lifecycle visibilities except the Read\n *   // visibility, since it is removed.\n *   @removeVisibility(Lifecycle.Read)\n *   secret_property: string;\n * }\n * ```\n */\nextern dec removeVisibility(target: ModelProperty, ...visibilities: valueof EnumMember[]);\n\n/**\n * Removes properties that do not have at least one of the given visibility modifiers\n * active.\n *\n * If no visibility modifiers are supplied, this decorator has no effect.\n *\n * See also: [Automatic visibility](https://typespec.io/docs/libraries/http/operations#automatic-visibility)\n *\n * When using an emitter that applies visibility automatically, it is generally\n * not necessary to use this decorator.\n *\n * @param visibilities List of visibilities that apply to this property.\n *\n * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * // The spread operator will copy all the properties of Dog into DogRead,\n * // and @withVisibility will then remove those that are not visible with\n * // create or update visibility.\n * //\n * // In this case, the id property is removed, and the name and secretName\n * // properties are kept.\n * @withVisibility(Lifecycle.Create, Lifecycle.Update)\n * model DogCreateOrUpdate {\n *   ...Dog;\n * }\n *\n * // In this case the id and name properties are kept and the secretName property\n * // is removed.\n * @withVisibility(Lifecycle.Read)\n * model DogRead {\n *   ...Dog;\n * }\n * ```\n */\nextern dec withVisibility(target: Model, ...visibilities: valueof EnumMember[]);\n\n/**\n * Set the visibility of key properties in a model if not already set.\n *\n * This will set the visibility modifiers of all key properties in the model if the visibility is not already _explicitly_ set,\n * but will not change the visibility of any properties that have visibility set _explicitly_, even if the visibility\n * is the same as the default visibility.\n *\n * Visibility may be set explicitly using any of the following decorators:\n *\n * - `@visibility`\n * - `@removeVisibility`\n * - `@invisible`\n *\n * @param visibility The desired default visibility value. If a key property already has visibility set, it will not be changed.\n */\nextern dec withDefaultKeyVisibility(target: Model, visibility: valueof EnumMember);\n\n/**\n * Declares the visibility constraint of the parameters of a given operation.\n *\n * A parameter or property nested within a parameter will be visible if it has _any_ of the visibilities\n * in the list.\n *\n * It is invalid to call this decorator with no visibility modifiers.\n *\n * @param visibilities List of visibility modifiers that apply to the parameters of this operation.\n */\nextern dec parameterVisibility(target: Operation, ...visibilities: valueof EnumMember[]);\n\n/**\n * Declares the visibility constraint of the return type of a given operation.\n *\n * A property within the return type of the operation will be visible if it has _any_ of the visibilities\n * in the list.\n *\n * It is invalid to call this decorator with no visibility modifiers.\n *\n * @param visibilities List of visibility modifiers that apply to the return type of this operation.\n */\nextern dec returnTypeVisibility(target: Operation, ...visibilities: valueof EnumMember[]);\n\n/**\n * Returns the model with non-updateable properties removed.\n */\nextern dec withUpdateableProperties(target: Model);\n\n/**\n * Declares the default visibility modifiers for a visibility class.\n *\n * The default modifiers are used when a property does not have any visibility decorators\n * applied to it.\n *\n * The modifiers passed to this decorator _MUST_ be members of the target Enum.\n *\n * @param visibilities the list of modifiers to use as the default visibility modifiers.\n */\nextern dec defaultVisibility(target: Enum, ...visibilities: valueof EnumMember[]);\n\n/**\n * A visibility class for resource lifecycle phases.\n *\n * These visibilities control whether a property is visible during the various phases of a resource\'s lifecycle.\n *\n * @example\n * ```typespec\n * model Dog {\n *  @visibility(Lifecycle.Read)\n *  id: int32;\n *\n *  @visibility(Lifecycle.Create, Lifecycle.Update)\n *  secretName: string;\n *\n *  name: string;\n * }\n * ```\n *\n * In this example, the `id` property is only visible during the read phase, and the `secretName` property is only visible\n * during the create and update phases. This means that the server will return the `id` property when returning a `Dog`,\n * but the client will not be able to set or update it. In contrast, the `secretName` property can be set when creating\n * or updating a `Dog`, but the server will never return it. The `name` property has no visibility modifiers and is\n * therefore visible in all phases.\n */\nenum Lifecycle {\n  /**\n   * The property is visible when a resource is being created.\n   */\n  Create,\n\n  /**\n   * The property is visible when a resource is being read.\n   */\n  Read,\n\n  /**\n   * The property is visible when a resource is being updated.\n   */\n  Update,\n\n  /**\n   * The property is visible when a resource is being deleted.\n   */\n  Delete,\n\n  /**\n   * The property is visible when a resource is being queried.\n   *\n   * In HTTP APIs, this visibility applies to parameters of GET or HEAD operations.\n   */\n  Query,\n}\n\n/**\n * A visibility filter, used to specify which properties should be included when\n * using the `withVisibilityFilter` decorator.\n *\n * The filter matches any property with ALL of the following:\n * - If the `any` key is present, the property must have at least one of the specified visibilities.\n * - If the `all` key is present, the property must have all of the specified visibilities.\n * - If the `none` key is present, the property must have none of the specified visibilities.\n */\nmodel VisibilityFilter {\n  any?: EnumMember[];\n  all?: EnumMember[];\n  none?: EnumMember[];\n}\n\n/**\n * Applies the given visibility filter to the properties of the target model.\n *\n * This transformation is recursive, so it will also apply the filter to any nested\n * or referenced models that are the types of any properties in the `target`.\n *\n * If a `nameTemplate` is provided, newly-created type instances will be named according\n * to the template. See the `@friendlyName` decorator for more information on the template\n * syntax. The transformed type is provided as the argument to the template.\n *\n * @param target The model to apply the visibility filter to.\n * @param filter The visibility filter to apply to the properties of the target model.\n * @param nameTemplate The name template to use when renaming new model instances.\n *\n * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   name: string;\n * }\n *\n * @withVisibilityFilter(#{ all: #[Lifecycle.Read] })\n * model DogRead {\n *  ...Dog\n * }\n * ```\n */\nextern dec withVisibilityFilter(\n  target: Model,\n  filter: valueof VisibilityFilter,\n  nameTemplate?: valueof string\n);\n\n/**\n * Transforms the `target` model to include only properties that are visible during the\n * "Update" lifecycle phase.\n *\n * Any nested models of optional properties will be transformed into the "CreateOrUpdate"\n * lifecycle phase instead of the "Update" lifecycle phase, so that nested models may be\n * fully updated.\n *\n * If a `nameTemplate` is provided, newly-created type instances will be named according\n * to the template. See the `@friendlyName` decorator for more information on the template\n * syntax. The transformed type is provided as the argument to the template.\n *\n * @param target The model to apply the transformation to.\n * @param nameTemplate The name template to use when renaming new model instances.\n *\n * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * @withLifecycleUpdate\n * model DogUpdate {\n *   ...Dog\n * }\n * ```\n */\nextern dec withLifecycleUpdate(target: Model, nameTemplate?: valueof string);\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Create" resource lifecycle phase.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Create` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   name: string;\n * }\n *\n * // This model has only the `name` field.\n * model CreateDog is Create<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ all: #[Lifecycle.Create] }, NameTemplate)\nmodel Create<T extends Reflection.Model, NameTemplate extends valueof string = "Create{name}"> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Read" resource lifecycle phase.\n *\n * The "Read" lifecycle phase is used for properties returned by operations that read data, like\n * HTTP GET operations.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Read` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * // This model has the `id` and `name` fields, but not `secretName`.\n * model ReadDog is Read<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ all: #[Lifecycle.Read] }, NameTemplate)\nmodel Read<T extends Reflection.Model, NameTemplate extends valueof string = "Read{name}"> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Update" resource lifecycle phase.\n *\n * The "Update" lifecycle phase is used for properties passed as parameters to operations\n * that update data, like HTTP PATCH operations.\n *\n * This transformation will include only the properties that have the `Lifecycle.Update`\n * visibility modifier, and the types of all properties will be replaced with the\n * equivalent `CreateOrUpdate` transformation.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * // This model will have the `secretName` and `name` fields, but not the `id` field.\n * model UpdateDog is Update<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withLifecycleUpdate(NameTemplate)\nmodel Update<T extends Reflection.Model, NameTemplate extends valueof string = "Update{name}"> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Create" or "Update" resource lifecycle phases.\n *\n * The "CreateOrUpdate" lifecycle phase is used by default for properties passed as parameters to operations\n * that can create _or_ update data, like HTTP PUT operations.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Create` or `Lifecycle.Update` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create)\n *   immutableSecret: string;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * // This model will have the `immutableSecret`, `secretName`, and `name` fields, but not the `id` field.\n * model CreateOrUpdateDog is CreateOrUpdate<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ any: #[Lifecycle.Create, Lifecycle.Update] }, NameTemplate)\nmodel CreateOrUpdate<\n  T extends Reflection.Model,\n  NameTemplate extends valueof string = "CreateOrUpdate{name}"\n> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Delete" resource lifecycle phase.\n *\n * The "Delete" lifecycle phase is used for properties passed as parameters to operations\n * that delete data, like HTTP DELETE operations.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Delete` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   // Set when the Dog is removed from our data store. This happens when the\n *   // Dog is re-homed to a new owner.\n *   @visibility(Lifecycle.Delete)\n *   nextOwner: string;\n *\n *   name: string;\n * }\n *\n * // This model will have the `nextOwner` and `name` fields, but not the `id` field.\n * model DeleteDog is Delete<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ all: #[Lifecycle.Delete] }, NameTemplate)\nmodel Delete<T extends Reflection.Model, NameTemplate extends valueof string = "Delete{name}"> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Query" resource lifecycle phase.\n *\n * The "Query" lifecycle phase is used for properties passed as parameters to operations\n * that read data, like HTTP GET or HEAD operations. This should not be confused for\n * the `@query` decorator, which specifies that the property is transmitted in the\n * query string of an HTTP request.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Query` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   // When getting information for a Dog, you can set this field to true to include\n *   // some extra information about the Dog\'s pedigree that is normally not returned.\n *   // Alternatively, you could just use a separate option parameter to get this\n *   // information.\n *   @visibility(Lifecycle.Query)\n *   includePedigree?: boolean;\n *\n *   name: string;\n *\n *   // Only included if `includePedigree` is set to true in the request.\n *   @visibility(Lifecycle.Read)\n *   pedigree?: string;\n * }\n *\n * // This model will have the `includePedigree` and `name` fields, but not `id` or `pedigree`.\n * model QueryDog is Query<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ all: #[Lifecycle.Query] }, NameTemplate)\nmodel Query<T extends Reflection.Model, NameTemplate extends valueof string = "Query{name}"> {\n  ...T;\n}\n',
  "lib/rest.tsp": 'import "@typespec/http";\nimport "./rest-decorators.tsp";\nimport "./resource.tsp";\nimport "../dist/src/tsp-index.js";\n\nnamespace TypeSpec.Rest;\n\n/**\n * A URL that points to a resource.\n * @template Resource The type of resource that the URL points to.\n */\n@doc("The location of an instance of {name}", Resource)\n@Private.resourceLocation(Resource)\nscalar ResourceLocation<Resource extends {}> extends url;\n',
  "../http/lib/main.tsp": 'import "../dist/src/tsp-index.js";\nimport "./decorators.tsp";\nimport "./private.decorators.tsp";\nimport "./auth.tsp";\n\nnamespace TypeSpec.Http;\n\nusing Private;\n\n/**\n * Describes an HTTP response.\n *\n * @template Status The status code of the response.\n */\n@doc("")\nmodel Response<Status> {\n  @doc("The status code.")\n  @statusCode\n  statusCode: Status;\n}\n\n/**\n * Defines a model with a single property of the given type, marked with `@body`.\n *\n * This can be useful in situations where you cannot use a bare type as the body\n * and it is awkward to add a property.\n *\n * @template Type The type of the model\'s `body` property.\n */\n@doc("")\nmodel Body<Type> {\n  @body\n  @doc("The body type of the operation request or response.")\n  body: Type;\n}\n\n/**\n * The Location header contains the URL where the status of the long running operation can be checked.\n */\nmodel LocationHeader {\n  @doc("The Location header contains the URL where the status of the long running operation can be checked.")\n  @header\n  location: string;\n}\n\n// Don\'t put @doc on these, change `getStatusCodeDescription` implementation\n// to update the default descriptions for these status codes. This ensures\n// that we get consistent emit between different ways to spell the same\n// responses in TypeSpec.\n\n/**\n * The request has succeeded.\n */\nmodel OkResponse is Response<200>;\n/**\n * The request has succeeded and a new resource has been created as a result.\n */\nmodel CreatedResponse is Response<201>;\n/**\n * The request has been accepted for processing, but processing has not yet completed.\n */\nmodel AcceptedResponse is Response<202>;\n/**\n * There is no content to send for this request, but the headers may be useful.\n */\nmodel NoContentResponse is Response<204>;\n/**\n * The URL of the requested resource has been changed permanently. The new URL is given in the response.\n */\nmodel MovedResponse is Response<301> {\n  ...LocationHeader;\n}\n/**\n * The client has made a conditional request and the resource has not been modified.\n */\nmodel NotModifiedResponse is Response<304>;\n/**\n * The server could not understand the request due to invalid syntax.\n */\nmodel BadRequestResponse is Response<400>;\n/**\n * Access is unauthorized.\n */\nmodel UnauthorizedResponse is Response<401>;\n/**\n * Access is forbidden.\n */\nmodel ForbiddenResponse is Response<403>;\n/**\n * The server cannot find the requested resource.\n */\nmodel NotFoundResponse is Response<404>;\n/**\n * The request conflicts with the current state of the server.\n */\nmodel ConflictResponse is Response<409>;\n\n/**\n * Produces a new model with the same properties as T, but with `@query`,\n * `@header`, `@body`, and `@path` decorators removed from all properties.\n *\n * @template Data The model to spread as the plain data.\n */\n@plainData\nmodel PlainData<Data> {\n  ...Data;\n}\n\n/**\n * A file in an HTTP request, response, or multipart payload.\n *\n * Files have a special meaning that the HTTP library understands. When the body of an HTTP request, response,\n * or multipart payload is _effectively_ an instance of `TypeSpec.Http.File` or any type that extends it, the\n * operation is treated as a file upload or download.\n *\n * When using file bodies, the fields of the file model are defined to come from particular locations by default:\n *\n * - `contentType`: The `Content-Type` header of the request, response, or multipart payload (CANNOT be overridden or changed).\n * - `contents`: The body of the request, response, or multipart payload (CANNOT be overridden or changed).\n * - `filename`: The `filename` parameter value of the `Content-Disposition` header of the response or multipart payload\n *   (MAY be overridden or changed).\n *\n * A File may be used as a normal structured JSON object in a request or response, if the request specifies an explicit\n * `Content-Type` header. In this case, the entire File model is serialized as if it were any other model. In a JSON payload,\n * it will have a structure like:\n *\n * ```\n * {\n *   "contentType": <string?>,\n *   "filename": <string?>,\n *   "contents": <string, base64>\n * }\n * ```\n *\n * The `contentType` _within_ the file defines what media types the data inside the file can be, but if the specification\n * defines a `Content-Type` for the payload as HTTP metadata, that `Content-Type` metadata defines _how the file is\n * serialized_. See the examples below for more information.\n *\n * NOTE: The `filename` and `contentType` fields are optional. Furthermore, the default location of `filename`\n * (`Content-Disposition: <disposition>; filename=<filename>`) is only valid in HTTP responses and multipart payloads. If\n * you wish to send the `filename` in a request, you must use HTTP metadata decorators to describe the location of the\n * `filename` field. You can combine the metadata decorators with `@visibility` to control when the `filename` location\n * is overridden, as shown in the examples below.\n *\n * @template ContentType The allowed media (MIME) types of the file contents.\n * @template Contents The type of the file contents. This can be `string`, `bytes`, or any scalar that extends them.\n *\n * @example\n * ```tsp\n * // Download a file\n * @get op download(): File;\n *\n * // Upload a file\n * @post op upload(@bodyRoot file: File): void;\n * ```\n *\n * @example\n * ```tsp\n * // Upload and download files in a multipart payload\n * op multipartFormDataUpload(\n *   @multipartBody fields: {\n *     files: HttpPart<File>[];\n *   },\n * ): void;\n *\n * op multipartFormDataDownload(): {\n *   @multipartBody formFields: {\n *     files: HttpPart<File>[];\n *   }\n * };\n * ```\n *\n * @example\n * ```tsp\n * // Declare a custom type of text file, where the filename goes in the path\n * // in requests.\n * model SpecFile extends File<"application/json" | "application/yaml", string> {\n *   // Provide a header that contains the name of the file when created or updated\n *   @header("x-filename")\n *   @path filename: string;\n * }\n *\n * @get op downloadSpec(@path name: string): SpecFile;\n *\n * @post op uploadSpec(@bodyRoot spec: SpecFile): void;\n * ```\n *\n * @example\n * ```tsp\n * // Declare a custom type of binary file\n * model ImageFile extends File {\n *   contentType: "image/png" | "image/jpeg";\n *   @path filename: string;\n * }\n *\n * @get op downloadImage(@path name: string): ImageFile;\n *\n * @post op uploadImage(@bodyRoot image: ImageFile): void;\n * ```\n *\n * @example\n * ```tsp\n * // Use a File as a structured JSON object. The HTTP library will warn you that the File will be serialized as JSON,\n * // so you should suppress the warning if it\'s really what you want instead of a binary file upload/download.\n *\n * // The response body is a JSON object like `{"contentType":<string?>,"filename":<string?>,"contents":<string>}`\n * @get op downloadTextFileJson(): {\n *   @header contentType: "application/json",\n *   @body file: File<"text/plain", string>,\n * };\n *\n * // The request body is a JSON object like `{"contentType":<string?>,"filename":<string?>,"contents":<base64>}`\n * @post op uploadBinaryFileJson(\n *   @header contentType: "application/json",\n *   @body file: File<"image/png", bytes>,\n * ): void;\n *\n */\n@summary("A file in an HTTP request, response, or multipart payload.")\n@Private.httpFile\nmodel File<ContentType extends string = string, Contents extends bytes | string = bytes> {\n  /**\n   * The allowed media (MIME) types of the file contents.\n   *\n   * In file bodies, this value comes from the `Content-Type` header of the request or response. In JSON bodies,\n   * this value is serialized as a field in the response.\n   *\n   * NOTE: this is not _necessarily_ the same as the `Content-Type` header of the request or response, but\n   * it will be for file bodies. It may be different if the file is serialized as a JSON object. It always refers to the\n   * _contents_ of the file, and not necessarily the way the file itself is transmitted or serialized.\n   */\n  @summary("The allowed media (MIME) types of the file contents.")\n  contentType?: ContentType;\n\n  /**\n   * The name of the file, if any.\n   *\n   * In file bodies, this value comes from the `filename` parameter of the `Content-Disposition` header of the response\n   * or multipart payload. In JSON bodies, this value is serialized as a field in the response.\n   *\n   * NOTE: By default, `filename` cannot be sent in request payloads and can only be sent in responses and multipart\n   * payloads, as the `Content-Disposition` header is not valid in requests. If you want to send the `filename` in a request,\n   * you must extend the `File` model and override the `filename` property with a different location defined by HTTP metadata\n   * decorators.\n   */\n  @summary("The name of the file, if any.")\n  filename?: string;\n\n  /**\n   * The contents of the file.\n   *\n   * In file bodies, this value comes from the body of the request, response, or multipart payload. In JSON bodies,\n   * this value is serialized as a field in the response.\n   */\n  @summary("The contents of the file.")\n  contents: Contents;\n}\n\nmodel HttpPartOptions {\n  /** Name of the part when using the array form. */\n  name?: string;\n}\n\n@Private.httpPart(Type, Options)\nmodel HttpPart<Type, Options extends valueof HttpPartOptions = #{}> {}\n\nmodel Link {\n  target: url;\n  rel: string;\n  attributes?: Record<unknown>;\n}\n\nscalar LinkHeader<T extends Record<url> | Link[]> extends string;\n\n/**\n * Create a MergePatch Request body for updating the given resource Model.\n * The MergePatch request created by this template provides a TypeSpec description of a\n * JSON MergePatch request that can successfully update the given resource.\n * The transformation follows the definition of JSON MergePatch requests in\n * rfc 7396: https://www.rfc-editor.org/rfc/rfc7396,\n * applying the merge-patch transform recursively to keyed types in the resource Model.\n *\n * Using this template in a PATCH request body overrides the `implicitOptionality`\n * setting for PATCH operations and sets `application/merge-patch+json` as the request\n * content-type.\n *\n * @template T The type of the resource to create a MergePatch update request body for.\n * @template NameTemplate A StringTemplate used to name any models created by applying\n * the merge-patch transform to the resource. The default name template is `{name}MergePatchUpdate`,\n * for example, the merge patch transform of model `Widget` is named `WidgetMergePatchUpdate`.\n *\n * @example\n * ```tsp\n * // An operation updating a \'Widget\' using merge-patch\n * @patch op update(@body request: MergePatchUpdate<Widget>): Widget;\n * ```\n *\n * @example\n * ```tsp\n * // An operation updating a \'Widget\' using merge-patch\n * @patch op update(@bodyRoot request: MergePatchUpdate<Widget>): Widget;\n * ```\n *\n * @example\n * ```tsp\n * // An operation updating a \'Widget\' using merge-patch\n * @patch op update(...MergePatchUpdate<Widget>): Widget;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@mediaTypeHint("application/merge-patch+json")\n@applyMergePatch(T, NameTemplate, #{ visibilityMode: Private.MergePatchVisibilityMode.Update })\nmodel MergePatchUpdate<\n  T extends Reflection.Model,\n  NameTemplate extends valueof string = "{name}MergePatchUpdate"\n> {}\n\n/**\n * Create a MergePatch Request body for creating or updating the given resource Model.\n * The MergePatch request created by this template provides a TypeSpec description of a\n * JSON MergePatch request that can successfully create or update the given resource.\n * The transformation follows the definition of JSON MergePatch requests in\n * rfc 7396: https://www.rfc-editor.org/rfc/rfc7396,\n * applying the merge-patch transform recursively to keyed types in the resource Model.\n *\n * Using this template in a PATCH request body overrides the `implicitOptionality`\n * setting for PATCH operations and sets `application/merge-patch+json` as the request\n * content-type.\n *\n * @template T The type of the resource to create a MergePatch update request body for.\n * @template NameTemplate A StringTemplate used to name any models created by applying\n * the merge-patch transform to the resource. The default name template is `{name}MergePatchCreateOrUpdate`,\n * for example, the merge patch transform of model `Widget` is named `WidgetMergePatchCreateOrUpdate`.\n *\n * @example\n * ```tsp\n * // An operation updating a \'Widget\' using merge-patch\n * @patch op update(@body request: MergePatchCreateOrUpdate<Widget>): Widget;\n * ```\n *\n * @example\n * ```tsp\n * // An operation updating a \'Widget\' using merge-patch\n * @patch op update(@bodyRoot request: MergePatchCreateOrUpdate<Widget>): Widget;\n * ```\n *\n * @example\n * ```tsp\n * // An operation updating a \'Widget\' using merge-patch\n * @patch op update(...MergePatchCreateOrUpdate<Widget>): Widget;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@mediaTypeHint("application/merge-patch+json")\n@applyMergePatch(\n  T,\n  NameTemplate,\n  #{ visibilityMode: Private.MergePatchVisibilityMode.CreateOrUpdate }\n)\nmodel MergePatchCreateOrUpdate<\n  T extends Reflection.Model,\n  NameTemplate extends valueof string = "{name}MergePatchCreateOrUpdate"\n> {}\n',
  "../http/lib/decorators.tsp": 'namespace TypeSpec.Http;\n\nusing TypeSpec.Reflection;\n\n/**\n * Header options.\n */\nmodel HeaderOptions {\n  /**\n   * Name of the header when sent over HTTP.\n   */\n  name?: string;\n\n  /**\n   * Equivalent of adding `*` in the path parameter as per [RFC-6570](https://datatracker.ietf.org/doc/html/rfc6570#section-3.2.3)\n   *\n   *  | Style  | Explode | Primitive value = 5 | Array = [3, 4, 5] | Object = {"role": "admin", "firstName": "Alex"} |\n   *  | ------ | ------- | ------------------- | ----------------- | ----------------------------------------------- |\n   *  | simple | false   | `5   `              | `3,4,5`           | `role,admin,firstName,Alex`                     |\n   *  | simple | true    | `5`                 | `3,4,5`           | `role=admin,firstName=Alex`                     |\n   *\n   */\n  explode?: boolean;\n}\n\n/**\n * Specify this property is to be sent or received as an HTTP header.\n *\n * @param headerNameOrOptions Optional name of the header when sent over HTTP or header options.\n *  By default the header name will be the property name converted from camelCase to kebab-case. (e.g. `contentType` -> `content-type`)\n *\n * @example\n *\n * ```typespec\n * op read(@header accept: string): {@header("ETag") eTag: string};\n * op create(@header({name: "X-Color", format: "csv"}) colors: string[]): void;\n * ```\n *\n * @example Implicit header name\n *\n * ```typespec\n * op read(): {@header contentType: string}; // headerName: content-type\n * op update(@header ifMatch: string): void; // headerName: if-match\n * ```\n */\nextern dec header(target: ModelProperty, headerNameOrOptions?: valueof string | HeaderOptions);\n\n/**\n * Cookie Options.\n */\nmodel CookieOptions {\n  /**\n   * Name in the cookie.\n   */\n  name?: string;\n}\n\n/**\n * Specify this property is to be sent or received in the cookie.\n *\n * @param cookieNameOrOptions Optional name of the cookie in the cookie or cookie options.\n *  By default the cookie name will be the property name converted from camelCase to snake_case. (e.g. `authToken` -> `auth_token`)\n *\n * @example\n *\n * ```typespec\n * op read(@cookie token: string): {data: string[]};\n * op create(@cookie({name: "auth_token"}) data: string[]): void;\n * ```\n *\n * @example Implicit header name\n *\n * ```typespec\n * op read(): {@cookie authToken: string}; // headerName: auth_token\n * op update(@cookie AuthToken: string): void; // headerName: auth_token\n * ```\n */\nextern dec cookie(target: ModelProperty, cookieNameOrOptions?: valueof string | CookieOptions);\n\n/**\n * Query parameter options.\n */\nmodel QueryOptions {\n  /**\n   * Name of the query when included in the url.\n   */\n  name?: string;\n\n  /**\n   * If true send each value in the array/object as a separate query parameter.\n   * Equivalent of adding `*` in the path parameter as per [RFC-6570](https://datatracker.ietf.org/doc/html/rfc6570#section-3.2.3)\n   *\n   *  | Style  | Explode | Uri Template   | Primitive value id = 5 | Array id = [3, 4, 5]    | Object id = {"role": "admin", "firstName": "Alex"} |\n   *  | ------ | ------- | -------------- | ---------------------- | ----------------------- | -------------------------------------------------- |\n   *  | simple | false   | `/users{?id}`  | `/users?id=5`          | `/users?id=3,4,5`       | `/users?id=role,admin,firstName,Alex`              |\n   *  | simple | true    | `/users{?id*}` | `/users?id=5`          | `/users?id=3&id=4&id=5` | `/users?role=admin&firstName=Alex`                 |\n   *\n   */\n  explode?: boolean;\n}\n\n/**\n * Specify this property is to be sent as a query parameter.\n *\n * @param queryNameOrOptions Optional name of the query when included in the url or query parameter options.\n *\n * @example\n *\n * ```typespec\n * op read(@query select: string, @query("order-by") orderBy: string): void;\n * op list(@query(#{name: "id", explode: true}) ids: string[]): void;\n * ```\n */\nextern dec query(target: ModelProperty, queryNameOrOptions?: valueof string | QueryOptions);\n\nmodel PathOptions {\n  /** Name of the parameter in the uri template. */\n  name?: string;\n\n  /**\n   * When interpolating this parameter in the case of array or object expand each value using the given style.\n   * Equivalent of adding `*` in the path parameter as per [RFC-6570](https://datatracker.ietf.org/doc/html/rfc6570#section-3.2.3)\n   */\n  explode?: boolean;\n\n  /**\n   * Different interpolating styles for the path parameter.\n   * - `simple`: No special encoding.\n   * - `label`: Using `.` separator.\n   * - `matrix`: `;` as separator.\n   * - `fragment`: `#` as separator.\n   * - `path`: `/` as separator.\n   */\n  style?: "simple" | "label" | "matrix" | "fragment" | "path";\n\n  /**\n   * When interpolating this parameter do not encode reserved characters.\n   * Equivalent of adding `+` in the path parameter as per [RFC-6570](https://datatracker.ietf.org/doc/html/rfc6570#section-3.2.3)\n   */\n  allowReserved?: boolean;\n}\n\n/**\n * Explicitly specify that this property is to be interpolated as a path parameter.\n *\n * @param paramNameOrOptions Optional name of the parameter in the uri template or options.\n *\n * @example\n *\n * ```typespec\n * @route("/read/{explicit}/things/{implicit}")\n * op read(@path explicit: string, implicit: string): void;\n * ```\n */\nextern dec path(target: ModelProperty, paramNameOrOptions?: valueof string | PathOptions);\n\n/**\n * Explicitly specify that this property type will be exactly the HTTP body.\n *\n * This means that any properties under `@body` cannot be marked as headers, query parameters, or path parameters.\n * If wanting to change the resolution of the body but still mix parameters, use `@bodyRoot`.\n *\n * @example\n *\n * ```typespec\n * op upload(@body image: bytes): void;\n * op download(): {@body image: bytes};\n * ```\n */\nextern dec body(target: ModelProperty);\n\n/**\n * Specify that the body resolution should be resolved from that property.\n * By default the body is resolved by including all properties in the operation request/response that are not metadata.\n * This allows to nest the body in a property while still allowing to use headers, query parameters, and path parameters in the same model.\n *\n * @example\n *\n * ```typespec\n * op upload(@bodyRoot user: {name: string, @header id: string}): void;\n * op download(): {@bodyRoot user: {name: string, @header id: string}};\n * ```\n */\nextern dec bodyRoot(target: ModelProperty);\n/**\n * Specify that this property shouldn\'t be included in the HTTP body.\n * This can be useful when bundling metadata together that would result in an empty property to be included in the body.\n *\n * @example\n *\n * ```typespec\n * op upload(name: string, @bodyIgnore headers: {@header id: string}): void;\n * ```\n */\nextern dec bodyIgnore(target: ModelProperty);\n\n/**\n * @example\n *\n * ```tsp\n * op upload(\n *   @header `content-type`: "multipart/form-data",\n *   @multipartBody body: {\n *     fullName: HttpPart<string>,\n *     headShots: HttpPart<Image>[]\n *   }\n * ): void;\n * ```\n */\nextern dec multipartBody(target: ModelProperty);\n\n/**\n * Specify the status code for this response. Property type must be a status code integer or a union of status code integer.\n *\n * @example\n *\n * ```typespec\n * op read(): {\n *   @statusCode _: 200;\n *   @body pet: Pet;\n * };\n * op create(): {\n *   @statusCode _: 201 | 202;\n * };\n * ```\n */\nextern dec statusCode(target: ModelProperty);\n\n/**\n * Specify the HTTP verb for the target operation to be `GET`.\n *\n * @example\n *\n * ```typespec\n * @get op read(): string\n * ```\n */\nextern dec get(target: Operation);\n\n/**\n * Specify the HTTP verb for the target operation to be `PUT`.\n *\n * @example\n *\n * ```typespec\n * @put op set(pet: Pet): void\n * ```\n */\nextern dec put(target: Operation);\n\n/**\n * Specify the HTTP verb for the target operation to be `POST`.\n *\n * @example\n *\n * ```typespec\n * @post op create(pet: Pet): void\n * ```\n */\nextern dec post(target: Operation);\n\n/**\n * Options for PATCH operations.\n */\nmodel PatchOptions {\n  /**\n   * If set to `false`, disables the implicit transform that makes the body of a\n   * PATCH operation deeply optional.\n   */\n  implicitOptionality?: boolean;\n}\n\n/**\n * Specify the HTTP verb for the target operation to be `PATCH`.\n *\n * @param options Options for the PATCH operation.\n *\n * @example\n *\n * ```typespec\n * @patch op update(pet: Pet): void;\n * ```\n *\n * @example\n * ```typespec\n * // Disable implicit optionality, making the body of the PATCH operation use the\n * // optionality as defined in the `Pet` model.\n * @patch(#{ implicitOptionality: false })\n * op update(pet: Pet): void;\n * ```\n */\nextern dec patch(target: Operation, options?: valueof PatchOptions);\n\n/**\n * Specify the HTTP verb for the target operation to be `DELETE`.\n *\n * @example\n *\n * ```typespec\n * @delete op set(petId: string): void\n * ```\n */\nextern dec delete(target: Operation);\n\n/**\n * Specify the HTTP verb for the target operation to be `HEAD`.\n * @example\n *\n * ```typespec\n * @head op ping(petId: string): void\n * ```\n */\nextern dec head(target: Operation);\n\n/**\n * Specify an endpoint for this service. Multiple `@server` decorators can be used to specify multiple endpoints.\n *\n *  @param url Server endpoint\n *  @param description Description of the endpoint\n *  @param parameters Optional set of parameters used to interpolate the url.\n *\n * @example\n *\n * ```typespec\n * @service\n * @server("https://example.com")\n * namespace PetStore;\n * ```\n *\n * @example With a description\n *\n * ```typespec\n * @service\n * @server("https://example.com", "Single server endpoint")\n * namespace PetStore;\n * ```\n *\n * @example Parameterized\n *\n * ```typespec\n * @server("https://{region}.foo.com", "Regional endpoint", {\n *   @doc("Region name")\n *   region?: string = "westus",\n * })\n * ```\n *\n * @example Multiple\n * ```typespec\n * @service\n * @server("https://example.com", "Standard endpoint")\n * @server("https://{project}.private.example.com", "Private project endpoint", {\n *   project: string;\n * })\n * namespace PetStore;\n * ```\n *\n */\nextern dec server(\n  target: Namespace,\n  url: valueof string,\n  description?: valueof string,\n  parameters?: Record<unknown>\n);\n\n/**\n * Specify authentication for a whole service or specific methods. See the [documentation in the Http library](https://typespec.io/docs/libraries/http/authentication) for full details.\n *\n * @param auth Authentication configuration. Can be a single security scheme, a union(either option is valid authentication) or a tuple (must use all authentication together)\n * @example\n *\n * ```typespec\n * @service\n * @useAuth(BasicAuth)\n * namespace PetStore;\n * ```\n */\nextern dec useAuth(target: Namespace | Interface | Operation, auth: {} | Union | {}[]);\n\n/**\n * Defines the relative route URI template for the target operation as defined by [RFC 6570](https://datatracker.ietf.org/doc/html/rfc6570#section-3.2.3)\n *\n * `@route` can only be applied to operations, namespaces, and interfaces.\n *\n * @param uriTemplate Uri template for this operation.\n *\n * @example Simple path parameter\n *\n * ```typespec\n * @route("/widgets/{id}") op getWidget(@path id: string): Widget;\n * ```\n *\n * @example Reserved characters\n * ```typespec\n * @route("/files{+path}") op getFile(@path path: string): bytes;\n * ```\n *\n * @example Query parameter\n * ```typespec\n * @route("/files") op list(select?: string, filter?: string): Files[];\n * @route("/files{?select,filter}") op listFullUriTemplate(select?: string, filter?: string): Files[];\n * ```\n */\nextern dec route(target: Namespace | Interface | Operation, path: valueof string);\n\n/**\n * `@sharedRoute` marks the operation as sharing a route path with other operations.\n *\n * When an operation is marked with `@sharedRoute`, it enables other operations to share the same\n * route path as long as those operations are also marked with `@sharedRoute`.\n *\n * `@sharedRoute` can only be applied directly to operations.\n *\n * ```typespec\n * @sharedRoute\n * @route("/widgets")\n * op getWidget(@path id: string): Widget;\n * ```\n */\nextern dec sharedRoute(target: Operation);\n',
  "../http/lib/private.decorators.tsp": "/**\n * Private decorators. Those are meant for internal use inside Http types only.\n */\nnamespace TypeSpec.Http.Private;\n\nextern dec plainData(target: TypeSpec.Reflection.Model);\nextern dec httpFile(target: TypeSpec.Reflection.Model);\nextern dec httpPart(\n  target: TypeSpec.Reflection.Model,\n  type: unknown,\n  options: valueof HttpPartOptions\n);\n\n/**\n * Specify if inapplicable metadata should be included in the payload for the given entity.\n * @param value If true, inapplicable metadata will be included in the payload.\n */\nextern dec includeInapplicableMetadataInPayload(target: unknown, value: valueof boolean);\n\n/**\n * The visibility mode for the merge patch transform.\n */\nenum MergePatchVisibilityMode {\n  /**\n   * The Update mode. This is used when a resource can be updated but must already exist.\n   */\n  Update,\n\n  /**\n   * The Create or Update mode. This is used when a resource can be created OR updated in a single operation.\n   */\n  CreateOrUpdate,\n}\n\n/**\n * Options for the `@applyMergePatch` decorator.\n */\nmodel ApplyMergePatchOptions {\n  /**\n   * The visibility mode to use.\n   */\n  visibilityMode: MergePatchVisibilityMode;\n}\n\n/**\n * Performs the canonical merge-patch transformation on the given model and injects its\n * transformed properties into the target.\n */\nextern dec applyMergePatch(\n  target: Reflection.Model,\n  source: Reflection.Model,\n  nameTemplate: valueof string,\n  options: valueof ApplyMergePatchOptions\n);\n\n/**\n * Marks a model that was generated by applying the MergePatch\n * transform and links to its source model\n */\nextern dec mergePatchModel(target: Reflection.Model, source: Reflection.Model);\n\n/**\n * Links a modelProperty mutated as part of a mergePatch transform to\n * its source property;\n */\nextern dec mergePatchProperty(target: Reflection.ModelProperty, source: Reflection.ModelProperty);\n",
  "../http/lib/auth.tsp": 'namespace TypeSpec.Http;\n\n@doc("Authentication type")\nenum AuthType {\n  @doc("HTTP")\n  http,\n\n  @doc("API key")\n  apiKey,\n\n  @doc("OAuth2")\n  oauth2,\n\n  @doc("OpenID connect")\n  openIdConnect,\n\n  @doc("Empty auth")\n  noAuth,\n}\n\n/**\n * Basic authentication is a simple authentication scheme built into the HTTP protocol.\n * The client sends HTTP requests with the Authorization header that contains the word Basic word followed by a space and a base64-encoded string username:password.\n * For example, to authorize as demo / `p@55w0rd` the client would send\n * ```\n * Authorization: Basic ZGVtbzpwQDU1dzByZA==\n * ```\n */\n@doc("")\nmodel BasicAuth {\n  @doc("Http authentication")\n  type: AuthType.http;\n\n  @doc("basic auth scheme")\n  scheme: "Basic";\n}\n\n/**\n * Bearer authentication (also called token authentication) is an HTTP authentication scheme that involves security tokens called bearer tokens.\n * The name \u201CBearer authentication\u201D can be understood as \u201Cgive access to the bearer of this token.\u201D The bearer token is a cryptic string, usually generated by the server in response to a login request.\n * The client must send this token in the Authorization header when making requests to protected resources:\n * ```\n * Authorization: Bearer <token>\n * ```\n */\n@doc("")\nmodel BearerAuth {\n  @doc("Http authentication")\n  type: AuthType.http;\n\n  @doc("bearer auth scheme")\n  scheme: "Bearer";\n}\n\n@doc("Describes the location of the API key")\nenum ApiKeyLocation {\n  @doc("API key is a header value")\n  header,\n\n  @doc("API key is a query parameter")\n  query,\n\n  @doc("API key is found in a cookie")\n  cookie,\n}\n\n/**\n * An API key is a token that a client provides when making API calls. The key can be sent in the query string:\n *\n * ```\n * GET /something?api_key=abcdef12345\n * ```\n *\n * or as a request header\n *\n * ```\n * GET /something HTTP/1.1\n * X-API-Key: abcdef12345\n * ```\n *\n * or as a cookie\n *\n * ```\n * GET /something HTTP/1.1\n * Cookie: X-API-KEY=abcdef12345\n * ```\n *\n * @template Location The location of the API key\n * @template Name The name of the API key\n */\n@doc("")\nmodel ApiKeyAuth<Location extends ApiKeyLocation, Name extends string> {\n  @doc("API key authentication")\n  type: AuthType.apiKey;\n\n  @doc("location of the API key")\n  in: Location;\n\n  @doc("name of the API key")\n  name: Name;\n}\n\n/**\n * OAuth 2.0 is an authorization protocol that gives an API client limited access to user data on a web server.\n *\n * OAuth relies on authentication scenarios called flows, which allow the resource owner (user) to share the protected content from the resource server without sharing their credentials.\n * For that purpose, an OAuth 2.0 server issues access tokens that the client applications can use to access protected resources on behalf of the resource owner.\n * For more information about OAuth 2.0, see oauth.net and RFC 6749.\n *\n * @template Flows The list of supported OAuth2 flows\n * @template Scopes The list of OAuth2 scopes, which are common for every flow from `Flows`. This list is combined with the scopes defined in specific OAuth2 flows.\n */\n@doc("")\nmodel OAuth2Auth<Flows extends OAuth2Flow[], Scopes extends string[] = []> {\n  @doc("OAuth2 authentication")\n  type: AuthType.oauth2;\n\n  @doc("Supported OAuth2 flows")\n  flows: Flows;\n\n  @doc("Oauth2 scopes of every flow. Overridden by scope definitions in specific flows")\n  defaultScopes: Scopes;\n}\n\n@doc("Describes the OAuth2 flow type")\nenum OAuth2FlowType {\n  @doc("authorization code flow")\n  authorizationCode,\n\n  @doc("implicit flow")\n  implicit,\n\n  @doc("password flow")\n  password,\n\n  @doc("client credential flow")\n  clientCredentials,\n}\n\nalias OAuth2Flow = AuthorizationCodeFlow | ImplicitFlow | PasswordFlow | ClientCredentialsFlow;\n\n@doc("Authorization Code flow")\nmodel AuthorizationCodeFlow {\n  @doc("authorization code flow")\n  type: OAuth2FlowType.authorizationCode;\n\n  @doc("the authorization URL")\n  authorizationUrl: string;\n\n  @doc("the token URL")\n  tokenUrl: string;\n\n  @doc("the refresh URL")\n  refreshUrl?: string;\n\n  @doc("list of scopes for the credential")\n  scopes?: string[];\n}\n\n@doc("Implicit flow")\nmodel ImplicitFlow {\n  @doc("implicit flow")\n  type: OAuth2FlowType.implicit;\n\n  @doc("the authorization URL")\n  authorizationUrl: string;\n\n  @doc("the refresh URL")\n  refreshUrl?: string;\n\n  @doc("list of scopes for the credential")\n  scopes?: string[];\n}\n\n@doc("Resource Owner Password flow")\nmodel PasswordFlow {\n  @doc("password flow")\n  type: OAuth2FlowType.password;\n\n  @doc("the token URL")\n  tokenUrl: string;\n\n  @doc("the refresh URL")\n  refreshUrl?: string;\n\n  @doc("list of scopes for the credential")\n  scopes?: string[];\n}\n\n@doc("Client credentials flow")\nmodel ClientCredentialsFlow {\n  @doc("client credential flow")\n  type: OAuth2FlowType.clientCredentials;\n\n  @doc("the token URL")\n  tokenUrl: string;\n\n  @doc("the refresh URL")\n  refreshUrl?: string;\n\n  @doc("list of scopes for the credential")\n  scopes?: string[];\n}\n\n/**\n * OpenID Connect (OIDC) is an identity layer built on top of the OAuth 2.0 protocol and supported by some OAuth 2.0 providers, such as Google and Azure Active Directory.\n * It defines a sign-in flow that enables a client application to authenticate a user, and to obtain information (or "claims") about that user, such as the user name, email, and so on.\n * User identity information is encoded in a secure JSON Web Token (JWT), called ID token.\n * OpenID Connect defines a discovery mechanism, called OpenID Connect Discovery, where an OpenID server publishes its metadata at a well-known URL, typically\n *\n * ```http\n * https://server.com/.well-known/openid-configuration\n * ```\n */\nmodel OpenIdConnectAuth<ConnectUrl extends string> {\n  /** Auth type */\n  type: AuthType.openIdConnect;\n\n  /** Connect url. It can be specified relative to the server URL */\n  openIdConnectUrl: ConnectUrl;\n}\n\n/**\n * This authentication option signifies that API is not secured at all.\n * It might be useful when overriding authentication on interface of operation level.\n */\n@doc("")\nmodel NoAuth {\n  type: AuthType.noAuth;\n}\n',
  "lib/rest-decorators.tsp": 'namespace TypeSpec.Rest;\n\nusing TypeSpec.Reflection;\n\n/**\n * This interface or operation should resolve its route automatically. To be used with resource types where the route segments area defined on the models.\n *\n * @example\n *\n * ```typespec\n * @autoRoute\n * interface Pets {\n *   get(@segment("pets") @path id: string): void; //-> route: /pets/{id}\n * }\n * ```\n */\nextern dec autoRoute(target: Interface | Operation);\n\n/**\n * Defines the preceding path segment for a @path parameter in auto-generated routes.\n *\n * @param name Segment that will be inserted into the operation route before the path parameter\'s name field.\n *\n * @example\n * @autoRoute\n * interface Pets {\n *   get(@segment("pets") @path id: string): void; //-> route: /pets/{id}\n * }\n */\nextern dec segment(target: Model | ModelProperty | Operation, name: valueof string);\n\n/**\n * Returns the URL segment of a given model if it has `@segment` and `@key` decorator.\n * @param type Target model\n */\nextern dec segmentOf(target: Operation, type: Model);\n\n/**\n * Defines the separator string that is inserted before the action name in auto-generated routes for actions.\n *\n * @param seperator Seperator seperating the action segment from the rest of the url\n */\nextern dec actionSeparator(\n  target: Model | ModelProperty | Operation,\n  seperator: valueof "/" | ":" | "/:"\n);\n\n/**\n * Mark this model as a resource type with a name.\n *\n * @param collectionName type\'s collection name\n */\nextern dec resource(target: Model, collectionName: valueof string);\n\n/**\n * Mark model as a child of the given parent resource.\n * @param parent Parent model.\n */\nextern dec parentResource(target: Model, parent: Model);\n\n/**\n * Specify that this is a Read operation for a given resource.\n *\n * @param resourceType Resource marked with @resource\n */\nextern dec readsResource(target: Operation, resourceType: Model);\n\n/**\n * Specify that this is a Create operation for a given resource.\n *\n * @param resourceType Resource marked with @resource\n */\nextern dec createsResource(target: Operation, resourceType: Model);\n\n/**\n * Specify that this is a CreateOrReplace operation for a given resource.\n *\n * @param resourceType Resource marked with @resource\n */\nextern dec createsOrReplacesResource(target: Operation, resourceType: Model);\n\n/**\n * Specify that this is a CreatesOrUpdate operation for a given resource.\n *\n * @param resourceType Resource marked with @resource\n */\nextern dec createsOrUpdatesResource(target: Operation, resourceType: Model);\n\n/**\n * Specify that this is a Update operation for a given resource.\n *\n * @param resourceType Resource marked with @resource\n */\nextern dec updatesResource(target: Operation, resourceType: Model);\n\n/**\n * Specify that this is a Delete operation for a given resource.\n *\n * @param resourceType Resource marked with @resource\n */\nextern dec deletesResource(target: Operation, resourceType: Model);\n\n/**\n * Specify that this is a List operation for a given resource.\n *\n * @param resourceType Resource marked with @resource\n */\nextern dec listsResource(target: Operation, resourceType: Model);\n\n/**\n * Specify this operation is an action. (Scoped to a resource item /pets/{petId}/my-action)\n * @param name Name of the action. If not specified, the name of the operation will be used.\n */\nextern dec action(target: Operation, name?: valueof string);\n\n/**\n * Specify this operation is a collection action. (Scopped to a resource, /pets/my-action)\n * @param resourceType Resource marked with @resource\n * @param name Name of the action. If not specified, the name of the operation will be used.\n */\nextern dec collectionAction(target: Operation, resourceType: Model, name?: valueof string);\n\n/**\n * Copy the resource key parameters on the model\n * @param filter Filter to exclude certain properties.\n */\nextern dec copyResourceKeyParameters(target: Model, filter?: valueof string);\n\nnamespace Private {\n  extern dec resourceLocation(target: string, resourceType: Model);\n  extern dec validateHasKey(target: unknown, value: unknown);\n  extern dec validateIsError(target: unknown, value: unknown);\n  extern dec actionSegment(target: Operation, value: valueof string);\n  extern dec resourceTypeForKeyParam(entity: ModelProperty, resourceType: Model);\n}\n',
  "lib/resource.tsp": 'import "@typespec/http";\nimport "../dist/src/internal-decorators.js";\n\nnamespace TypeSpec.Rest.Resource;\n\nusing Http;\n\n@doc("The default error response for resource operations.")\nmodel ResourceError {\n  @doc("The error code.")\n  code: int32;\n\n  @doc("The error message.")\n  message: string;\n}\n\n/**\n * Dynamically gathers keys of the model type `Resource`.\n *\n * @template Resource The target resource model.\n */\n@doc("Dynamically gathers keys of the model type Resource.")\n@copyResourceKeyParameters\n@friendlyName("{name}Key", Resource)\nmodel KeysOf<Resource> {}\n\n/**\n * Dynamically gathers parent keys of the model type `Resource`.\n *\n * @template Resource The target resource model.\n */\n@doc("Dynamically gathers parent keys of the model type Resource.")\n@copyResourceKeyParameters("parent")\n@friendlyName("{name}ParentKey", Resource)\nmodel ParentKeysOf<Resource> {}\n\n/**\n * Represents operation parameters for the resource of type `Resource`.\n *\n * @template Resource The resource model.\n */\n@doc("Represents operation parameters for resource Resource.")\nmodel ResourceParameters<Resource extends {}> {\n  ...KeysOf<Resource>;\n}\n\n/**\n * Represents collection operation parameters for the resource of type `Resource`.\n *\n * @template Resource The resource model.\n */\n@doc("Represents collection operation parameters for resource Resource.")\nmodel ResourceCollectionParameters<Resource extends {}> {\n  ...ParentKeysOf<Resource>;\n}\n\n/**\n * Represents the resource GET operation.\n *\n * @template Resource The resource model.\n * @template Error The error response.\n */\n@Private.validateHasKey(Resource)\n@Private.validateIsError(Error)\ninterface ResourceRead<Resource extends {}, Error> {\n  /**\n   * Gets an instance of the resource.\n   *\n   * @template Resource The resource model.\n   */\n  @autoRoute\n  @doc("Gets an instance of the resource.")\n  @readsResource(Resource)\n  get(...ResourceParameters<Resource>): Resource | Error;\n}\n\n/**\n * Resource create operation completed successfully.\n *\n * @template Resource The resource model that was created.\n */\n@doc("Resource create operation completed successfully.")\nmodel ResourceCreatedResponse<Resource> {\n  ...CreatedResponse;\n  @bodyRoot body: Resource;\n}\n\n/**\n * Resource create or replace operation template.\n *\n * @template Resource The resource model to create or replace.\n * @template Error The error response.\n */\ninterface ResourceCreateOrReplace<Resource extends {}, Error> {\n  /**\n   * Creates or replaces a instance of the resource.\n   *\n   * @template Resource The resource model to create or replace.\n   * @template Error The error response.\n   */\n  @autoRoute\n  @doc("Creates or replaces an instance of the resource.")\n  @createsOrReplacesResource(Resource)\n  createOrReplace(\n    ...ResourceParameters<Resource>,\n    @bodyRoot resource: ResourceCreateModel<Resource>,\n  ): Resource | ResourceCreatedResponse<Resource> | Error;\n}\n\n/**\n * Resource create or update operation model.\n *\n * @template Resource The resource model to create or update.\n */\n@friendlyName("{name}Update", Resource)\nmodel ResourceCreateOrUpdateModel<Resource extends {}>\n  is OptionalProperties<UpdateableProperties<DefaultKeyVisibility<Resource, Lifecycle.Read>>>;\n\n/**\n * Resource create or update operation template.\n *\n * @template Resource The resource model to create or update.\n * @template Error The error response.\n */\ninterface ResourceCreateOrUpdate<Resource extends {}, Error> {\n  /**\n   * Creates or update an instance of the resource.\n   *\n   * @template Resource The resource model to create or update.\n   * @template Error The error response.\n   */\n  @autoRoute\n  @doc("Creates or update an instance of the resource.")\n  @createsOrUpdatesResource(Resource)\n  @patch(#{ implicitOptionality: true }) // for legacy behavior\n  createOrUpdate(\n    ...ResourceParameters<Resource>,\n    @bodyRoot resource: ResourceCreateOrUpdateModel<Resource>,\n  ): Resource | ResourceCreatedResponse<Resource> | Error;\n}\n\n/**\n * Resource create operation model.\n *\n * @template Resource The resource model to create.\n */\n@friendlyName("{name}Create", Resource)\n@withVisibility(Lifecycle.Create)\nmodel ResourceCreateModel<Resource extends {}> is DefaultKeyVisibility<Resource, Lifecycle.Read>;\n\n/**\n * Resource create operation template.\n *\n * @template Resource The resource model to create.\n * @template Error The error response.\n */\ninterface ResourceCreate<Resource extends {}, Error> {\n  /**\n   * Creates a new instance of the resource.\n   *\n   * @template Resource The resource model to create.\n   * @template Error The error response.\n   */\n  @autoRoute\n  @doc("Creates a new instance of the resource.")\n  @createsResource(Resource)\n  create(\n    ...ResourceCollectionParameters<Resource>,\n    @bodyRoot resource: ResourceCreateModel<Resource>,\n  ): Resource | ResourceCreatedResponse<Resource> | Error;\n}\n\n/**\n * Resource update operation template.\n *\n * @template Resource The resource model to update.\n * @template Error The error response.\n */\n@Private.validateHasKey(Resource)\n@Private.validateIsError(Error)\ninterface ResourceUpdate<Resource extends {}, Error> {\n  /**\n   * Updates an existing instance of the resource.\n   *\n   * @template Resource The resource model to update.\n   * @template Error The error response.\n   */\n  @autoRoute\n  @doc("Updates an existing instance of the resource.")\n  @updatesResource(Resource)\n  @patch(#{ implicitOptionality: true }) // for legacy behavior\n  update(\n    ...ResourceParameters<Resource>,\n    @bodyRoot properties: ResourceCreateOrUpdateModel<Resource>,\n  ): Resource | Error;\n}\n\n@doc("Resource deleted successfully.")\nmodel ResourceDeletedResponse {\n  @doc("The status code.")\n  @statusCode\n  _: 200;\n}\n\n/**\n * Resource delete operation template.\n *\n * @template Resource The resource model to delete.\n * @template Error The error response.\n */\n@Private.validateHasKey(Resource)\n@Private.validateIsError(Error)\ninterface ResourceDelete<Resource extends {}, Error> {\n  /**\n   * Deletes an existing instance of the resource.\n   *\n   * @template Resource The resource model to delete.\n   * @template Error The error response.\n   */\n  @autoRoute\n  @doc("Deletes an existing instance of the resource.")\n  @deletesResource(Resource)\n  delete(...ResourceParameters<Resource>): ResourceDeletedResponse | Error;\n}\n\n/**\n * Structure for a paging response using `value` and `nextLink` to represent pagination.\n *\n * @template Resource The resource type of the collection.\n */\n@doc("Paged response of {name} items", Resource)\n@friendlyName("{name}CollectionWithNextLink", Resource)\nmodel CollectionWithNextLink<Resource extends {}> {\n  @doc("The items on this page")\n  @pageItems\n  value: Resource[];\n\n  @doc("The link to the next page of items")\n  @nextLink\n  nextLink?: ResourceLocation<Resource>;\n}\n\n/**\n * Resource list operation template.\n *\n * @template Resource The resource model to list.\n * @template Error The error response.\n */\ninterface ResourceList<Resource extends {}, Error> {\n  /**\n   * Lists all instances of the resource.\n   *\n   * @template Resource The resource model to list.\n   * @template Error The error response.\n   */\n  @autoRoute\n  @doc("Lists all instances of the resource.")\n  @listsResource(Resource)\n  list(...ResourceCollectionParameters<Resource>): CollectionWithNextLink<Resource> | Error;\n}\n\n/**\n * Resource operation templates for resource instances.\n *\n * @template Resource The resource model.\n * @template Error The error response.\n */\n@Private.validateHasKey(Resource)\n@Private.validateIsError(Error)\ninterface ResourceInstanceOperations<Resource extends {}, Error>\n  extends ResourceRead<Resource, Error>,\n    ResourceUpdate<Resource, Error>,\n    ResourceDelete<Resource, Error> {}\n\n/**\n * Resource operation templates for resource collections.\n *\n * @template Resource The resource model.\n * @template Error The error response.\n */\n@Private.validateHasKey(Resource)\n@Private.validateIsError(Error)\ninterface ResourceCollectionOperations<Resource extends {}, Error>\n  extends ResourceCreate<Resource, Error>,\n    ResourceList<Resource, Error> {}\n\n/**\n * Resource operation templates for resources.\n *\n * @template Resource The resource model.\n * @template Error The error response.\n */\n@Private.validateHasKey(Resource)\n@Private.validateIsError(Error)\ninterface ResourceOperations<Resource extends {}, Error>\n  extends ResourceInstanceOperations<Resource, Error>,\n    ResourceCollectionOperations<Resource, Error> {}\n\n/**\n * Singleton resource read operation template.\n *\n * @template Singleton The singleton resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\n@Private.validateHasKey(Resource)\n@Private.validateIsError(Error)\ninterface SingletonResourceRead<Singleton extends {}, Resource extends {}, Error> {\n  /**\n   * Gets the singleton resource.\n   *\n   * @template Singleton The singleton resource model.\n   * @template Resource The resource model.\n   */\n  @autoRoute\n  @doc("Gets the singleton resource.")\n  @segmentOf(Singleton)\n  @readsResource(Singleton)\n  get(...ResourceParameters<Resource>): Singleton | Error;\n}\n\n/**\n * Singleton resource update operation template.\n *\n * @template Singleton The singleton resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\n@Private.validateHasKey(Resource)\n@Private.validateIsError(Error)\ninterface SingletonResourceUpdate<Singleton extends {}, Resource extends {}, Error> {\n  /**\n   * Updates the singleton resource.\n   *\n   * @template Singleton The singleton resource model.\n   * @template Resource The resource model.\n   */\n  @autoRoute\n  @doc("Updates the singleton resource.")\n  @segmentOf(Singleton)\n  @updatesResource(Singleton)\n  @patch(#{ implicitOptionality: true }) // for legacy behavior\n  update(\n    ...ResourceParameters<Resource>,\n\n    @body\n    properties: ResourceCreateOrUpdateModel<Singleton>,\n  ): Singleton | Error;\n}\n\n/**\n * Singleton resource operation templates for singleton resource instances.\n *\n * @template Singleton The singleton resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\ninterface SingletonResourceOperations<Singleton extends {}, Resource extends {}, Error>\n  extends SingletonResourceRead<Singleton, Resource, Error>,\n    SingletonResourceUpdate<Singleton, Resource, Error> {}\n\n/**\n * Extension resource read operation template.\n *\n * @template Extension The extension resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\n@Private.validateHasKey(Resource)\n@Private.validateIsError(Error)\ninterface ExtensionResourceRead<Extension extends {}, Resource extends {}, Error> {\n  /**\n   * Gets an instance of the extension resource.\n   *\n   * @template Extension The extension resource model.\n   * @template Resource The resource model.\n   */\n  @autoRoute\n  @doc("Gets an instance of the extension resource.")\n  @readsResource(Extension)\n  get(...ResourceParameters<Resource>, ...ResourceParameters<Extension>): Extension | Error;\n}\n\n/**\n * Extension resource create or update operation template.\n *\n * @template Extension The extension resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\ninterface ExtensionResourceCreateOrUpdate<Extension extends {}, Resource extends {}, Error> {\n  /**\n   * Creates or update an instance of the extension resource.\n   *\n   * @template Extension The extension resource model.\n   * @template Resource The resource model.\n   */\n  @autoRoute\n  @doc("Creates or update an instance of the extension resource.")\n  @createsOrUpdatesResource(Extension)\n  @patch(#{ implicitOptionality: true }) // for legacy behavior\n  createOrUpdate(\n    ...ResourceParameters<Resource>,\n    ...ResourceParameters<Extension>,\n    @bodyRoot resource: ResourceCreateOrUpdateModel<Extension>,\n  ): Extension | ResourceCreatedResponse<Extension> | Error;\n}\n\n/**\n * Extension resource create operation template.\n *\n * @template Extension The extension resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\ninterface ExtensionResourceCreate<Extension extends {}, Resource extends {}, Error> {\n  /**\n   * Creates a new instance of the extension resource.\n   *\n   * @template Extension The extension resource model.\n   * @template Resource The resource model.\n   */\n  @autoRoute\n  @doc("Creates a new instance of the extension resource.")\n  @createsResource(Extension)\n  create(\n    ...ResourceParameters<Resource>,\n    @bodyRoot resource: ResourceCreateModel<Extension>,\n  ): Extension | ResourceCreatedResponse<Extension> | Error;\n}\n\n/**\n * Extension resource update operation template.\n *\n * @template Extension The extension resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\ninterface ExtensionResourceUpdate<Extension extends {}, Resource extends {}, Error> {\n  /**\n   * Updates an existing instance of the extension resource.\n   *\n   * @template Extension The extension resource model.\n   * @template Resource The resource model.\n   */\n  @autoRoute\n  @doc("Updates an existing instance of the extension resource.")\n  @updatesResource(Extension)\n  @patch(#{ implicitOptionality: true }) // for legacy behavior\n  update(\n    ...ResourceParameters<Resource>,\n    ...ResourceParameters<Extension>,\n\n    @body\n    properties: ResourceCreateOrUpdateModel<Extension>,\n  ): Extension | Error;\n}\n\n/**\n * Extension resource delete operation template.\n *\n * @template Extension The extension resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\ninterface ExtensionResourceDelete<Extension extends {}, Resource extends {}, Error> {\n  /**\n   * Deletes an existing instance of the extension resource.\n   *\n   * @template Extension The extension resource model.\n   * @template Resource The resource model.\n   */\n  @autoRoute\n  @doc("Deletes an existing instance of the extension resource.")\n  @deletesResource(Extension)\n  delete(\n    ...ResourceParameters<Resource>,\n    ...ResourceParameters<Extension>,\n  ): ResourceDeletedResponse | Error;\n}\n\n/**\n * Extension resource list operation template.\n *\n * @template Extension The extension resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\ninterface ExtensionResourceList<Extension extends {}, Resource extends {}, Error> {\n  /**\n   * Lists all instances of the extension resource.\n   *\n   * @template Extension The extension resource model.\n   * @template Resource The resource model.\n   */\n  @autoRoute\n  @doc("Lists all instances of the extension resource.")\n  @listsResource(Extension)\n  list(\n    ...ResourceParameters<Resource>,\n    ...ResourceCollectionParameters<Extension>,\n  ): CollectionWithNextLink<Extension> | Error;\n}\n\n/**\n * Extension resource operation templates for extension resource instances.\n *\n * @template Extension The extension resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\ninterface ExtensionResourceInstanceOperations<Extension extends {}, Resource extends {}, Error>\n  extends ExtensionResourceRead<Extension, Resource, Error>,\n    ExtensionResourceUpdate<Extension, Resource, Error>,\n    ExtensionResourceDelete<Extension, Resource, Error> {}\n\n/**\n * Extension resource operation templates for extension resource collections.\n *\n * @template Extension The extension resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\ninterface ExtensionResourceCollectionOperations<Extension extends {}, Resource extends {}, Error>\n  extends ExtensionResourceCreate<Extension, Resource, Error>,\n    ExtensionResourceList<Extension, Resource, Error> {}\n\n/**\n * Extension resource operation templates for extension resource instances and collections.\n *\n * @template Extension The extension resource model.\n * @template Resource The resource model.\n * @template Error The error response.\n */\ninterface ExtensionResourceOperations<Extension extends {}, Resource extends {}, Error>\n  extends ExtensionResourceInstanceOperations<Extension, Resource, Error>,\n    ExtensionResourceCollectionOperations<Extension, Resource, Error> {}\n'
};
var _TypeSpecLibrary_ = {
  jsSourceFiles: TypeSpecJSSources,
  typespecSourceFiles: TypeSpecSources
};
export {
  $action,
  $actionSegment,
  $actionSeparator,
  $autoRoute,
  $collectionAction,
  $copyResourceKeyParameters,
  $createsOrReplacesResource,
  $createsOrUpdatesResource,
  $createsResource,
  $decorators,
  $deletesResource,
  $lib,
  $listsResource,
  $parentResource,
  $readsResource,
  $resource,
  $resourceLocation,
  $resourceTypeForKeyParam,
  $segment,
  $segmentOf,
  $updatesResource,
  _TypeSpecLibrary_,
  getAction,
  getActionDetails,
  getActionSegment,
  getActionSeparator,
  getCollectionAction,
  getCollectionActionDetails,
  getParentResource,
  getResourceLocationType,
  getResourceOperation,
  getResourceTypeForKeyParam,
  getResourceTypeKey,
  getSegment,
  isAutoRoute,
  isListOperation,
  setResourceOperation,
  setResourceTypeKey
};

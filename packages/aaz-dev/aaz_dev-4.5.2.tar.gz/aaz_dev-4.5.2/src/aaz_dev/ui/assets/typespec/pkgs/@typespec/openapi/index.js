var __defProp = Object.defineProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// src/typespec/core/packages/openapi/dist/src/index.js
var src_exports = {};
__export(src_exports, {
  $decorators: () => $decorators,
  $defaultResponse: () => $defaultResponse,
  $extension: () => $extension,
  $externalDocs: () => $externalDocs,
  $info: () => $info,
  $operationId: () => $operationId,
  checkDuplicateTypeName: () => checkDuplicateTypeName,
  getExtensions: () => getExtensions,
  getExternalDocs: () => getExternalDocs,
  getInfo: () => getInfo,
  getOpenAPITypeName: () => getOpenAPITypeName,
  getOperationId: () => getOperationId,
  getParameterKey: () => getParameterKey,
  getTagsMetadata: () => getTagsMetadata,
  isDefaultResponse: () => isDefaultResponse,
  isReadonlyProperty: () => isReadonlyProperty,
  resolveInfo: () => resolveInfo,
  resolveOperationId: () => resolveOperationId,
  setExtension: () => setExtension,
  setInfo: () => setInfo,
  shouldInline: () => shouldInline
});

// src/typespec/core/packages/openapi/dist/src/decorators.js
import { compilerAssert, getDoc, getService, getSummary, isType, serializeValueAsJson } from "@typespec/compiler";
import { useStateMap } from "@typespec/compiler/utils";
import * as http from "@typespec/http";

// src/typespec/core/packages/openapi/dist/src/helpers.js
import { getFriendlyName, getLifecycleVisibilityEnum, getProperty, getTypeName, getVisibilityForClass, isGlobalNamespace, isService, isTemplateInstance } from "@typespec/compiler";

// src/typespec/core/packages/openapi/dist/src/lib.js
import { createTypeSpecLibrary, paramMessage } from "@typespec/compiler";
var $lib = createTypeSpecLibrary({
  name: "@typespec/openapi",
  diagnostics: {
    "invalid-extension-key": {
      severity: "error",
      messages: {
        default: paramMessage`OpenAPI extension must start with 'x-' but was '${"value"}'`
      }
    },
    "duplicate-type-name": {
      severity: "error",
      messages: {
        default: paramMessage`Duplicate type name: '${"value"}'. Check @friendlyName decorators and overlap with types in TypeSpec or service namespace.`,
        parameter: paramMessage`Duplicate parameter key: '${"value"}'. Check @friendlyName decorators and overlap with types in TypeSpec or service namespace.`
      }
    },
    "not-url": {
      severity: "error",
      messages: {
        default: paramMessage`${"property"}: ${"value"} is not a valid URL.`
      }
    },
    "duplicate-tag": {
      severity: "error",
      messages: {
        default: paramMessage`"Metadata for tag '${"tagName"}' was specified twice."`
      }
    },
    "tag-metadata-target-service": {
      severity: "error",
      messages: {
        default: paramMessage`@tagMetadata must be used on the service namespace. Did you mean to annotate '${"namespace"}'  with '@service'?`
      }
    }
  },
  state: {
    tagsMetadata: { description: "State for the @tagMetadata decorator." }
  }
});
var { createDiagnostic, reportDiagnostic, createStateSymbol, stateKeys: OpenAPIKeys } = $lib;

// src/typespec/core/packages/openapi/dist/src/helpers.js
function shouldInline(program, type) {
  if (getFriendlyName(program, type)) {
    return false;
  }
  switch (type.kind) {
    case "Model":
      return !type.name || isTemplateInstance(type);
    case "Scalar":
      return program.checker.isStdType(type) || isTemplateInstance(type);
    case "Enum":
    case "Union":
      return !type.name;
    default:
      return true;
  }
}
function getOpenAPITypeName(program, type, options, existing) {
  const name = getFriendlyName(program, type) ?? getTypeName(type, options);
  checkDuplicateTypeName(program, type, name, existing);
  return name;
}
function checkDuplicateTypeName(program, type, name, existing) {
  if (existing && existing[name]) {
    reportDiagnostic(program, {
      code: "duplicate-type-name",
      format: {
        value: name
      },
      target: type
    });
  }
}
function getParameterKey(program, property, newParam, existingParams, options) {
  const parent = property.model;
  let key = getOpenAPITypeName(program, parent, options);
  if (parent.properties.size > 1) {
    key += `.${property.name}`;
  }
  if (existingParams[key]) {
    reportDiagnostic(program, {
      code: "duplicate-type-name",
      messageId: "parameter",
      format: {
        value: key
      },
      target: property
    });
  }
  return key;
}
function resolveOperationId(program, operation) {
  const explicitOperationId = getOperationId(program, operation);
  if (explicitOperationId) {
    return explicitOperationId;
  }
  if (operation.interface) {
    return `${operation.interface.name}_${operation.name}`;
  }
  const namespace = operation.namespace;
  if (namespace === void 0 || isGlobalNamespace(program, namespace) || isService(program, namespace)) {
    return operation.name;
  }
  return `${namespace.name}_${operation.name}`;
}
function isReadonlyProperty(program, property) {
  const Lifecycle = getLifecycleVisibilityEnum(program);
  const visibility = getVisibilityForClass(program, property, getLifecycleVisibilityEnum(program));
  return visibility.size === 1 && visibility.has(Lifecycle.members.get("Read"));
}
function isOpenAPIExtensionKey(key) {
  return key.startsWith("x-");
}
function validateIsUri(program, target, url, propertyName) {
  try {
    new URL(url);
    return true;
  } catch {
    reportDiagnostic(program, {
      code: "not-url",
      target,
      format: { property: propertyName, value: url }
    });
    return false;
  }
}
function validateAdditionalInfoModel(program, target, jsonObject, reference) {
  const propertyModel = program.resolveTypeReference(reference)[0];
  if (jsonObject && propertyModel) {
    const diagnostics = checkNoAdditionalProperties(jsonObject, target, propertyModel);
    program.reportDiagnostics(diagnostics);
    if (diagnostics.length > 0) {
      return false;
    }
  }
  return true;
}
function checkNoAdditionalProperties(jsonObject, target, source) {
  const diagnostics = [];
  for (const name of Object.keys(jsonObject)) {
    const sourceProperty = getProperty(source, name);
    if (sourceProperty) {
      if (sourceProperty.type.kind === "Model") {
        const nestedDiagnostics = checkNoAdditionalProperties(jsonObject[name], target, sourceProperty.type);
        diagnostics.push(...nestedDiagnostics);
      }
    } else if (!isOpenAPIExtensionKey(name)) {
      diagnostics.push(createDiagnostic({
        code: "invalid-extension-key",
        format: { value: name },
        target
      }));
    }
  }
  return diagnostics;
}

// src/typespec/core/packages/openapi/dist/src/decorators.js
var operationIdsKey = createStateSymbol("operationIds");
var $operationId = (context, entity, opId) => {
  context.program.stateMap(operationIdsKey).set(entity, opId);
};
function getOperationId(program, entity) {
  return program.stateMap(operationIdsKey).get(entity);
}
var openApiExtensionKey = createStateSymbol("openApiExtension");
var $extension = (context, entity, extensionName, value) => {
  compilerAssert(!value || !isType(value), "OpenAPI extension value must be a value but was a type", context.getArgumentTarget(1));
  const processed = convertRemainingValuesToExtensions(context.program, value);
  setExtension(context.program, entity, extensionName, processed);
};
function convertRemainingValuesToExtensions(program, value) {
  switch (typeof value) {
    case "string":
    case "number":
    case "boolean":
      return value;
    case "object":
      if (value === null) {
        return null;
      }
      if (Array.isArray(value)) {
        return value.map((x) => convertRemainingValuesToExtensions(program, x));
      }
      if (isTypeSpecValue(value)) {
        return serializeValueAsJson(program, value, value.type);
      } else {
        const result = {};
        for (const [key, val] of Object.entries(value)) {
          if (val === void 0) {
            continue;
          }
          result[key] = convertRemainingValuesToExtensions(program, val);
        }
        return result;
      }
    default:
      return value;
  }
}
function isTypeSpecValue(value) {
  return "entityKind" in value && value.entityKind === "Value";
}
function setInfo(program, entity, data) {
  program.stateMap(infoKey).set(entity, data);
}
function setExtension(program, entity, extensionName, data) {
  const openApiExtensions = program.stateMap(openApiExtensionKey);
  const typeExtensions = openApiExtensions.get(entity) ?? /* @__PURE__ */ new Map();
  typeExtensions.set(extensionName, data);
  openApiExtensions.set(entity, typeExtensions);
}
function getExtensions(program, entity) {
  return program.stateMap(openApiExtensionKey).get(entity) ?? /* @__PURE__ */ new Map();
}
var defaultResponseKey = createStateSymbol("defaultResponse");
var $defaultResponse = (context, entity) => {
  http.setStatusCode(context.program, entity, ["*"]);
  context.program.stateSet(defaultResponseKey).add(entity);
};
function isDefaultResponse(program, entity) {
  return program.stateSet(defaultResponseKey).has(entity);
}
var externalDocsKey = createStateSymbol("externalDocs");
var $externalDocs = (context, target, url, description) => {
  const doc = { url };
  if (description) {
    doc.description = description;
  }
  context.program.stateMap(externalDocsKey).set(target, doc);
};
function getExternalDocs(program, entity) {
  return program.stateMap(externalDocsKey).get(entity);
}
var infoKey = createStateSymbol("info");
var $info = (context, entity, data) => {
  if (data === void 0) {
    return;
  }
  if (!validateAdditionalInfoModel(context.program, context.getArgumentTarget(0), data, "TypeSpec.OpenAPI.AdditionalInfo")) {
    return;
  }
  if (data.termsOfService) {
    if (!validateIsUri(context.program, context.getArgumentTarget(0), data.termsOfService, "TermsOfService")) {
      return;
    }
  }
  setInfo(context.program, entity, data);
};
function getInfo(program, entity) {
  return program.stateMap(infoKey).get(entity);
}
function resolveInfo(program, entity) {
  const info = getInfo(program, entity);
  const service = getService(program, entity);
  return omitUndefined({
    ...info,
    title: info?.title ?? service?.title,
    version: info?.version,
    summary: info?.summary ?? getSummary(program, entity),
    description: info?.description ?? getDoc(program, entity)
  });
}
function omitUndefined(data) {
  return Object.fromEntries(Object.entries(data).filter(([k, v]) => v !== void 0));
}
var [getTagsMetadata, setTagsMetadata] = useStateMap(OpenAPIKeys.tagsMetadata);
var tagMetadataDecorator = (context, entity, name, tagMetadata) => {
  if (!entity.decorators.some((decorator) => decorator.definition?.name === "@service" && decorator.definition?.namespace.name === "TypeSpec")) {
    reportDiagnostic(context.program, {
      code: "tag-metadata-target-service",
      format: {
        namespace: entity.name
      },
      target: context.getArgumentTarget(0)
    });
    return;
  }
  const tags = getTagsMetadata(context.program, entity) ?? {};
  if (tags[name]) {
    reportDiagnostic(context.program, {
      code: "duplicate-tag",
      format: { tagName: name },
      target: context.getArgumentTarget(0)
    });
    return;
  }
  if (!validateAdditionalInfoModel(context.program, context.getArgumentTarget(0), tagMetadata, "TypeSpec.OpenAPI.TagMetadata")) {
    return;
  }
  if (tagMetadata.externalDocs?.url) {
    if (!validateIsUri(context.program, context.getArgumentTarget(0), tagMetadata.externalDocs.url, "externalDocs.url")) {
      return;
    }
  }
  tags[name] = tagMetadata;
  setTagsMetadata(context.program, entity, tags);
};

// src/typespec/core/packages/openapi/dist/src/tsp-index.js
var tsp_index_exports = {};
__export(tsp_index_exports, {
  $decorators: () => $decorators,
  $lib: () => $lib
});
var $decorators = {
  "TypeSpec.OpenAPI": {
    defaultResponse: $defaultResponse,
    extension: $extension,
    externalDocs: $externalDocs,
    info: $info,
    operationId: $operationId,
    tagMetadata: tagMetadataDecorator
  }
};

// virtual:virtual:entry.js
var TypeSpecJSSources = {
  "dist/src/index.js": src_exports,
  "dist/src/tsp-index.js": tsp_index_exports
};
var TypeSpecSources = {
  "package.json": '{"name":"@typespec/openapi","version":"1.4.0","author":"Microsoft Corporation","description":"TypeSpec library providing OpenAPI concepts","homepage":"https://typespec.io","readme":"https://github.com/microsoft/typespec/blob/main/README.md","license":"MIT","repository":{"type":"git","url":"git+https://github.com/microsoft/typespec.git"},"bugs":{"url":"https://github.com/microsoft/typespec/issues"},"keywords":["typespec"],"type":"module","main":"dist/src/index.js","tspMain":"lib/main.tsp","exports":{".":{"typespec":"./lib/main.tsp","types":"./dist/src/index.d.ts","default":"./dist/src/index.js"},"./testing":{"types":"./dist/src/testing/index.d.ts","default":"./dist/src/testing/index.js"}},"engines":{"node":">=20.0.0"},"scripts":{"clean":"rimraf ./dist ./temp","build":"pnpm gen-extern-signature && tsc -p . && pnpm lint-typespec-library && pnpm api-extractor","watch":"tsc -p . --watch","gen-extern-signature":"tspd --enable-experimental gen-extern-signature .","lint-typespec-library":"tsp compile . --warn-as-error --import @typespec/library-linter --no-emit","test":"vitest run","test:watch":"vitest -w","test:ui":"vitest --ui","test:ci":"vitest run --coverage --reporter=junit --reporter=default","lint":"eslint . --max-warnings=0","lint:fix":"eslint . --fix","regen-docs":"tspd doc .  --enable-experimental --llmstxt --output-dir ../../website/src/content/docs/docs/libraries/openapi/reference","api-extractor":"api-extractor run --local --verbose"},"files":["lib/*.tsp","dist/**","!dist/test/**"],"peerDependencies":{"@typespec/compiler":"workspace:^","@typespec/http":"workspace:^"},"devDependencies":{"@types/node":"~24.3.0","@typespec/compiler":"workspace:^","@typespec/http":"workspace:^","@typespec/library-linter":"workspace:^","@typespec/rest":"workspace:^","@typespec/tspd":"workspace:^","@vitest/coverage-v8":"^3.1.2","@vitest/ui":"^3.1.2","c8":"^10.1.3","rimraf":"~6.0.1","typescript":"~5.9.2","vitest":"^3.1.2"}}',
  "../compiler/lib/intrinsics.tsp": 'import "../dist/src/lib/intrinsic/tsp-index.js";\nimport "./prototypes.tsp";\n\n// This file contains all the intrinsic types of typespec. Everything here will always be loaded\nnamespace TypeSpec;\n\n/**\n * Represent a byte array\n */\nscalar bytes;\n\n/**\n * A numeric type\n */\nscalar numeric;\n\n/**\n * A whole number. This represent any `integer` value possible.\n * It is commonly represented as `BigInteger` in some languages.\n */\nscalar integer extends numeric;\n\n/**\n * A number with decimal value\n */\nscalar float extends numeric;\n\n/**\n * A 64-bit integer. (`-9,223,372,036,854,775,808` to `9,223,372,036,854,775,807`)\n */\nscalar int64 extends integer;\n\n/**\n * A 32-bit integer. (`-2,147,483,648` to `2,147,483,647`)\n */\nscalar int32 extends int64;\n\n/**\n * A 16-bit integer. (`-32,768` to `32,767`)\n */\nscalar int16 extends int32;\n\n/**\n * A 8-bit integer. (`-128` to `127`)\n */\nscalar int8 extends int16;\n\n/**\n * A 64-bit unsigned integer (`0` to `18,446,744,073,709,551,615`)\n */\nscalar uint64 extends integer;\n\n/**\n * A 32-bit unsigned integer (`0` to `4,294,967,295`)\n */\nscalar uint32 extends uint64;\n\n/**\n * A 16-bit unsigned integer (`0` to `65,535`)\n */\nscalar uint16 extends uint32;\n\n/**\n * A 8-bit unsigned integer (`0` to `255`)\n */\nscalar uint8 extends uint16;\n\n/**\n * An integer that can be serialized to JSON (`\u22129007199254740991 (\u2212(2^53 \u2212 1))` to `9007199254740991 (2^53 \u2212 1)` )\n */\nscalar safeint extends int64;\n\n/**\n * A 64 bit floating point number. (`\xB15.0 \xD7 10^\u2212324` to `\xB11.7 \xD7 10^308`)\n */\nscalar float64 extends float;\n\n/**\n * A 32 bit floating point number. (`\xB11.5 x 10^\u221245` to `\xB13.4 x 10^38`)\n */\nscalar float32 extends float64;\n\n/**\n * A decimal number with any length and precision. This represent any `decimal` value possible.\n * It is commonly represented as `BigDecimal` in some languages.\n */\nscalar decimal extends numeric;\n\n/**\n * A 128-bit decimal number.\n */\nscalar decimal128 extends decimal;\n\n/**\n * A sequence of textual characters.\n */\nscalar string;\n\n/**\n * A date on a calendar without a time zone, e.g. "April 10th"\n */\nscalar plainDate {\n  /**\n   * Create a plain date from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const date = plainDate.fromISO("2024-05-06");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * A time on a clock without a time zone, e.g. "3:00 am"\n */\nscalar plainTime {\n  /**\n   * Create a plain time from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const time = plainTime.fromISO("12:34");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * An instant in coordinated universal time (UTC)"\n */\nscalar utcDateTime {\n  /**\n   * Create a date from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const time = utcDateTime.fromISO("2024-05-06T12:20-12Z");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * A date and time in a particular time zone, e.g. "April 10th at 3:00am in PST"\n */\nscalar offsetDateTime {\n  /**\n   * Create a date from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const time = offsetDateTime.fromISO("2024-05-06T12:20-12-0700");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * A duration/time period. e.g 5s, 10h\n */\nscalar duration {\n  /**\n   * Create a duration from an ISO 8601 string.\n   * @example\n   *\n   * ```tsp\n   * const time = duration.fromISO("P1Y1D");\n   * ```\n   */\n  init fromISO(value: string);\n}\n\n/**\n * Boolean with `true` and `false` values.\n */\nscalar boolean;\n\n/**\n * @dev Array model type, equivalent to `Element[]`\n * @template Element The type of the array elements\n */\n@indexer(integer, Element)\nmodel Array<Element> {}\n\n/**\n * @dev Model with string properties where all the properties have type `Property`\n * @template Element The type of the properties\n */\n@indexer(string, Element)\nmodel Record<Element> {}\n',
  "../compiler/lib/prototypes.tsp": "namespace TypeSpec.Prototypes;\n\nextern dec getter(target: unknown);\n\nnamespace Types {\n  interface ModelProperty {\n    @getter type(): unknown;\n  }\n\n  interface Operation {\n    @getter returnType(): unknown;\n    @getter parameters(): unknown;\n  }\n\n  interface Array<TElementType> {\n    @getter elementType(): TElementType;\n  }\n}\n",
  "../compiler/lib/std/main.tsp": '// TypeSpec standard library. Everything in here can be omitted by using `--nostdlib` cli flag or `nostdlib` in the config.\nimport "./types.tsp";\nimport "./decorators.tsp";\nimport "./reflection.tsp";\nimport "./visibility.tsp";\n',
  "../compiler/lib/std/types.tsp": 'namespace TypeSpec;\n\n/**\n * Represent a 32-bit unix timestamp datetime with 1s of granularity.\n * It measures time by the number of seconds that have elapsed since 00:00:00 UTC on 1 January 1970.\n */\n@encode("unixTimestamp", int32)\nscalar unixTimestamp32 extends utcDateTime;\n\n/**\n * Represent a URL string as described by https://url.spec.whatwg.org/\n */\nscalar url extends string;\n\n/**\n * Represents a collection of optional properties.\n *\n * @template Source An object whose spread properties are all optional.\n */\n@doc("The template for adding optional properties.")\n@withOptionalProperties\nmodel OptionalProperties<Source> {\n  ...Source;\n}\n\n/**\n * Represents a collection of updateable properties.\n *\n * @template Source An object whose spread properties are all updateable.\n */\n@doc("The template for adding updateable properties.")\n@withUpdateableProperties\nmodel UpdateableProperties<Source> {\n  ...Source;\n}\n\n/**\n * Represents a collection of omitted properties.\n *\n * @template Source An object whose properties are spread.\n * @template Keys The property keys to omit.\n */\n@doc("The template for omitting properties.")\n@withoutOmittedProperties(Keys)\nmodel OmitProperties<Source, Keys extends string> {\n  ...Source;\n}\n\n/**\n * Represents a collection of properties with only the specified keys included.\n *\n * @template Source An object whose properties are spread.\n * @template Keys The property keys to include.\n */\n@doc("The template for picking properties.")\n@withPickedProperties(Keys)\nmodel PickProperties<Source, Keys extends string> {\n  ...Source;\n}\n\n/**\n * Represents a collection of properties with default values omitted.\n *\n * @template Source An object whose spread property defaults are all omitted.\n */\n@withoutDefaultValues\nmodel OmitDefaults<Source> {\n  ...Source;\n}\n\n/**\n * Applies a visibility setting to a collection of properties.\n *\n * @template Source An object whose properties are spread.\n * @template Visibility The visibility to apply to all properties.\n */\n@doc("The template for setting the default visibility of key properties.")\n@withDefaultKeyVisibility(Visibility)\nmodel DefaultKeyVisibility<Source, Visibility extends valueof Reflection.EnumMember> {\n  ...Source;\n}\n',
  "../compiler/lib/std/decorators.tsp": 'import "../../dist/src/lib/tsp-index.js";\n\nusing TypeSpec.Reflection;\n\nnamespace TypeSpec;\n\n/**\n * Typically a short, single-line description.\n * @param summary Summary string.\n *\n * @example\n * ```typespec\n * @summary("This is a pet")\n * model Pet {}\n * ```\n */\nextern dec summary(target: unknown, summary: valueof string);\n\n/**\n * Attach a documentation string. Content support CommonMark markdown formatting.\n * @param doc Documentation string\n * @param formatArgs Record with key value pair that can be interpolated in the doc.\n *\n * @example\n * ```typespec\n * @doc("Represent a Pet available in the PetStore")\n * model Pet {}\n * ```\n */\nextern dec doc(target: unknown, doc: valueof string, formatArgs?: {});\n\n/**\n * Attach a documentation string to describe the successful return types of an operation.\n * If an operation returns a union of success and errors it only describes the success. See `@errorsDoc` for error documentation.\n * @param doc Documentation string\n *\n * @example\n * ```typespec\n * @returnsDoc("Returns doc")\n * op get(): Pet | NotFound;\n * ```\n */\nextern dec returnsDoc(target: Operation, doc: valueof string);\n\n/**\n * Attach a documentation string to describe the error return types of an operation.\n * If an operation returns a union of success and errors it only describes the errors. See `@returnsDoc` for success documentation.\n * @param doc Documentation string\n *\n * @example\n * ```typespec\n * @errorsDoc("Errors doc")\n * op get(): Pet | NotFound;\n * ```\n */\nextern dec errorsDoc(target: Operation, doc: valueof string);\n\n/**\n * Service options.\n */\nmodel ServiceOptions {\n  /**\n   * Title of the service.\n   */\n  title?: string;\n}\n\n/**\n * Mark this namespace as describing a service and configure service properties.\n * @param options Optional configuration for the service.\n *\n * @example\n * ```typespec\n * @service\n * namespace PetStore;\n * ```\n *\n * @example Setting service title\n * ```typespec\n * @service(#{title: "Pet store"})\n * namespace PetStore;\n * ```\n */\nextern dec service(target: Namespace, options?: valueof ServiceOptions);\n\n/**\n * Specify that this model is an error type. Operations return error types when the operation has failed.\n *\n * @example\n * ```typespec\n * @error\n * model PetStoreError {\n *   code: string;\n *   message: string;\n * }\n * ```\n */\nextern dec error(target: Model);\n\n/**\n * Applies a media type hint to a TypeSpec type. Emitters and libraries may choose to use this hint to determine how a\n * type should be serialized. For example, the `@typespec/http` library will use the media type hint of the response\n * body type as a default `Content-Type` if one is not explicitly specified in the operation.\n *\n * Media types (also known as MIME types) are defined by RFC 6838. The media type hint should be a valid media type\n * string as defined by the RFC, but the decorator does not enforce or validate this constraint.\n *\n * Notes: the applied media type is _only_ a hint. It may be overridden or not used at all. Media type hints are\n * inherited by subtypes. If a media type hint is applied to a model, it will be inherited by all other models that\n * `extend` it unless they delcare their own media type hint.\n *\n * @param mediaType The media type hint to apply to the target type.\n *\n * @example create a model that serializes as XML by default\n *\n * ```tsp\n * @mediaTypeHint("application/xml")\n * model Example {\n *   @visibility(Lifecycle.Read)\n *   id: string;\n *\n *   name: string;\n * }\n * ```\n */\nextern dec mediaTypeHint(target: Model | Scalar | Enum | Union, mediaType: valueof string);\n\n// Cannot apply this to the scalar itself. Needs to be applied here so that we don\'t crash nostdlib scenarios\n@@mediaTypeHint(TypeSpec.bytes, "application/octet-stream");\n\n// @@mediaTypeHint(TypeSpec.string "text/plain") -- This is hardcoded in the compiler to avoid circularity\n// between the initialization of the string scalar and the `valueof string` required to call the\n// `mediaTypeHint` decorator.\n\n/**\n * Specify a known data format hint for this string type. For example `uuid`, `uri`, etc.\n * This differs from the `@pattern` decorator which is meant to specify a regular expression while `@format` accepts a known format name.\n * The format names are open ended and are left to emitter to interpret.\n *\n * @param format format name.\n *\n * @example\n * ```typespec\n * @format("uuid")\n * scalar uuid extends string;\n * ```\n */\nextern dec format(target: string | ModelProperty, format: valueof string);\n\n/**\n * Specify the the pattern this string should respect using simple regular expression syntax.\n * The following syntax is allowed: alternations (`|`), quantifiers (`?`, `*`, `+`, and `{ }`), wildcard (`.`), and grouping parentheses.\n * Advanced features like look-around, capture groups, and references are not supported.\n *\n * This decorator may optionally provide a custom validation _message_. Emitters may choose to use the message to provide\n * context when pattern validation fails. For the sake of consistency, the message should be a phrase that describes in\n * plain language what sort of content the pattern attempts to validate. For example, a complex regular expression that\n * validates a GUID string might have a message like "Must be a valid GUID."\n *\n * @param pattern Regular expression.\n * @param validationMessage Optional validation message that may provide context when validation fails.\n *\n * @example\n * ```typespec\n * @pattern("[a-z]+", "Must be a string consisting of only lower case letters and of at least one character.")\n * scalar LowerAlpha extends string;\n * ```\n */\nextern dec pattern(\n  target: string | bytes | ModelProperty,\n  pattern: valueof string,\n  validationMessage?: valueof string\n);\n\n/**\n * Specify the minimum length this string type should be.\n * @param value Minimum length\n *\n * @example\n * ```typespec\n * @minLength(2)\n * scalar Username extends string;\n * ```\n */\nextern dec minLength(target: string | ModelProperty, value: valueof integer);\n\n/**\n * Specify the maximum length this string type should be.\n * @param value Maximum length\n *\n * @example\n * ```typespec\n * @maxLength(20)\n * scalar Username extends string;\n * ```\n */\nextern dec maxLength(target: string | ModelProperty, value: valueof integer);\n\n/**\n * Specify the minimum number of items this array should have.\n * @param value Minimum number\n *\n * @example\n * ```typespec\n * @minItems(1)\n * model Endpoints is string[];\n * ```\n */\nextern dec minItems(target: unknown[] | ModelProperty, value: valueof integer);\n\n/**\n * Specify the maximum number of items this array should have.\n * @param value Maximum number\n *\n * @example\n * ```typespec\n * @maxItems(5)\n * model Endpoints is string[];\n * ```\n */\nextern dec maxItems(target: unknown[] | ModelProperty, value: valueof integer);\n\n/**\n * Specify the minimum value this numeric type should be.\n * @param value Minimum value\n *\n * @example\n * ```typespec\n * @minValue(18)\n * scalar Age is int32;\n * ```\n */\nextern dec minValue(target: numeric | ModelProperty, value: valueof numeric);\n\n/**\n * Specify the maximum value this numeric type should be.\n * @param value Maximum value\n *\n * @example\n * ```typespec\n * @maxValue(200)\n * scalar Age is int32;\n * ```\n */\nextern dec maxValue(target: numeric | ModelProperty, value: valueof numeric);\n\n/**\n * Specify the minimum value this numeric type should be, exclusive of the given\n * value.\n * @param value Minimum value\n *\n * @example\n * ```typespec\n * @minValueExclusive(0)\n * scalar distance is float64;\n * ```\n */\nextern dec minValueExclusive(target: numeric | ModelProperty, value: valueof numeric);\n\n/**\n * Specify the maximum value this numeric type should be, exclusive of the given\n * value.\n * @param value Maximum value\n *\n * @example\n * ```typespec\n * @maxValueExclusive(50)\n * scalar distance is float64;\n * ```\n */\nextern dec maxValueExclusive(target: numeric | ModelProperty, value: valueof numeric);\n\n/**\n * Mark this string as a secret value that should be treated carefully to avoid exposure\n *\n * @example\n * ```typespec\n * @secret\n * scalar Password is string;\n * ```\n */\nextern dec secret(target: string | ModelProperty);\n\n/**\n * Attaches a tag to an operation, interface, or namespace. Multiple `@tag` decorators can be specified to attach multiple tags to a TypeSpec element.\n * @param tag Tag value\n */\nextern dec tag(target: Namespace | Interface | Operation, tag: valueof string);\n\n/**\n * Specifies how a templated type should name their instances.\n * @param name name the template instance should take\n * @param formatArgs Model with key value used to interpolate the name\n *\n * @example\n * ```typespec\n * @friendlyName("{name}List", T)\n * model List<Item> {\n *   value: Item[];\n *   nextLink: string;\n * }\n * ```\n */\nextern dec friendlyName(target: unknown, name: valueof string, formatArgs?: unknown);\n\n/**\n * Mark a model property as the key to identify instances of that type\n * @param altName Name of the property. If not specified, the decorated property name is used.\n *\n * @example\n * ```typespec\n * model Pet {\n *   @key id: string;\n * }\n * ```\n */\nextern dec key(target: ModelProperty, altName?: valueof string);\n\n/**\n * Specify this operation is an overload of the given operation.\n * @param overloadbase Base operation that should be a union of all overloads\n *\n * @example\n * ```typespec\n * op upload(data: string | bytes, @header contentType: "text/plain" | "application/octet-stream"): void;\n * @overload(upload)\n * op uploadString(data: string, @header contentType: "text/plain" ): void;\n * @overload(upload)\n * op uploadBytes(data: bytes, @header contentType: "application/octet-stream"): void;\n * ```\n */\nextern dec overload(target: Operation, overloadbase: Operation);\n\n/**\n * Provide an alternative name for this type when serialized to the given mime type.\n * @param mimeType Mime type this should apply to. The mime type should be a known mime type as described here https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types without any suffix (e.g. `+json`)\n * @param name Alternative name\n *\n * @example\n *\n * ```typespec\n * model Certificate {\n *   @encodedName("application/json", "exp")\n *   @encodedName("application/xml", "expiry")\n *   expireAt: int32;\n * }\n * ```\n *\n * @example Invalid values\n *\n * ```typespec\n * @encodedName("application/merge-patch+json", "exp")\n *              ^ error cannot use subtype\n * ```\n */\nextern dec encodedName(target: unknown, mimeType: valueof string, name: valueof string);\n\n/**\n * Options for `@discriminated` decorator.\n */\nmodel DiscriminatedOptions {\n  /**\n   * How is the discriminated union serialized.\n   * @default object\n   */\n  envelope?: "object" | "none";\n\n  /** Name of the discriminator property */\n  discriminatorPropertyName?: string;\n\n  /** Name of the property envelopping the data */\n  envelopePropertyName?: string;\n}\n\n/**\n * Specify that this union is discriminated.\n * @param options Options to configure the serialization of the discriminated union.\n *\n * @example\n *\n * ```typespec\n * @discriminated\n * union Pet{ cat: Cat, dog: Dog }\n *\n * model Cat { name: string, meow: boolean }\n * model Dog { name: string, bark: boolean }\n * ```\n * Serialized as:\n * ```json\n * {\n *   "kind": "cat",\n *   "value": {\n *     "name": "Whiskers",\n *     "meow": true\n *   }\n * },\n * {\n *   "kind": "dog",\n *   "value": {\n *     "name": "Rex",\n *     "bark": false\n *   }\n * }\n * ```\n *\n * @example Custom property names\n *\n * ```typespec\n * @discriminated(#{discriminatorPropertyName: "dataKind", envelopePropertyName: "data"})\n * union Pet{ cat: Cat, dog: Dog }\n *\n * model Cat { name: string, meow: boolean }\n * model Dog { name: string, bark: boolean }\n * ```\n * Serialized as:\n * ```json\n * {\n *   "dataKind": "cat",\n *   "data": {\n *     "name": "Whiskers",\n *     "meow": true\n *   }\n * },\n * {\n *   "dataKind": "dog",\n *   "data": {\n *     "name": "Rex",\n *     "bark": false\n *   }\n * }\n * ```\n */\nextern dec discriminated(target: Union, options?: valueof DiscriminatedOptions);\n\n/**\n * Specify the property to be used to discriminate this type.\n * @param propertyName The property name to use for discrimination\n *\n * @example\n *\n * ```typespec\n * @discriminator("kind")\n * model Pet{ kind: string }\n *\n * model Cat extends Pet {kind: "cat", meow: boolean}\n * model Dog extends Pet  {kind: "dog", bark: boolean}\n * ```\n */\nextern dec discriminator(target: Model, propertyName: valueof string);\n\n/**\n * Known encoding to use on utcDateTime or offsetDateTime\n */\nenum DateTimeKnownEncoding {\n  /**\n   * RFC 3339 standard. https://www.ietf.org/rfc/rfc3339.txt\n   * Encode to string.\n   */\n  rfc3339: "rfc3339",\n\n  /**\n   * RFC 7231 standard. https://www.ietf.org/rfc/rfc7231.txt\n   * Encode to string.\n   */\n  rfc7231: "rfc7231",\n\n  /**\n   * Encode a datetime to a unix timestamp.\n   * Unix timestamps are represented as an integer number of seconds since the Unix epoch and usually encoded as an int32.\n   */\n  unixTimestamp: "unixTimestamp",\n}\n\n/**\n * Known encoding to use on duration\n */\nenum DurationKnownEncoding {\n  /**\n   * ISO8601 duration\n   */\n  ISO8601: "ISO8601",\n\n  /**\n   * Encode to integer or float\n   */\n  seconds: "seconds",\n}\n\n/**\n * Known encoding to use on bytes\n */\nenum BytesKnownEncoding {\n  /**\n   * Encode to Base64\n   */\n  base64: "base64",\n\n  /**\n   * Encode to Base64 Url\n   */\n  base64url: "base64url",\n}\n\n/**\n * Encoding for serializing arrays\n */\nenum ArrayEncoding {\n  /** Each values of the array is separated by a | */\n  pipeDelimited,\n\n  /** Each values of the array is separated by a <space> */\n  spaceDelimited,\n}\n\n/**\n * Specify how to encode the target type.\n * @param encodingOrEncodeAs Known name of an encoding or a scalar type to encode as(Only for numeric types to encode as string).\n * @param encodedAs What target type is this being encoded as. Default to string.\n *\n * @example offsetDateTime encoded with rfc7231\n *\n * ```tsp\n * @encode("rfc7231")\n * scalar myDateTime extends offsetDateTime;\n * ```\n *\n * @example utcDateTime encoded with unixTimestamp\n *\n * ```tsp\n * @encode("unixTimestamp", int32)\n * scalar myDateTime extends unixTimestamp;\n * ```\n *\n * @example encode numeric type to string\n *\n * ```tsp\n * model Pet {\n *   @encode(string) id: int64;\n * }\n * ```\n */\nextern dec encode(\n  target: Scalar | ModelProperty,\n  encodingOrEncodeAs: (valueof string | EnumMember) | Scalar,\n  encodedAs?: Scalar\n);\n\n/** Options for example decorators */\nmodel ExampleOptions {\n  /** The title of the example */\n  title?: string;\n\n  /** Description of the example */\n  description?: string;\n}\n\n/**\n * Provide an example value for a data type.\n *\n * @param example Example value.\n * @param options Optional metadata for the example.\n *\n * @example\n *\n * ```tsp\n * @example(#{name: "Fluffy", age: 2})\n * model Pet {\n *  name: string;\n *  age: int32;\n * }\n * ```\n */\nextern dec example(\n  target: Model | Enum | Scalar | Union | ModelProperty | UnionVariant,\n  example: valueof unknown,\n  options?: valueof ExampleOptions\n);\n\n/**\n * Operation example configuration.\n */\nmodel OperationExample {\n  /** Example request body. */\n  parameters?: unknown;\n\n  /** Example response body. */\n  returnType?: unknown;\n}\n\n/**\n * Provide example values for an operation\'s parameters and corresponding return type.\n *\n * @param example Example value.\n * @param options Optional metadata for the example.\n *\n * @example\n *\n * ```tsp\n * @opExample(#{parameters: #{name: "Fluffy", age: 2}, returnType: #{name: "Fluffy", age: 2, id: "abc"})\n * op createPet(pet: Pet): Pet;\n * ```\n */\nextern dec opExample(\n  target: Operation,\n  example: valueof OperationExample,\n  options?: valueof ExampleOptions\n);\n\n/**\n * Returns the model with required properties removed.\n */\nextern dec withOptionalProperties(target: Model);\n\n/**\n * Returns the model with any default values removed.\n */\nextern dec withoutDefaultValues(target: Model);\n\n/**\n * Returns the model with the given properties omitted.\n * @param omit List of properties to omit\n */\nextern dec withoutOmittedProperties(target: Model, omit: string | Union);\n\n/**\n * Returns the model with only the given properties included.\n * @param pick List of properties to include\n */\nextern dec withPickedProperties(target: Model, pick: string | Union);\n\n//---------------------------------------------------------------------------\n// Paging\n//---------------------------------------------------------------------------\n\n/**\n * Mark this operation as a `list` operation that returns a paginated list of items.\n */\nextern dec list(target: Operation);\n\n/**\n * Pagination property defining the number of items to skip.\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n * }\n * @list op listPets(@offset skip: int32, @pageSize pageSize: int8): Page<Pet>;\n * ```\n */\nextern dec offset(target: ModelProperty);\n\n/**\n * Pagination property defining the page index.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n * }\n * @list op listPets(@pageIndex page: int32, @pageSize pageSize: int8): Page<Pet>;\n * ```\n */\nextern dec pageIndex(target: ModelProperty);\n\n/**\n * Specify the pagination parameter that controls the maximum number of items to include in a page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n * }\n * @list op listPets(@pageIndex page: int32, @pageSize pageSize: int8): Page<Pet>;\n * ```\n */\nextern dec pageSize(target: ModelProperty);\n\n/**\n * Specify the the property that contains the array of page items.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n * }\n * @list op listPets(@pageIndex page: int32, @pageSize pageSize: int8): Page<Pet>;\n * ```\n */\nextern dec pageItems(target: ModelProperty);\n\n/**\n * Pagination property defining the token to get to the next page.\n * It MUST be specified both on the request parameter and the response.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @continuationToken continuationToken: string;\n * }\n * @list op listPets(@continuationToken continuationToken: string): Page<Pet>;\n * ```\n */\nextern dec continuationToken(target: ModelProperty);\n\n/**\n * Pagination property defining a link to the next page.\n *\n * It is expected that navigating to the link will return the same set of responses as the operation that returned the current page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @nextLink next: url;\n *   @prevLink prev: url;\n *   @firstLink first: url;\n *   @lastLink last: url;\n * }\n * @list op listPets(): Page<Pet>;\n * ```\n */\nextern dec nextLink(target: ModelProperty);\n\n/**\n * Pagination property defining a link to the previous page.\n *\n * It is expected that navigating to the link will return the same set of responses as the operation that returned the current page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @nextLink next: url;\n *   @prevLink prev: url;\n *   @firstLink first: url;\n *   @lastLink last: url;\n * }\n * @list op listPets(): Page<Pet>;\n * ```\n */\nextern dec prevLink(target: ModelProperty);\n\n/**\n * Pagination property defining a link to the first page.\n *\n * It is expected that navigating to the link will return the same set of responses as the operation that returned the current page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @nextLink next: url;\n *   @prevLink prev: url;\n *   @firstLink first: url;\n *   @lastLink last: url;\n * }\n * @list op listPets(): Page<Pet>;\n * ```\n */\nextern dec firstLink(target: ModelProperty);\n\n/**\n * Pagination property defining a link to the last page.\n *\n * It is expected that navigating to the link will return the same set of responses as the operation that returned the current page.\n *\n * @example\n * ```tsp\n * model Page<T> {\n *   @pageItems items: T[];\n *   @nextLink next: url;\n *   @prevLink prev: url;\n *   @firstLink first: url;\n *   @lastLink last: url;\n * }\n * @list op listPets(): Page<Pet>;\n * ```\n */\nextern dec lastLink(target: ModelProperty);\n\n//---------------------------------------------------------------------------\n// Debugging\n//---------------------------------------------------------------------------\n\n/**\n * A debugging decorator used to inspect a type.\n * @param text Custom text to log\n */\nextern dec inspectType(target: unknown, text: valueof string);\n\n/**\n * A debugging decorator used to inspect a type name.\n * @param text Custom text to log\n */\nextern dec inspectTypeName(target: unknown, text: valueof string);\n',
  "../compiler/lib/std/reflection.tsp": "namespace TypeSpec.Reflection;\n\nmodel Enum {}\nmodel EnumMember {}\nmodel Interface {}\nmodel Model {}\nmodel ModelProperty {}\nmodel Namespace {}\nmodel Operation {}\nmodel Scalar {}\nmodel Union {}\nmodel UnionVariant {}\nmodel StringTemplate {}\n",
  "../compiler/lib/std/visibility.tsp": '// Copyright (c) Microsoft Corporation\n// Licensed under the MIT license.\n\nimport "../../dist/src/lib/tsp-index.js";\n\nusing TypeSpec.Reflection;\n\nnamespace TypeSpec;\n\n/**\n * Sets the visibility modifiers that are active on a property, indicating that it is only considered to be present\n * (or "visible") in contexts that select for the given modifiers.\n *\n * A property without any visibility settings applied for any visibility class (e.g. `Lifecycle`) is considered to have\n * the default visibility settings for that class.\n *\n * If visibility for the property has already been set for a visibility class (for example, using `@invisible` or\n * `@removeVisibility`), this decorator will **add** the specified visibility modifiers to the property.\n *\n * See: [Visibility](https://typespec.io/docs/language-basics/visibility)\n *\n * The `@typespec/http` library uses `Lifecycle` visibility to determine which properties are included in the request or\n * response bodies of HTTP operations. By default, it uses the following visibility settings:\n *\n * - For the return type of operations, properties are included if they have `Lifecycle.Read` visibility.\n * - For POST operation parameters, properties are included if they have `Lifecycle.Create` visibility.\n * - For PUT operation parameters, properties are included if they have `Lifecycle.Create` or `Lifecycle.Update` visibility.\n * - For PATCH operation parameters, properties are included if they have `Lifecycle.Update` visibility.\n * - For DELETE operation parameters, properties are included if they have `Lifecycle.Delete` visibility.\n * - For GET or HEAD operation parameters, properties are included if they have `Lifecycle.Query` visibility.\n *\n * By default, properties have all five Lifecycle visibility modifiers enabled, so a property is visible in all contexts\n * by default.\n *\n * The default settings may be overridden using the `@returnTypeVisibility` and `@parameterVisibility` decorators.\n *\n * See also: [Automatic visibility](https://typespec.io/docs/libraries/http/operations#automatic-visibility)\n *\n * @param visibilities List of visibilities which apply to this property.\n *\n * @example\n *\n * ```typespec\n * model Dog {\n *   // The service will generate an ID, so you don\'t need to send it.\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   // The service will store this secret name, but won\'t ever return it.\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   // The regular name has all vi\n *   name: string;\n * }\n * ```\n */\nextern dec visibility(target: ModelProperty, ...visibilities: valueof EnumMember[]);\n\n/**\n * Indicates that a property is not visible in the given visibility class.\n *\n * This decorator removes all active visibility modifiers from the property within\n * the given visibility class, making it invisible to any context that selects for\n * visibility modifiers within that class.\n *\n * @param visibilityClass The visibility class to make the property invisible within.\n *\n * @example\n * ```typespec\n * model Example {\n *   @invisible(Lifecycle)\n *   hidden_property: string;\n * }\n * ```\n */\nextern dec invisible(target: ModelProperty, visibilityClass: Enum);\n\n/**\n * Removes visibility modifiers from a property.\n *\n * If the visibility modifiers for a visibility class have not been initialized,\n * this decorator will use the default visibility modifiers for the visibility\n * class as the default modifier set.\n *\n * @param target The property to remove visibility from.\n * @param visibilities The visibility modifiers to remove from the target property.\n *\n * @example\n * ```typespec\n * model Example {\n *   // This property will have all Lifecycle visibilities except the Read\n *   // visibility, since it is removed.\n *   @removeVisibility(Lifecycle.Read)\n *   secret_property: string;\n * }\n * ```\n */\nextern dec removeVisibility(target: ModelProperty, ...visibilities: valueof EnumMember[]);\n\n/**\n * Removes properties that do not have at least one of the given visibility modifiers\n * active.\n *\n * If no visibility modifiers are supplied, this decorator has no effect.\n *\n * See also: [Automatic visibility](https://typespec.io/docs/libraries/http/operations#automatic-visibility)\n *\n * When using an emitter that applies visibility automatically, it is generally\n * not necessary to use this decorator.\n *\n * @param visibilities List of visibilities that apply to this property.\n *\n * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * // The spread operator will copy all the properties of Dog into DogRead,\n * // and @withVisibility will then remove those that are not visible with\n * // create or update visibility.\n * //\n * // In this case, the id property is removed, and the name and secretName\n * // properties are kept.\n * @withVisibility(Lifecycle.Create, Lifecycle.Update)\n * model DogCreateOrUpdate {\n *   ...Dog;\n * }\n *\n * // In this case the id and name properties are kept and the secretName property\n * // is removed.\n * @withVisibility(Lifecycle.Read)\n * model DogRead {\n *   ...Dog;\n * }\n * ```\n */\nextern dec withVisibility(target: Model, ...visibilities: valueof EnumMember[]);\n\n/**\n * Set the visibility of key properties in a model if not already set.\n *\n * This will set the visibility modifiers of all key properties in the model if the visibility is not already _explicitly_ set,\n * but will not change the visibility of any properties that have visibility set _explicitly_, even if the visibility\n * is the same as the default visibility.\n *\n * Visibility may be set explicitly using any of the following decorators:\n *\n * - `@visibility`\n * - `@removeVisibility`\n * - `@invisible`\n *\n * @param visibility The desired default visibility value. If a key property already has visibility set, it will not be changed.\n */\nextern dec withDefaultKeyVisibility(target: Model, visibility: valueof EnumMember);\n\n/**\n * Declares the visibility constraint of the parameters of a given operation.\n *\n * A parameter or property nested within a parameter will be visible if it has _any_ of the visibilities\n * in the list.\n *\n * It is invalid to call this decorator with no visibility modifiers.\n *\n * @param visibilities List of visibility modifiers that apply to the parameters of this operation.\n */\nextern dec parameterVisibility(target: Operation, ...visibilities: valueof EnumMember[]);\n\n/**\n * Declares the visibility constraint of the return type of a given operation.\n *\n * A property within the return type of the operation will be visible if it has _any_ of the visibilities\n * in the list.\n *\n * It is invalid to call this decorator with no visibility modifiers.\n *\n * @param visibilities List of visibility modifiers that apply to the return type of this operation.\n */\nextern dec returnTypeVisibility(target: Operation, ...visibilities: valueof EnumMember[]);\n\n/**\n * Returns the model with non-updateable properties removed.\n */\nextern dec withUpdateableProperties(target: Model);\n\n/**\n * Declares the default visibility modifiers for a visibility class.\n *\n * The default modifiers are used when a property does not have any visibility decorators\n * applied to it.\n *\n * The modifiers passed to this decorator _MUST_ be members of the target Enum.\n *\n * @param visibilities the list of modifiers to use as the default visibility modifiers.\n */\nextern dec defaultVisibility(target: Enum, ...visibilities: valueof EnumMember[]);\n\n/**\n * A visibility class for resource lifecycle phases.\n *\n * These visibilities control whether a property is visible during the various phases of a resource\'s lifecycle.\n *\n * @example\n * ```typespec\n * model Dog {\n *  @visibility(Lifecycle.Read)\n *  id: int32;\n *\n *  @visibility(Lifecycle.Create, Lifecycle.Update)\n *  secretName: string;\n *\n *  name: string;\n * }\n * ```\n *\n * In this example, the `id` property is only visible during the read phase, and the `secretName` property is only visible\n * during the create and update phases. This means that the server will return the `id` property when returning a `Dog`,\n * but the client will not be able to set or update it. In contrast, the `secretName` property can be set when creating\n * or updating a `Dog`, but the server will never return it. The `name` property has no visibility modifiers and is\n * therefore visible in all phases.\n */\nenum Lifecycle {\n  /**\n   * The property is visible when a resource is being created.\n   */\n  Create,\n\n  /**\n   * The property is visible when a resource is being read.\n   */\n  Read,\n\n  /**\n   * The property is visible when a resource is being updated.\n   */\n  Update,\n\n  /**\n   * The property is visible when a resource is being deleted.\n   */\n  Delete,\n\n  /**\n   * The property is visible when a resource is being queried.\n   *\n   * In HTTP APIs, this visibility applies to parameters of GET or HEAD operations.\n   */\n  Query,\n}\n\n/**\n * A visibility filter, used to specify which properties should be included when\n * using the `withVisibilityFilter` decorator.\n *\n * The filter matches any property with ALL of the following:\n * - If the `any` key is present, the property must have at least one of the specified visibilities.\n * - If the `all` key is present, the property must have all of the specified visibilities.\n * - If the `none` key is present, the property must have none of the specified visibilities.\n */\nmodel VisibilityFilter {\n  any?: EnumMember[];\n  all?: EnumMember[];\n  none?: EnumMember[];\n}\n\n/**\n * Applies the given visibility filter to the properties of the target model.\n *\n * This transformation is recursive, so it will also apply the filter to any nested\n * or referenced models that are the types of any properties in the `target`.\n *\n * If a `nameTemplate` is provided, newly-created type instances will be named according\n * to the template. See the `@friendlyName` decorator for more information on the template\n * syntax. The transformed type is provided as the argument to the template.\n *\n * @param target The model to apply the visibility filter to.\n * @param filter The visibility filter to apply to the properties of the target model.\n * @param nameTemplate The name template to use when renaming new model instances.\n *\n * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   name: string;\n * }\n *\n * @withVisibilityFilter(#{ all: #[Lifecycle.Read] })\n * model DogRead {\n *  ...Dog\n * }\n * ```\n */\nextern dec withVisibilityFilter(\n  target: Model,\n  filter: valueof VisibilityFilter,\n  nameTemplate?: valueof string\n);\n\n/**\n * Transforms the `target` model to include only properties that are visible during the\n * "Update" lifecycle phase.\n *\n * Any nested models of optional properties will be transformed into the "CreateOrUpdate"\n * lifecycle phase instead of the "Update" lifecycle phase, so that nested models may be\n * fully updated.\n *\n * If a `nameTemplate` is provided, newly-created type instances will be named according\n * to the template. See the `@friendlyName` decorator for more information on the template\n * syntax. The transformed type is provided as the argument to the template.\n *\n * @param target The model to apply the transformation to.\n * @param nameTemplate The name template to use when renaming new model instances.\n *\n * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * @withLifecycleUpdate\n * model DogUpdate {\n *   ...Dog\n * }\n * ```\n */\nextern dec withLifecycleUpdate(target: Model, nameTemplate?: valueof string);\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Create" resource lifecycle phase.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Create` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   name: string;\n * }\n *\n * // This model has only the `name` field.\n * model CreateDog is Create<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ all: #[Lifecycle.Create] }, NameTemplate)\nmodel Create<T extends Reflection.Model, NameTemplate extends valueof string = "Create{name}"> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Read" resource lifecycle phase.\n *\n * The "Read" lifecycle phase is used for properties returned by operations that read data, like\n * HTTP GET operations.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Read` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * // This model has the `id` and `name` fields, but not `secretName`.\n * model ReadDog is Read<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ all: #[Lifecycle.Read] }, NameTemplate)\nmodel Read<T extends Reflection.Model, NameTemplate extends valueof string = "Read{name}"> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Update" resource lifecycle phase.\n *\n * The "Update" lifecycle phase is used for properties passed as parameters to operations\n * that update data, like HTTP PATCH operations.\n *\n * This transformation will include only the properties that have the `Lifecycle.Update`\n * visibility modifier, and the types of all properties will be replaced with the\n * equivalent `CreateOrUpdate` transformation.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * // This model will have the `secretName` and `name` fields, but not the `id` field.\n * model UpdateDog is Update<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withLifecycleUpdate(NameTemplate)\nmodel Update<T extends Reflection.Model, NameTemplate extends valueof string = "Update{name}"> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Create" or "Update" resource lifecycle phases.\n *\n * The "CreateOrUpdate" lifecycle phase is used by default for properties passed as parameters to operations\n * that can create _or_ update data, like HTTP PUT operations.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Create` or `Lifecycle.Update` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   @visibility(Lifecycle.Create)\n *   immutableSecret: string;\n *\n *   @visibility(Lifecycle.Create, Lifecycle.Update)\n *   secretName: string;\n *\n *   name: string;\n * }\n *\n * // This model will have the `immutableSecret`, `secretName`, and `name` fields, but not the `id` field.\n * model CreateOrUpdateDog is CreateOrUpdate<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ any: #[Lifecycle.Create, Lifecycle.Update] }, NameTemplate)\nmodel CreateOrUpdate<\n  T extends Reflection.Model,\n  NameTemplate extends valueof string = "CreateOrUpdate{name}"\n> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Delete" resource lifecycle phase.\n *\n * The "Delete" lifecycle phase is used for properties passed as parameters to operations\n * that delete data, like HTTP DELETE operations.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Delete` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   // Set when the Dog is removed from our data store. This happens when the\n *   // Dog is re-homed to a new owner.\n *   @visibility(Lifecycle.Delete)\n *   nextOwner: string;\n *\n *   name: string;\n * }\n *\n * // This model will have the `nextOwner` and `name` fields, but not the `id` field.\n * model DeleteDog is Delete<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ all: #[Lifecycle.Delete] }, NameTemplate)\nmodel Delete<T extends Reflection.Model, NameTemplate extends valueof string = "Delete{name}"> {\n  ...T;\n}\n\n/**\n * A copy of the input model `T` with only the properties that are visible during the\n * "Query" resource lifecycle phase.\n *\n * The "Query" lifecycle phase is used for properties passed as parameters to operations\n * that read data, like HTTP GET or HEAD operations. This should not be confused for\n * the `@query` decorator, which specifies that the property is transmitted in the\n * query string of an HTTP request.\n *\n * This transformation is recursive, and will include only properties that have the\n * `Lifecycle.Query` visibility modifier.\n *\n * If a `NameTemplate` is provided, the new model will be named according to the template.\n * The template uses the same syntax as the `@friendlyName` decorator.\n *\n * @template T The model to transform.\n * @template NameTemplate The name template to use for the new model.\n *\n *  * @example\n * ```typespec\n * model Dog {\n *   @visibility(Lifecycle.Read)\n *   id: int32;\n *\n *   // When getting information for a Dog, you can set this field to true to include\n *   // some extra information about the Dog\'s pedigree that is normally not returned.\n *   // Alternatively, you could just use a separate option parameter to get this\n *   // information.\n *   @visibility(Lifecycle.Query)\n *   includePedigree?: boolean;\n *\n *   name: string;\n *\n *   // Only included if `includePedigree` is set to true in the request.\n *   @visibility(Lifecycle.Read)\n *   pedigree?: string;\n * }\n *\n * // This model will have the `includePedigree` and `name` fields, but not `id` or `pedigree`.\n * model QueryDog is Query<Dog>;\n * ```\n */\n@doc("")\n@friendlyName(NameTemplate, T)\n@withVisibilityFilter(#{ all: #[Lifecycle.Query] }, NameTemplate)\nmodel Query<T extends Reflection.Model, NameTemplate extends valueof string = "Query{name}"> {\n  ...T;\n}\n',
  "lib/main.tsp": 'import "../dist/src/tsp-index.js";\nimport "./decorators.tsp";\n',
  "lib/decorators.tsp": 'using TypeSpec.Reflection;\n\nnamespace TypeSpec.OpenAPI;\n\n/**\n * Specify the OpenAPI `operationId` property for this operation.\n *\n * @param operationId Operation id value.\n *\n * @example\n *\n * ```typespec\n * @operationId("download")\n * op read(): string;\n * ```\n */\nextern dec operationId(target: Operation, operationId: valueof string);\n\n/**\n * Attach some custom data to the OpenAPI element generated from this type.\n *\n * @param key Extension key.\n * @param value Extension value.\n *\n * @example\n *\n * ```typespec\n * @extension("x-custom", "My value")\n * @extension("x-pageable", #{nextLink: "x-next-link"})\n * op read(): string;\n * ```\n */\nextern dec extension(target: unknown, key: valueof string, value: valueof unknown);\n\n/**\n * Specify that this model is to be treated as the OpenAPI `default` response.\n * This differs from the compiler built-in `@error` decorator as this does not necessarily represent an error.\n *\n * @example\n *\n * ```typespec\n * @defaultResponse\n * model PetStoreResponse is object;\n *\n * op listPets(): Pet[] | PetStoreResponse;\n * ```\n */\nextern dec defaultResponse(target: Model);\n\n/**\n * Specify the OpenAPI `externalDocs` property for this type.\n *\n * @param url Url to the docs\n * @param description Description of the docs\n *\n * @example\n * ```typespec\n * @externalDocs("https://example.com/detailed.md", "Detailed information on how to use this operation")\n * op listPets(): Pet[];\n * ```\n */\nextern dec externalDocs(target: unknown, url: valueof string, description?: valueof string);\n\n/** Additional information for the OpenAPI document. */\nmodel AdditionalInfo {\n  /** The title of the API. Overrides the `@service` title. */\n  title?: string;\n\n  /** A short summary of the API. Overrides the `@summary` provided on the service namespace. */\n  summary?: string;\n\n  /** The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API implementation version). */\n  version?: string;\n\n  /** A URL to the Terms of Service for the API. MUST be in the format of a URL. */\n  termsOfService?: url;\n\n  /** The contact information for the exposed API. */\n  contact?: Contact;\n\n  /** The license information for the exposed API. */\n  license?: License;\n\n  ...Record<unknown>;\n}\n\n/** Contact information for the exposed API. */\nmodel Contact {\n  /** The identifying name of the contact person/organization. */\n  name?: string;\n\n  /** The URL pointing to the contact information. MUST be in the format of a URL. */\n  url?: url;\n\n  /** The email address of the contact person/organization. MUST be in the format of an email address. */\n  email?: string;\n\n  ...Record<unknown>;\n}\n\n/** License information for the exposed API. */\nmodel License {\n  /** The license name used for the API. */\n  name: string;\n\n  /** A URL to the license used for the API. MUST be in the format of a URL. */\n  url?: url;\n\n  ...Record<unknown>;\n}\n\n/**\n * Specify OpenAPI additional information.\n * The service `title` is already specified using `@service`.\n * @param additionalInfo Additional information\n */\nextern dec info(target: Namespace, additionalInfo: valueof AdditionalInfo);\n\n/** Metadata to a single tag that is used by operations. */\nmodel TagMetadata {\n  /** A description of the API. */\n  description?: string;\n\n  /** An external Docs information of the API. */\n  externalDocs?: ExternalDocs;\n\n  /** Attach some custom data, The extension key must start with `x-`. */\n  ...Record<unknown>;\n}\n\n/** External Docs information. */\nmodel ExternalDocs {\n  /** Documentation url */\n  url: string;\n\n  /** Optional description */\n  description?: string;\n\n  /** Attach some custom data, The extension key must start with `x-`. */\n  ...Record<unknown>;\n}\n\n/**\n * Specify OpenAPI additional information.\n * @param name tag name\n * @param tagMetadata Additional information\n *\n * @example\n * ```typespec\n * @service()\n * @tagMetadata("Tag Name", #{description: "Tag description", externalDocs: #{url: "https://example.com", description: "More info.", `x-custom`: "string"}, `x-custom`: "string"})\n * namespace PetStore {}\n * ```\n */\nextern dec tagMetadata(target: Namespace, name: valueof string, tagMetadata: valueof TagMetadata);\n'
};
var _TypeSpecLibrary_ = {
  jsSourceFiles: TypeSpecJSSources,
  typespecSourceFiles: TypeSpecSources
};
export {
  $decorators,
  $defaultResponse,
  $extension,
  $externalDocs,
  $info,
  $operationId,
  _TypeSpecLibrary_,
  checkDuplicateTypeName,
  getExtensions,
  getExternalDocs,
  getInfo,
  getOpenAPITypeName,
  getOperationId,
  getParameterKey,
  getTagsMetadata,
  isDefaultResponse,
  isReadonlyProperty,
  resolveInfo,
  resolveOperationId,
  setExtension,
  setInfo,
  shouldInline
};

import httpsFiles from '../examples/js2py/o03-https-production-files.json'
import containerOpsFiles from '../examples/js2py/o02-containers-files.json'
import operatingSystemFiles from '../examples/js2py/o01-operating-system-files.json'
import reliableOperationFiles from '../examples/js2py/s03-reliable-operations-files.json'
import authorizationFiles from '../examples/js2py/s02-authorization-files.json'
import identityFiles from '../examples/js2py/s01-identity-files.json'
import recoveryFiles from '../examples/js2py/o06-recovery-files.json'
import observabilityFiles from '../examples/js2py/o05-observability-files.json'
import releaseFiles from '../examples/js2py/o04-release-files.json'
import graduationFiles from '../examples/js2py/g01-graduation-files.json'
import httpContractFiles from '../examples/js2py/h02-http-contract-files.json'
import externalServiceFiles from '../examples/js2py/a02-external-services-files.json'
import asyncModelFiles from '../examples/js2py/a01-async-model-files.json'
import databaseTestingFiles from '../examples/js2py/d06-database-testing-files.json'
import migrationFiles from '../examples/js2py/d05-migrations-files.json'
import ormFiles from '../examples/js2py/d04-sqlalchemy-files.json'
import transactionFiles from '../examples/js2py/d03-transactions-files.json'
import sqlFiles from '../examples/js2py/d02-sql-files.json'
import relationalFiles from '../examples/js2py/d01-relational-data-files.json'
import apiTestingFiles from '../examples/js2py/h06-api-testing-files.json'
import dependencyFiles from '../examples/js2py/h05-dependencies-files.json'
import validationFiles from '../examples/js2py/h04-validation-files.json'
import fastApiFiles from '../examples/js2py/h03-first-fastapi-files.json'
import serviceProcessFiles from '../examples/js2py/h01-service-process-files.json'
import resourceFiles from '../examples/js2py/u14-resources-files.json'
import decoratorFiles from '../examples/js2py/u13-decorators-files.json'
import modelFiles from '../examples/js2py/u12-models-files.json'
import typingFiles from '../examples/js2py/u11-typing-files.json'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import u00Files from '../examples/js2py/u00-files.json'
import firstScriptFiles from '../examples/js2py/u00-first-script-files.json'
import scalarFiles from '../examples/js2py/u01-scalars-files.json'
import containerFiles from '../examples/js2py/u02-containers-files.json'
import controlFlowFiles from '../examples/js2py/u03-control-flow-files.json'
import functionFiles from '../examples/js2py/u04-functions-files.json'
import exceptionFiles from '../examples/js2py/u05-exceptions-files.json'
import moduleFiles from '../examples/js2py/u06-modules-files.json'
import fileFiles from '../examples/js2py/u07-files-files.json'

import environmentFiles from '../examples/js2py/u08-environments-files.json'

import testingFiles from '../examples/js2py/u09-testing-files.json'

import projectFiles from '../examples/js2py/u10-local-project-files.json'
import productDeliveryFiles from '../examples/js2py/product-delivery-files.json'

function readExample(lab: string, files: string[], file: string): string {
  if (!files.includes(file)) {
    throw new Error(`Unknown js2py ${lab} example: ${file}`)
  }

  return readFileSync(
    join(process.cwd(), 'examples', 'js2py', lab, file),
    'utf8',
  ).trimEnd()
}

// Server/build-time only: the published lesson and download share source files.
export function getFirstScriptExample(file: string): string {
  return readExample('u00-first-script', firstScriptFiles, file)
}

export function getScalarExample(file: string): string {
  return readExample('u01-scalars', scalarFiles, file)
}

export function getContainerExample(file: string): string {
  return readExample('u02-containers', containerFiles, file)
}

export function getControlFlowExample(file: string): string {
  return readExample('u03-control-flow', controlFlowFiles, file)
}

export function getFunctionExample(file: string): string {
  return readExample('u04-functions', functionFiles, file)
}

export function getExceptionExample(file: string): string {
  return readExample('u05-exceptions', exceptionFiles, file)
}

export function getModuleExample(file: string): string {
  return readExample('u06-modules', moduleFiles, file)
}

export function getFileExample(file: string): string {
  return readExample('u07-files', fileFiles, file)
}

// Retained for historical authoring material, not the introductory lesson.
export function getU00Example(file: string): string {
  return readExample('u00-environment', u00Files, file)
}

export function getEnvironmentExample(file: string): string {
  return readExample('u08-environments', environmentFiles, file)
}

export function getTestingExample(file: string): string {
  return readExample('u09-testing', testingFiles, file)
}

export function getProjectExample(file: string): string {
  return readExample('u10-local-project', projectFiles, file)
}

export function getTypingExample(file: string): string {
  return readExample('u11-typing', typingFiles, file)
}

export function getModelExample(file: string): string {
  return readExample('u12-models', modelFiles, file)
}

export function getDecoratorExample(file: string): string {
  return readExample('u13-decorators', decoratorFiles, file)
}

export function getResourceExample(file: string): string {
  return readExample('u14-resources', resourceFiles, file)
}

export function getProductDeliveryExample(file: string): string {
  return readExample('product-delivery', productDeliveryFiles, file)
}

export function getServiceProcessExample(file: string): string {
  return readExample('h01-service-process', serviceProcessFiles, file)
}

export function getFastApiExample(file: string): string {
  return readExample('h03-first-fastapi', fastApiFiles, file)
}

export function getValidationExample(file: string): string {
  return readExample('h04-validation', validationFiles, file)
}

export function getDependencyExample(file: string): string {
  return readExample('h05-dependencies', dependencyFiles, file)
}

export function getApiTestingExample(file: string): string {
  return readExample('h06-api-testing', apiTestingFiles, file)
}

export function getRelationalExample(file: string): string {
  return readExample('d01-relational-data', relationalFiles, file)
}

export function getSqlExample(file: string): string {
  return readExample('d02-sql', sqlFiles, file)
}

export function getTransactionExample(file: string): string {
  return readExample('d03-transactions', transactionFiles, file)
}

export function getOrmExample(file: string): string {
  return readExample('d04-sqlalchemy', ormFiles, file)
}

export function getMigrationExample(file: string): string {
  return readExample('d05-migrations', migrationFiles, file)
}

export function getDatabaseTestingExample(file: string): string {
  return readExample('d06-database-testing', databaseTestingFiles, file)
}

export function getAsyncModelExample(file: string): string {
  return readExample('a01-async-model', asyncModelFiles, file)
}

export function getExternalServiceExample(file: string): string {
  return readExample('a02-external-services', externalServiceFiles, file)
}

export function getHttpContractExample(file: string): string {
  return readExample('h02-http-contract', httpContractFiles, file)
}

export function getGraduationExample(file: string): string {
  return readExample('g01-graduation', graduationFiles, file)
}

export function getReleaseExample(file: string): string {
  return readExample('o04-release', releaseFiles, file)
}

export function getObservabilityExample(file: string): string {
  return readExample('o05-observability', observabilityFiles, file)
}

export function getRecoveryExample(file: string): string {
  return readExample('o06-recovery', recoveryFiles, file)
}

export function getIdentityExample(file: string): string {
  return readExample('s01-identity', identityFiles, file)
}

export function getAuthorizationExample(file: string): string {
  return readExample('s02-authorization', authorizationFiles, file)
}

export function getReliableOperationExample(file: string): string {
  return readExample('s03-reliable-operations', reliableOperationFiles, file)
}

export function getOperatingSystemExample(file: string): string {
  return readExample('o01-operating-system', operatingSystemFiles, file)
}

export function getContainerOpsExample(file: string): string {
  return readExample('o02-containers', containerOpsFiles, file)
}

export function getHttpsExample(file: string): string {
  return readExample('o03-https-production', httpsFiles, file)
}

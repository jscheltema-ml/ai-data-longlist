locals {
  config = jsondecode(file("${path.module}/../config/${var.environment}.json"))
}

data "azurerm_storage_account" "storage" {
  name                = module.storage.storage_account_name
  resource_group_name = module.resource_group.resource_group_name

  depends_on = [module.storage]
}

data "azurerm_container_registry" "shared" {
  name                = local.config.terraform_vars.container_registry_name
  resource_group_name = local.config.terraform_vars.container_registry_resource_group_name
}

module "resource_group" {
  source                   = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/resource_group?ref=main"
  resource_group_base_name = local.config.terraform_vars.project_name
  environment              = var.environment
}

module "storage" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/storage_account?ref=main"

  storage_account_base_name = local.config.terraform_vars.project_name
  resource_group_name       = module.resource_group.resource_group_name
  environment               = var.environment
}

module "log_analytics_workspace" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/log_analytics_workspace?ref=main"

  log_analytics_workspace_base_name = local.config.terraform_vars.project_name
  resource_group_name               = module.resource_group.resource_group_name
  environment                       = var.environment

}

module "application_insights" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/application_insights?ref=main"

  application_insights_base_name = local.config.terraform_vars.project_name
  resource_group_name            = module.resource_group.resource_group_name
  environment                    = var.environment
  location                       = local.config.terraform_vars.location
  workspace_id                   = module.log_analytics_workspace.log_analytics_workspace_id
}

# User Assigned Identity for Container App (AcrPull + Blob access)
module "user_assigned_identity" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/user_assigned_identity?ref=main"

  user_id_base_name   = local.config.terraform_vars.project_name
  resource_group_name = module.resource_group.resource_group_name
  environment         = var.environment
}

module "role_assignment_acr_pull" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/role_assignment?ref=main"

  scope                = data.azurerm_container_registry.shared.id
  role_definition_name = "AcrPull"
  principal_id         = module.user_assigned_identity.principal_id
}

module "role_assignment_blob_contributor" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/role_assignment?ref=main"

  scope                = module.storage.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.user_assigned_identity.principal_id
}

# Blob container holding the per-run JSON payloads (one blob per run).
module "storage_container_run_payloads" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/storage_account_container?ref=main"

  sa_container_name  = local.config.terraform_vars.storage_container_name
  storage_account_id = module.storage.storage_account_id
}

module "container_app_environment" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/container_app_environment?ref=main"

  container_app_environment_base_name = local.config.terraform_vars.project_name
  resource_group_name                 = module.resource_group.resource_group_name
  environment                         = var.environment
  location                            = "northeurope" // this is the default, but to keep it clean
  log_analytics_workspace_id          = module.log_analytics_workspace.log_analytics_workspace_id
}

module "container_app" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/container_app?ref=main"

  container_app_base_name      = local.config.terraform_vars.project_name
  resource_group_name          = module.resource_group.resource_group_name
  environment                  = var.environment
  container_app_environment_id = module.container_app_environment.id
  container_registry_name      = local.config.terraform_vars.project_name
  container_registry_image     = "${data.azurerm_container_registry.shared.login_server}/${local.config.terraform_vars.project_name}:latest"
  container_registry_server    = data.azurerm_container_registry.shared.login_server
  container_registry_identity  = module.user_assigned_identity.id
  identity_ids                 = [module.user_assigned_identity.id]
  cpu                          = local.config.terraform_vars.cpu
  memory                       = local.config.terraform_vars.memory
  min_replicas                 = local.config.terraform_vars.min_replicas
  max_replicas                 = local.config.terraform_vars.max_replicas
  http_concurrent_requests     = local.config.terraform_vars.http_concurrent_requests
  # Pinned rather than left to the module default (8080) so the port is stated in one
  # place and matches the Dockerfile CMD.
  ingress_target_port = 8000

  secrets = [
    {
      name                = "azure-api-key"
      identity            = module.user_assigned_identity.id
      key_vault_secret_id = "${module.key_vault.vault_uri}secrets/azure-api-key"
    },
    {
      name                = "posthog-api-key"
      identity            = module.user_assigned_identity.id
      key_vault_secret_id = "${module.key_vault.vault_uri}secrets/posthog-api-key"
    },
  ]

  env_vars = [
    { name = "STORAGE_ACCOUNT_NAME", value = module.storage.storage_account_name },
    { name = "STORAGE_ACCOUNT_KEY", value = data.azurerm_storage_account.storage.primary_access_key },
    { name = "STORAGE_CONTAINER_NAME", value = local.config.terraform_vars.storage_container_name },
    { name = "AZURE_CLIENT_ID", value = module.user_assigned_identity.client_id },
    { name = "APPLICATIONINSIGHTS_CONNECTION_STRING", value = module.application_insights.connection_string },
    { name = "APP_CLIENT_ID", value = local.config.terraform_vars.app_client_id },
    { name = "AZURE_API_VERSION", value = local.config.terraform_vars.azure_api_version },
    { name = "AZURE_ENDPOINT", value = local.config.terraform_vars.azure_endpoint },
    { name = "LLM_DEPLOYMENT", value = local.config.terraform_vars.llm_deployment },
    { name = "FOUNDRY_ENDPOINT", value = local.config.terraform_vars.foundry_endpoint },
    { name = "FOUNDRY_DEPLOYMENT", value = local.config.terraform_vars.foundry_deployment },
    { name = "AZURE_TENANT_ID", value = data.azurerm_client_config.current.tenant_id },
    { name = "POSTHOG_HOST", value = "https://eu.i.posthog.com" },
    { name = "ENVIRONMENT", value = var.environment },
    { name = "LOG_LEVEL", value = local.config.terraform_vars.log_level },
    { name = "NOISY_LOG_LEVEL", value = local.config.terraform_vars.noisy_log_level },

    # Secrets, referenced by the entries in `secrets` above rather than inlined.
    { name = "AZURE_API_KEY", secret_name = "azure-api-key" },
    { name = "POSTHOG_API_KEY", secret_name = "posthog-api-key" },
  ]

  depends_on = [module.role_assignment_acr_pull]
}

module "key_vault" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/key_vault?ref=main"

  resource_group_name = module.resource_group.resource_group_name
  environment         = var.environment
  keyvault_base_name  = local.config.terraform_vars.project_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
}

module "role_assignment_keyvault" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/role_assignment?ref=main"

  scope                = module.key_vault.vault_id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

module "role_assignment_keyvault_secrets_user" {
  source = "git::https://github.com/Marktlink/ai-data-shared-infra.git//modules/role_assignment?ref=main"

  scope                = module.key_vault.vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = module.user_assigned_identity.principal_id
}

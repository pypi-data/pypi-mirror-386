from gql import gql
from typing import Sequence

class createMethods:

    _CreateProxyQuery = """
    mutation CreateProxy(
  $description: String!
  $name: String!
  $organization_id: Int!
  $debug: Boolean!
  $log_level: String!
  $proxy_mode: String!
  $default_identity_id: Int
  $provider_data: [ProxyProviders_insert_input!]!
  $allow_noncloud_traffic: Boolean!
  $default_mode: proxysettings_default_mode_type!
  $learning_mode: Boolean!
) {
  insert_Proxies_one(
    object: {
      description: $description
      name: $name
      organization_id: $organization_id
      ProxySettings: {
        data: {
          proxy_mode: $proxy_mode
          debug: $debug
          log_level: $log_level
          default_identity_id: $default_identity_id
          allow_noncloud_traffic: $allow_noncloud_traffic
          default_mode: $default_mode
          learning_mode: $learning_mode
        }
      }
      ProxyProviders: { data: $provider_data }
    }
  ) {
    name
    organization_id
    status
    id
    ProxySettings {
      id
      default_identity_id
      debug
      log_level
      proxy_mode
      default_mode
      learning_mode
      allow_noncloud_traffic
    }
    ProxyProviders {
      id
      provider_id
    }
  }
}
    """

    def CreateProxy(self):
        query = gql(self._CreateProxyQuery)
        variables = {
        }
        operation_name = "CreateProxy"
        operation_type = "write"
        return self.execute(
            query,
            variable_values=variables,
            operation_name=operation_name,
            operation_type=operation_type,
        )

    _CreateProxyV2Query = """
    mutation CreateProxyV2(
  $name: String!
  $description: String!
  $organization_id: Int!
  $debug: Boolean = false
  $log_level: String!
  $proxy_mode: String = "HYBRID"
  $default_mode: proxysettings_default_mode_type!
  $learning_mode: Boolean!
  # @genqlient(pointer: true)
  $default_identity_id: Int = null
  $allow_noncloud_traffic: Boolean = false
  $tags: jsonb! = []
  $providers: [ProxyProviders_insert_input!] = []
  $identities: [ProxyIdentities_insert_input!] = []
  $domain_acls: [ProxyDomainAcls_insert_input!] = []
  $rego_raise_error: Boolean = false
  $on_error_action: rule_evaluation_action!
  $config_update_freq_secs: Int! = 10
  $idle_connection_timeout: Int! = 30
  $inspect_body_size_limit: Int! = 10000000
  $rego_version: String
) {
  insert_Proxies(
    objects: {
      description: $description
      name: $name
      organization_id: $organization_id
      tags: $tags
      ProxySettings: {
        data: {
          proxy_mode: $proxy_mode
          debug: $debug
          log_level: $log_level
          default_identity_id: $default_identity_id
          allow_noncloud_traffic: $allow_noncloud_traffic
          default_mode: $default_mode
          learning_mode: $learning_mode
          rego_raise_error: $rego_raise_error
          on_error_action: $on_error_action
          config_update_freq_secs: $config_update_freq_secs
          idle_connection_timeout: $idle_connection_timeout
          inspect_body_size_limit: $inspect_body_size_limit
          rego_version: $rego_version
        }
      }
      ProxyProviders: { data: $providers }
      ProxyIdentities: { data: $identities }
      ProxyDomainAcls: { data: $domain_acls }
    }
  ) {
    returning {
      id
      description
      name
      organization_id
      status
      tags
      ProxySettings {
        id
        debug
        log_level
        proxy_mode
        default_mode
        learning_mode
        default_identity_id
        allow_noncloud_traffic
        rego_raise_error
        on_error_action
        config_update_freq_secs
        idle_connection_timeout
        inspect_body_size_limit
        rego_version
      }
      ProxyProviders {
        id
        provider_id
        enabled
      }
      ProxyIdentities {
        deleted
        id
        identity_id
        proxy_id
      }
      ProxyDomainAcls {
        DomainAcl {
          name
          id
          DomainAclEntries {
            id
            action
            domain
          }
        }
      }
    }
  }
}
    """

    def CreateProxyV2(self):
        query = gql(self._CreateProxyV2Query)
        variables = {
        }
        operation_name = "CreateProxyV2"
        operation_type = "write"
        return self.execute(
            query,
            variable_values=variables,
            operation_name=operation_name,
            operation_type=operation_type,
        )

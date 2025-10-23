# tg-wrap

This app simply wraps terragrunt (which is a wrapper around terraform, which is a wrapper around cloud APIs, which is...).

> ❓ Wait, why on earth do we need a wrapper for a wrapper (for a wrapper)?

Well, first of all it is pretty opinionated so what works for us, doesn't necessarily work for you.

But our reasoning for creating this is as follows:

## 1. Less typing

terraform is great, and in combination with terragrunt even greater! But let's face it, terragrunt does not excel in conciseness! The options are pretty long, which leads to lots of typing. We don't like typing!

> With the [terragrunt cli redesign](https://terragrunt.gruntwork.io/docs/migrate/cli-redesign/) in 2025 this has been addresses, to a certain extent.

## 2. Testing modules locally

However, more importantly, we are heavily utilising [TG_SOURCE](https://terragrunt.gruntwork.io/docs/features/units/#working-locally) when developing.

The thing is that as long as you use `run --all` you can use one setting for that variable (and conveniently set it as an environment variable), while if you run a regular command, you need to specify the full path. Which is obviously different for each project.

Which leads to (even) more typing, and worse: a higher chance for errors.

Luckily you can use `run --all` and add the appriopriate flags to ensure it behaves like a regular plan|apply|destroy etc. But again, more typing.

Nothing a [bunch a aliases](https://gitlab.com/lunadata/terragrunt-utils/-/blob/main/tg-shell.sh) can't solve though! But we didn't found this a very sustainable solution.

## 3. But the original reason was: Errors when using run --all are challenging

One of the main boons of terragrunt is the ability to break up large projects in smaller steps while still retaining the inter-dependencies. However, when working on such a large project and something goes wrong somewhere in the middle is pretty challenging.

terragrunt's error messages are pretty massive, and this is extrapolated with every individual project in your dependency chain.

And if it fails somewhere at the front, it keeps on trying until the last one, blowing up your terminal in the process.

So we wanted a possibility to run the projects step by step, using the dependency graph of terragrunt and have a bit more control over it.

And when you can run it step by step, you can make the process also re-startable, which is also pretty handy!

And this was not something a bunch of aliases could solve, hence this wrapper was born. And while we we're at it, replacing the aliases with this was then pretty straightforward next step as well.

## 4. Analyzing plan files

When using the run --all on large environments, analyzing what is about to be changed is not going to be easier. Hence we created the `tgwrap analyze` function that lists all the planned changes and (if a config file is availabe) calculates a drift score and runs a [terrasafe](https://pypi.org/project/terrasafe/) style validation check.

> you can ignore minor changes, such as tag updates, with `tgwrap analyze -i tags`

It needs a config file as follows:

```yaml
---
#
# Critically of resources as interpreted by 'tgwrap analyze'.
# It uses it for a 'terrasafe' like validation if resources can safely be deleted.
# On top of that it tries to analyze and quantify the drift impact of the changes,
# so that this can be monitored.
#
low:
  # defaults:
  #   terrasafe_level: ignore_deletions
  #   drift_impact:
  #     default: minor
  #     delete: medium
  azuread_application.: {} # if we you want to use the defaults
  azuread_app_role_assignment: # or if you want to override these
    drift_impact:
      delete: minor
  # and so on, and so forth
medium:
  # defaults:
  #   terrasafe_level: ignore_deletion_if_recreation
  #   drift_impact:
  #     default: medium
  #     delete: major
  azurerm_data_factory_linked_service_key_vault.: {}
  # and so on, and so forth
high:
  # defaults:
  #   terrasafe_level: unauthorized_deletion
  #   drift_impact:
  #     default: major
  #     update: medium
  azuread_group.:
    drift_impact:
      create: minor
      update: minor
  azurerm_application_insights.: {}
  # and so on, and so forth
```

### Speeding up the performance of analyze

This `analyze` function turned out to be pretty slow, where most of the time went into the `terragrunt show` function that is executed for each individual module.

This was a bit surprising as the plan file is already available on the file system, but it turns out that terragrunt is taking quite a bit of time for managing the depdencies. Even when you're excluding the external dependencies and are located in a particular module.

So, if you add the following to your root `terragrunt.hcl`:

```hcl
terraform {
  after_hook "link_to_current_module" {
    commands = ["init", "plan", "apply", "validate", "destroy"]
    execute  = ["bash", "-c", "ln -sf $(pwd) ${get_terragrunt_dir()}/.terragrunt-cache/current"]
  }
}
```

The directory where the plan file is stored (including the other resources that terraform needs) becomes predictable and it becomes possible to run a native `terraform show` (instead `terragrunt show`) which dramatically speed up things.

Just set the proper value as an environment variable:

```console
export TGWRAP_PLANFILE_DIR=".terragrunt-cache/current"
```

Or pass it along with the `--planfile-dir|-P` option and it will use that.

## 5. Logging the results

`tgwrap` supports logging the analyze results to an [Azure Log Analytics](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-overview) custom table.

For that, the custom table need to be present, including a [data collection endpoint](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/data-collection-endpoint-overview?tabs=portal) and associated [data collection rule](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/data-collection-rule-overview?tabs=portal).

When you want to activate this, just pass `--data-collection-endpoint` (or, more conveniently, set the `TGWRAP_ANALYZE_DATA_COLLECTION_ENDPOINT` environment variable) with the url to which the data can be posted.

> Note that for this to work, `tgwrap` assumes that there is a functioning [azure cli](https://learn.microsoft.com/en-us/cli/azure/) available on the system.

A payload as below will be posted, and the log analytics table should be able to accomodate for that:

```json
[
  {
    "scope": "terragrunt/dlzs/data-platform/global/platform/rbac/",
    "principal": "myself",
    "repo": "https://gitlab.com/my-git-repo.git",
    "creations": 0,
    "updates": 0,
    "deletions": 0,
    "minor": 0,
    "medium": 0,
    "major": 0,
    "unknown": 0,
    "total": 0,
    "score": 0.0,
    "details": [
      {
        "drifts": {
          "minor": 0,
          "medium": 0,
          "major": 0,
          "unknown": 0,
          "total": 0,
          "score": 0.0
        },
        "all": [],
        "creations": [],
        "updates": [],
        "deletions": [],
        "unauthorized": [],
        "unknowns": [],
        "module": ""
      }
    ]
  }
]
```

The log analytics (custom) table should have a schema that is able to cope with the message above:

| Field          | Type     |
|----------------|----------|
| creations      | Int      |
| deletions      | Int      |
| details        | Dynamic  |
| major          | Int      |
| medium         | Int      |
| minor          | Int      |
| principal      | String   |
| repo           | String   |
| scope          | String   |
| score          | Int      |
| TimeGenerated  | Datetime |
| total          | Int      |
| unknown        | Int      |
| updates        | Int      |

# Terraform vs OpenTofu

`tgwrap` is compatible with both [terraform](https://www.terraform.io/) and [opentofu](https://opentofu.org/).

As we are **almost** exclusively relying on `terragrunt` to invoke them on our behalf, there is not much exposure to that decision.

> ⚠️ However, there is one exception (and maybe there will be more in the future) where this is not true. For that we rely on the existance of the `tf` binary (or symbolic link, or alias and so on). It is managed automatically by the [tenv tool](https://github.com/tofuutils/tenv) (higly recommended!), but if you don't want to use it, make sure you create an alias or something like that.

# More than a wrapper

Over time, tgwrap became more than a wrapper, blantly violating [#1 of the unix philosophy](https://en.wikipedia.org/wiki/Unix_philosophy#:~:text=The%20Unix%20philosophy%20is%20documented,%2C%20as%20yet%20unknown%2C%20program.): 'Make each program do one thing well'.

For instance, the 'analyze' functionality is already an example, but more features such as deploying a landing zone has crept into the application. It makes sense for how we're using it, but we're fully aware this makes it less generically applicable.

## Usage

```console
# general help
tgwrap --help

tgwrap run -h

# run a plan
tgwrap plan # which is the same as tgwrap run plan

# run all a plan
tgwrap plan -A

# or do the same in step-by-step mode (which, by definition implies --all)
tgwrap plan -s

# if you want to add additional arguments it is recommended to use -- as separator (although it *might* work without)
tgwrap output -- -json
```

> Note: special precautions are needed when passing on parameters that contain quotes. For instance, if you want to move state like below, escape the double quote in the staate address:

`tgwrap state mv 'azuread_group.this[\"viewers\"]' 'azuread_group.this[\"readers\"]'`

## Using the `exclude` and `include` dir options

When using a `run --all` you can use the ``--queue-exclude-dir | -E` and `--queue-include-dir | -I` options to exclude certain unit directories, **or** to **only** include a given unit. You can add these options multiple times (but it doesn't make sense to use both include and exclude at the same time!).

Most, but not all, of these options are passed along straight away to terragrunt, which interprets this in the following way:

For example:

```console
# to exclude a particular unit in the same dir
tgwrap plan -A -E path/to/unit-to-exclude

# to exclude a directory full of units
tgwrap plan -A -E 'path/*'

# or to exclude a directory multiple levels deep
tgwrap plan -A -E 'path/**/*'

# include a subdirectory (pay attention to the quotes!)
tgwrap plan -A -I 'path/to/include/*'
```

> ⚠️ Note: always quote the options that contain wildcards!

## Deploy manifests

In order to easily deploy a new version of the terraform (and associated terragrunt) modules, we include a manifest file in the root of the landing zone:

```yaml
---
git_repository: ssh://git@gitlab.com/my-org/my-terraform-modules-repo.git
base_path: terragrunt/my-platform # path where the terragrunt modules are stored
config_path: terragrunt/config/platform-dev # path (relative to base path) where the config files are stored

deploy: # which modules do you want to deploy
  dtap:
    applies_to_stages:
      - dev
      - tst
      - acc
      - prd
    source_stage: dev
    source_dir: platform # optional, if the source modules are not directly in the stage dir, but in <stage>/<source_dir> directory
    base_dir: platform # optional, if you want to deploy the base modules in its own dir, side by side with substacks
    include_global_config_files: false # optional, overrides the CLI input
    config_dir: ../../../config # this is relative to where you run the deploy
    configs:
      - my-config.hcl
      - ../my-ss-config-dir
    # skip_all_modules: True # could be handy if you only want to deploy substacks and no regular modules
    exclude_modules: # these modules will always be excluded, can be omitted
      - my-specific-module
    include_modules: {} # omit or use an empty dict for all of them
      # or specify your modules as follows
      # base: {} # just a simple include
      # networking-connected: # or a bit more complicated
      #  - source: networking
      #  - target: networking-connected

substacks:
  is01:
    source: shared-integration/intsvc01
    target: integration/is01
    exclude_modules:  # a list of modules that will always be excluded, can be omitted
      - my-specific-module
    configs:
      - my-ss-config.hcl
      - ../my-ss-config-dir
  is02:
    applies_to_stages: # optional list of stages to include the substack in
      - dev
    source: shared-integration/intsvc01
    target: integration/is02

# global configuration files that are deployed as well
# note that these files are typically applicable to all landing zones and stages!
# this might lead to unexpected behaviour
# note that you can exclude syncing these files with a command line switch
global_config_files:
  root-terragrunt:
    source: ../../terragrunt.hcl # relative to base_path
    target: ../../terragrunt.hcl # can be omitted, then it is same as source path
  terrasafe-config:
    source: ../../terrasafe-config.json
```

## Inspecting deployed infrastructure

Testing infra-as-code is hard, even though test frameworks are becoming more common these days. But the standard test approaches typically work with temporary infrastructures, while it is often also useful to test a deployed infrastructure.

Frameworks like [Chef's InSpec](https://docs.chef.io/inspec/) aims at solving that, but it is pretty config management heavy (but there are add-ons for aws and azure infra). It has a steep learning curve, we only need a tiny part of it, and also comes with a commercial license.

For what we need ('is infra deployed and are the main role assignments still in place') it was pretty easy to implement in python.

For this, you can now run the `inspect` command, which will then inspect real infrastructure and role assignments, and report back whether it meets the expectations (as declared in a config file):

```yaml
---
location:
  code: westeurope
  full: West Europe

# the entra id groups ar specified as a map as these will be checked for existence
# but also used for role assignment validation
entra_id_groups:
  platform_admins: '{domain}-platform-admins'
  cost_admins: '{domain}-cost-admins'
  data_admins: '{domain}-data-admins'
  just_testing: group-does-not-exist

# the resources to check
resources:
  - identifier: 'kv-{domain}-euw-{stage}-base'
    # due to length limitations in resource names, some shortening in the name might have taken place
    # so you can provide alternative ids
    alternative_ids:
    - 'kv-{domain}-euw-{stage}-bs'
    - 'kv{domain}euw{stage}bs'
    - 'kv{domain}euw{stage}base'
    type: key_vault
    resource_group: 'rg-{domain}-euw-{stage}-base'
    role_assignments:
      - platform_admins: Owner
      - platform_admins: Key Vault Secrets Officer
      - data_admins: Key Vault Secrets Officer
```

After which you can run the following:

```console
tgwrap inspect -d domain -s sbx -a 886d4e58-a178-4c50-ae65-xxxxxxxxxx -c ./inspect-config.yml
......

Inspection status:
entra_id_group: dps-platform-admins
	-> Resource:	OK (Resource dps-platform-admins of type entra_id_group OK)
entra_id_group: dps-cost-admins
	-> Resource:	OK (Resource dps-cost-admins of type entra_id_group OK)
entra_id_group: dps-data-admins
	-> Resource:	OK (Resource dps-data-admins of type entra_id_group OK)
entra_id_group: group-does-not-exist
	-> Resource:	NEX (Resource group-does-not-exist of type entra_id_group not found)
key_vault: kv-dps-euw-sbx-base
	-> Resource:	OK (Resource kv-dps-euw-sbx-base of type key_vault OK)
	-> RBAC:	NOK (Principal platform_admins has NOT role Owner assigned; )
subscription: 886d4e58-a178-4c50-ae65-xxxxxxxxxx
	-> Resource:	OK (Resource 886d4e58-a178-4c50-ae65-xxxxxxxxxx of type subscription OK)
	-> RBAC:	NC (Role assignments not checked)
```

You can sent the results also to a data collection endpoint (seel also [Logging the results](#logging-the-results)).

For that, a custom table should exist with the following structure:


| Field                      | Type     |
|----------------------------|----------|
| domain                     | String   |
| substack                   | String   |
| stage                      | String   |
| subscription_id            | String   |
| resource_type              | String   |
| inspect_status_code        | String   |
| inspect_status             | String   |
| inspect_message            | String   |
| rbac_assignment_status_code| String   |
| rbac_assignment_status     | String   |
| rbac_assignment_message    | String   |
| resource                   | String   |

## Project layout

- `tgwrap/` holds the CLI entry points (`cli.py`, `main.py`) and runtime feature modules such as `analyze.py`, `deploy.py`, and `inspector.py`.
- `tgwrap/core/` contains orchestration utilities. `wrapper.py` wires the services into the CLI-facing `TgWrap` façade, while `constants.py` shares values like `STAGES` and the `DateTimeEncoder`.
- `tgwrap/services/` hosts focused building blocks used by the wrapper:
  - `graph_runner.py` assembles and executes the Terragrunt dependency graph.
  - `analyzer.py` coordinates plan analysis using the graph runner, command constructor, and analyze helpers.
  - `deployer.py` encapsulates deployment, sync, and version-inspection workflows.
  - `azure.py` wraps Azure CLI interactions (tokens, telemetry posting) shared between analyzer and inspector flows.
- `tests/` mirrors runtime modules with pytest suites.
- `examples/` contains Terragrunt layouts for manual checks.
- `docs/` stores long-form documentation, and `dist/` receives build artifacts created by `poetry build`.

## Generating change logs

tgwrap can generate a change log by running:

```console
tgwrap change-log [--changelog-file ./CHANGELOG.md]
```

The (optional) change log file will be, if passed along. tgwrap then checks the file for the existance of a start and end markers, in the following format:

```python
  start_marker = '<!-- BEGINNING OF OF TGWRAP CHANGELOG SECTION -->'
  end_marker = '<!-- END OF TGWRAP CHANGELOG SECTION -->'
```

If they exist, everything between these lines will be replaced by the new change log.

## Development

In order to develop, you need to apply it to your terragrunt projects. For that you can use the `--terragrunt-working-dir` option and just run it from the poetry directory. Alternatively you can use the [tgwrap-dev](./tgwrap-dev) script and invoke that from your terragrunt directories. Either put it in your `PATH` or create an alias for convenience.

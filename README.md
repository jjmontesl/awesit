# Sitetool

Sitetool is a tool to manage website deployments and development.

It manages information about Joomla deployments and provides
methods to backup and deploy Joomla sites across different
staging environments.


# Requirements

- "Replace" panel (list webs, backups, pending updates, security extensions...)
- Backup Joomla (backups are slow ie 10 min)
- Update some content (1-N articles or modules, w/ images)
- Update an extension or extensions manually

Lean Canvas Tasks:

- Update outdated extensions automatically (joomla "button")
- Update Joomla (through joomla "button")


## Configuration

Sitetool requires information about the environments it manages.

  BACKUP_PATH = '/home/$user/sitetool/backups/'
  WORKINGDIR_PATH = '/home/$user/sitetool/sites/'

Configuration is done in YAML format. It is recommended to keep
your sitetool configuration versioned.


## Usage

sitetool <command> [options...] [-h]

  sitetool backup testsite1:prod backup:local
  sitetool backup testsite1:prod backup:local2

  sitetool deploy site1 backup-local 5d site1:dev
  sitetool deploy site1:prod site1:dev  # Pa nota

  sitetool listbackup backups site1 (?)


## Commands

sitetool backup testsite1:prod backup:default --db --files
sitetool backup backup:default:-5d testsite1:dev --db

sitetool backup-deploy testsite1:prod :dev

sitetool deploy backup:main/site:env site:dev
sitetool deploy backup:default:testsite1:dev:-5d testsite1:dev --artifacts=files

sitetool git-deploy
sitetool deploy git: ///home/user/ :default:testsite1:dev:-5d testsite1:dev --artifacts=files
git?? (could it act as a source, like backup?)

sitetool backup-list

sitetool backup-diff backup:default:testsite1:prod:

sitetool joomla-data-merge testsite1:dev :prod --models:articles,products --overwrite --noop
sitetool joomla-data-export --format:filedir testsite1:prod ~/sites/testsite1 --models:articles,categories
sitetool joomla-datadir?-import --format:filedir ~/sites/testsite1 testsite1:prod --models:articles,categories --background

sitetool joomla-extension-install testsite1:dev <extension.zip>
sitetool joomla-extension-list *:prod  # testsite1:dev  # List extensions and versions and upgrades

sitetool browser testsite1:prod


## Examples

** Copy a site from production for local development **

** Push changes to Joomla articles to preproduction **

** Restore an entire site from a backup **

** Update joomla extension in a site **


## Backup

## Backup scheduling

TODO: Is this necessary? (wishlist or separate tool?)

## Deployment

## TODO:

Analysis TODO:

- https://github.com/2createStudio/shuttle-export
- Separate database / files export (ie. php vs ftp vs ...)
- "Driver type"? (files / database / configs-alterations-chain(joomla? prestashop?))
- Enumerate drivers (and types / scope if applicable)
- Actions: define pipeline/settings/scope for each action (backup, deploy... ???)
- Improve config, complex scenario before starting

- How to deal with versioning? git before changes to be able to check diffs and and commits... (?) (files only, in principle?)

Wishlist TODO:

- Evolution towards merging data (or files, or media!) from
  specific applications/modules (merge/update Joomla articles, Prestashop etc)
- Stress ability to merge/extract from files or directories
- Monitoring: response times, check health (ie via PHP tool or custom regexps on URLs)
- Drivers/Tools to synchronzie from other strategies??? (ie. filesystem-folders -> joomla articles)
- Containers, Virtualization, Other tools... (Docker / Lando) - local first for dev envs
- Selenium integration?

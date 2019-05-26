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

Configuration is done in YAML format. Configuration may eventually
include templates and other files. It is recommended to keep
your sitetool configuration versioned.

SiteTool reads by default configuration from user home `~/.sitetool.conf . This
can be changed using the `-c` command line option.

You can find an example configuration in the `sitetool.conf.sample` file.
Copy it to your home `~/.sitetool.conf` and **modify it** to reflect the
sites you will be managing.


## Usage

    usage: sitetool [-h] [-d] [-c CONFIG] command [command options]

      Commands:
        backup-list
        backup
        deploy
        backup-delete
        sites
        browser
        backup-deploy

    positional arguments:
      command               subcommand to run

    optional arguments:
      -d, --debug           debug logging
      -c CONFIG, --config CONFIG
                            config file


## Commands

    $ # List your configured sites, computing their size
    $ sitetool sites -f

    backup:main      [ 4865.9M /    17 files] (an hour ago) ~/sitetool/backup/
    backup:testssh   [    8.5M /     2 files] (16 minutes ago) /tmp/sitetoolbackup/
    site1:prod       [  201.7M /  1089 files] (11 hours ago) /opt/site1
    site2:prod       [  409.5M / 12816 files] (37 minutes ago) /opt/site2
    site2:tmp        [    0.0M /     0 files] (-) /tmp/site2/
    site3:dev        [   43.8M /  1037 files] (3 months ago) ~/git/site3-page/
    site3:prod       [   34.4M /   152 files] (2 years ago) /opt/site3-page
    site3:tmp        [   34.4M /   152 files] (20 hours ago) /tmp/site3/
    ...
    Listed sites: 14


    $ # Backup a site (to the default storage: `backup:main`)
    $ sitetool backup site1:prod

    $ # Backup a site to a different storage
    $ sitetool backup site1:prod backup:external-hd

    $ # List backups
    $ sitetool backup-list

    backup:main           site1:prod    -1   318.7M site1-prod-20190524-215511-files.tar.gz (19 hours ago)
    backup:main           site2:prod    -1  1992.8M site2-prod-20190524-214501-files.tar.gz (19 hours ago)
    backup:main           site3:prod    -1   113.7M site3-prod-20190525-000025-files.tar.gz (17 hours ago)
    backup:main        gitolite:prod    -1  2248.7M gitolite-prod-20190525-002522-files.tar.gz (17 hours ago)
    backup:main       testsite2:prod    -4     8.4M testsite2-prod-20190525-161658-files.tar.gz (an hour ago)
    backup:main       testsite2:prod    -3     0.1M testsite2-prod-20190525-161658-db.tar.gz (an hour ago)
    backup:main       testsite2:prod    -2     8.4M testsite2-prod-20190525-162048-files.tar.gz (an hour ago)
    backup:main       testsite2:prod    -1     0.1M testsite2-prod-20190525-162048-db.tar.gz (an hour ago)
    backup:testssh    testsite2:prod    -2     8.4M testsite2-prod-20190525-173754-files.tar.gz (21 minutes ago)
    backup:testssh    testsite2:prod    -1     0.1M testsite2-prod-20190525-173754-db.tar.gz (21 minutes ago)
    ...
    Listed jobs: 19  Total size: 4874.4MB


    # Deploy a site last backup to development environment
    sitetool deploy ::site1:prod:-1 site1:dev

    # Open a browser tab for a site
    sitetool browser testsite1:prod


    sitetool joomla-data-merge testsite1:dev :prod --models:articles,products --overwrite --noop
    sitetool joomla-data-export --format:filedir testsite1:prod ~/sites/testsite1 --models:articles,categories
    sitetool joomla-datadir?-import --format:filedir ~/sites/testsite1 testsite1:prod --models:articles,categories --background

    sitetool joomla-extension-install testsite1:dev <extension.zip>
    sitetool joomla-extension-list *:prod  # testsite1:dev  # List extensions and versions and upgrades


## Documentation


## TODO:

- Add complete file ignore support to local and ssh files (currently local uses ignores just for listing)
- Use proper temporary names for files during backup/deploy/upload/download! (could be conflicts with current implementation)
- Connect only once to each backup storage when exploring backups! (avoids hitting SSH connections)

- (?) https://github.com/2createStudio/shuttle-export
- (?) How to deal with versioning? git before changes to be able to check diffs and and commits... (?) (files only, in principle?)

- (?) Backup scheduling
- (?) Monitoring: response times, check health (ie via PHP tool or custom regexps on URLs)
- (?) Containers, Virtualization, Other tools... (Docker / Lando)


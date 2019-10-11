# Awesit - Another Website Tool

Awesit is a tool to manage website deploy, backup and update workflows.

Awesit can help developers, content workers, webmasters and users to
backup deployed sites and replicate them to different environments.
It can also calculate file and database differences between environments.
It can also serve as a backup system and scheduler.

Features:

- Backup and restore files and databases across configured sites.
- Backup and restore databases (currently MySQL).
- Manage different site environments (production, staging, development...).
- Manage backups and backup storages.
- Access files locally or through SSH, SFTP, FTP...
- Access files and databases through a PHP helper script.
- Calculate differences and synchronize files and data across environments.
- List Joomla sites, version, PHP info, extensions...

See the Examples section below for more information.


## Usage

    usage: sit [-h] [-d] [-c CONFIG] command [command options]

      Commands:
        backup               Backup a given site
        backup-delete        Delete backup jobs data (use with caution!)
        backup-list          Show available backup jobs
        browser              Opens a browser tab pointing to a site
        db-diff              Compare data in two databases with same schema.
        db-serialize         Dump database tables into serialized format usable to calculate differences.
        deploy               Deploys a backup to a given environment
        files-diff           Show differences between two sites file trees
        joomla-info          Show information about Joomla installations
        sites                Show configured sites and environments

      Use  sit <command> -h  for help about that command.

    positional arguments:
      command               command to run

    optional arguments:
      -d, --debug           debug logging
      -c CONFIG, --config CONFIG
                            config file


## Installation

Requires Python 3.6 or above.

Clone the source repository:

    git clone https://github.com/jjmontesl/awesit

Enter the directory and install:

    python3.6 setup.py install


In order to use Awesit, **you must define a configuration file** that
describes your different site projects and deployment environments.


## Configuration

Awesit requires information about the environments it manages.

Configuration is done in YAML format. Configuration may eventually
include templates and other files. Depending on your use case,
you may wish to keep your configuration files versioned.

Awesit reads by default configuration from user home `~/.awesit.conf`.
This can be changed using the `-c` command line option.

You can find an example configuration in the `awesit.conf.sample` file.
Copy it to your home directory with name `.awesit.conf` and
**edit it** to reflect the sites you will be managing.


## Examples

**Site Management**

    $ # List configured sites, computing their size
    $ sit sites -f

    backup:main      [ 4865.9M /    17 files] (an hour ago) ~/awesit/backup/
    backup:testssh   [    8.5M /     2 files] (16 minutes ago) /tmp/awesitbackup/
    site1:prod       [  201.7M /  1089 files] (11 hours ago) /opt/site1
    site2:prod       [  409.5M / 12816 files] (37 minutes ago) /opt/site2
    site2:tmp        [    0.0M /     0 files] (-) /tmp/site2/
    site3:dev        [   43.8M /  1037 files] (3 months ago) ~/git/site3-page/
    site3:prod       [   34.4M /   152 files] (2 years ago) /opt/site3-page
    site3:tmp        [   34.4M /   152 files] (20 hours ago) /tmp/site3/
    ...
    Listed sites: 14

**Backup**

    $ # Backup a site (to the default storage: `backup:main`)
    $ sit backup site1:prod

    $ # Backup a site to a different storage
    $ sit backup site1:prod backup:external-hd

    $ # List backups
    $ sit backup-list

    backup:main           site1:prod    1   318.7M site1-prod-20190524-215511-files.tar.gz (19 hours ago)
    backup:main           site2:prod    1  1992.8M site2-prod-20190524-214501-files.tar.gz (19 hours ago)
    backup:main           site3:prod    1   113.7M site3-prod-20190525-000025-files.tar.gz (17 hours ago)
    backup:main        gitolite:prod    1  2248.7M gitolite-prod-20190525-002522-files.tar.gz (17 hours ago)
    backup:main       testsite2:prod    4     8.4M testsite2-prod-20190525-161658-files.tar.gz (an hour ago)
    backup:main       testsite2:prod    3     0.1M testsite2-prod-20190525-161658-db.tar.gz (an hour ago)
    backup:main       testsite2:prod    2     8.4M testsite2-prod-20190525-162048-files.tar.gz (an hour ago)
    backup:main       testsite2:prod    1     0.1M testsite2-prod-20190525-162048-db.tar.gz (an hour ago)
    backup:testssh    testsite2:prod    2     8.4M testsite2-prod-20190525-173754-files.tar.gz (21 minutes ago)
    backup:testssh    testsite2:prod    1     0.1M testsite2-prod-20190525-173754-db.tar.gz (21 minutes ago)
    ...
    Listed jobs: 19  Total size: 4874.4MB

**Restore / Deploy**

    # Deploy a site last backup to development environment
    sit deploy backup:main:site1:prod:1 site1:dev

**Browser**

    # Open a browser tab for a site
    sit browser testsite1:prod

    # Open browser tabs for all environments of a site
    sit browser testsite1:

**Joomla sites**

    # List Joomla sites, with extensions list and verbose info
    sit joomla-info -v -e

    testsite2:prod
      Joomla! 3.9.6 Stable [ Amani ] 7-May-2019 15:00 GMT (178 extensions) - PHP 7.1.29
      178 extensions (component: 34, library: 5, module: 39, plugin: 93, template: 4, language: 1, file: 1, package: 1)
      44 directories (0 non writable)
      http://localhost:8080
      Extensions (178):
        com_actionlogs                        3.9.0 D  component
        com_admin                             3.0.0    component
        com_ajax                              3.2.0    component
        com_associations                      3.7.0 D  component
        com_banners                           3.0.0    component
        ...

    # Dump detailed Joomla information in JSON format (and pipe output through less)
    sit joomla-info mysite:prod --json | less


## Documentation


## License

Awesit is created and maintained by Pablo Arias and Jose Juan Montes.

License definition is pending (AGPL, MIT or Apache licenses are being considered).


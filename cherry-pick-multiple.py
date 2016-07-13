#! /usr/bin/env python
# coding: utf-8
"""Iterates over Github repositories and cherry pick commit(s) from a source repo.
"""

from github import Github
from git import Repo
from optparse import OptionParser
import json
import shutil
import tempfile
import time

parser = OptionParser()
parser.add_option('-p', '--print', dest = 'print_only', help = 'Just print the results, do not update the repo', default=False, action='store_true')
(options, args) = parser.parse_args()

config = json.load(open(args[0]))
pause_seconds = 120

g = Github(config['github_auth_key'])

upstream_repo = g.get_organization(config['repo_owner']).get_repo(config['source']['repo_name'])

for target_repo in config['targets']:
    # Initialize repo.
    repo = g.get_organization(config['repo_owner']).get_repo(target_repo['repo_name'])
    print 'Updating: ' + repo.name
    tmp_dirpath = tempfile.mkdtemp()
    cur_repo = Repo.clone_from(repo.ssh_url, tmp_dirpath)

    # Check out the desired branch.
    print cur_repo.git.checkout(target_repo['branch'])

    # Fetch Upstream.
    upstream_ref = cur_repo.create_remote('cherry-source', upstream_repo.ssh_url)
    for fetch_info in upstream_ref.fetch():
        print("Updated %s to %s" % (fetch_info.ref, fetch_info.commit))

    # Cherry pick commits from config.
    for cherry_commit in config['source']['commits']:
        print cur_repo.git.cherry_pick(cherry_commit)

    # Push to Github.
    if not options.print_only:
        print cur_repo.git.push('origin', target_repo['branch'])
        print "Sleeping for " + str(pause_seconds) + " seconds to be polite.."
        time.sleep(pause_seconds)

    shutil.rmtree(tmp_dirpath)

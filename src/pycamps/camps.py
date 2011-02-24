# Main class for pycamps

import os
import sys
import re
import time
import shutil

import git
from git.errors import InvalidGitRepositoryError, NoSuchPathError, GitCommandError

import func.overlord.client as fc

from pycamps.db import *
import pycamps.settings as settings

class CampError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        repr(self.value)


class Camps:
    """
    Certain variables are stored per camp in the ~/user/campX/INFO file:
    
    'camp_id': each camp *must* have a unique id
    'description': to help identify one camp from another
    'db_user, db_pass, db_host, db_port': useful for connecting and running queries and the like
    """
    
    def __init__(self):
    
        """Initializes some basic information about the camp. 
        User name and campsdb instances, for example."""
    
        #print arguments
    
        self.login = os.getenv('LOGNAME')
        self.campdb = PyCampsDB()

    def _clone_db_lvm_snap(self, client):
        """Clones the campmaster db into a particular camp db 
        using logical volume snapshots"""
        
        lv_snapshot_cmd = "lvcreate -L %s -s -p rw -n %s /dev/%s/%s" % (settings.CAMPS_LV_SIZE, settings.CAMPS_BASENAME + str(self.camp_id), settings.CAMPS_VG, settings.CAMPS_LV)
        client.command.run(lv_snapshot_cmd)
        print "camp%d database snapshot complete" % self.camp_id


    def _clone_db_rsync(self, client):
        """Clones the campmaster db into a particular camp db 
        using logical volume snapshots"""

        rsync_cmd = "/usr/bin/rsync -a %s/%smaster/* %s/%s" % (settings.DB_ROOT, settings.CAMPS_BASENAME, settings.DB_ROOT, settings.CAMPS_BASENAME + str(self.camp_id))
        client.command.run(rsync_cmd)

    def _chown_db_path(self, client):
        chown_cmd = "/bin/chown -R %s.%s %s/%s" % (settings.DB_USER, settings.DB_GROUP, settings.DB_ROOT, settings.CAMPS_BASENAME + str(self.camp_id))
        client.command.run(chown_cmd)

    def _add_db_config(self, client):
        mysql_config = "echo '\n%s\n' >> /etc/my.cnf" % (settings.DB_CONFIG % {'camp_id': self.camp_id, 'port': (settings.DB_BASE_PORT + self.camp_id)})
        client.command.run(mysql_config)
        print "camp%d database configured" % self.camp_id

    def _clone_db(self, client):
        """Clones the campmaster db into a particular camp db
        and adds appropriate configs into the database itself"""

        # determine the method of cloning
        if settings.DB_CLONE_METHOD == "RSYNC":
            self._clone_db_rsync(client)
        else:
            self._clone_db_lvm_snap(client)
        self._chown_db_path(client)
        self._add_db_config(client)

    def _clone_docroot(self):
        try:
            # setup the blank repo 
            repo = git.Repo(settings.GIT_ROOT)
            # clone the blank repo
            self.clone = repo.clone(self.camppath)
            # create a campX branch
            branch = self.clone.create_head(settings.CAMPS_BASENAME + str(self.camp_id))
            # checkout the campX branch
            self.camp_repo = self.clone.heads[settings.CAMPS_BASENAME + str(self.camp_id)].checkout()
            # if the origin exists, remove it (we may not need this in the future)
            self.clone.delete_remote(self.clone.remotes.origin)
            # create the origin remote
            self.clone.create_remote('origin', settings.GIT_REMOTE)
            self.clone.remotes.origin.pull('refs/heads/master:refs/heads/camp%s' % str(self.camp_id) )
            print "Cloning camp%d web data complete" % self.camp_id

        except NoSuchPathError, e:
            raise CampError("Cannot clone the non-existent directory: %s" % e)

    def _web_config(self):
        """configure the camp to work with the web server.  Default server is apache"""

        # confirm the full path exists, if not, create it
        try:
            os.stat('%s/%s' %(self.camppath, settings.WEB_CONFIG_BASE) )
        except OSError, e:
            os.makedirs('%s/%s' %(self.camppath, settings.WEB_CONFIG_BASE), 0775)

        # write the config file out
        # assuming here that the full directory structure is built
        self.web_conf_file = '''%s/%s/%s''' % (self.camppath, settings.WEB_CONFIG_BASE, settings.WEB_CONFIG_FILE)
        file = open(self.web_conf_file, 'w+')
        file.write('''Alias /%s %s/%s\n''' % (self.campname, self.camppath, settings.WEB_DOCROOT) )
        file.close()

# originally, I had thought committing the configs for apache was a good idea
# instead, I've decided that adding the web configs to the .gitignore is better

#    def _push_web_config(self):
#
#        # commit it to the git repo and push it
#        index = self.clone.index
#        index.add(['''%s/%s/%s''' % (self.camppath, settings.WEB_CONFIG_BASE, settings.WEB_CONFIG_FILE)])
#        commit = index.commit('''automated from pycamps: adding web config file''')
#        self.clone.remotes.origin.push('refs/heads/camp%s:refs/heads/camp%s' % (str(self.camp_id), str(self.camp_id)) )

    def _web_symlink_config(self, func_client):
        # do the symbolic link to httpd_config_root

        symlink_httpd_config = '''/bin/ln -s %s %s/%s.conf''' % (self.web_conf_file, settings.HTTP_CONFIG_DIR, self.campname)
        result = func_client.command.run(symlink_httpd_config)

    def _restart_web(self, func_client):
        # restart the web service
        web_restart_cmd = '''service httpd restart'''
        result = func_client.command.run(web_restart_cmd)

    def _start_db(self, func_client, camp_id):
        result = func_client.command.run("/usr/bin/mysqld_multi start %s" % camp_id)
        time.sleep(5)
        result = func_client.command.run("(/bin/ps -ef | /bin/grep mysql | /bin/grep %s | /bin/grep -v grep)" % camp_id)
        if result[settings.FUNC_DB_HOST][0] != 0:
            raise CampError('Unable to start camp%s, contact the administrator <%s>' % (camp_id, settings.ADMIN_EMAIL))

    def _stop_db(self, func_client, camp_id):
        result = func_client.command.run("/usr/bin/mysqld_multi stop %s" % camp_id)
        time.sleep(5)
        result = func_client.command.run("(/bin/ps -ef | /bin/grep mysql | /bin/grep %s | /bin/grep -v grep)" % camp_id)
        if result[settings.FUNC_DB_HOST][0] != 1:
            raise CampError('Unable to stop camp%s, contact the administrator <%s>' % (camp_id, settings.ADMIN_EMAIL))

    def _get_camp_id(self):
        """Attempt to obtain the camp_id by looking at the basename of the path.  
           If the path is not in a camp, this function will fail."""
        camp_basename = os.path.basename(os.getcwd())
        if re.match("^%s\d+$" % settings.CAMPS_BASENAME, camp_basename):
            return re.split("^%s" % settings.CAMPS_BASENAME, camp_basename)[1]
        else:
            return None

    def stop(self, arguments):
        if arguments.id == None:
            camp_id = self._get_camp_id()
            if camp_id == None:
                raise CampError("The camp_id was not supplied or could not be obtained")
        else:
            camp_id = arguments.id

        if arguments.db:
            print "Stopping database on camp%s" % camp_id
            client = fc.Client(settings.FUNC_DB_HOST)
            self._stop_db(client, camp_id)
            # wait for it to stop
            time.sleep(5)
            # should actually check that the db is stopped 
            print "camp%s database successfully stopped" % camp_id

        if arguments.web:
            pass

    def start(self, arguments):
        if arguments.id == None:
            camp_id = self._get_camp_id()
            if camp_id == None:
                raise CampError("The camp_id was not supplied or could not be obtained")
        else:
            camp_id = arguments.id

        if arguments.db:
            print "Starting database on camp%s" % camp_id
            client = fc.Client(settings.FUNC_DB_HOST)
            self._start_db(client, camp_id)
            # wait for it to start
            time.sleep(5)
            print "camp%s database server successfully started" % camp_id
        if arguments.web:
            print "camp%s web server successfully started" % camp_id
            pass

    def restart(self, arguments):
        self.stop(arguments)
        self.start(arguments)

    def remove(self, arguments):
        """Removes a camp directory and its corresponding db directory"""

        # add something here to check for pycampsadmin later on

        if arguments.id == None:
            camp_id = self._get_camp_id()
            if camp_id != None and arguments.force == None:
                raise CampError("""A camp cannot be removed from within its own directory.""")

        camp_id = arguments.id
        try:
            filestats = os.stat('%s/%s' %(settings.CAMPS_ROOT, settings.CAMPS_BASENAME + str(camp_id)) )
            if os.getuid() != filestats[4]:
                if arguments.force == None:
                    raise CampError("""A camp can only be removed by its owner.""")
        except OSError, e:
            if arguments.force == None:
                raise CampError("""The camp directory %s/%s does not exist.""" % (settings.CAMPS_ROOT, settings.CAMPS_BASENAME + str(camp_id)) )


        client = fc.Client(settings.FUNC_DB_HOST)
        # self._stop_camp_db(client, camp_id)
        rm_db_cmd = "/bin/rm -r %s/%s" % (settings.DB_ROOT, settings.CAMPS_BASENAME + str(camp_id))
        # ensure the db is stopped for this camp
        self._stop_db(client, camp_id)
        print "camp%s database stopped" % camp_id
        client.command.run(rm_db_cmd)
        print "camp%s database directory removed" % camp_id
        os.chdir(settings.CAMPS_ROOT)
        try:
            shutil.rmtree("%s/%s" % (settings.CAMPS_ROOT, settings.CAMPS_BASENAME + str(camp_id)) )
        except OSError, e:
            if arguments.force == None:
                raise CampError(e)
        print "camp%s directory removed" % camp_id
        self.campdb.deactivate_camp(camp_id)

    def list(self, arguments=None):
        camps = self.campdb.camp_list(arguments.all)
        for c in camps:
            if c[9]:
                print "camp%d [ owner: %s, path: %s/camp%d, %s ]" % (c[0], c[3], c[2], c[0], "ACTIVE")
            else:
                print "camp%d [ owner: %s, path: %s/camp%d, %s ]" % (c[0], c[3], c[2], c[0], "INACTIVE")

    def create(self, arguments):
        """Initializes a new camp within the current user's home directory.  The following occurs:
        
        git clone -b campX origin/master #clones master branch 
        git remote add camps/campX <path/url to central repo> #creates remote branch configuration
        git push camps/campX 
        creates new snapshot from live db
        configures new database on devdb
        creates symbolic link to static data (images)
        """

        try:
            self.camp_id = self.campdb.create_camp(arguments.desc, settings.CAMPS_ROOT, self.login, settings.DB_USER, settings.DB_PASS, settings.DB_HOST)
            self.camppath = """%s/%s""" % (settings.CAMPS_ROOT, settings.CAMPS_BASENAME + str(self.camp_id) )
            self.basecamp = """%s/%s""" % (settings.CAMPS_ROOT, settings.GIT_ROOT)
            self.campname = settings.CAMPS_BASENAME + str(self.camp_id)
            print "== Creating camp%d ==\n" % self.camp_id
            db_client = fc.Client(settings.FUNC_DB_HOST)
            self._clone_db(db_client)
            self._start_db(db_client, self.camp_id)
            self._clone_docroot()
            web_client = fc.Client(settings.FUNC_WEB_HOST)
            self._web_config()
            self._web_symlink_config(web_client)
            self._restart_web(web_client)
        except CampError, e:
                self.campdb.delete_camp(self.camp_id)
                #also possibly need to delete the camp db instance
                raise CampError(e.value)

    def test(self, arguments):
        print "Running test"
        print str(arguments)
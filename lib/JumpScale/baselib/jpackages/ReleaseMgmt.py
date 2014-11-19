import os, re, tarfile
import difflib
from JumpScale import j
from JumpScale.core.baseclasses import BaseType

##########################################
#
# Module containing classes to manage code differences between releases
#
# Author: A-server - Luk Macken
# Date: April  12, 2010
#
###########################################


def compareDependencyFiles(file1, file2):
    """
    Compare two files with lists of jpackages, to find out which ones are new, which ones have been removed, and which ones have been changed between the two.
    The files need to be compiled with releaseMgmt.createDependencyFile()

    Parameters:
    - file1, file2: string - the pathnames of the files to be compared

    Returns:
    - a list of strings, each string is a line starting with '+' if the line is added in file2, '-' if it is removed from file2, '?' for some additional explanation w.r.t. possible changes
    """
    with open(file1, 'r') as f1:
        f1stringlist = f1.readlines()
    with open(file2, 'r') as f2:
        f2stringlist = f2.readlines()
    d = difflib.Differ()
    return list(d.compare(f1stringlist, f2stringlist))


class ReleaseMgmt():
    """
    @qlocation = j.packages.releasemgmt
    """


    def generateBillOfMaterials(self, jpackagesObject, outputFile):
        """
        Create a file with all jpackages and their versions that a given jpackages depends upon ('parents')
        The file will contain the domain, the name, the version and the build nr from the parent jpackages.
        The file will be sorted.

        Parameters: 
        - jpackagesObject: Object - the jpackages object where you want to list the parents for
        - outputFile: string - the file where the parent jpackages list will be written to

        Returns: None
        """
        # sortPackage and sortLevelPackages are some auxiliary functions to sort jpackages
        def sortPackages(p1, p2):
            return sortLevelPackages(p1, p2, 0)

        def sortLevelPackages(p1, p2, level):
            p1levels = (p1.domain, p1.name, p1.version, p1.buildNr)
            p2levels = (p2.domain, p2.name, p2.version, p2.buildNr)
            if level > 3:
                return 0
            else: 
                if p1levels[level] < p2levels[level]:
                    return -1
                elif p1levels[level] > p2levels[level]:
                    return +1
                else:
                    return sortLevelPackages(p1, p2, level+1)

        # here comes the main body of the method
        with open(outputFile, 'w') as f:  
            parentpckgs = jpackagesObject.getDependencies(recursive=True)
            parentpckgs.sort(sortPackages)
            for parent in parentpckgs:
                f.write(parent.domain + "|" + parent.name + "|" + str(parent.version) + "|" + str(parent.buildNr) + os.linesep)


    def listChangedPackagesAsStrings(self, earlierFile, laterFile, comparison='+'):
        """
        Given two files with a list of packages, this method will give back the packages that have been added or removed between the two.

        Parameters:
        - earlierFile: string - file containing the packages for an earlier release
        - laterFile: string - file containing the packages for a later release. Added packages will be given back by this method if comparison = '+'
        - comparison: char - '+' if you want the added packages back. '-' if you want the removed packages back.

        Returns:
        list of strings - each string is the name of a package
        """
        if comparison not in ('+', '-'):
            raise Exception('comparison must be \'+\' (default) or \'-\', no other values are accepted')
        complist = compareDependencyFiles(earlierFile, laterFile)
        addedstringlist = []
        for str in complist:
            if str.startswith(comparison):
                addedstringlist.append(re.sub('^[+-]', '', str).strip()) # remove the leading + or - from the string
        return addedstringlist


    def _listChangedPackagesAsObjects(self, earlierFile, laterFile, comparison='+'):
        """
        Given two files with a list of packages, this method will give back the packages that have been added or removed between the two.

        Parameters:
        - earlierFile: string - file containing the packages for an earlier release
        - laterFile: string - file containing the packages for a later release. Added packages will be given back by this method if comparison = '+'
        - comparison: char - '+' if you want the added packages back. '-' if you want the removed packages back.

        Returns:
        list of package objects
        """
        strlist = self.listChangedPackagesAsStrings(earlierFile, laterFile, comparison)
        addedpackagelist = []
        for str in strlist:
            pckfound = False
            pckattributes = str.split('|')
            pckfoundlist = j.packages.find(name=pckattributes[1],domain=pckattributes[0], version=pckattributes[2])
            for pck in pckfoundlist:
                if repr(pck.buildNr) == pckattributes[3]:
                    addedpackagelist.append(pck)
                    pckfound = True
            if not pckfound:
                raise RuntimeError('No package could be found in domain %s with name %s, version nr %s and buildnr %s' % (pckattributes[0], pckattributes[1], pckattributes[2], pckattributes[3]))
        return addedpackagelist


    def createTgzForChangedPackages(self, earlierFile, laterFile, tempDir = '/opt/qbase3/var/tmp/changedpackages', tarName = 'changedPack.tgz'):
        """
        Given two files with a list of packages, this method will download to a temporary folder the packages that have been added to laterFile.
        Each package will be downloaded in a subdirectory corresponding to its domain.
        Packages will be downloaded for all platforms.
        Next to the packages, the metadata will be copied as well to the temporary folder.
        Finally the folders and files will be compressed in a tgz file
        Note that the packages and metadata are downloaded from the location specified in bundledownload in /opt/qbase3/cfg/jpackages/sources.cfg
        If there are no changes between the two package files, an empty tgz file will be created.

        Parameters:
        - earlierFile: string - file containing the packages for an earlier release
        - laterFile: string - file containing the packages for a later release. Added packages will be given back by this method if comparison = '+'
        - tempDir: string - temporary directory where files will be downloaded. This directory will be cleaned up at the beginning of the method and must be located in an existing directory!
        - tarName: string - name of the tgz file to be created

        Returns:
        None
        """
        failed = False
        # First check if earlierFile or laterFile are located within the directory that will be removed. 
        absTempDir = os.path.abspath(tempDir)
        if ((os.path.dirname(os.path.abspath(earlierFile)) == absTempDir) or (os.path.dirname(os.path.abspath(laterFile)) == absTempDir)):
            raise RuntimeError ('the given files are located within the temporary directory that will be cleaned up. \
                                             Please move the files to another location or choose another temporary directory')
        
        # Check if temp dir is not a couple of levels deep. This gives troubles when cleaning up
        if not j.system.fs.exists(j.system.fs.getParent(absTempDir)):
            raise RuntimeError ('the temporary directory must be located in an existing directory')
        j.system.fs.removeDirTree(tempDir, onlyLogWarningOnRemoveError=True)
        j.system.fs.createDir(tempDir)
        pcklist = self._listChangedPackagesAsObjects(earlierFile, laterFile, '+')
        # get all jpackages from the location specified in bundledownload in /opt/qbase6/cfg/jpackages/sources.cfg
        for pck in pcklist:
            pck.download(dependencies=False, destinationDirectory=tempDir, allplatforms=True)
        # We now need the domains that contain downloaded packages. These correspond to the directories created in the temporary directory
        domainlist = j.system.fs.listDirsInDir(tempDir, recursive=False, dirNameOnly=True)         
        tarpath = j.system.fs.joinPaths(tempDir, tarName) 
        # Create the tgz file and add the domain directories to it, as well as the metadata files
        tar = tarfile.open(name=tarpath, mode='w:gz')
        try:   
            for domain in domainlist:
                domainobject = j.packages.getDomainObject(domain)
                metadatabranchfile = domainobject.metadataBranch + '.branch.tgz'
                metadatatarfile = j.system.fs.joinPaths(j.packages.getMetaTarPath(domain), metadatabranchfile)
                domaindir = j.system.fs.joinPaths(tempDir, domain)
                if j.system.fs.exists(metadatatarfile):
                    j.system.fs.copyFile(metadatatarfile, domaindir)
                else:
                    failed = True
                    raise RuntimeError('Metadata tarfile %s does not exist for domain %s. Run i.jp.updateMetaDataAll() first' % (metadatatarfile, domain))
                tar.add(name=domaindir, arcname=domain, recursive=True)
                j.system.fs.removeDirTree(domaindir, onlyLogWarningOnRemoveError=True)
        finally:
            tar.close()
            if failed:
                j.system.fs.removeDirTree(tempDir, onlyLogWarningOnRemoveError=True)  # clean up everything
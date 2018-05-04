# -*- coding: utf-8 -*-

import sys, premiumizeme

# create PremiumizeMeButler object
pmb = premiumizeme.pmb("ENTER-YOUR-CUSTOMER-ID-HERE", "ENTER-YOUR-PIN-HERE")

# download a folder completely
outputFolder = "/path/to/download/to"
downloadFolder = "folderinmycloud"
pmb.fetchFolder(outputFolder, downloadFolder)

# download a folder completely (and skip some file types by extension)
outputFolder = "/path/to/download/to"
downloadFolder = "folderinmycloud"
skipFileTypes = {".sfv", ".txt", ".jpg"}
pmb.fetchFolder(outputFolder, downloadFolder, skipFileTypes)

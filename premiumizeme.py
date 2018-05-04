# -*- coding: utf-8 -*-

import urllib, urllib2, json, os

class pmb:

	# ==========================================================================================================
	#  CONSTANTS
	# ==========================================================================================================



	# ==========================================================================================================
	#  URIs for different API requests
	# ==========================================================================================================
	uriFolders = "https://www.premiumize.me/api/folder/list"
	uriDeleteItem = "https://www.premiumize.me/api/item/delete"
	uriDeleteFolder = "https://www.premiumize.me/api/folder/delete"
	uriCreateFolder = "https://www.premiumize.me/api/folder/create"


	# ==========================================================================================================
	#  CONSTRUCTOR
	# ==========================================================================================================
	def __init__(self, auth_customer_id, auth_pin):
		self.auth_customer_id = auth_customer_id
		self.auth_pin = auth_pin


	def _makeApiRequest(self, apiUri, queryParams = None):
		uri = apiUri + "?customer_id=" + self.auth_customer_id + "&pin=" + self.auth_pin

		# build request if queryParams are present
		if queryParams:
			uri = uri + "&" + urllib.urlencode(queryParams)

		# fetch response
		request = urllib2.Request(uri)
		response = urllib2.urlopen(request).read()

		# return json data
		return json.loads(response.decode("utf-8"))


	def _createFolderLocally(self, path):
		if not os.path.exists(path):
			os.makedirs(path)


	def _createFolder(self, folderName, parentId = None):
		if parentId:
			response = self._makeApiRequest(pmb.uriCreateFolder, {"name": folderName, "parent_id": parentId})
		else:
			response = self._makeApiRequest(pmb.uriCreateFolder, {"name": folderName})

		if response["status"] != "success":
			print "   -> ERROR creating folder: " + folderName
			print "      -> Message: " + response["message"]
		else:
			print "   -> created folder " + folderName


	def _deleteFolder(self, folderId):
		response = self._makeApiRequest(pmb.uriDeleteFolder, {"id": folderId})

		if response["status"] != "success":
			print "   -> ERROR deleting folder"
			print "      -> Message: " + response["message"]
		else:
			print "   -> deleted from Premiumize.me"


	def _deleteItem(self, item):
		response = self._makeApiRequest(pmb.uriDeleteItem, {"id": item["id"]})

		if response["status"] != "success":
			print "   -> ERROR deleting:" + item["name"]
			print "      -> Message: " + response["message"]
		else:
			print "   -> deleted from Premiumize.me"


	def _downloadFile(self, url, outputFolder):
		try:
			filename = os.path.basename(url)
			print " - Downloading: " + filename
			req = urllib2.urlopen(url)
			with open(outputFolder + "/" + filename, "wb") as f:
				while True:
					chunk = req.read(16384)
					if not chunk: break
					f.write(chunk)
			print "   -> SUCCESS"
			return True

		except urllib2.HTTPError, e:
			print "   -> ERROR: ", e.code, url
			return False

		except urllib2.URLError, e:
			print "   -> ERROR: ", e.reason, url
			return False


	def _downloadFolder(self, response, outputFolder, skipFileTypes):
		# iterate over all items in current folder
		for item in response["content"]:

			# file => download and delete
			if item["type"] == "file":
				skipped = False

				# check for skipFileTypes
				if skipFileTypes:
					for skipFileType in skipFileTypes:
						# extract extension from download URL
						filename, extension = os.path.splitext(item["name"])

						# if extension matches skipFileTypes => skip and delete it
						if extension == "." + skipFileType:
							print " - SKIPPING: " + item["name"]
							self._deleteItem(item)
							skipped = True
							break

				# not skipped => download it and if successful delete it
				if not skipped:
					if self._downloadFile(item["link"], outputFolder):
						self._deleteItem(item)

			# folder => create folder locally and go deeper
			if item["type"] == "folder":
				print " - SUBFOLDER: " + item["name"]
				print "************************"

				# fetch folder listing
				response2 = self._makeApiRequest(pmb.uriFolders, {"id" : item["id"]})

				if response2["status"] != "success":
					print " - Error fetching folder listing"
					print "   -> Message: " + response2["message"]
				else:
					newOutputFolder = outputFolder + "/" + item["name"]

					# create folder
					self._createFolderLocally(newOutputFolder)

					# recurse over subfolder
					self._downloadFolder(response2, newOutputFolder, skipFileTypes)


	def _countFolder(self, response, count = 0):
		# iterate over all items in current folder
		for item in response["content"]:

			# folder => go deeper
			if item["type"] == "folder":
				# fetch folder listing
				response2 = self._makeApiRequest(pmb.uriFolders, {"id" : item["id"]})
				count = count + self._countFolder(response2, count)

			# file => count it
			if item["type"] == "file":
				count = count + 1

		return count


	def getFolderId(self, folderName = "root", folderId = None):
		if folderId:
			response = self._makeApiRequest(pmb.uriFolders, {"id" : folderId})
		else:
			response = self._makeApiRequest(pmb.uriFolders)

		if response["status"] == "success":
			if response["name"] == folderName:
				return folderId

			else:
				# correct folder not yet found. iterate over subfolders
				for item in response["content"]:
					if item["type"] == "folder":
						id = self.getFolderId(folderName, item["id"])
						if id:
							return id


	def fetchFolder(self, outputFolder, folderName = "root", recreateFolder = False, skipFileTypes = None, path = "", folderId = None, recursion = False):

		if not recursion:
			print "--------------------------------------------------"
			print " [PremiumizeMeButler] fetchFolder"
			print "--------------------------------------------------"
			print " * outputFolder:  " + outputFolder
			print " * folderName:    " + folderName
			if skipFileTypes:
				for skipFileType in skipFileTypes:
					print " * skipFileType:  " + skipFileType
			self._createFolderLocally(outputFolder)

		if folderId:
			response = self._makeApiRequest(pmb.uriFolders, {"id" : folderId})
		else:
			response = self._makeApiRequest(pmb.uriFolders)

		if response["status"] != "success":
			print " - Error fetching folder listing for: " + folderName
			print "   -> Message: " + response["message"]
		else:

			if response["name"] == folderName:
				print ""
				print " --> Found correct folder: " + path
				self._downloadFolder(response, outputFolder, skipFileTypes)

				if folderId:
					print ""
					print " --> Checking if folder is empty now..."

					# re-fetch response for this folder
					response = self._makeApiRequest(pmb.uriFolders, {"id" : folderId})

					if self._countFolder(response) == 0:
						print " - Folder is empty: deleting it"
						self._deleteFolder(folderId)
						
						if recreateFolder:
							print " - Re-creating folder"
							self._createFolder(folderName, response["parent_id"])
					else:
						print " - Folder not yet empty! Leaving it as is."

			else:
				# correct folder not yet found. iterate over subfolders
				for item in response["content"]:
					if item["type"] == "folder":
						newPath = path + "/" + item["name"]
						self.fetchFolder(outputFolder, folderName, recreateFolder, skipFileTypes, newPath, item["id"], True)

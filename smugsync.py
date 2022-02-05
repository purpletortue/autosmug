#!/usr/bin/env python3
# smugsync v2.3

# to keep my sanity since local directories can be both folders and galleries in SmugMug
# I use the following terminology in the code:

# local filesystem directory intended to be a 'Folder' in SmugMug is called a directory
# local filesystem directory intended to be a 'Gallery' in SmugMug is called an album
# The code determines the directory 'type' by the presence of a file called .smgallery or .smfolder

# Remote SmugMug Folder is called a folder
# Remote SmugMug Gallery is caled a gallery

from smugmug import SmugMug
from pathlib import Path
import argparse, sys, os, hashlib, json, time, mimetypes, fnmatch

#
# SmugMug modules
#

def list_albums(verbose):
    """
    Download all albums in an account
    """
    smugmug = SmugMug(verbose)

    album_names = []

    albums = smugmug.get_album_names()
    for album_name in albums:
        print(album_name)

def get_template_id(template_name):
    template_id = None
    template_id = smugmug.get_template_id(template_name)
    if template_id == None:
        print('Error: Could not find album template named \'' + template_name + '\'')
        sys.exit(1)

def get_root_node_id(self):
    """
    Get the root node ID of the account.
    Returns node id string
    """
    #smugmug = SmugMug() TODO: Add error handling
    response = self.request('GET', self.smugmug_api_base_url + "/user/"+self.username, headers={'Accept': 'application/json'})
    node = response['Response']['User']['Uris']['Node']
    node_id = node['Uri'].rsplit('/',1)[1]
    #print(node_id)
    return node_id

def get_child_nodes(self, parent_node_id):
    """
    Get a list of child nodes given the parents node_id
    """
    start = 1
    stepsize = 100
    nodes = []
    while(True):
        params = {'start': start, 'count': stepsize}
        response = self.request('GET', self.smugmug_api_base_url + "/node/" + parent_node_id + "!children", params=params, headers={'Accept': 'application/json'})
        for node in (response['Response']['Node'] if 'Node' in response['Response'] else []):
            #print(node)
            nodes.append({"Name": node["Name"], "NodeID": node["NodeID"], "HasChildren": node["HasChildren"], "Type": node["Type"]})
            #print(nodes)
        if 'NextPage' in response['Response']['Pages']:
            start += stepsize
        else:
            break
    return nodes

def get_node_id(self, parent_node_id, node_name):
    """
    Get/Return the node_id of a given node name directly under the given parent node id
    """
    child_nodes = []
    child_nodes = get_child_nodes(self, parent_node_id)
    for child in child_nodes:
        if node_name == child["Name"]:
            return child["NodeID"]
    if args.verbose:
        print('Could not find node ' + node_name + ', under parent NodeID ' + parent_node_id)
    return False

def get_starting_node_id(self, path):
    parent_node_id = get_root_node_id(smugmug)
    node_path = []
    node_path = path('/')
    for node_name in node_path:
        node_id = get_node_id(smugmug, parent_node_id, node_name)
        parent_node_id = node_id

def find_node(parent_node_id, node_name):
    """
    Find the node_id given a node name starting from a parent node id
    Returns array with NodeID and Name
    """
    smugmug = SmugMug()
    #root_node_id = get_root_node_id(smugmug)
    nodes = get_child_nodes(smugmug, parent_node_id)
    # Match against folder type nodes
    #print(nodes)
    for node in nodes[:]:
        #print(node)
        if node["Type"] == 'Folder':
            if node["Name"] == node_name:
                #print('Found matching folder node')
                return node
                break
            if node["HasChildren"] == 'False':
                nodes.remove(node)
        else:
            nodes.remove(node)
    #If nothing found in starting folder, check sub-folders
    else:
        try:
            if nodes:
                #print("Did not find checking sub folders")
                for node in nodes:
                    #print(node)
                    found = find_node(node["NodeID"], node_name)
                    if found:
                        return found
        except:
            print('Could not find folder ' + node_name)

def create_node(self, parent_node_id, node_name, node_type ):
    #Creates a node and returns the nodeid
    #TODO still need to add error checking
    if node_type == 'Folder':
        data = {"Type": node_type, "Name": node_name, "UrlName": smugmug.create_nice_name(node_name)}
        response = self.request('POST', self.smugmug_api_base_url + "/node/"+parent_node_id + "!children", data=json.dumps(data), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})

        return response['Response']['Node']['NodeID']
        #TODO add response error checking
    if node_type == 'Album':
        data = {"Type": node_type, "Name": node_name, "UrlName": smugmug.create_nice_name(node_name), "Privacy": 'Unlisted'}
        response = self.request('POST', self.smugmug_api_base_url + "/node/"+parent_node_id + "!children", data=json.dumps(data), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        return response['Response']['Node']['NodeID']

def get_album_key(self, node_id):
    response = smugmug.request('GET', smugmug.smugmug_api_base_url + "/node/"+node_id, headers={'Accept': 'application/json'})
    albumkey = response['Response']['Node']['Uris']['Album']['Uri'].rsplit('/',1)[1]
    #print(albumkey)
    return albumkey

def create_tree(self, source, dest):
    """
    Create tree structure given localsource directory
    and smugmug destination node name & ID
    """
    parent_node = dest
    #handle initial root folder case
    #if dest["Name"] == basenode["Name"]:
        #parent_node = basenode
    #else:
    #    parent_node = find_node()
    #if entry == args.source:

    subdirs = []
    subdirs = has_dirs(source)

    # for each subfolder
    for subdir in subdirs:
        #determine if gallery or folder
        if has_files(subdir):
            album_name = subdir.rsplit('/', 1)[1]
            if not find_node(parent_node["NodeID"], album_name):
                print(album_name + ' album does not exist, creating')
                create_node(smugmug, parent_node["NodeID"], album_name, 'Album' )
            else:
                print(album_name + ' album exists')
        elif has_dirs(subdir):
            folder_name = subdir.rsplit('/', 1)[1]
            subdir_node = find_node(parent_node["NodeID"], folder_name)
            if not subdir_node:
                print(folder_name + ' folder does not exist, creating')
                create_node(smugmug, parent_node["NodeID"], folder_name, 'Folder' )
                time.sleep(30)
            else:
                print(folder_name + ' folder exists')
            create_tree(self, subdir, subdir_node)

def upload_image(self, image_data, image_name, image_type, album_id):
    """Upload an image"""
    response = self.request('POST', self.smugmug_upload_uri,
        data=image_data,
        header_auth = True,
        headers={'X-Smug-AlbumUri': "/api/v2/album/"+album_id,
            'X-Smug-Version':self.smugmug_api_version,
            'X-Smug-ResponseType':'JSON',
            'Content-MD5': hashlib.md5(image_data).hexdigest(),
            'X-Smug-FileName':image_name,
            'Content-Length' : str(len(image_data)),
            'Content-Type': image_type})
    return response

def remove_image(self, image_uri):
    """Remove an image"""
    #print(image_uri)
    response = self.request('DELETE', 'https://api.smugmug.com'+image_uri,
        header_auth = True,
        headers={'Accept': 'application/json',
            'X-Smug-Version':self.smugmug_api_version,
            'X-Smug-ResponseType':'JSON'})
    #print(response)
    return response

def upload_overwrite_image(self, image_data, image_name, image_type, album_id, image_uri):
    """Upload and overwrite an existing image"""
    response = self.request('POST', self.smugmug_upload_uri,
        data=image_data,
        header_auth = True,
        headers={'X-Smug-AlbumUri': "/api/v2/album/"+album_id,
            'X-Smug-Version':self.smugmug_api_version,
            'X-Smug-ResponseType':'JSON',
            'Content-MD5': hashlib.md5(image_data).hexdigest(),
            'X-Smug-FileName':image_name,
            'Content-Length' : str(len(image_data)),
            'Content-Type': image_type,
            'X-Smug-ImageUri': image_uri})
    return response

def upload_files(self, album_id, image_paths):
    # Uploading the images
    total = len(image_paths)
    count = 0

    #album_image_names = smugmug.get_album_image_names(album_id)
    album_images = smugmug.get_album_images(album_id)
    for image_path in image_paths:
        if args.verbose == True:
            print('----------------------------------------------------')
        count += 1
        image_name = os.path.basename(image_path)
        sys.stdout.write('Checking ' + image_name + ' [' + str(count) + '/' + str(total) + ']... ')
        sys.stdout.flush()
        if args.verbose == True:
            print('')
        #print(album_images['FileName'])
        for image in album_images:
            if image_name == image['FileName']:
                try:
                    image_data = open(image_path, 'rb').read()
                    filehash = hashlib.md5(image_data).hexdigest()
                    if filehash == image['ArchivedMD5']:
                        print('File is the same, skipping.')
                        sys.stdout.flush()
                    else:
                        sys.stdout.write('File has changed, updating... ')
                        sys.stdout.flush()
                        # Finding the mime type
                        image_type = mimetypes.guess_type(image_path)[0]

                        # Uploading image
                        #print(image['Uris']['Image']['Uri'])
                        #sys.exit(1)
                        result = upload_overwrite_image(self, image_data=image_data, image_name=image_name, image_type=image_type, album_id=album_id, image_uri=image['Uris']['Image']['Uri'])
                        #print(result)
                        if result['stat'] != 'ok':
                            print('Error: Upload failed for file \'' + image + '\'')
                            print('Printing server response:')
                            print(result)
                            sys.exit(1)
                        print('Done')
                except IOError as e:
                    print("I/O error({0}): {1}".format(e.errno, e.strerror))
                    raise
                #print('File already exists, skipping.')
                sys.stdout.flush()
                break
        #if image_name in album_images['FileName']:
        #    print('File already exists, skipping.')
        #    sys.stdout.flush()
        else:
            # Loading the image data
            try:
                image_data = open(image_path, 'rb').read()
            except IOError as e:
                print("I/O error({0}): {1}".format(e.errno, e.strerror))
                raise

            sys.stdout.write('File is new, uploading...')
            # Finding the mime type
            image_type = mimetypes.guess_type(image_path)[0]

            # Uploading image
            result = upload_image(self, image_data=image_data, image_name=image_name, image_type=image_type, album_id=album_id)

            if result['stat'] != 'ok':
                print('Error: Upload failed for file \'' + image + '\'')
                print('Printing server response:')
                print(result)
                sys.exit(1)
            print('Done')

    # Small additional check if the number of images matches
    album_images = smugmug.get_album_images(album_id)
    if len(image_paths) != len(image_paths):
        print('Warning: You selected ' + str(len(args.images)) + ' images, but there are ' + str(len(existing_images)) + ' in the online album.')

    #print('Album done')

def remove_images(self, album_id, local_path):
    # Remove files from gallery that do not exist locally

    #album_image_names = smugmug.get_album_image_names(album_id)
    album_images = smugmug.get_album_images(album_id)
    resolved_path = Path(local_path).resolve()
    str_path = str(resolved_path)
    image_uris = []
    for image in album_images:
        #print(image)
        filename = image['FileName']
        #print(local_path)
        local_file = str_path + '/' + filename
        if not Path(local_file).is_file():
            image_uris.append(image['Uri'])

    if len(image_uris) == 0:
        print("Album done")
    elif 0 < len(image_uris) < (len(album_images) * .15) :
        print("Removing",len(image_uris),"images from album")
        for image_uri in image_uris:
            result = remove_image(smugmug, image_uri)
        print("Album done")
    elif len(image_uris) >= (len(album_images) * .15):
        print("More images to remove than reasonably expected, skipping removal.")
        print("Album not done")

#
# Local filesystem modules
#

def is_album(dir_path):
    """Determines if a given local directory should map to a SmugMug Folder or
        Gallery by presence of a .smgallery file"""
    if os.path.isfile(dir_path + "/.smgallery"):
        return True
    else:
        return False

def is_folder(dir_path):
    """Determines if a given local directory should map to a SmugMug Folder or
        Gallery by presence of a .smfolder file"""
    if os.path.isfile(dir_path + "/.smfolder"):
        return True
    else:
        return False

def process_dir_as_gallery(directory, parent_node_id):
    # Process local-directory as a gallery inside SmugMug Parent NodeID
    dir_path = str(Path(directory).resolve())
    dirname = dir_path.rsplit('/',1)[-1]
    print('Processing album ' + dirname)
    album_name = dirname
    node_id = get_node_id(smugmug, parent_node_id, album_name)
    if not node_id:
        response = create_node(smugmug, parent_node_id, album_name, 'Album')
        node_id = response

    files = has_images(dir_path)
    if files:
        albumkey = get_album_key(smugmug, node_id)
        upload_files(smugmug, albumkey, files)
        remove_images(smugmug, albumkey, dir_path)

def process_dir_as_folder(directory, parent_node_id):
    # Process local-directory as a folder inside SmugMug Parent NodeID
    dir_path = str(Path(directory).resolve())
    dirname = dir_path.rsplit('/',1)[-1]
#    smugmug=SmugMug(args.verbose)
    if args.verbose: print('Working on ' + dirname)

    node_id = get_node_id(smugmug, parent_node_id, dirname)
    if not node_id:
        print('creating node ' + dirname)
        response = create_node(smugmug, parent_node_id, dirname, 'Folder')
        node_id = response

    #Check subdirectories for processing
    subdirs = []
    subdirs = has_dirs(dir_path)
    if subdirs:
        for subdir in subdirs:
                if is_folder(subdir):
                    print('Processing subdir as folder: ' + subdir)
                    parent_node_id = node_id
                    process_dir_as_folder(subdir, parent_node_id)
                elif is_album(subdir):
                    print('Processing subdir as gallery: ' + subdir)
                    parent_node_id = node_id
                    process_dir_as_gallery(subdir, parent_node_id)
                else:
                    skipped.append(subdir)

def has_images(dir_path):
    dir_contents = get_contents(dir_path)
    """Get paths for all files in a directory, only 1 level deep"""
    files = []
    for entry in dir_contents:
        if os.path.isfile(entry) and fnmatch.fnmatch(entry, '*.jpg'):
            files.append(entry)
    files.sort()
    return files

def get_contents(dir_path):
    """Get paths for all contents in a directory, only 1 level deep"""
    dir_contents = []
    for entry in os.listdir(dir_path):
        dir_contents.append(os.path.join(dir_path, entry))
    dir_contents.sort()
    return dir_contents

def has_files(dir_path):
    dir_contents = get_contents(dir_path)
    """Get paths for all files in a directory, only 1 level deep"""
    files = []
    for entry in dir_contents:
        if os.path.isfile(entry) and fnmatch.fnmatch(entry, '*.jpg'):
            files.append(entry)
    files.sort()
    return files

def has_dirs(dir_path):
    dir_contents = get_contents(dir_path)
    """Get paths for all directories in a directory, only 1 level deep"""
    dirs = []
    for entry in dir_contents:
        if os.path.isdir(entry):
            dirs.append(entry)
    dirs.sort()
    return dirs

def process_directory(directory, parent_node_id):
    # Process local-directory with corresponding SmugMug Parent NodeID
    dirname = directory.rsplit('/',1)[-1]
    smugmug=SmugMug(args.verbose)
    if args.verbose: print('Working on ' + directory)
    files = []
    files = has_files(directory)
    subdirs = []
    subdirs = has_dirs(directory)

    #process as a folder on smugmug
    if subdirs:
        node_id = get_node_id(smugmug, parent_node_id, dirname)
        if not node_id:
            print('creating node ' + dirname)
            response = create_node(smugmug, parent_node_id, dirname, 'Folder')
            node_id = response
        for subdir in subdirs:
        #    print('Processing subdir ' + subdir)
        #    parent_node_id = node_id
        #    subdir_name = subdir.rsplit('/',1)[-1]
        #    subnode_id = get_node_id(smugmug, parent_node_id, subdir_name)
        #    if not subnode_id:
        #        print('creating node ' + subdir_name)
        #        response = create_node(smugmug, parent_node_id, subdir_name, 'Folder')
        #        subnode_id = response
            process_directory(subdir, node_id)

    #process as a gallery on smugmug
    elif files:
        print('Processing album ' + dirname)
        if subdirs: print(subdirs)
        album_name = dirname
        node_id = get_node_id(smugmug, parent_node_id, album_name)
        if not node_id:
            response = create_node(smugmug, parent_node_id, album_name, 'Album')
            node_id = response
        albumkey = get_album_key(smugmug, node_id)
        upload_files(smugmug, albumkey, files)



def validate_args(args):
    global root_node_id
    global starting_node_id
    global parent_node_id
    #confirm starting local directory exists
    if not os.path.isdir(args.source):
        print("SOURCE directory ("+ args.source + ") does not exist")
        sys.exit(1)
    #confirm starting local directory is a folder or gallery
    target = ''
    if is_album(args.source): target = 'Album'
    if is_folder(args.source): target = 'Folder'
    if not target:
        print("SOURCE directory ("+ args.source + ") can not be identified as a gallery or folder")
        print("The directory must contain either a .smfolder or .smgallery file in order to sync with SmugMug")
        sys.exit(1)

    smugmug = SmugMug(args.verbose)
    #confirm starting node pre-exists in SmugMug
    parent_node_id = root_node_id
    node_path = []
    node_path = args.dest.split('/')
    #TODO: Should change to allow for node's with the same name at the same level
    #TODO: Code also assumes Galleries are only at the end of the 'tree'
    cur_node_id = root_node_id
    for node_name in node_path:
        parent_node_id = cur_node_id
        cur_node_id = get_node_id(smugmug, parent_node_id, node_name)

    if not cur_node_id:
        print("Destination node ("+ args.dest +") not found on SmugMug.")
        print("Starting node must pre-exist, subfolders/galleries will be created if needed")
        sys.exit(1)
    else:
        starting_node_id = cur_node_id

    #confirm starting node matches local expectation
    response = smugmug.request('GET', smugmug.smugmug_api_base_url + "/node/"+cur_node_id, headers={'Accept': 'application/json'})
    if not response['Response']['Node']['Type'] == target:
        print("DEST must match the expected node type of the SOURCE")
        print("Expected " + target)
        sys.exit(1)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Sync (currently upload-only) local folder to SmugMug.')
    parser.add_argument('source', metavar='SOURCE', type=str, help='Local directory (tree) to upload')
    parser.add_argument('dest', metavar='DEST', type=str, help='Full path to SmugMug destination node')
    #parser.add_argument('-a', '--album', dest='album', metavar='ALBUM_NAME', type=str, help='set album name')
    parser.add_argument('-t', '--template', dest='template', metavar='TEMPLATE_NAME', type=str, default='ArchiveGallery', help='set album template name')
    parser.add_argument('-r', '--resume', dest='resume', action='store_true', default=False, help='if album already exists, add photos in there. default: false')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='verbose output')
    args = parser.parse_args()

    smugmug = SmugMug(args.verbose)

    #Smugmug basenode to sync with
    root_node_id = get_root_node_id(smugmug)
    starting_node_id = None
    parent_node_id = None

    #validate cli arguments and sets starting_node_id as the given starting point
    validate_args(args)
    #print(starting_node_id)
    #print(parent_node_id)
    skipped = []
    if is_album(args.source):
        process_dir_as_gallery(args.source, parent_node_id)

    if is_folder(args.source):
        process_dir_as_folder(args.source, parent_node_id)

    #TODO: Pretty the skipped output
    if skipped:
        print("The following directories were skipped due to no .smgallery/.smfolder file")
        print(skipped)

"""
    dirs = []
    print(args.source)
    dirs = has_dirs(args.source)
    for directory in dirs:
        process_directory(directory, starting_node_id)
"""

"""
for each directory
    determine if dir is album or folder
    if album, create if not exists
        process each file under albums
    if folder, create if not exists
        Loop again

"""
    #create_tree(smugmug, args.source, basenode)

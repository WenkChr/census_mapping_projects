import zipfile
import os
import sys

def zipallinfolder(infolder, outfolder):


    def list_directory_files(directory_path, file_extension):
        # returns a list of all file paths with a specific extension from the given directory
        return_list = []

        # check to ensure directory exists
        if not os.path.exists(directory_path):
            print 'Given directory does not exist check inputs'
            sys.exit()

        # If the path exists then iterate over the directory and get all files with the specific file extension we want
        for o_file in os.listdir(directory_path):
            if o_file.endswith(file_extension):
                return_list.append(os.path.join(directory_path, o_file))

        return return_list

    working_dir = infolder
    out_folder = outfolder

    files = list_directory_files(working_dir, '.mxd')
    print 'Zipping {} mxd files and associated data'.format(len(files))
    for f in files:
        path_parts = os.path.split(f)
        file_name = path_parts[1]
        # if file_name[3:10] != '52-6130':
        #     continue
        print 'Zipping map ' + file_name
        mdb_path = os.path.join(path_parts[0], path_parts[1].split('.')[0] + '.mdb')
        zipName = os.path.join(out_folder, path_parts[1].split('.')[0] + '.zip')
        if os.path.exists(zipName):  # If zipFile already exists delete it be fore replacing
            os.remove(zipName)
        with zipfile.ZipFile(zipName, 'w') as z_file:
            z_file.write(f, path_parts[1])
            z_file.write(mdb_path, os.path.split(mdb_path)[1])


working_dir = 'INPUT PATH TO AUGMENTED FILES'
out_folder = 'INPUT PATH TO AN OUTPUT FOLDER'

zipallinfolder(working_dir, out_folder)

print 'DONE!'

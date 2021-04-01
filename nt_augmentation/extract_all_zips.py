import os
import zipfile

# -----------------------------------------------------------------------------
# Functions

# -----------------------------------------------------------------------------
# Inputs
in_path = 'INPUT PATH TO FOLDER CONTAINING GMS ZIP FILES HERE'
out_path = 'INPUT PATH TO EMPTY OUTPUT DIRECTORY HERE'
# -----------------------------------------------------------------------------
# Logic
zip_count = 0
for root, dirs, files in os.walk(in_path):
    for name in files:
        print 'Looking at file {} of {}'.format(files.index(name) + 1, len(files))
        if name.endswith('.zip'):
            print 'Extracting all files from ' + name
            zip_path = os.path.join(root, name) # Get full path to zipfile
            zip_ref = zipfile.ZipFile(zip_path)  # create zipfile object
            zip_ref.extractall(out_path)  # Extract all contents to extract path
            zip_ref.close()  # Close file to prevent locking issues
            zip_count += 1

print '{} zips extracted'.format(zip_count)
print 'DONE!'

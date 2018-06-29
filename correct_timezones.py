import os
import sys
import datetime

WINDOWS_ENCODING = '\\'
UNIX_ENCODING = '/'

SYSTEM_TYPE = 'windows'

def correct_time(s):
    f = '%Y-%m-%d %H:%M:%S' # format of s
    TIME_CORRECTION = 7     # UTC => PST
    date = datetime.datetime.strptime(s, f)
    date = date - datetime.timedelta(hours=TIME_CORRECTION)
    return date.isoformat(' ')


def correct(d, s):
    # given a directory and a filename, corrects for timezone
    file = open(os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + d + separator() + s)
    contents = file.read().splitlines()

    header = contents[0]

    corrected_contents = []

    corrected_contents.append(header + '\n')

    for line in contents[1:]:
        values = line.split(',')

        sample_date = correct_time(values[1])
        system_date = correct_time(values[-1])

        values[1] = sample_date
        values[-1] = system_date

        corrected_line = ','.join(map(str, values)) + '\n'
        corrected_contents.append(corrected_line)

    corrected_file = os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + d + separator() + "corrected_" + s
    with open (corrected_file, 'w') as text_file:
        text_file.write(''.join(corrected_contents))
    return corrected_file

def get_files(path, absolute=False, system_type=SYSTEM_TYPE):
    # Returns a list of paths to uncorrected files in a directory.
    # path: the path to the directory
    # absolute: whether or not the filePath should be relative, i.e. ~/myFile.file vs. ~/.../myFile.file
    # system_type: 'windows' or 'unix'
    def get_script_path(p):
        return os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + p

    files = [file for file in os.listdir(get_script_path(path)) if 'corrected_' not in file]
    print(files)
    return [get_script_path(path) + separator() + file for file in files] if absolute else files


def separator():
    return WINDOWS_ENCODING if SYSTEM_TYPE == 'windows' else UNIX_ENCODING

def correct_all(subdirectory):
    print('Correcting all uncorrected datasets in ' + subdirectory)
    for file in get_files(subdirectory):
        print('\tCorrecting ' + file)
        corrected_file = correct(subdirectory, file)
        print('\tWrote corrected dataset to ' + corrected_file)
    print('Finished')


correct_all('data')
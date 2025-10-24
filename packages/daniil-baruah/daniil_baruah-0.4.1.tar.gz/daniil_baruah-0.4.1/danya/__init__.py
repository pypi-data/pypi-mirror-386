from pathlib import Path
from random import randint
import subprocess
import time
import platform
from zipfile import ZipFile
import csv
# Errors

class NotFile(Exception):
    '''
    Error if this object is not file.
    '''
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return f"This is not file: {self.filename}"
    

class NoFile(Exception):
    """
    Error if there is no file.
    """
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return f"There is no {self.filename}"


class NoCodePath(Exception):
    """
    Error if there is no 'code' in PATH.
    """
    def __init__(self):
        self.sentence = "There is no 'code' in PATH. Before downloading the VS code please mark 'ADD TO PATH' "

    def __str__(self):
        return self.sentence

# Communicating with files
non_creating_files = [
    # Базы данных
    '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',

    # Исполняемые / бинарные
    '.exe', '.dll', '.bin', '.msi', '.sys', '.bat', '.cmd',

    # Компиляция и байткод
    '.pyc', '.pyo', '.class', '.o', '.so', '.a', '.lib',

    # Архивы
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',

    # Образы дисков
    '.iso', '.dmg', '.img',

    # Конфигурационные или системные
    '.ini', '.cfg', '.conf', '.reg', '.log',

    # Машинное обучение / базы
    '.h5', '.hdf5', '.pkl', '.npy', '.npz',

    # Прочие "не текстовые"
    '.tmp', '.swp', '.bak', '.lock'
]

safe_extensions = [
    # Скрипты и программные файлы
    '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.rb', '.go', '.php', '.sh', '.bat', '.ps1',

    # Веб-файлы
    '.html', '.htm', '.css', '.json', '.xml', '.yaml', '.yml', '.md', '.markdown', '.rst', '.json5', '.toml',

    # Текстовые документы
    '.txt', '.rtf', '.doc', '.docx', '.odt', '.tex', '.bib',

    # Таблицы
    '.csv', '.xls', '.xlsx', '.ods',

    # Презентации
    '.ppt', '.pptx', '.odp', '.key',

    # Конфигурационные и лог-файлы (текстовые)
    '.ini', '.cfg', '.conf', '.log', ''
]

def create_file_or_dir(filename):
    '''
    This function creates files or dirs.
    Support Windows and MacOs
    '''
    path = Path(filename)
    if path.suffix in non_creating_files or path.suffix not in safe_extensions:
        return 'Unsupported type of the file'

    if path.suffix:
        if path.exists():
            return 'You already have this file!'
        else:
            path.touch()
            return f'New file has been created successfully! {filename}'
    else:
        if path.exists():
            return 'You already have this directory!'
        else:
            path.mkdir()
            return f'New directory has been created successfully! {filename}'



def edit_file(filename):
    """
    This function edits FILES.
    Support Windows and MacOs.
    Returns 'text' you have inputed
    """
    path = Path(filename)
    all_text = []

    if '.' not in filename:
        raise NotFile(filename)

    else:
        
        def write():
            while True:
                qty_of_str = input('Please enter the quantity of strings: ')
                try:
                    qty_of_str = int(qty_of_str)
                    break
                except ValueError:
                    print('❌ This is not a number, try again.')

            for _ in range(qty_of_str):
                prompts = [
                    'Please write your text: ',
                    'Enter your text: ',
                    "Don’t be slow, write faster! ",
                    "Don’t be shy, nobody will see this! ",
                    "Write down something! "
                ]
                text_for_input = prompts[randint(0, len(prompts) - 1)]
                text = input(text_for_input)
                all_text.append(text)
                with open(filename, 'a', encoding='utf-8') as file:
                    file.write(text + '\n')

            print('✅ All text was written successfully!')

        if not path.exists():
            create_file_or_dir(filename=filename)

        write()

 


def read_file(filename):
    '''
    This function reads FILES.
    Support Windows and MacOs.
    '''
    path = Path(filename)
    all_text = []

    if '.' not in filename:
        raise NotFile(filename)
    
    else:
        
        def read():
            with open(filename) as file:
                lines = file.readlines()
                print(f'Reading {filename}...')
                print()
                for line in lines:
                    clean_line = line.strip()
                    print(clean_line)
                    all_text.append(clean_line)
                print()
                print('End of the file.')

        

        if not path.exists():
            create_file_or_dir(filename=filename)
            return

        read()
    return all_text


def delete_file(filename):
    '''
    You can easily delete files using this function.
    But if there is no file, there will be error.
    Please use try/except block!!!
    Support Windows and MacOs.
    '''
    path = Path(filename)

    if not path.exists():
        raise NoFile(filename=filename)

    if '.' in filename:
        path.unlink()
        print(f'{filename} was successfully deleted!')
        return

    else:
        path.rmdir()
        print(f"{filename} was successfully deleted!")
        return
    
my_name = 'Daniil'

# Turn apps

YOUR_OS = platform.system()
if YOUR_OS == 'Windows':
    def turn_vs_code(sec=0):
        """
        Turn on VS Code.
        Waits `sec` seconds and then launches VS Code.
        Works on any computer if 'code' is in PATH.
        Suppor Windows and MacOs.
        """
        if not isinstance(sec, int):
            sec = 0
        try:
            if YOUR_OS == 'Windows':
                import shutil

                code = shutil.which("code")
                if code is None:
                    raise NoCodePath()
                time.sleep(sec)
                subprocess.run([code])
            elif YOUR_OS == 'Darwin':
                subprocess.run(['open', '-a', "Visual Studio Code"])
        except Exception as e:
            print("Error:", e)


def turn_excel_or_numbers(sec=0):
    '''
    Turn on Microsoft Excel or Numbers.
    Waits `sec` seconds and then launches Microsoft Excel or Numbers.
    Support Windows and MacOs.
    '''
    if not isinstance(sec, int):
        sec = 0
    time.sleep(sec)
    try:
        if YOUR_OS == 'Windows':
            subprocess.run(["start", "excel"], shell=True)
        elif YOUR_OS == 'Darwin':
            subprocess.run(["open", "-a", "Numbers"])

    except Exception as e:
        print('Error:', e)

def turn_word_or_pages(sec=0):
    '''
    Turn on Microsoft Word or Pages.
    Waits `sec` seconds and then launches Microsoft Word or Pages.
    Support Windows and MacOs.
    '''
    if not isinstance(sec, int):
        sec = 0
    time.sleep(sec)
    try:
        if YOUR_OS == 'Windows':
            subprocess.run(["start", "winword"], shell=True)
        elif YOUR_OS == 'Darwin':
            subprocess.run(['open', '-a' "Pages"])

    except Exception as e:
        print('Error:', e)

def turn_powerpoint_or_keynote(sec=0):
    '''
    Turn on Microsoft PowerPoint or Keynote.
    Waits `sec` seconds and then launches Microsoft PowerPoint or KeyNote.
    Support only Windows.
    '''
    if not isinstance(sec, int):
        sec = 0
    time.sleep(sec)
    try:
        if YOUR_OS == 'Windows':
            subprocess.run(["start", "powerpnt"], shell=True)
        elif YOUR_OS == 'Darwin':
            subprocess.run(['open', '-a', 'Keynote'])
            return

    except Exception as e:
        print('Error:', e)

def turn_google_or_safari(sec=0):
    '''
    Turn on Google or Safari.
    Waits `sec` seconds and then launches Google or Safari.
    Support Windows and MacOs.
    '''
    if not isinstance(sec, int):
        sec = 0

    time.sleep(sec)
    try:
        if YOUR_OS == 'Windows':
            subprocess.run(['start', 'chrome'], shell=True)

        elif YOUR_OS == 'Darwin':
            subprocess.run(['open', '-a', "Safari"]) 

    except Exception as e:
        print('Error:', e)

def turn_notepad_or_textedit(sec=0):
    '''
    Turn on notepad or Textedit.
    Waits `sec` seconds and then launches notepad or Textedit.
    Support Windows and MacOs.
    '''
    if not isinstance(sec, int):
        sec = 0

    time.sleep(sec)
    try:
        if YOUR_OS == 'Windows':
            subprocess.run(['start', 'notepad'], shell=True)

        elif YOUR_OS == 'Darwin':
            subprocess.run(['open', '-a', "TextEdit"]) 

    except Exception as e:
        print('Error:', e)



# Create ZipFile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

def create_zipfile(filename):
    """
    Create zipfile from file or directory.
    If the file/directory does not exist, it creates it automatically.
    The original file or folder remains after archiving.
    Works on Windows and macOS.
    """

    path = Path(filename)

    
    create_file_or_dir(filename)  

    
    if not path.exists():
        print(f'❌ Не удалось создать файл/директорию: {filename}')
        return

    
    zip_name = f"{path.stem}.zip" if path.is_file() else f"{path.name}.zip"

    with ZipFile(zip_name, 'w', compression=ZIP_DEFLATED) as zipf:
        if path.is_file():
            zipf.write(path, arcname=path.name)
        elif path.is_dir():
            for file in path.rglob('*'):
                zipf.write(file, arcname=file.relative_to(path))

    print(f'✅ Zip-файл создан: {zip_name}')



def write_csv(filename, sep=','):
    path = Path(filename)

    
    if path.suffix != '.csv':
        print("Error: file must be a CSV!")
        return
    
    if not path.exists():
        create_file_or_dir(filename)


    
    with open(path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=sep)

        
        while True:
            num = input("Please enter the quantity of rows: ")
            try:
                num = int(num)
                break
            except Exception:
                print("❌ This is not a number. Try again.")

        for _ in range(num):
            text = input('Enter the text (separate phrases with "space"): ')
            
            words = [w for w in text.split() if w.strip()]
            if words:  
                writer.writerow(words)



def read_csv(filename):
    path = Path(filename)

    if path.suffix != '.csv':
        print("Error: file must be a CSV!")
        return
    
    if not path.exists():
        create_file_or_dir(filename)

    with open(filename) as csv_file:
        reader_for_text = csv.reader(csv_file)
        all_text = list(reader_for_text)
        
        print('Start of the file:')
        print()
        for line in all_text:
            print(line)

        print()
        print('End of the file!')

        

    return all_text



    



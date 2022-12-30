import os
import shutil
import db
import tkinter as tk
from tkinter import filedialog as fd
from time import sleep

win = tk.Tk()
win.withdraw()

cwd = os.path.join(os.getcwd(), 'Folders')
folders = {'Active': os.path.join(cwd, 'Active'),
           'Store': os.path.join(os.getcwd(), 'Folders', 'Store'),
           'Video': ['Video'],
           'Assets': ['Assets'],
           'Music': ['Assets', 'Music'],
           'SFX': ['Assets', 'SFX'],
           'Sprites': ['Assets', 'Sprites'],
           'VFX': ['Assets', 'VFX'],
           'Free': ['Free']}
trash_folder = os.path.join(folders['Store'], 'Trash')
if not os.path.exists(trash_folder):
    os.makedirs(trash_folder)
asset_type = {'sf': 'SFX', 'mu': 'Music', 'sp': 'Sprites', 'vf': 'VFX', 'vi': 'Video', 'f': 'Free'}

"""     COMMANDS
            crp - creates new project
            dlp - deletes a project
            dla - deletes asset from project
            dlu - deletes user
            crap- creates asset
            clap- loads asset
            ga  - gets attribution
            rma - removes asset
            lp  - loads project
            atd - adds asset to database
            dtp - gets asset from database into project
            """


def copyfile(source, destination):
    try:
        shutil.copy(source, destination)
        print("File moved")
    except shutil.SameFileError:
        print("Source and destination are the same")
    except PermissionError as e:
        print("Needs permission: ", e)
    except Exception as e:
        print("Error: ", e)


def resetActiveFolder():
    if not os.path.exists(folders['Active']):
        os.makedirs(folders['Active'])
    else:
        shutil.rmtree(folders['Active'], ignore_errors=True)
        os.makedirs(folders['Active'])

    for folder in folders:

        if folder in ('Active', 'Store', 'Free'):
            continue

        path = os.path.join(cwd, 'Active')
        for f in folders[folder]:
            path = os.path.join(path, f)

        if not os.path.exists(path):
            os.makedirs(path)

    fp = open(os.path.join(folders['Active'], 'Script.txt'), 'w')
    fp.close()


def deleteDirectory(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
        print(f"Successfully Deleted {path}")
        if os.path.exists(path):
            print(f"Could not delete {path}")
        else:
            print(f"Successfully Deleted {path}")
    else:
        print("Path does not exit")


def deleteFile(path):
    if os.path.exists(path):
        shutil.move(path, trash_folder)
        shutil.rmtree(trash_folder, ignore_errors=True)
        os.makedirs(trash_folder)
        if os.path.exists(path):
            print(f"Could not delete {path}")
        else:
            print(f"Successfully Deleted {path}")
    else:
        print("Path does not exit")


def restart(old):
    del old
    proj = ProjectOrganiser()
    proj.db.cursor.close()


class Project:
    def __init__(self, id, name, desc=''):
        self.id = id
        self.name = name
        self.desc = desc
        self.assets = {}
        self.path = os.path.join(folders['Store'], 'Projects', id)
        self.createFiles()

    def createFiles(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            os.makedirs(os.path.join(self.path, "Assets"))
            os.makedirs(os.path.join(self.path, "Video"))

        for folder in folders:

            if folder in ['Active', 'Store']:
                continue

            path = self.path
            for f in folders[folder]:
                path = os.path.join(path, f)

            if not os.path.exists(path):
                os.makedirs(path)

    def getAssetID(self):
        ids = []
        for asset in self.assets:
            asst = self.assets[asset]
            ids.append((asst.id, asst.gp))
        return ids


class Asset:
    def __init__(self, id, master, name, type, description, attribution=None, gp='p'):
        self.id = id
        self.name = name
        self.master = master
        self.file_ext = self.name.split('.')[-1]
        self.type = type
        self.desc = description
        self.attr = attribution
        self.gp = gp
        self.path = self.setPath()

    def setPath(self):
        path = ''
        if self.gp == 'g':
            path = os.path.join(folders['Store'], 'Assets', self.type, f'{self.id}.{self.file_ext}')
        elif self.gp == 'p':
            path = os.path.join(folders['Store'], 'Projects', self.master.id)
            for f in folders[self.type]:
                path = os.path.join(path, f)
            path = os.path.join(path, f"{self.id}.{self.file_ext}")
        return path


class ProjectOrganiser:
    def __init__(self):
        self.projects = {}
        self.activeProject = None
        self.assets = {}
        self.all_assets = {}

        self.db = db.DataBase()
        if not self.db.connected:
            print("\n\nDatabase connection failed\n\n")
            return
        self.user = self.login()

        self.loadProjects()
        self.loop()

    def login(self):
        while 1:
            username = input("\nWhat is your username? >")
            user = self.db.checkUser(username)

            if self.db.checkUser(username) is not None:
                print(f"\nWelcome {user[0]}\n")
                return user
            else:
                yn = input("\nWould you like to create an account? (y/n) \n>")
                if yn == 'y':
                    user = self.db.createUser(username)
                    print(f"\nWelcome {user[0]}\n")
                    return user
                else:
                    continue

    def deleteUser(self):
        y_n = input(f'ARE YOU SURE YOU WANT TO DELETE {self.user[0]}?!?! \nIT IS IRREVERSIBLE(y/n)> ')
        if y_n != 'y':
            return

        prjs = dict(self.projects)
        success = self.db.deleteUser(self.user[1])
        if not success:
            return

        for project in prjs:
            self.deleteProject(prjs[project].name)
        restart(self)

    def loadProjects(self):
        resetActiveFolder()
        projects = self.db.loadProjects(self.user[1])

        if projects is None:
            return

        if len(projects) < 1:
            print("\nNo projects available, creating one now\n")
            self.createProject(input("Give it a name > "))

        for project in projects:

            prj = Project(project[0], project[1], project[2])
            self.projects[prj.name] = prj

            self.activeProject = prj

        self.loadAssets()
        print(f"\nProjects loaded successfully \nAvailable Projects: {[x for x in self.projects]} \n"
              f"Active Project: {self.activeProject.name}")

        sleep(2)
        os.system('cls')

    def loadProject(self, name):
        if name not in self.projects:
            print(f"\nProject [{name}] is not in the database")
            return

        self.activeProject = self.projects[name]

        resetActiveFolder()
        self.loadAssets()

        sleep(2)
        os.system('cls')

    def createProject(self, name):
        resetActiveFolder()
        desc = input('\nWanna add a description?> ')
        id = self.db.createProject(name, self.user[1], desc)

        if id is None:
            return

        self.projects[name] = Project(id, name)
        self.activeProject = self.projects[name]

        sleep(2)
        os.system('cls')

    def deleteProject(self, name):
        if name not in self.projects:
            print(f"\nProject [{name}] is not in the database")
            return

        proj = self.projects[name]
        success = self.db.deleteProject(proj.id, proj.getAssetID())
        if not success:
            return
        self.projects.pop(name)
        deleteFile(proj.path)

        sleep(2)
        os.system('cls')

    def loadAssets(self):
        if len(self.projects) < 1:
            return

        all_assets = self.db.getAssets(self.activeProject.id)
        if all_assets is None:
            return

        personal, general, all_general = all_assets[0], all_assets[1], all_assets[2]

        for asset in general:
            asst = Asset(asset[0], self.activeProject, asset[1], asset[2], asset[3], asset[4], 'g')
            name = asset[1]
            if asset[1] not in self.activeProject.assets:
                self.activeProject.assets[asset[1]] = asst
            else:
                i = 0
                while 1:
                    name = asset[1].split('.')
                    name = f"{name[0]}[{i}].{name[1]}"
                    if name not in self.activeProject.assets:
                        self.activeProject.assets[name] = asst
                        break
                    else:
                        i += 1
            file_ext = asset[1].split('.')[-1]

            source = os.path.join(folders['Store'], 'Assets', asset[2], f"{asset[0]}.{file_ext}")

            dest = os.path.join(folders['Active'])
            for f in folders[asset[2]]:
                if asset[2] == 'Free':
                    continue
                elif asset[2] == 'Video':
                    dest = os.path.join(dest, 'Video')
                else:
                    dest = os.path.join(dest, f)
            dest = os.path.join(dest, name)
            copyfile(source, dest)

        for asset in personal:
            asst = Asset(asset[0], self.activeProject, asset[1], asset[2], asset[3], gp='p')
            name = asset[1]
            if asset[1] not in self.activeProject.assets:
                self.activeProject.assets[asset[1]] = asst
            else:
                i = 0
                while 1:
                    name = asset[1].split('.')
                    name = f"{name[0]}[{i}].{name[1]}"
                    if name not in self.activeProject.assets:
                        self.activeProject.assets[name] = asst
                        break
                    else:
                        i += 1

            file_ext = asset[1].split('.')[-1]

            source = os.path.join(folders['Store'], 'Projects', self.activeProject.id)
            for f in folders[asset[2]]:
                source = os.path.join(source, f)
            source = os.path.join(source, f"{asset[0]}.{file_ext}")

            dest = os.path.join(folders['Active'])
            for f in folders[asset[2]]:
                if asset[2] == 'Free':
                    continue
                else:
                    dest = os.path.join(dest, f)
            dest = os.path.join(dest, name)
            copyfile(source, dest)

        for asset in all_general:
            asst = Asset(asset[0], self.activeProject, asset[1], asset[2], asset[3], asset[4], 'g')
            self.all_assets[asset[1]] = asst

        sleep(2)
        os.system('cls')

    def addAsset(self):

        # Makes sure that there is a project available to avoid errors
        if len(self.projects) < 1:
            print("There is no project to import to")
            return

        # Gets the path of the file relative to the active folder
        path = input('\nPath to file >')
        active = folders['Active']
        path = path.split(',')

        for item in path:
            active = os.path.join(active, item)

        if not os.path.exists(active):
            print("\nFile Does not exist")
            return

        # Gets the type of file for database loading and saving
        type = self.getAssetType()

        while 1:
            gp = input("General or Personal (g,p) >")
            if gp in ('g', 'p'): break

        desc = input("\nDescription >")

        if gp == 'g':
            attr = input("\nAttribution >")
        else:
            attr = ""

        print(f'''\nPlease double check information \n
                    Name:       {path[-1]}  \n
                    Type:       {type} {gp}\n
                    Description:{desc}\n
                    Attribution:{attr}\n''')

        if input("(y/n)") != 'y':
            return

        id = self.db.addAsset(self.activeProject.id, path[-1], type, desc, attr, gp)

        if id is None:
            print('Could not add asset')
            return

        asst = Asset(id, self.activeProject, path[-1], type, desc, attr, gp)
        if path[-1] not in self.activeProject.assets:
            self.activeProject.assets[path[-1]] = asst
        else:
            i = 0
            while 1:
                name = path[-1].split('.')
                name = f"{name[0]}[{i}].{name[1]}"
                if name not in self.activeProject.assets:
                    self.activeProject.assets[name] = asst
                    break
                else:
                    i += 1

        file_ext = path[-1].split('.')[-1]
        dest = ''
        if gp == 'p':
            dest = os.path.join(folders['Store'],'Projects',self.activeProject.id)
            for f in folders[type]:
                dest = os.path.join(dest, f)
            dest = os.path.join(dest, f"{id}.{file_ext}")
        elif gp == 'g':
            dest = os.path.join(folders['Store'], 'Assets', type, f'{id}.{file_ext}')

        print(active)
        copyfile(active, dest)

        sleep(2)
        os.system('cls')

    def assetToDatabase(self):
        print("\nOpening dialogue")

        path = fd.askopenfilename()
        if not os.path.exists(path):
            return

        path = os.path.normpath(path)
        filename = os.path.basename(path)
        file_ext = filename.split('.')[-1]

        name = input("\nWant to change the name? >")
        if name == '':
            name = filename
        else:
            name = f"{name}.{file_ext}"
        type = self.getAssetType()
        desc = input("\nDescription:\n")
        attr = input("Attribution:\n")

        print(f'''\nPlease Confirm information
                  Name: {name}\n
                  Type: {type}\n
                  Desc: {desc}\n
                  Attr: {attr}\n''')
        y_n = input("(y/n)")
        if y_n != 'y':
            return

        id = self.db.importToDatabase(name, type, desc, attr)
        if id is None:
            return
        asst = Asset(id, self, name, type, desc, attr, 'g')
        savepath = asst.path
        del asst

        copyfile(path, savepath)
        print("Successfully added to database")

        sleep(2)
        os.system('cls')

    def databaseToProject(self):
        assets = self.db.get_general_assets()
        print("Available General Assets >", [x for x in assets])
        name = input("> ")
        if name not in assets:
            print(f"{name} not in general assets")
            return

        print(assets[name])
        asset_id = assets[name][1]
        type = assets[name][2]
        desc = assets[name][3]
        attr = assets[name][4]
        asst = Asset(asset_id, self, name, type, desc, attr, 'g')
        path = asst.path
        self.activeProject.assets[name] = asst

        success = self.db.importFromDatabase(asset_id, self.activeProject.id)
        if success is None:
            return

        dest = os.path.join(folders['Active'])
        for thing in folders[type]:
            dest = os.path.join(dest, thing)
        dest = os.path.join(dest, name)

        copyfile(path, dest)

        sleep(2)
        os.system('cls')

    def getAttribution(self):
        if len(self.projects) < 1:
            print("\n There are no projects available")
            return

        attr_path = os.path.join(folders['Active'], 'Attributions.txt')

        with open(attr_path, 'w', encoding='utf-8') as f:
            for asset in self.activeProject.assets:
                asst = self.activeProject.assets[asset]
                if asst.attr != 'None':
                    f.write(f'\n{asst.name} \n')
                    f.write(f'{asst.attr}\n\n')

    def deleteAsset(self, name):
        if name not in self.activeProject.assets:
            print(f"\n{name} not in Assets \n")
            return

        asst = self.activeProject.assets[name]
        success = self.db.deleteAsset(asst.id, asst.gp)
        if not success:
            return
        self.activeProject.assets.pop(name)
        deleteFile(asst.path)

        sleep(2)
        os.system('cls')

    def removeAsset(self, name):
        if name not in self.activeProject.assets:
            print(f"\n{name} not in Assets\n")
            return

        asst = self.activeProject.assets[name]

        success = self.db.removeAsset(asst.id, self.activeProject.id)
        if not success:
            return
        self.activeProject.assets.pop(name)

        sleep(2)
        os.system('cls')

    def getAssetType(self):
        while 1:
            type = input('\nFile type (mu,sf, sp, vf,vi, f)>')
            if type in asset_type:
                return asset_type[type]

    def loop(self):
        while 1:
            command = input("\nCmd> ")

            if command == 'exit':
                break
            elif command == 'crp':
                prj = input("\nProject Name > ")
                self.createProject(prj)
            elif command == 'dlp':
                print([x for x in self.projects])
                name = input("Project Name > ")
                self.deleteProject(name)
            elif command == 'dla':
                print(self.activeProject.assets)
                name = input("Name > ")
                self.deleteAsset(name)
            elif command == 'dlu':
                y_n = input(f"\n Are you sure you want to delete User: {self.user[0]}?? (y/n)")
                if y_n == 'y':
                    self.deleteUser()
            elif command == 'crap':
                self.addAsset()
            elif command == 'clap':
                self.loadAssets()
            elif command == 'ga':
                self.getAttribution()
            elif command == 'rma':
                print(f'Available assets: ', [self.activeProject.assets[x].name for x in self.activeProject.assets if self.activeProject.assets[x].gp == 'g'])
                name = input("Asset name > ")
                self.removeAsset(name)
            elif command == 'lp':
                print(self.projects)
                prj = input("Project Name: > ")
                self.loadProject(prj)
            elif command == 'atd':
                self.assetToDatabase()
            elif command == 'dtp':
                self.databaseToProject()


if __name__ == '__main__':
    prog = ProjectOrganiser()

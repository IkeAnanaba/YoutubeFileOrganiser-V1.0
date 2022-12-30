import mysql.connector


class DataBase:
    def __init__(self):
        self.users = {}

        # Database initialisation functions
        self.connected = self.connect()

        if not self.connected:
            return

        self.getUsers()
        print(f"Available Profiles: {[x for x in self.users]}\n")

    def connect(self):
        try:
            self.dataB = mysql.connector.connect(host='localhost', user='Your_database_access_name', password='Your_database_password')
            self.cursor = self.dataB.cursor()
            self.cursor.execute('USE ytorganiserdb;')
            print("\n\nSuccessfully connected to Database")
            return True
        except Exception as e:
            print(f"Could not connect due to Error > {e}")
            return False

    def getUsers(self):
        try:
            self.cursor.execute("SELECT BIN_TO_UUID(user_id) user_id, user_name FROM accnt;")
            users = self.cursor.fetchall()

            for user in users:
                self.users[user[1]] = user[0]

            print("\nUsers acquired \n\n")
        except Exception as e:
            print(f"Could not get users due to Error > {e}")

    def checkUser(self, username):
        if username in self.users:
            return username, self.users[username]
        return None

    def createUser(self, username):
        try:
            self.cursor.execute('SELECT UUID();')
            id = self.cursor.fetchall()[0][0]
            self.cursor.execute(f'''INSERT INTO accnt (user_id, user_name) 
                                    VALUES (UUID_TO_BIN('{id}'), "{username}");''')
            self.cursor.execute('COMMIT;')
            self.users[username] = id

            print(f"User created successfully")

            return username, id
        except Exception as e:
            print(f"Could not create user due to exception: {e}")
            return None

    def deleteUser(self, id):
        try:
            self.cursor.execute(f''' DELETE FROM accnt WHERE user_id = UUID_TO_BIN('{id}') ;''')
            self.cursor.execute('commit;')
            return True
        except Exception as e:
            print(f"Could not delete user due to exception: {e}")
            return False

    def loadProjects(self, id):
        try:
            self.cursor.execute(f'''SELECT BIN_TO_UUID(project_id) project_id, project_name, descript, isActive
                                    FROM project 
                                    WHERE BIN_TO_UUID(user_id) = '{id}';''')
            projects = self.cursor.fetchall()
            return projects
        except Exception as e:
            print(f"Could not load projects due to exception: {e}")
            return None

    def createProject(self, name, id, desc):
        try:
            self.deactivateProjects()
            self.cursor.execute('SELECT UUID();')
            proj_id = self.cursor.fetchone()[0]
            self.cursor.execute(f''' INSERT INTO project 
                                     (project_id, user_id, project_name, descript, date_created, isActive)
                                     VALUES 
                                     (UUID_TO_BIN('{proj_id}'),UUID_TO_BIN('{id}'),'{name}', '{desc}', CURDATE(),TRUE);
                                ''')
            self.cursor.execute('COMMIT;')
            self.cursor.fetchone()

            return proj_id
        except Exception as e:
            print(f"Could not load projects due to exception: {e}")
            return None

    def deleteProject(self, proj_id, assets):
        try:
            for asset in assets:
                self.deleteAsset(asset[0], asset[1])
            self.cursor.execute(f'''DELETE FROM project WHERE BIN_TO_UUID(project.project_id) = '{proj_id}';''')
            self.cursor.execute('COMMIT;')
            return True
        except Exception as e:
            print(f"Could not delete projects due to exception: {e}")
            return False

    def deactivateProjects(self):
        try:
            self.cursor.execute(f''' UPDATE project SET isActive = FALSE ''')
            self.cursor.execute('commit')
            return True
        except Exception as e:
            print(f"Could not deactivate projects due to exception: {e}")
            return False

    def getAssets(self, project_id):
        print(f"Getting assets for : {project_id}\n")
        try:
            self.cursor.execute(f'''SELECT BIN_TO_UUID(asset_id), asset_name, asset_type, descript
                                    FROM asset 
                                    WHERE BIN_TO_UUID(project_id) = '{project_id}' ;''')
            personal = self.cursor.fetchall()
            self.cursor.execute(f'''SELECT  BIN_TO_UUID(general_asset.asset_id) , asset_name, asset_type, descript,
                                    attribution
                                    FROM general_asset
                                    INNER JOIN asset_project 
                                    ON asset_project.asset_id = general_asset.asset_id
                                    WHERE asset_project.project_id = UUID_TO_BIN('{project_id}') ;''')
            general = self.cursor.fetchall()
            self.cursor.execute(f'''SELECT BIN_TO_UUID(asset_id), asset_name, asset_type, descript, attribution
                                    from general_asset''')
            all = self.cursor.fetchall()
            return personal, general, all
        except Exception as e:
            print(f"Could not load assets due to exception: {e}")
            return None

    def addAsset(self, project_id, name, type, desc, attr, gp):
        try:
            self.cursor.execute('SELECT UUID();')
            asset_id = self.cursor.fetchone()[0]
            query_map = {'g': [f'''INSERT INTO general_asset
                                  VALUES ( UUID_TO_BIN('{asset_id}'), '{name}', '{type}', '{desc}', '{attr}');''',
                               f'''INSERT INTO asset_project 
                                  VALUES(UUID_TO_BIN('{asset_id}'),UUID_TO_BIN('{project_id}'));'''],

                         'p': [f'''INSERT INTO asset
                                  VALUES ( UUID_TO_BIN('{asset_id}'), UUID_TO_BIN('{project_id}'),
                                  '{name}', '{type}', '{desc}' );''']}

            for query in query_map[gp]:
                self.cursor.execute(query)
                self.cursor.execute('COMMIT;')
            return asset_id
        except Exception as e:
            print(f"Could not add asset due to exception: {e}")
            return None

    def deleteAsset(self, id, gp):
        try:
            if gp == 'p':
                self.cursor.execute(f"DELETE from asset WHERE BIN_TO_UUID(asset.asset_id) = '{id}';")
                self.cursor.execute('COMMIT;')
                print(f"Successfully Deleted {id} from database")
                return True
            elif gp == 'g':
                self.cursor.execute(f"DELETE from asset_project WHERE BIN_TO_UUID(asset_project.asset_id) = '{id}'; ")
                self.cursor.execute(f"DELETE from general_asset WHERE BIN_TO_UUID(general_asset.asset_id) = '{id}'; ")
                self.cursor.execute('COMMIT;')
                print(f"Successfully Deleted {id} from database")
                return True
        except Exception as e:
            print("Could not delete Asset because of error: ", e)
            return False

    def removeAsset(self, asset_id, project_id):
        try:
            self.cursor.execute(f'''DELETE FROM asset_project
                                    WHERE BIN_TO_UUID(asset_project.asset_id) = '{asset_id}'
                                    AND BIN_TO_UUID(asset_project.project_id) = '{project_id}' ''')
            self.cursor.execute('COMMIT;')
            print(f'\nRemoved {asset_id} from {project_id} successfully\n')
            return True
        except Exception as e:
            print("Could not remove asset from this project due to exception ", e)
            return False

    def importToDatabase(self, name, type, desc, attr):
        try:
            self.cursor.execute('SELECT UUID();')
            asset_id = self.cursor.fetchone()[0]
            self.cursor.execute(f'''INSERT INTO general_asset
                                  VALUES ( UUID_TO_BIN('{asset_id}'), '{name}', '{type}', '{desc}', '{attr}');''')
            self.cursor.execute('COMMIT;')
            return asset_id
        except Exception as e:
            print(f"Could not add asset due to exception: {e}")
            return None

    def importFromDatabase(self, asset_id, project_id):
        try:
            self.cursor.execute(f''' INSERT INTO asset_project (asset_id, project_id)
                                     VALUES ( UUID_TO_BIN('{asset_id}'), UUID_TO_BIN('{project_id}') )''')
            self.cursor.execute("COMMIT;")
            print("Imported successfully")
            return True
        except Exception as e:
            print(f"Could not import asset due to exception: {e}")
            return None

    def get_general_assets(self):
        try:
            self.cursor.execute(f"SELECT asset_name, BIN_TO_UUID(asset_id), asset_type, descript, attribution "
                                f"from general_asset")
            assets = self.cursor.fetchall()
            all_assets = {}
            for asset in assets:
                all_assets[asset[0]] = asset
            return all_assets
        except Exception as e:
            print(f"Could not get the general assets dur to exception: {e}")
            return None
